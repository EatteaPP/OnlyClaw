from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workspace.skills._shared.browser_resolution import get_browser_candidates, load_config, resolve_executable


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


def _browser_label(browser: str) -> str:
    return browser.capitalize()


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        params = json.loads(raw) if raw else {}
        config = load_config()

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

        candidates = get_browser_candidates(browser, config)
        executable = resolve_executable(candidates)
        if executable is None:
            result(
                False,
                (
                    f"Browser executable not found: {browser}. "
                    f"Please install {_browser_label(browser)} or configure "
                    f"apps.browsers.{browser}.executable_candidates in config.yaml."
                ),
                {"browser": browser, "url": url},
            )
            return

        subprocess.Popen([executable, url], shell=False)
        result(True, f"Opened URL with {browser}: {url}", {"url": url, "browser": browser})
    except Exception as exc:
        result(False, f"Failed to open URL: {exc}")


if __name__ == "__main__":
    main()
