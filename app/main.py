from fastapi import FastAPI

from app.config import Settings, get_settings


def create_app(settings: Settings | None = None, provider=None, embedder=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Atendente E&V")
    app.state.settings = settings

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
