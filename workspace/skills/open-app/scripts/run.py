from __future__ import annotations

import json
import subprocess
import sys
import webbrowser


APP_COMMANDS = {
    "edge": ["msedge"],
    "chrome": ["chrome"],
    "firefox": ["firefox"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
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


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        params = json.loads(raw) if raw else {}
        app = str(params.get("app") or "").lower().strip()

        if sys.platform != "win32":
            result(False, "open-app is only supported on Windows.", {"app": app})
            return

        if app == "default_browser":
            webbrowser.open("about:blank")
            result(True, "Opened app: default_browser", {"app": app})
            return

        if app not in APP_COMMANDS:
            result(False, f"Unsupported app: {app}", {"app": app})
            return

        subprocess.Popen(APP_COMMANDS[app], shell=False)
        result(True, f"Opened app: {app}", {"app": app})
    except Exception as exc:
        result(False, f"Failed to open app: {exc}")


if __name__ == "__main__":
    main()

