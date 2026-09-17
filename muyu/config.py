"""Configuration resolution: presets, env vars, and ~/.muyu/config.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

PRESETS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "glm": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4.6"},
    "kimi": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
}

CONFIG_PATH = Path.home() / ".muyu" / "config.yaml"


@dataclass
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    preset: str = "custom"
    temperature: float = 0.4

    @classmethod
    def resolve(cls, preset: str | None = None) -> "LlmConfig":
        """Resolution order: explicit preset > env > config file > deepseek preset."""
        preset = preset or os.environ.get("MUYU_PRESET")
        cfg: dict = {}
        if CONFIG_PATH.exists():
            try:
                cfg = yaml.safe_load(CONFIG_PATH.read_text()) or {}
            except yaml.YAMLError:
                cfg = {}
        chosen = preset or cfg.get("preset") or "deepseek"
        if chosen not in PRESETS and chosen != "custom":
            raise SystemExit(
                f"unknown preset {chosen!r}; pick one of {sorted(PRESETS)} or 'custom'"
            )
        base = PRESETS.get(chosen, {})
        base_url = (
            os.environ.get("MUYU_BASE_URL") or cfg.get("base_url") or base.get("base_url")
        )
        api_key = os.environ.get("MUYU_API_KEY") or cfg.get("api_key") or ""
        model = os.environ.get("MUYU_MODEL") or cfg.get("model") or base.get("model")
        if not (base_url and model):
            raise SystemExit(
                "incomplete LLM config: set preset + MUYU_API_KEY, or write "
                f"base_url/model/api_key into {CONFIG_PATH}"
            )
        return cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
            preset=chosen,
            temperature=float(cfg.get("temperature", 0.4)),
        )
