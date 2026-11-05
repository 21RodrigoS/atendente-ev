from app.config import Settings
from app.providers.base import LLMProvider
from app.providers.openai_compat import OpenAICompatProvider


def build_provider(settings: Settings) -> LLMProvider:
    return OpenAICompatProvider(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
