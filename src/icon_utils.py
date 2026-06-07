from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_icon_path(icon_path: str | None) -> Path | None:
    if not icon_path:
        return None

    candidate = Path(icon_path)
    if not candidate.is_absolute():
        candidate = (_project_root() / candidate).resolve()

    return candidate if candidate.exists() else None


def create_placeholder_icon() -> QIcon:
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(30, 30, 32))
    painter.setPen(QPen(QColor(92, 92, 96), 8))
    painter.drawRoundedRect(12, 12, 232, 232, 42, 42)

    painter.setPen(QPen(QColor(220, 72, 72), 18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRect(62, 74, 132, 132), 30 * 16, 300 * 16)

    painter.setPen(QPen(QColor(236, 236, 236), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    font = QFont()
    font.setBold(True)
    font.setPixelSize(72)
    painter.setFont(font)
    painter.drawText(QRect(0, 96, 256, 80), Qt.AlignmentFlag.AlignCenter, "C")

    painter.end()
    return QIcon(pixmap)


def load_app_icon(icon_path: str | None) -> QIcon:
    resolved_path = resolve_icon_path(icon_path)
    if resolved_path is not None:
        icon = QIcon(str(resolved_path))
        if not icon.isNull():
            return icon
        print(f"[icon] Warning: failed to load icon at {resolved_path}; using placeholder icon.")

    return create_placeholder_icon()
