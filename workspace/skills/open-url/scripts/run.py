from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
from urllib.parse import urlparse


BROWSER_COMMANDS = {
    "edge": ["msedge"],
    "chrome": ["chrome"],
    "firefox": ["firefox"],
}


def result(success: bool, message: str, data: dict | None = None) -> None:
    print(
        json.dumps(
            {
                "success": success,
                "message": message,
                "data": data or {},
            },
            ensure_ascii=False,
        )
    )


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        params = json.loads(raw) if raw else {}

        url = str(params.get("url") or "").strip()
        browser = str(params.get("browser") or "default").lower().strip()

        if sys.platform != "win32":
            result(False, "open-url is only supported on Windows.", {"url": url, "browser": browser})
            return

        if not is_allowed_url(url):
            result(False, f"Unsupported or invalid URL: {url}", {"url": url, "browser": browser})
            return

        if browser == "default":
            webbrowser.open(url)
            result(True, f"Opened URL with default browser: {url}", {"url": url, "browser": browser})
            return

        if browser not in BROWSER_COMMANDS:
            result(False, f"Unsupported browser: {browser}", {"url": url, "browser": browser})
            return

        subprocess.Popen(BROWSER_COMMANDS[browser] + [url], shell=False)
        result(True, f"Opened URL with {browser}: {url}", {"url": url, "browser": browser})
    except Exception as exc:
        result(False, f"Failed to open URL: {exc}")


if __name__ == "__main__":
    main()

