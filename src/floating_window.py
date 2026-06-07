from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFocusEvent, QKeySequence, QShortcut
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLineEdit, QMainWindow, QTextEdit, QVBoxLayout, QWidget


class FloatingWindow(QMainWindow):
    def __init__(self, config: dict, command_router) -> None:
        super().__init__()
        self.config = config
        self.command_router = command_router
        self._build_ui()
        self.apply_config(config)

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter a command...")
        self.input_box.returnPressed.connect(self._submit_command)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Results will appear here.")

        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.escape_shortcut.activated.connect(self.hide)

        layout.addWidget(self.input_box)
        layout.addWidget(self.result_box)
        self.setCentralWidget(central_widget)

    def apply_config(self, config: dict) -> None:
        self.config = config
        window_config = config.get("window", {})
        app_config = config.get("app", {})
        was_visible = self.isVisible()

        if was_visible:
            self.hide()

        self.setWindowTitle(window_config.get("title", app_config.get("name", "OnlyClaw")))
        self.setWindowOpacity(float(window_config.get("opacity", 0.86)))
        self.escape_shortcut.setEnabled(bool(config.get("behavior", {}).get("hide_on_escape", True)))

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

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.focus_input()

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        super().focusOutEvent(event)
        if self.config.get("behavior", {}).get("hide_on_lost_focus", True):
            QTimer.singleShot(0, self._hide_if_not_active)

    def _hide_if_not_active(self) -> None:
        if not self.isActiveWindow() and self.isVisible():
            self.hide()

    def focus_input(self) -> None:
        behavior = self.config.get("behavior", {})
        if behavior.get("focus_textbox_on_show", True):
            self.input_box.setFocus()
            if behavior.get("select_all_text_on_show", True):
                self.input_box.selectAll()

    def present(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.focus_input()

    def _submit_command(self) -> None:
        command = self.input_box.text().strip()
        if not command:
            return

        result = self.command_router.handle(command)
        if isinstance(result, dict):
            summary = str(result.get("summary") or result.get("message") or "")
            if not summary and isinstance(result.get("execution"), dict):
                execution = result["execution"]
                success = bool(execution.get("success", False))
                message = str(execution.get("message", "")).strip()
                skill_info = result.get("skill")
                skill_name = ""
                if isinstance(skill_info, dict):
                    skill_name = str(skill_info.get("name", "")).strip()
                if not skill_name:
                    skill_name = str(result.get("skill_name", "")).strip()

                if success:
                    summary = f"已執行 {skill_name}：{message}"
                else:
                    summary = f"執行 {skill_name} 失敗：{message}"

            self.result_box.setPlainText(summary or str(result))
        else:
            self.result_box.setPlainText(str(result))

        if self.config.get("behavior", {}).get("hide_after_submit", False):
            self.hide()
