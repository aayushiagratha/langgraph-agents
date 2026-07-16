import logging

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from brand_voice.graph import run_brand_voice_check
from brand_voice.persist import persist_results
from common.auth import require_api_key
from common.openrouter import OpenRouterError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agents")

app = FastAPI(title="Brand Voice Guardian")


class BrandVoiceCheckRequest(BaseModel):
    brand_voice_guidelines: str
    content_to_review: str
    company_name: str = "unknown"
    content_type: str = "general"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/brand-voice-check", dependencies=[Depends(require_api_key)])
async def brand_voice_check(payload: BrandVoiceCheckRequest):
    missing = [
        field
        for field in ("brand_voice_guidelines", "content_to_review")
        if not getattr(payload, field, "").strip()
    ]
    if missing:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Missing required fields: {', '.join(missing)}"},
        )

    try:
        state = await run_brand_voice_check(
            brand_voice_guidelines=payload.brand_voice_guidelines,
            content_to_review=payload.content_to_review,
            company_name=payload.company_name,
            content_type=payload.content_type,
        )
        persist_results(
            generation_run_id=state["generation_run_id"],
            content_type=payload.content_type,
            audit_output=state["audit_output"],
            rewrite_output=state["rewrite_output"],
        )
        return {
            "status": "completed",
            "generation_run_id": state["generation_run_id"],
            "compliance_score": state["audit_output"]["compliance_score"],
            "grade": state["audit_output"].get("grade"),
            "audit_output": state["audit_output"],
            "rewrite_output": state["rewrite_output"],
        }
    except OpenRouterError as exc:
        logger.exception("OpenRouter call failed")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})
    except Exception as exc:  # noqa: BLE001 - mirrors n8n's catch-all Catch Response node
        logger.exception("Brand voice check failed")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Workflow execution failed. Please try again."},
        )
