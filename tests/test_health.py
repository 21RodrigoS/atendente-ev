from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_ok():
    client = TestClient(create_app(Settings(db_url="sqlite://")))
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
