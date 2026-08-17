import asyncio
import uuid

import pytest

import brand_voice.graph as graph
from brand_voice.prompts import AUDIT_SYSTEM_PROMPT, REWRITE_SYSTEM_PROMPT


def test_audit_node_returns_audit_output(monkeypatch):
    async def fake_call(system_prompt, user_prompt, temperature, top_p=0.1):
        return {"compliance_score": 75, "grade": "C"}

    monkeypatch.setattr(graph, "call_json_agent", fake_call)
    state = {
        "brand_voice_guidelines": "g", "content_type": "email", "content_to_review": "c",
    }
    result = asyncio.run(graph.audit_node(state))
    assert result == {"audit_output": {"compliance_score": 75, "grade": "C"}}


def test_audit_node_raises_on_missing_compliance_score(monkeypatch):
    async def fake_call(system_prompt, user_prompt, temperature, top_p=0.1):
        return {"grade": "C"}  # no compliance_score

    monkeypatch.setattr(graph, "call_json_agent", fake_call)
    state = {"brand_voice_guidelines": "g", "content_type": "email", "content_to_review": "c"}
    with pytest.raises(ValueError):
        asyncio.run(graph.audit_node(state))


def test_rewrite_node_returns_rewrite_output(monkeypatch):
    async def fake_call(system_prompt, user_prompt, temperature, top_p=0.1):
        return {"rewritten_content": "on-brand text"}

    monkeypatch.setattr(graph, "call_json_agent", fake_call)
    state = {"brand_voice_guidelines": "g", "content_type": "email", "content_to_review": "c"}
    result = asyncio.run(graph.rewrite_node(state))
    assert result == {"rewrite_output": {"rewritten_content": "on-brand text"}}


def test_rewrite_node_raises_on_missing_rewritten_content(monkeypatch):
    async def fake_call(system_prompt, user_prompt, temperature, top_p=0.1):
        return {"notes": "nothing to rewrite"}  # no rewritten_content

    monkeypatch.setattr(graph, "call_json_agent", fake_call)
    state = {"brand_voice_guidelines": "g", "content_type": "email", "content_to_review": "c"}
    with pytest.raises(ValueError):
        asyncio.run(graph.rewrite_node(state))


def test_run_brand_voice_check_merges_both_branches_without_swapping(monkeypatch):
    async def fake_call(system_prompt, user_prompt, temperature, top_p=0.1):
        if system_prompt == AUDIT_SYSTEM_PROMPT:
            return {"compliance_score": 88, "grade": "B"}
        assert system_prompt == REWRITE_SYSTEM_PROMPT
        return {"rewritten_content": "on-brand rewrite"}

    monkeypatch.setattr(graph, "call_json_agent", fake_call)

    result = asyncio.run(graph.run_brand_voice_check(
        brand_voice_guidelines="Be warm.",
        content_to_review="BUY NOW!!!",
        company_name="Acme",
        content_type="email",
    ))

    assert result["audit_output"] == {"compliance_score": 88, "grade": "B"}
    assert result["rewrite_output"] == {"rewritten_content": "on-brand rewrite"}
    assert result["company_name"] == "Acme"
    # a real, freshly generated run id, not a placeholder
    assert uuid.UUID(result["generation_run_id"])
