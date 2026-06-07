from __future__ import annotations

import re


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


def extract_app(command: str) -> str | None:
    text = command.lower()

    if "edge" in text or "microsoft edge" in text:
        return "edge"
    if "chrome" in text or "google chrome" in text:
        return "chrome"
    if "firefox" in text:
        return "firefox"
    if "notepad" in text or "記事本" in text:
        return "notepad"
    if "calculator" in text or "小算盤" in text or "計算機" in text:
        return "calculator"
    if "browser" in text or "瀏覽器" in text or "預設瀏覽器" in text:
        return "default_browser"
    return None


def contains_unsafe_scheme(command: str) -> bool:
    return bool(UNSAFE_SCHEME_RE.search(command))
