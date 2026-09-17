"""Minimal OpenAI-compatible chat client (no SDK dependency)."""

from __future__ import annotations

import json

import httpx

from .config import LlmConfig


def chat(cfg: LlmConfig, system: str, user: str, timeout: float = 120.0) -> str:
    payload = {
        "model": cfg.model,
        "temperature": cfg.temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    resp = httpx.post(
        f"{cfg.base_url.rstrip('/')}/chat/completions",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise SystemExit(f"unexpected response shape from endpoint: {json.dumps(data)[:300]}") from e
