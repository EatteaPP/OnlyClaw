from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayApp:
    def __init__(
        self,
        app: QApplication,
        window,
        reload_callback,
        exit_callback,
        icon,
        tooltip: str,
        enabled: bool,
    ) -> None:
        self.app = app
        self.window = window
        self.reload_callback = reload_callback
        self.exit_callback = exit_callback
        self.tray: QSystemTrayIcon | None = None

        if not enabled:
            return

        self.tray = QSystemTrayIcon(self.app)
        fallback_icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon if icon is not None and not icon.isNull() else fallback_icon)
        self.tray.setToolTip(tooltip)

        menu = QMenu()

        self.toggle_action = QAction("Show / Hide", menu)
        self.toggle_action.triggered.connect(self.toggle_window)
        menu.addAction(self.toggle_action)

        reload_action = QAction("Reload Config", menu)
        reload_action.triggered.connect(self.reload_callback)
        menu.addAction(reload_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_callback)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()

    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show_and_focus(force_focus=True)

    def shutdown(self) -> None:
        if self.tray is None:
            return

        try:
            self.tray.hide()
        finally:
            self.tray.deleteLater()
            self.tray = None
