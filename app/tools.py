import unicodedata
from decimal import ROUND_DOWN, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Order, OrderItem, Product

MIN_KG, MAX_KG = 0.5, 20.0
CLUB_MIN_KG = 4.0
CLUB_DISCOUNT_PERCENT = 7


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


def find_product(session: Session, name: str) -> Product | None:
    wanted = normalize(name)
    for product in session.scalars(select(Product)):
        if normalize(product.slug) == wanted or normalize(product.name) == wanted:
            return product
    return None


def _valid_kg(kg) -> bool:
    return isinstance(kg, int | float) and not isinstance(kg, bool) and MIN_KG <= kg <= MAX_KG


def _total_cents(price_cents: int, kg: float, club: bool = False) -> int:
    total = Decimal(price_cents) * Decimal(str(kg))
    if club:
        total = total * (100 - CLUB_DISCOUNT_PERCENT) / 100
    return int(total.to_integral_value(rounding=ROUND_DOWN))


def get_price(session: Session, flavor: str, kg: float = 1.0, club: bool = False) -> dict:
    product = find_product(session, flavor)
    if product is None:
        return _err(f"sabor '{flavor}' não encontrado")
    if not _valid_kg(kg):
        return _err(f"quantidade deve ficar entre {MIN_KG} e {MAX_KG} kg")
    if club and kg < CLUB_MIN_KG:
        return _err(f"o clube exige no mínimo {CLUB_MIN_KG:g} kg")
    return {
        "ok": True,
        "flavor": product.name,
        "kg": kg,
        "total_cents": _total_cents(product.price_cents, kg, club),
    }


def check_availability(session: Session, flavor: str) -> dict:
    product = find_product(session, flavor)
    if product is None:
        return _err(f"sabor '{flavor}' não encontrado")
    return {"ok": True, "flavor": product.name, "in_stock": product.in_stock}


def create_order(session: Session, session_id: str, items: list[dict]) -> dict:
    if not items:
        return _err("pedido sem itens")
    resolved: list[tuple[Product, float]] = []
    for item in items:
        product = find_product(session, str(item.get("flavor", "")))
        kg = item.get("kg")
        if product is None:
            return _err(f"sabor '{item.get('flavor')}' não encontrado")
        if not _valid_kg(kg):
            return _err(f"quantidade deve ficar entre {MIN_KG} e {MAX_KG} kg")
        if not product.in_stock:
            return _err(f"{product.name} está sem estoque")
        resolved.append((product, kg))
    order = Order(session_id=session_id)
    session.add(order)
    session.flush()
    total = 0
    for product, kg in resolved:
        session.add(OrderItem(order_id=order.id, product_id=product.id, kg=kg))
        total += _total_cents(product.price_cents, kg)
    session.commit()
    return {"ok": True, "order_id": order.id, "total_cents": total}


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Preço total de um sabor para uma quantidade em kg (clube opcional).",
            "parameters": {
                "type": "object",
                "properties": {
                    "flavor": {"type": "string"},
                    "kg": {"type": "number"},
                    "club": {"type": "boolean"},
                },
                "required": ["flavor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Diz se um sabor está em estoque.",
            "parameters": {
                "type": "object",
                "properties": {"flavor": {"type": "string"}},
                "required": ["flavor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Registra um pedido. Só chamar depois que o cliente confirmar sabores e kg.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"flavor": {"type": "string"}, "kg": {"type": "number"}},
                            "required": ["flavor", "kg"],
                        },
                    }
                },
                "required": ["items"],
            },
        },
    },
]


def run_tool(session: Session, session_id: str, name: str, args: dict) -> dict:
    try:
        if name == "get_price":
            return get_price(session, **args)
        if name == "check_availability":
            return check_availability(session, **args)
        if name == "create_order":
            return create_order(session, session_id, **args)
    except TypeError:
        return _err("argumentos inválidos")
    return _err(f"ferramenta desconhecida: {name}")
