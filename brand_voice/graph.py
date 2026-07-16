import uuid
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from common.openrouter import call_json_agent
from .prompts import (
    AUDIT_SYSTEM_PROMPT,
    REWRITE_SYSTEM_PROMPT,
    audit_user_prompt,
    rewrite_user_prompt,
)


class BrandVoiceState(TypedDict, total=False):
    generation_run_id: str
    company_name: str
    content_type: str
    brand_voice_guidelines: str
    content_to_review: str
    audit_output: Optional[dict]
    rewrite_output: Optional[dict]


async def audit_node(state: BrandVoiceState) -> dict:
    result = await call_json_agent(
        system_prompt=AUDIT_SYSTEM_PROMPT,
        user_prompt=audit_user_prompt(
            state["brand_voice_guidelines"], state.get("content_type", ""), state["content_to_review"]
        ),
        temperature=0.1,
    )
    if not isinstance(result.get("compliance_score"), (int, float)):
        raise ValueError("Audit Agent: invalid schema — missing compliance_score")
    return {"audit_output": result}


async def rewrite_node(state: BrandVoiceState) -> dict:
    result = await call_json_agent(
        system_prompt=REWRITE_SYSTEM_PROMPT,
        user_prompt=rewrite_user_prompt(
            state["brand_voice_guidelines"], state.get("content_type", ""), state["content_to_review"]
        ),
        temperature=0.3,
    )
    if not result.get("rewritten_content"):
        raise ValueError("Rewrite Agent: invalid schema — missing rewritten_content")
    return {"rewrite_output": result}


def build_graph():
    graph = StateGraph(BrandVoiceState)
    graph.add_node("audit", audit_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_edge(START, "audit")
    graph.add_edge(START, "rewrite")
    graph.add_edge("audit", END)
    graph.add_edge("rewrite", END)
    return graph.compile()


_compiled_graph = build_graph()


async def run_brand_voice_check(
    brand_voice_guidelines: str,
    content_to_review: str,
    company_name: str = "unknown",
    content_type: str = "general",
) -> BrandVoiceState:
    initial_state: BrandVoiceState = {
        "generation_run_id": str(uuid.uuid4()),
        "company_name": company_name,
        "content_type": content_type,
        "brand_voice_guidelines": brand_voice_guidelines,
        "content_to_review": content_to_review,
    }
    final_state = await _compiled_graph.ainvoke(initial_state)
    return final_state
