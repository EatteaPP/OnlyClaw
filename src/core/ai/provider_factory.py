from __future__ import annotations

import os
from typing import Any

from .gemini_provider import GeminiAiProvider
from .mock_provider import MockAiProvider
from .openai_provider import OpenAiProvider
from .provider import AiProvider


def _ai_config(config: dict[str, Any]) -> dict[str, Any]:
    ai_config = config.get("ai", {})
    return ai_config if isinstance(ai_config, dict) else {}


def _provider_settings(config: dict[str, Any], provider_name: str) -> dict[str, Any]:
    providers = _ai_config(config).get("providers", {})
    if not isinstance(providers, dict):
        return {}
    settings = providers.get(provider_name, {})
    return settings if isinstance(settings, dict) else {}


def create_ai_provider(config: dict[str, Any]) -> AiProvider:
    ai_config = _ai_config(config)
    if not ai_config.get("enabled", True):
        return MockAiProvider()

    provider_name = os.getenv("ONLYCLAW_AI_PROVIDER")
    if not provider_name:
        provider_name = str(ai_config.get("default_provider", "mock"))

    provider_name = provider_name.strip().lower() or "mock"
    settings = _provider_settings(config, provider_name)

    if not settings.get("enabled", True):
        return MockAiProvider()

    try:
        if provider_name == "openai":
            return OpenAiProvider(settings)
        if provider_name == "gemini":
            return GeminiAiProvider(settings)
        if provider_name == "mock":
            return MockAiProvider()
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"[ai] Warning: failed to create '{provider_name}' provider: {exc}")
        return MockAiProvider()

    return MockAiProvider()

