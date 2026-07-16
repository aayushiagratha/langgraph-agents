import json

from common.db import get_connection

MODEL_USED = "deepseek/deepseek-v4-flash"


def persist_results(generation_run_id: str, content_type: str, audit_output: dict, rewrite_output: dict) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO brand_voice_runs (generation_run_id, agent, output, model_used, content_type, status)
                VALUES (%s, 'audit', %s::jsonb, %s, %s, 'completed'),
                       (%s, 'rewrite', %s::jsonb, %s, %s, 'completed')
                """,
                (
                    generation_run_id,
                    json.dumps(audit_output),
                    MODEL_USED,
                    content_type,
                    generation_run_id,
                    json.dumps(rewrite_output),
                    MODEL_USED,
                    content_type,
                ),
            )
        conn.commit()
