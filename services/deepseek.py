from __future__ import annotations
import json
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import get_settings

log = logging.getLogger(__name__)


class DeepSeekError(RuntimeError):
    pass


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
)
async def _post(payload: dict[str, Any]) -> dict[str, Any]:
    s = get_settings()
    async with httpx.AsyncClient(timeout=s.deepseek_timeout) as client:
        r = await client.post(
            f"{s.deepseek_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {s.deepseek_api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if r.status_code >= 400:
            raise DeepSeekError(f"DeepSeek {r.status_code}: {r.text[:300]}")
        return r.json()


async def chat_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.4) -> dict[str, Any]:
    s = get_settings()
    payload = {
        "model": s.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }
    data = await _post(payload)
    try:
        return json.loads(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise DeepSeekError(f"Malformed DeepSeek response: {e}") from e


async def chat_text(system_prompt: str, user_prompt: str, *, temperature: float = 0.5) -> str:
    s = get_settings()
    payload = {
        "model": s.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": 800,
    }
    data = await _post(payload)
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise DeepSeekError(f"Malformed DeepSeek response: {e}") from e
