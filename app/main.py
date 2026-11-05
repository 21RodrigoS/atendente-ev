from collections.abc import Iterator
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.agent import Agent
from app.config import Settings, get_settings
from app.db import Message, Order, OrderItem, Product, init_db, make_engine, seed_products
from app.providers import build_provider
from app.rag.index import load_index
from app.ratelimit import RateLimiter

ROOT = Path(__file__).resolve().parent.parent


class ChatIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str


def create_app(settings: Settings | None = None, provider=None, embedder=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Atendente E&V")
    app.state.settings = settings

    engine = make_engine(settings.db_url)
    init_db(engine)
    SessionLocal = sessionmaker(engine, expire_on_commit=False)
    with SessionLocal() as db:
        seed_products(db, ROOT / "data" / "products.json")

    if embedder is None:
        from app.rag.embedder import FastEmbedder

        embedder = FastEmbedder()
    agent = Agent(provider or build_provider(settings), load_index(ROOT / "knowledge", embedder))
    limiter = RateLimiter(settings.rate_limit_per_minute)

    def get_db() -> Iterator[Session]:
        with SessionLocal() as db:
            yield db

    def admin_only(x_admin_token: str | None = Header(default=None)) -> None:
        if not settings.admin_token or x_admin_token != settings.admin_token:
            raise HTTPException(status_code=401, detail="token inválido")

    def handle_message(db: Session, session_id: str, text: str):
        result = agent.answer(db, session_id, text)
        sources = ",".join(result.sources)
        db.add(Message(session_id=session_id, role="user", content=text, grounded=result.grounded))
        db.add(
            Message(
                session_id=session_id,
                role="assistant",
                content=result.text,
                grounded=result.grounded,
                sources=sources,
            )
        )
        db.commit()
        return result

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def simulator():
        return FileResponse(ROOT / "web" / "index.html")

    @app.get("/admin", include_in_schema=False)
    def admin_page():
        return FileResponse(ROOT / "web" / "admin.html")

    @app.post("/chat")
    def chat(body: ChatIn, request: Request, db: Session = Depends(get_db)):
        text = body.message.strip()
        if not text or len(text) > settings.max_message_chars:
            raise HTTPException(
                status_code=422,
                detail=f"a mensagem deve ter entre 1 e {settings.max_message_chars} caracteres",
            )
        if not limiter.allow(request.client.host if request.client else "unknown"):
            raise HTTPException(status_code=429, detail="muitas mensagens, tente em instantes")
        result = handle_message(db, body.session_id, text)
        return {"reply": result.text, "sources": result.sources, "grounded": result.grounded}

    @app.get("/webhook/whatsapp", response_class=PlainTextResponse)
    def webhook_verify(
        mode: str = Query("", alias="hub.mode"),
        token: str = Query("", alias="hub.verify_token"),
        challenge: str = Query("", alias="hub.challenge"),
    ):
        if mode != "subscribe" or not settings.admin_token or token != settings.admin_token:
            raise HTTPException(status_code=403, detail="verificação falhou")
        return challenge

    @app.post("/webhook/whatsapp")
    def webhook_receive(payload: dict, request: Request, db: Session = Depends(get_db)):
        try:
            msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
            session_id, text = str(msg["from"]), str(msg["text"]["body"]).strip()
        except (KeyError, IndexError, TypeError):
            return {"status": "ignored"}
        if not text or len(text) > settings.max_message_chars:
            return {"status": "ignored"}
        if not limiter.allow(session_id):
            return {"status": "rate_limited"}
        handle_message(db, session_id, text)  # envio real de volta ao WhatsApp: fora do escopo
        return {"status": "ok"}

    @app.get("/admin/messages", dependencies=[Depends(admin_only)])
    def admin_messages(db: Session = Depends(get_db)):
        rows = db.scalars(select(Message).order_by(Message.id.desc()).limit(100)).all()
        return [_message_dict(m) for m in reversed(rows)]

    @app.get("/admin/unanswered", dependencies=[Depends(admin_only)])
    def admin_unanswered(db: Session = Depends(get_db)):
        rows = db.scalars(
            select(Message)
            .where(Message.role == "user", Message.grounded.is_(False))
            .order_by(Message.id.desc())
            .limit(100)
        ).all()
        return [_message_dict(m) for m in rows]

    @app.get("/admin/orders", dependencies=[Depends(admin_only)])
    def admin_orders(db: Session = Depends(get_db)):
        out = []
        for order in db.scalars(select(Order).order_by(Order.id.desc()).limit(100)):
            items = db.execute(
                select(Product, OrderItem.kg)
                .join(OrderItem, OrderItem.product_id == Product.id)
                .where(OrderItem.order_id == order.id)
            ).all()
            out.append(
                {
                    "id": order.id,
                    "session_id": order.session_id,
                    "created_at": order.created_at.isoformat(),
                    "total_cents": int(sum(p.price_cents * kg for p, kg in items)),
                    "items": [{"flavor": p.name, "kg": kg} for p, kg in items],
                }
            )
        return out

    return app


def _message_dict(m: Message) -> dict:
    return {
        "id": m.id,
        "session_id": m.session_id,
        "role": m.role,
        "content": m.content,
        "grounded": m.grounded,
        "sources": m.sources,
        "created_at": m.created_at.isoformat(),
    }
