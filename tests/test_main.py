import pytest
from fastapi.testclient import TestClient

import main as main_module
from common.openrouter import OpenRouterError

client = TestClient(main_module.app)

VALID_PAYLOAD = {"brand_voice_guidelines": "Be warm.", "content_to_review": "BUY NOW!!!"}


@pytest.fixture(autouse=True)
def webhook_key(monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "test-secret")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_api_key_is_401():
    r = client.post("/brand-voice-check", json=VALID_PAYLOAD)
    assert r.status_code == 401


def test_wrong_api_key_is_401():
    r = client.post("/brand-voice-check", headers={"x-api-key": "nope"}, json=VALID_PAYLOAD)
    assert r.status_code == 401


def test_missing_required_fields_is_400():
    r = client.post(
        "/brand-voice-check",
        headers={"x-api-key": "test-secret"},
        json={"brand_voice_guidelines": "", "content_to_review": ""},
    )
    assert r.status_code == 400
    assert "brand_voice_guidelines" in r.json()["message"]


def test_successful_check_returns_scores(monkeypatch):
    async def fake_run(**kwargs):
        return {
            "generation_run_id": "run-1",
            "audit_output": {"compliance_score": 90, "grade": "A"},
            "rewrite_output": {"rewritten_content": "on-brand"},
        }

    persisted = {}

    def fake_persist(**kwargs):
        persisted.update(kwargs)

    monkeypatch.setattr(main_module, "run_brand_voice_check", fake_run)
    monkeypatch.setattr(main_module, "persist_results", fake_persist)

    r = client.post("/brand-voice-check", headers={"x-api-key": "test-secret"}, json=VALID_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["compliance_score"] == 90
    assert body["grade"] == "A"
    assert persisted["generation_run_id"] == "run-1"


def test_openrouter_error_returns_500(monkeypatch):
    async def fake_run(**kwargs):
        raise OpenRouterError("upstream failed")

    monkeypatch.setattr(main_module, "run_brand_voice_check", fake_run)

    r = client.post("/brand-voice-check", headers={"x-api-key": "test-secret"}, json=VALID_PAYLOAD)
    assert r.status_code == 500
    assert "upstream failed" in r.json()["message"]


def test_unexpected_error_returns_generic_500_message(monkeypatch):
    async def fake_run(**kwargs):
        raise RuntimeError("something broke internally")

    monkeypatch.setattr(main_module, "run_brand_voice_check", fake_run)

    r = client.post("/brand-voice-check", headers={"x-api-key": "test-secret"}, json=VALID_PAYLOAD)
    assert r.status_code == 500
    # the raw exception text should NOT leak to the caller
    assert "something broke internally" not in r.text
