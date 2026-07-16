import os

from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    expected = os.environ["WEBHOOK_API_KEY"]
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
