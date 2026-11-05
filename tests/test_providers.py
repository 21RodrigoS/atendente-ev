import json

import httpx
import pytest

from app.providers.base import LLMUnavailable
from app.providers.openai_compat import OpenAICompatProvider


def _provider(handler, retries=0):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatProvider(
        "https://x.test/v1", "k", "m", client=client, retries=retries, sleep=lambda s: None
    )


def _ok(message):
    return httpx.Response(200, json={"choices": [{"message": message}]})


def test_parses_text_reply():
    reply = _provider(lambda r: _ok({"content": "olá"})).chat([{"role": "user", "content": "oi"}])
    assert reply.text == "olá"
    assert reply.tool_calls == []


def test_parses_tool_call():
    msg = {
        "content": None,
        "tool_calls": [
            {"id": "c1", "function": {"name": "get_price", "arguments": '{"flavor": "manga"}'}}
        ],
    }
    reply = _provider(lambda r: _ok(msg)).chat([], tools=[{"type": "function"}])
    assert reply.tool_calls[0].name == "get_price"
    assert reply.tool_calls[0].arguments == {"flavor": "manga"}
    assert reply.tool_calls[0].id == "c1"


def test_429_raises_unavailable():
    with pytest.raises(LLMUnavailable):
        _provider(lambda r: httpx.Response(429)).chat([])


def test_timeout_raises_unavailable():
    def boom(request):
        raise httpx.ReadTimeout("t")

    with pytest.raises(LLMUnavailable):
        _provider(boom).chat([])


def test_sends_bearer_and_model():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        seen["url"] = str(request.url)
        return _ok({"content": "ok"})

    _provider(handler).chat([{"role": "user", "content": "x"}])
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "m"
    assert seen["url"] == "https://x.test/v1/chat/completions"


def test_retries_429_then_succeeds():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(429, headers={"retry-after": "1"})
        return _ok({"content": "ok"})

    assert _provider(handler, retries=3).chat([]).text == "ok"
    assert len(calls) == 3


def test_gives_up_after_retries():
    with pytest.raises(LLMUnavailable):
        _provider(lambda r: httpx.Response(429), retries=2).chat([])


def test_does_not_wait_when_retry_after_is_long():
    waits = []
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(429, headers={"retry-after": "82"}))
    )
    provider = OpenAICompatProvider(
        "https://x.test/v1", "k", "m", client=client, retries=3, sleep=waits.append
    )
    with pytest.raises(LLMUnavailable):
        provider.chat([])
    assert waits == []  # espera de 82 s (cota diária) não vale a pena: falha rápido
