import json
import os

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-flash"
PROVIDER_ORDER = ["Together", "AtlasCloud", "Venice"]


class OpenRouterError(Exception):
    pass


async def call_json_agent(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    top_p: float = 0.1,
) -> dict:
    api_key = os.environ["OPENROUTER_API_KEY"].strip()
    if api_key.lower().startswith("bearer "):
        api_key = api_key[7:].strip()
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "top_p": top_p,
        "response_format": {"type": "json_object"},
        "provider": {"order": PROVIDER_ORDER, "allow_fallbacks": True},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.environ.get("PUBLIC_URL", "http://localhost:8000"),
        "X-Title": "Brand Voice Guardian",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        raise OpenRouterError(f"OpenRouter request failed ({resp.status_code}): {resp.text[:500]}")
    data = resp.json()
    try:
        raw = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Unexpected OpenRouter response shape: {data}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenRouterError(f"Agent did not return valid JSON: {raw[:500]}") from exc
