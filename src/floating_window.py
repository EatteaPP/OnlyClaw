from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QTextEdit, QVBoxLayout, QWidget


class FloatingWindow(QMainWindow):
    def __init__(self, config: dict, command_router) -> None:
        super().__init__()
        self.config = config
        self.command_router = command_router
        self._focus_tracking_connected = False
        self._build_ui()
        self._setup_focus_tracking()
        self.apply_config(config)

    def _behavior(self) -> dict:
        return self.config.get("behavior", {})

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter a command...")
        self.input_box.returnPressed.connect(self.submit_command)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Results will appear here.")

        layout.addWidget(self.input_box)
        layout.addWidget(self.result_box)
        self.setCentralWidget(central_widget)

    def _setup_focus_tracking(self) -> None:
        app = QApplication.instance()
        if app is None or self._focus_tracking_connected:
            return
        app.focusChanged.connect(self._on_focus_changed)
        self._focus_tracking_connected = True

    def apply_config(self, config: dict) -> None:
        self.config = config
        window_config = config.get("window", {})
        app_config = config.get("app", {})
        was_visible = self.isVisible()

        if was_visible:
            self.hide()

        self.setWindowTitle(window_config.get("title", app_config.get("name", "OnlyClaw")))
        self.setWindowOpacity(float(window_config.get("opacity", 0.86)))

        flags = Qt.WindowType.Window
        if window_config.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        if window_config.get("frameless", True):
            flags |= Qt.WindowType.FramelessWindowHint
        if not window_config.get("show_taskbar_icon", True):
            flags |= Qt.WindowType.Tool
        self.setWindowFlags(flags)

        self.resize(int(window_config.get("width", 520)), int(window_config.get("height", 180)))
        self.move(int(window_config.get("x", 1200)), int(window_config.get("y", 120)))

        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(30, 30, 30, 220);
                color: #f0f0f0;
                font-size: 14px;
            }

            QLineEdit {
                background-color: rgba(45, 45, 45, 230);
                border: 1px solid rgba(120, 120, 120, 180);
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }

            QTextEdit {
                background-color: rgba(34, 34, 34, 180);
                border: 1px solid rgba(90, 90, 90, 120);
                border-radius: 8px;
                padding: 8px;
                color: #d8d8d8;
            }
            """
        )

        if was_visible:
            self.show()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape and self._behavior().get("hide_on_escape", True):
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)

    def focus_command_input(self, *, force: bool = False) -> None:
        behavior = self._behavior()
        if not force and not behavior.get("focus_textbox_on_show", True):
            return

        self.input_box.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        if behavior.get("select_all_text_on_show", True):
            self.input_box.selectAll()

    def show_and_focus(self, *, force_focus: bool = True) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

        behavior = self._behavior()
        delay_ms = int(behavior.get("focus_delay_ms", 80))
        if force_focus or behavior.get("focus_textbox_on_show", True):
            QTimer.singleShot(delay_ms, lambda: self.focus_command_input(force=True))

    def present(self) -> None:
        self.show_and_focus(force_focus=True)

    def _focus_widget_is_inside_window(self, widget) -> bool:
        if widget is None:
            return False
        if widget is self or widget is self.centralWidget():
            return True
        return self.isAncestorOf(widget)

    def _on_focus_changed(self, old, new) -> None:
        del old
        behavior = self._behavior()
        if not behavior.get("hide_on_lost_focus", True):
            return
        if not self.isVisible():
            return
        if self._focus_widget_is_inside_window(new):
            return
        QTimer.singleShot(120, self.hide_if_focus_outside)

    def hide_if_focus_outside(self) -> None:
        if not self.isVisible():
            return

        focused = QApplication.focusWidget()
        if self._focus_widget_is_inside_window(focused):
            return
        self.hide()

    def hide_if_not_active(self) -> None:
        if self.isVisible() and not self.isActiveWindow():
            self.hide()

    def submit_command(self) -> None:
        command = self.input_box.text().strip()
        if not command:
            return

        result = self.command_router.handle(command)
        if isinstance(result, dict):
            message = str(result.get("message") or result.get("summary") or "").strip()
            success = bool(result.get("success", False))
        else:
            message = str(result)
            success = False

        self.result_box.setPlainText(message or "No result returned.")

        behavior = self._behavior()
        hide_after_success = behavior.get("hide_after_successful_submit", behavior.get("hide_after_submit", True))
        if success:
            if behavior.get("clear_text_after_successful_submit", True):
                self.input_box.clear()
            elif behavior.get("clear_text_after_submit", False):
                self.input_box.clear()

            if hide_after_success:
                delay_ms = int(behavior.get("hide_after_success_delay_ms", 300))
                QTimer.singleShot(delay_ms, self.hide)
        else:
            if behavior.get("clear_text_after_submit", False):
                self.input_box.clear()

            if behavior.get("hide_after_failed_submit", False):
                delay_ms = int(behavior.get("hide_after_success_delay_ms", 300))
                QTimer.singleShot(delay_ms, self.hide)
