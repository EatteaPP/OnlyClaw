from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.command_router import CommandRouter
from src.config_loader import load_config
from src.floating_window import FloatingWindow
from src.hotkey_listener import HotkeyListener
from src.icon_utils import load_app_icon
from src.tray_app import TrayApp


class HotkeyBridge(QObject):
    triggered = Signal()


class AppController:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.config = load_config()
        self.icon = load_app_icon(self.config.get("app", {}).get("icon_path"))
        self.app.setWindowIcon(self.icon)
        self.router = CommandRouter(self.config["workspace"]["path"], self.config)
        self.window = FloatingWindow(self.config, self.router)
        self.window.setWindowIcon(self.icon)
        self.hotkey_listener: HotkeyListener | None = None
        self.tray: TrayApp | None = None
        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.triggered.connect(self.toggle_window)
        self._cleaned_up = False
        self._prepare_workspace()

    def _prepare_workspace(self) -> None:
        workspace_path = Path(self.config["workspace"]["path"])
        log_path = Path(self.config.get("logging", {}).get("path", workspace_path / "logs"))
        workspace_path.mkdir(parents=True, exist_ok=True)
        log_path.mkdir(parents=True, exist_ok=True)

    def setup_tray(self) -> None:
        tray_config = self.config.get("tray", {})
        self.tray = TrayApp(
            app=self.app,
            window=self.window,
            reload_callback=self.reload_config,
            exit_callback=self.exit_app,
            icon=self.icon,
            tooltip=str(tray_config.get("tooltip", "OnlyClaw - Personal Command Widget")),
            enabled=bool(tray_config.get("enabled", True)),
        )

    def setup_hotkey(self) -> None:
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()

        hotkey_config = self.config.get("hotkey", {})
        self.hotkey_listener = HotkeyListener(
            enabled=bool(hotkey_config.get("enabled", True)),
            key=str(hotkey_config.get("key", "ctrl")),
            interval_ms=int(hotkey_config.get("interval_ms", 450)),
            on_trigger=self.hotkey_bridge.triggered.emit,
        )
        self.hotkey_listener.start()

    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.present()

    def reload_config(self) -> None:
        self.config = load_config()
        self.icon = load_app_icon(self.config.get("app", {}).get("icon_path"))
        self.app.setWindowIcon(self.icon)
        self.router = CommandRouter(self.config["workspace"]["path"], self.config)
        self.window.command_router = self.router
        self.window.apply_config(self.config)
        self.window.setWindowIcon(self.icon)

        if self.tray is not None and self.tray.tray is not None:
            self.tray.tray.setIcon(self.icon)
            self.tray.tray.setToolTip(str(self.config.get("tray", {}).get("tooltip", "OnlyClaw - Personal Command Widget")))

        self._prepare_workspace()
        self.setup_hotkey()

        if self.window.isVisible():
            self.window.focus_input()

    def cleanup(self) -> None:
        if self._cleaned_up:
            return
        self._cleaned_up = True

        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

        if self.tray is not None:
            self.tray.shutdown()
            self.tray = None

        if self.window is not None:
            self.window.hide()
            self.window.close()

    def exit_app(self) -> None:
        self.cleanup()
        self.app.quit()


def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    os.chdir(PROJECT_ROOT)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = AppController(app)
    app.aboutToQuit.connect(controller.cleanup)
    controller.setup_tray()
    controller.setup_hotkey()

    if controller.config.get("app", {}).get("auto_show_on_startup", False):
        controller.window.present()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
