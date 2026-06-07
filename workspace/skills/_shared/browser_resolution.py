from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml


DEFAULT_BROWSER_CANDIDATES: dict[str, list[str]] = {
    "edge": [
        "msedge",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    ],
    "chrome": [
        "chrome",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    ],
    "firefox": [
        "firefox",
        "C:/Program Files/Mozilla Firefox/firefox.exe",
        "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
    ],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_config_path() -> Path:
    config_env = os.getenv("CONFIG_PATH", "./config.yaml")
    candidate = Path(config_env)
    if not candidate.is_absolute():
        candidate = (repo_root() / candidate).resolve()
    return candidate


def load_config() -> dict[str, Any]:
    for candidate in (resolve_config_path(), repo_root() / "config.example.yaml"):
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as file_handle:
                payload = yaml.safe_load(file_handle) or {}
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return {}


def get_browser_candidates(browser: str, config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_config()
    apps = config.get("apps", {}) if isinstance(config, dict) else {}
    browsers = apps.get("browsers", {}) if isinstance(apps, dict) else {}
    browser_config = browsers.get(browser, {}) if isinstance(browsers, dict) else {}

    if isinstance(browser_config, dict):
        candidates = browser_config.get("executable_candidates", [])
        if isinstance(candidates, list):
            normalized = [str(candidate).strip() for candidate in candidates if str(candidate).strip()]
            if normalized:
                return normalized

    return list(DEFAULT_BROWSER_CANDIDATES.get(browser, []))


def resolve_executable(candidates: list[str]) -> str | None:
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_absolute():
            if candidate_path.exists():
                return str(candidate_path)
            continue

        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    return None
