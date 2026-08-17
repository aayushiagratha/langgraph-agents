import asyncio

import pytest
from fastapi import HTTPException

import common.auth as auth


def test_missing_header_is_unauthorized(monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "secret123")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_api_key(x_api_key=""))
    assert exc.value.status_code == 401


def test_wrong_key_is_unauthorized(monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "secret123")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_api_key(x_api_key="wrong"))
    assert exc.value.status_code == 401


def test_correct_key_passes(monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "secret123")
    asyncio.run(auth.require_api_key(x_api_key="secret123"))  # raises nothing
