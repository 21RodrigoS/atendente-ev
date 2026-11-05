from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.rag.embedder import HashEmbedder


def _client():
    return TestClient(create_app(Settings(db_url="sqlite://"), embedder=HashEmbedder()))


def test_root_serves_simulator():
    resp = _client().get("/")
    assert resp.status_code == 200
    assert "Atendente E&V" in resp.text


def test_admin_page_served():
    resp = _client().get("/admin")
    assert resp.status_code == 200
    assert "X-Admin-Token" in resp.text
