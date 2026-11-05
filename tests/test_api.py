import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.base import LLMReply, LLMUnavailable
from app.providers.fake import FakeProvider
from app.rag.embedder import HashEmbedder

TOKEN = "segredo"


def make_client(script=None, provider=None, **settings):
    cfg = Settings(db_url="sqlite://", admin_token=TOKEN, **settings)
    provider = provider or FakeProvider(script or [LLMReply(text="Olá! Como posso ajudar?")] * 20)
    return TestClient(create_app(cfg, provider=provider, embedder=HashEmbedder()))


def test_chat_ok_and_persists():
    client = make_client()
    resp = client.post("/chat", json={"session_id": "a", "message": "oi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "Olá! Como posso ajudar?"
    assert body["grounded"] is True
    msgs = client.get("/admin/messages", headers={"X-Admin-Token": TOKEN}).json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]


@pytest.mark.parametrize("message", ["", "   "])
def test_empty_message_422(message):
    resp = make_client().post("/chat", json={"session_id": "a", "message": message})
    assert resp.status_code == 422


def test_too_long_message_422():
    resp = make_client(max_message_chars=10).post(
        "/chat", json={"session_id": "a", "message": "x" * 11}
    )
    assert resp.status_code == 422


def test_rate_limit_429():
    client = make_client(rate_limit_per_minute=2)
    codes = [client.post("/chat", json={"session_id": "a", "message": "oi"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_webhook_parses_whatsapp_payload():
    client = make_client()
    payload = {
        "entry": [
            {
                "changes": [
                    {"value": {"messages": [{"from": "5571999990000", "text": {"body": "oi"}}]}}
                ]
            }
        ]
    }
    assert client.post("/webhook/whatsapp", json=payload).status_code == 200
    msgs = client.get("/admin/messages", headers={"X-Admin-Token": TOKEN}).json()
    assert msgs[0]["session_id"] == "5571999990000"
    assert msgs[0]["content"] == "oi"


def test_webhook_ignores_status_updates():
    client = make_client()
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"status": "read"}]}}]}]}
    resp = client.post("/webhook/whatsapp", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ignored"}


def test_webhook_verify_challenge():
    client = make_client()
    ok = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": TOKEN, "hub.challenge": "1234"},
    )
    assert ok.status_code == 200 and ok.text == "1234"
    bad = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "x", "hub.challenge": "1234"},
    )
    assert bad.status_code == 403


@pytest.mark.parametrize("path", ["/admin/messages", "/admin/orders", "/admin/unanswered"])
def test_admin_requires_token(path):
    client = make_client()
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"X-Admin-Token": "errado"}).status_code == 401


def test_unanswered_lists_ungrounded():
    client = make_client(script=[LLMReply(text="[SEM_BASE]")])
    client.post("/chat", json={"session_id": "a", "message": "quem ganhou o jogo?"})
    rows = client.get("/admin/unanswered", headers={"X-Admin-Token": TOKEN}).json()
    assert [r["content"] for r in rows] == ["quem ganhou o jogo?"]


def test_llm_down_still_200_with_fallback():
    class Down:
        def chat(self, messages, tools=None):
            raise LLMUnavailable("429")

    resp = make_client(provider=Down()).post("/chat", json={"session_id": "a", "message": "oi"})
    assert resp.status_code == 200
    assert resp.json()["grounded"] is False


def test_orders_endpoint_lists_created_orders():
    from app.providers.base import ToolCall

    script = [
        LLMReply(tool_calls=[ToolCall("c", "create_order", {"items": [{"flavor": "manga", "kg": 2}]})]),
        LLMReply(text="Pedido registrado!"),
    ]
    client = make_client(script=script)
    client.post("/chat", json={"session_id": "a", "message": "confirmo 2kg de manga"})
    orders = client.get("/admin/orders", headers={"X-Admin-Token": TOKEN}).json()
    assert orders[0]["total_cents"] == 2800
    assert orders[0]["items"] == [{"flavor": "Manga", "kg": 2.0}]


def test_admin_token_comparison_is_constant_time(monkeypatch):
    import app.main as main_module

    calls = []
    real = main_module.secrets.compare_digest
    monkeypatch.setattr(main_module.secrets, "compare_digest", lambda a, b: calls.append(1) or real(a, b))
    client = make_client()
    assert client.get("/admin/messages", headers={"X-Admin-Token": TOKEN}).status_code == 200
    assert calls
