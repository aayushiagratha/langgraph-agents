import asyncio

import pytest

import common.openrouter as openrouter
from common.openrouter import OpenRouterError, call_json_agent


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


def make_fake_client(response, captured=None):
    """A stand-in for httpx.AsyncClient that returns `response` from .post()
    and, if `captured` is passed, records (url, headers, json) into it."""

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, headers=None, json=None):
            if captured is not None:
                captured["url"] = url
                captured["headers"] = headers
                captured["json"] = json
            return response

    return FakeAsyncClient


@pytest.fixture(autouse=True)
def restore_openrouter_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")


def test_call_json_agent_returns_parsed_json(monkeypatch):
    resp = FakeResponse(200, json_data={
        "choices": [{"message": {"content": '{"compliance_score": 91}'}}]
    })
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp))

    result = asyncio.run(call_json_agent("system", "user", temperature=0.1))
    assert result == {"compliance_score": 91}


def test_call_json_agent_non_200_raises(monkeypatch):
    resp = FakeResponse(500, text="server exploded")
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp))

    with pytest.raises(OpenRouterError):
        asyncio.run(call_json_agent("system", "user", temperature=0.1))


def test_call_json_agent_bad_response_shape_raises(monkeypatch):
    resp = FakeResponse(200, json_data={"unexpected": "shape"})
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp))

    with pytest.raises(OpenRouterError):
        asyncio.run(call_json_agent("system", "user", temperature=0.1))


def test_call_json_agent_invalid_json_content_raises(monkeypatch):
    resp = FakeResponse(200, json_data={
        "choices": [{"message": {"content": "not valid json"}}]
    })
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp))

    with pytest.raises(OpenRouterError):
        asyncio.run(call_json_agent("system", "user", temperature=0.1))


def test_call_json_agent_strips_bearer_prefix_from_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "Bearer sk-already-prefixed")
    resp = FakeResponse(200, json_data={
        "choices": [{"message": {"content": "{}"}}]
    })
    captured = {}
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp, captured))

    asyncio.run(call_json_agent("system", "user", temperature=0.1))
    assert captured["headers"]["Authorization"] == "Bearer sk-already-prefixed"


def test_call_json_agent_sends_model_and_provider_order(monkeypatch):
    resp = FakeResponse(200, json_data={
        "choices": [{"message": {"content": "{}"}}]
    })
    captured = {}
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", make_fake_client(resp, captured))

    asyncio.run(call_json_agent("sys-prompt", "user-prompt", temperature=0.2, top_p=0.5))
    assert captured["json"]["model"] == openrouter.MODEL
    assert captured["json"]["provider"]["order"] == openrouter.PROVIDER_ORDER
    assert captured["json"]["temperature"] == 0.2
    assert captured["json"]["top_p"] == 0.5
    assert captured["json"]["messages"][0] == {"role": "system", "content": "sys-prompt"}
