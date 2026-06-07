from __future__ import annotations

import re
from typing import Any


URL_RE = re.compile(r"https?://[^\s]+")
UNSAFE_SCHEME_RE = re.compile(r"\b(?:javascript|file|data|powershell|cmd):", re.IGNORECASE)


def extract_first_url(command: str) -> str | None:
    match = URL_RE.search(command)
    if not match:
        return None
    return match.group(0).rstrip(").,!?]")


def extract_browser(command: str) -> str:
    text = command.lower()

    if "edge" in text or "microsoft edge" in text:
        return "edge"
    if "chrome" in text or "google chrome" in text:
        return "chrome"
    if "firefox" in text:
        return "firefox"
    return "default"


def contains_unsafe_scheme(command: str) -> bool:
    return bool(UNSAFE_SCHEME_RE.search(command))


def _normalize_alias(alias: str) -> str:
    return " ".join(alias.lower().strip().split())


def _extract_open_app_skill(skill_index: list[dict[str, Any]]) -> dict[str, Any] | None:
    for skill in skill_index:
        if str(skill.get("name", "")).strip().lower() == "open-app":
            return skill
    return None


def extract_registered_app(command: str, skill_index: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    open_app_skill = _extract_open_app_skill(skill_index)
    if not isinstance(open_app_skill, dict):
        return None, None

    apps = open_app_skill.get("apps", {})
    if not isinstance(apps, dict):
        return None, None

    normalized_command = _normalize_alias(command)

    for app_key, app_config in apps.items():
        if not isinstance(app_config, dict):
            continue

        aliases = app_config.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, list):
            continue

        for alias in aliases:
            alias_text = str(alias).strip()
            if not alias_text:
                continue
            if _normalize_alias(alias_text) in normalized_command:
                return str(app_key).strip(), alias_text

    return None, None
