# Brand Voice Guardian

A LangGraph port of an n8n agent workflow: give it your brand voice guidelines and a piece of content, and it returns a compliance audit and an on-brand rewrite in one call.

The original runs as an [n8n workflow](https://github.com/aayushiagratha/positionpilot). This is the same pipeline rebuilt as a FastAPI service, as the first step of moving the agents off n8n.

## How it works

Two agents run in parallel from a LangGraph `StateGraph`, both against the same input:

```
        ┌── audit ──┐
START ──┤           ├── END
        └── rewrite ┘
```

- **Audit** (temperature 0.1) scores compliance 0–100, grades it, and lists violations with severity, the offending text, and the guideline each one breaks.
- **Rewrite** (temperature 0.3) rewrites the content on-brand and explains each change.

The rewrite deliberately does not wait for the audit. Both see the raw content, so a slow audit never blocks the rewrite, and the rewrite isn't biased by the audit's findings.

Both results are written to Postgres as two rows sharing one `generation_run_id`.

## API

`POST /brand-voice-check` — requires an `X-API-Key` header matching `WEBHOOK_API_KEY`.

```json
{
  "brand_voice_guidelines": "Plain English. No jargon. Active voice.",
  "content_to_review": "We leverage synergies to drive outcomes.",
  "company_name": "acme",
  "content_type": "landing page"
}
```

`brand_voice_guidelines` and `content_to_review` are required; the other two default to `"unknown"` and `"general"`.

Returns `compliance_score` and `grade` at the top level for quick checks, with the full `audit_output` and `rewrite_output` underneath:

```json
{
  "status": "completed",
  "generation_run_id": "6f1c…",
  "compliance_score": 42,
  "grade": "D",
  "audit_output": { "violations": [ … ], "strengths": [ … ], "tone_analysis": { … } },
  "rewrite_output": { "rewritten_content": "…", "changes_made": [ … ] }
}
```

`GET /health` needs no auth.

## Setup

Environment variables — all required except `PGPORT` and `PUBLIC_URL`:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter key. A leading `Bearer ` is stripped if present. |
| `WEBHOOK_API_KEY` | Shared secret callers send as `X-API-Key`. |
| `PGHOST` `PGDATABASE` `PGUSER` `PGPASSWORD` | Postgres connection. SSL is required. |
| `PGPORT` | Defaults to `5432`. |
| `PUBLIC_URL` | Sent to OpenRouter as `HTTP-Referer`. Defaults to `http://localhost:8000`. |

The table it writes to:

```sql
CREATE TABLE IF NOT EXISTS brand_voice_runs (
    id SERIAL PRIMARY KEY,
    generation_run_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    output JSONB,
    model_used TEXT,
    content_type TEXT,
    status TEXT DEFAULT 'pending_review',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Run it:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Or with Docker:

```bash
docker build -t brand-voice-guardian .
docker run -p 8000:8000 --env-file .env brand-voice-guardian
```

## Notes

Both agents use `deepseek/deepseek-v4-flash` through OpenRouter in JSON mode, with provider order pinned to Together → AtlasCloud → Venice and fallbacks allowed.

Each agent validates its own output before returning — the audit must produce a numeric `compliance_score`, the rewrite must produce non-empty `rewritten_content`. A malformed response fails the request rather than persisting junk.

No credentials are committed. Everything sensitive is read from the environment.
