from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMReply:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMUnavailable(Exception):
    """Provedor fora do ar, estourou limite ou demorou demais."""


class LLMProvider(Protocol):
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply: ...
