from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    db_url: str = "sqlite:///data/atendente.db"
    rate_limit_per_minute: int = 20
    max_message_chars: int = 1000
    admin_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
