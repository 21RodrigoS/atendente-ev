import json
import time

import httpx

from app.providers.base import LLMReply, LLMUnavailable, ToolCall

MAX_WAIT_SECONDS = 30.0


class OpenAICompatProvider:
    """Fala o formato OpenAI; serve para Groq, Gemini e outros só trocando as variáveis."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        client: httpx.Client | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        sleep=time.sleep,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=timeout)
        self.retries = retries
        self.sleep = sleep

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply:
        body: dict = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            body["tools"] = tools
        resp = None
        for attempt in range(self.retries + 1):
            try:
                resp = self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=body,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            except httpx.HTTPError as exc:
                raise LLMUnavailable(str(exc)) from exc
            if resp.status_code != 429 and resp.status_code < 500:
                break
            wait = self._wait(resp, attempt)
            if wait > MAX_WAIT_SECONDS:  # ex.: cota diária esgotada; esperar não compensa
                break
            if attempt < self.retries:  # limite por minuto do plano grátis: espera e tenta de novo
                self.sleep(wait)
        if resp.status_code == 429 or resp.status_code >= 500:
            raise LLMUnavailable(f"status {resp.status_code}")
        if resp.status_code >= 400:
            raise LLMUnavailable(f"erro do provedor: status {resp.status_code}")
        try:  # resposta fora do formato (inclusive argumentos que não são JSON) vira falha tratada
            message = resp.json()["choices"][0]["message"]
            calls = [
                ToolCall(
                    id=c["id"],
                    name=c["function"]["name"],
                    arguments=json.loads(c["function"].get("arguments") or "{}"),
                )
                for c in message.get("tool_calls") or []
            ]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise LLMUnavailable("resposta inesperada do provedor") from exc
        return LLMReply(text=message.get("content"), tool_calls=calls)

    @staticmethod
    def _wait(resp: httpx.Response, attempt: int) -> float:
        try:
            return float(resp.headers["retry-after"])
        except (KeyError, ValueError):
            return 2.0 * (attempt + 1)
