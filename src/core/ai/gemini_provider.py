from __future__ import annotations

import json
import os
from typing import Any

try:  # pragma: no cover - optional dependency
    from google import genai
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore[assignment]

from src.core.intent import (
    contains_unsafe_scheme,
    extract_browser,
    extract_first_url,
    extract_registered_app,
)

from .mock_provider import MockAiProvider
from .provider import AiProvider


class GeminiAiProvider(AiProvider):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.api_key_env = str(self.config.get("api_key_env", "GEMINI_API_KEY"))
        self.model_env = str(self.config.get("model_env", "GEMINI_MODEL"))
        self.default_model = str(self.config.get("default_model", "gemini-2.5-flash"))
        self.temperature = float(self.config.get("temperature", 0.1))
        self.timeout_seconds = int(self.config.get("timeout_seconds", 60))
        self.api_key = os.getenv(self.api_key_env, "").strip()
        self.model = os.getenv(self.model_env, self.default_model).strip() or self.default_model
        self._client = None

    def _error_result(self, message: str) -> dict[str, Any]:
        return {
            "status": "error",
            "intent": None,
            "skill_name": None,
            "confidence": 0.0,
            "parameters": {},
            "message": message,
        }

    def _client_or_error(self) -> tuple[Any | None, dict[str, Any] | None]:
        if genai is None:
            return None, self._error_result("Gemini SDK is not installed.")
        if not self.api_key:
            return None, self._error_result(f"Missing API key in {self.api_key_env}.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client, None

    def _classification_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string", "enum": ["matched", "capability_not_available", "error"]},
                "intent": {"type": ["string", "null"]},
                "skill_name": {"type": ["string", "null"]},
                "confidence": {"type": "number"},
                "parameters": {"type": "object"},
                "message": {"type": "string"},
            },
            "required": ["status", "intent", "skill_name", "confidence", "parameters", "message"],
        }

    def _system_prompt(self) -> str:
        return (
            "You are OnlyClaw's intent parser. "
            "Only choose from registered skills in the provided skill index. "
            "Do not invent skills, shell commands, browser actions, or desktop actions. "
            "If the selected skill is open-url, parameters.url is required. "
            "When the user input contains a string starting with http:// or https://, extract it exactly as parameters.url. "
            "If no browser is specified, use browser=default. "
            "Return JSON only."
        )

    def _build_prompt(self, command: str, skill_index: list[dict[str, Any]]) -> str:
        skills_json = json.dumps(skill_index, ensure_ascii=False, indent=2)
        example_json = json.dumps(
            {
                "status": "matched",
                "intent": "run_skill",
                "skill_name": "open-url",
                "confidence": 0.95,
                "parameters": {
                    "url": "https://www.google.com",
                    "browser": "default",
                },
                "message": "Matched open-url",
            },
            ensure_ascii=False,
            indent=2,
        )
        return (
            f"Command:\n{command}\n\n"
            f"Available skills:\n{skills_json}\n\n"
            "Choose the best matching skill if one is available. "
            "If no registered skill can handle the command, return capability_not_available. "
            "Extract only safe parameters needed by the skill.\n\n"
            "Example:\n"
            f"{example_json}"
        )

    def _normalize_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return self._error_result("Model returned an invalid payload.")

        required_keys = {"status", "intent", "skill_name", "confidence", "parameters", "message"}
        if not required_keys.issubset(payload):
            return self._error_result("Model response was missing required fields.")

        status = str(payload.get("status", "error"))
        if status not in {"matched", "capability_not_available", "error"}:
            status = "error"

        parameters = payload.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        confidence = payload.get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0

        return {
            "status": status,
            "intent": payload.get("intent"),
            "skill_name": payload.get("skill_name"),
            "confidence": confidence_value,
            "parameters": parameters,
            "message": str(payload.get("message", "")),
        }

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        client, error = self._client_or_error()
        if error is not None or client is None:
            return error["message"] if error is not None else "Gemini provider is unavailable."

        contents = prompt if system is None else f"{system}\n\n{prompt}"
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config={"temperature": self.temperature},
            )
            return str(getattr(response, "text", "")).strip()
        except Exception as exc:  # pragma: no cover - external API failure
            return f"Gemini provider error: {exc}"

    def classify_intent(self, command: str, skill_index: list[dict[str, Any]]) -> dict[str, Any]:
        if contains_unsafe_scheme(command):
            return {
                "status": "capability_not_available",
                "intent": None,
                "skill_name": None,
                "confidence": 0.0,
                "parameters": {},
                "message": "The command contains an unsafe URL scheme and cannot be opened.",
            }

        url = extract_first_url(command)
        if url:
            skill_names = {str(skill.get("name", "")).strip().lower(): skill for skill in skill_index}
            if skill_names.get("open-url") is not None:
                return {
                    "status": "matched",
                    "intent": "run_skill",
                    "skill_name": "open-url",
                    "confidence": 0.99,
                    "parameters": {
                        "url": url,
                        "browser": extract_browser(command),
                    },
                    "message": "Matched open-url by deterministic URL extraction",
                }

        app, matched_alias = extract_registered_app(command, skill_index)
        if app:
            skill_names = {str(skill.get("name", "")).strip().lower(): skill for skill in skill_index}
            if skill_names.get("open-app") is not None:
                return {
                    "status": "matched",
                    "intent": "run_skill",
                    "skill_name": "open-app",
                    "confidence": 0.95,
                    "parameters": {
                        "app": app,
                    },
                    "message": f"Matched open-app by registered app alias: {matched_alias}",
                }

        client, error = self._client_or_error()
        if error is not None or client is None:
            return error or self._error_result("Gemini provider is unavailable.")

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=self._build_prompt(command, skill_index),
                config={
                    "temperature": self.temperature,
                    "response_mime_type": "application/json",
                    "response_json_schema": self._classification_schema(),
                },
            )
            payload = json.loads(str(getattr(response, "text", "")).strip() or "{}")
            return self._normalize_result(payload)
        except Exception as exc:  # pragma: no cover - external API failure
            return self._error_result(f"Gemini provider error: {exc}")

    def summarize_result(self, command: str, result: dict[str, Any]) -> str:
        client, error = self._client_or_error()
        if error is not None or client is None:
            return error["message"] if error is not None else "Gemini provider is unavailable."

        prompt = (
            "Summarize the following OnlyClaw command execution result in one short paragraph.\n\n"
            f"Command: {command}\n"
            f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}"
        )
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": self.temperature},
            )
            summary = str(getattr(response, "text", "")).strip()
            return summary or MockAiProvider().summarize_result(command, result)
        except Exception as exc:  # pragma: no cover - external API failure
            return f"Gemini provider error: {exc}"
