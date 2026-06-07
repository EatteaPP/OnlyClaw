from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "name": "OnlyClaw",
        "auto_show_on_startup": False,
        "icon_path": "./assets/icons/onlyclaw.ico",
    },
    "tray": {
        "enabled": True,
        "tooltip": "OnlyClaw - Personal Command Widget",
    },
    "window": {
        "title": "OnlyClaw",
        "opacity": 0.86,
        "x": 1200,
        "y": 120,
        "width": 520,
        "height": 180,
        "always_on_top": True,
        "frameless": True,
        "show_taskbar_icon": True,
    },
    "hotkey": {
        "enabled": True,
        "mode": "double_press",
        "key": "ctrl",
        "interval_ms": 450,
    },
    "behavior": {
        "hide_on_escape": True,
        "hide_on_lost_focus": True,
        "hide_on_hotkey_when_visible": True,
        "hide_after_submit": False,
        "hide_after_successful_submit": True,
        "hide_after_failed_submit": False,
        "focus_textbox_on_show": True,
        "select_all_text_on_show": True,
        "focus_delay_ms": 80,
        "hide_after_success_delay_ms": 300,
        "clear_text_after_submit": False,
        "clear_text_after_successful_submit": True,
    },
    "workspace": {
        "path": "./workspace",
    },
    "logging": {
        "enabled": True,
        "path": "./workspace/logs",
    },
    "apps": {
        "browsers": {
            "edge": {
                "executable_candidates": [
                    "msedge",
                    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
                ],
            },
            "chrome": {
                "executable_candidates": [
                    "chrome",
                    "C:/Program Files/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                ],
            },
            "firefox": {
                "executable_candidates": [
                    "firefox",
                    "C:/Program Files/Mozilla Firefox/firefox.exe",
                    "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
                ],
            },
        },
    },
    "skills": {
        "enabled": True,
        "auto_execute_permissions": [
            "read-only",
            "local-app-launch",
            "open-url",
        ],
        "require_approval_permissions": [
            "approval-required",
            "dangerous",
        ],
    },
    "ai": {
        "enabled": True,
        "default_provider": "mock",
        "providers": {
            "mock": {
                "enabled": True,
            },
            "openai": {
                "enabled": True,
                "api_key_env": "OPENAI_API_KEY",
                "model_env": "OPENAI_MODEL",
                "default_model": "gpt-5.4-mini",
                "temperature": 0.1,
                "timeout_seconds": 60,
            },
            "gemini": {
                "enabled": True,
                "api_key_env": "GEMINI_API_KEY",
                "model_env": "GEMINI_MODEL",
                "default_model": "gemini-2.5-flash",
                "temperature": 0.1,
                "timeout_seconds": 60,
            },
        },
    },
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_path(value: str | None, fallback: str) -> Path:
    raw = value or fallback
    path = Path(raw)
    if not path.is_absolute():
        path = (_project_root() / path).resolve()
    return path


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(DEFAULT_CONFIG, config)

    merged["workspace"]["path"] = str(
        _resolve_path(
            merged.get("workspace", {}).get("path"),
            DEFAULT_CONFIG["workspace"]["path"],
        )
    )

    merged["logging"]["path"] = str(
        _resolve_path(
            merged.get("logging", {}).get("path"),
            DEFAULT_CONFIG["logging"]["path"],
        )
    )

    merged["app"]["icon_path"] = str(
        _resolve_path(
            merged.get("app", {}).get("icon_path"),
            DEFAULT_CONFIG["app"]["icon_path"],
        )
    )

    return merged


def load_config() -> dict[str, Any]:
    load_dotenv()

    project_root = _project_root()
    config_env = os.getenv("CONFIG_PATH", "./config.yaml")
    config_path = _resolve_path(config_env, "./config.yaml")
    example_path = project_root / "config.example.yaml"

    loaded: dict[str, Any] = {}
    source_path: Path | None = None

    for candidate in (config_path, example_path):
        if candidate.exists():
            try:
                with candidate.open("r", encoding="utf-8") as file_handle:
                    content = yaml.safe_load(file_handle) or {}
                if isinstance(content, dict):
                    loaded = content
                    source_path = candidate
                    break
                print(f"[config] Warning: {candidate} did not contain a mapping; using defaults.")
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[config] Warning: failed to load {candidate}: {exc}")

    if source_path is None and not loaded:
        print("[config] Warning: no config file found; using default configuration.")

    return _normalize_config(loaded)
