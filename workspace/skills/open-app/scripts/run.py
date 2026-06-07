from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
from pathlib import Path


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


def _browser_label(browser: str) -> str:
    return browser.capitalize()


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        params = json.loads(raw) if raw else {}
        config = load_config()
        app = str(params.get("app") or "").lower().strip()

        if sys.platform != "win32":
            result(False, "open-app is only supported on Windows.", {"app": app})
            return

        if app == "default_browser":
            webbrowser.open("about:blank")
            result(True, "Opened app: default_browser", {"app": app})
            return

        if app in {"edge", "chrome", "firefox"}:
            candidates = get_browser_candidates(app, config)
            executable = resolve_executable(candidates)
            if executable is None:
                result(
                    False,
                    (
                        f"Browser executable not found: {app}. "
                        f"Please install {_browser_label(app)} or configure "
                        f"apps.browsers.{app}.executable_candidates in config.yaml."
                    ),
                    {"app": app},
                )
                return

            subprocess.Popen([executable], shell=False)
            result(True, f"Opened app: {app}", {"app": app})
            return

        if app == "notepad":
            subprocess.Popen(["notepad"], shell=False)
            result(True, "Opened app: notepad", {"app": app})
            return

        if app == "calculator":
            subprocess.Popen(["calc"], shell=False)
            result(True, "Opened app: calculator", {"app": app})
            return

        result(False, f"Unsupported app: {app}", {"app": app})
    except Exception as exc:
        result(False, f"Failed to open app: {exc}")


if __name__ == "__main__":
    main()
