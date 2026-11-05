from app.providers.base import LLMReply


class FakeProvider:
    """Provedor de teste: devolve respostas roteirizadas, sem rede."""

    def __init__(self, script: list[LLMReply]):
        self.script = list(script)
        self.calls: list[dict] = []

    def chat(self, messages, tools=None) -> LLMReply:
        self.calls.append({"messages": [dict(m) for m in messages], "tools": tools})
        if not self.script:
            return LLMReply(text="[SEM_BASE]")
        return self.script.pop(0)
