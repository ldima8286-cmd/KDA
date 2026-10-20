"""Reusable KDA widgets: panels, stat cards, hero icons and the trend chart."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .images import ImageCache
from .theme import C


class Panel(QFrame):
    """A titled surface; add widgets with add()."""

    def __init__(self, title: str = "", note: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "panel")
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(18, 16, 18, 16)
        self._root.setSpacing(12)

        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(12)

        if title or note:
            head = QHBoxLayout()
            head.setContentsMargins(0, 0, 0, 2)
            head.setSpacing(12)
            title_label = QLabel(title)
            title_label.setProperty("panelTitle", True)
            head.addWidget(title_label)
            head.addStretch(1)
            note_label = QLabel(note)
            note_label.setProperty("panelNote", True)
            head.addWidget(note_label)
            self._root.addLayout(head)
            self.note_label = note_label
        else:
            self.note_label = QLabel()
            self.note_label.hide()

        self._root.addLayout(self._content)

    def add(self, widget: QWidget) -> None:
        self._content.addWidget(widget)

    def add_layout(self, layout) -> None:  # noqa: ANN001 - Qt layout type varies
        self._content.addLayout(layout)


class HeroIcon(QLabel):
    """24px hero thumbnail, loaded asynchronously by URL."""

    SIZE = 24

    def __init__(self, url: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("heroIcon", True)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        self._url = url
        cache = ImageCache.instance()
        cache.loaded.connect(self._on_loaded)
        self.set_source(url)

    def set_source(self, url: str | None) -> None:
        self._url = url
        cache = ImageCache.instance()
        cached = cache.cached(url)
        if cached is not None:
            self.setPixmap(cached)
        else:
            self.clear()
            cache.request(url)

    def _on_loaded(self, url: str, pixmap: QPixmap) -> None:
        if url == self._url:
            self.setPixmap(pixmap)


class Avatar(HeroIcon):
    """Player avatar: same async loader, larger square."""

    SIZE = 64

    def __init__(self, url: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(url, parent)
        self.setProperty("heroIcon", False)
        self.setProperty("avatar", True)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.set_source(url)


def hero_cell(url: str | None, name: str) -> QWidget:
    """Icon + name row used inside table cells."""
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(4, 2, 4, 2)
    lay.setSpacing(8)
    icon = HeroIcon(url)
    icon.setFixedSize(HeroIcon.SIZE, HeroIcon.SIZE)
    lay.addWidget(icon)
    label = QLabel(name)
    label.setProperty("heroName", True)
    lay.addWidget(label)
    lay.addStretch(1)
    return wrap


class StatCard(QFrame):
    """Label + big monospaced number, with an optional accent bar."""

    _ACCENTS = {"accent": C["gold"], "win": C["win"], "loss": C["loss"], "teal": C["teal"]}

    def __init__(
        self,
        label: str,
        value: str,
        sub: str = "",
        accent: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("role", "panel")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        bar = QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(f"background: {self._ACCENTS.get(accent, C['line2'])}; border-radius: 1px;")
        row.addWidget(bar)

        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(4)

        lab = QLabel(label.upper())
        lab.setProperty("statLabel", True)
        inner.addWidget(lab)

        self._value_label = QLabel(value)
        self._value_label.setProperty("value", True)
        inner.addWidget(self._value_label)

        self._sub_label = QLabel(sub) if sub else None
        if self._sub_label is not None:
            self._sub_label.setProperty("statSub", True)
            inner.addWidget(self._sub_label)

        row.addLayout(inner, 1)

    def set_value(self, value: str, sub: str | None = None) -> None:
        self._value_label.setText(value)
        if self._sub_label is not None and sub is not None:
            self._sub_label.setText(sub)


class TrendChart(QWidget):
    """Hand-rolled win-rate line chart (no charting dependency)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._points: list[dict[str, Any]] = []
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_points(self, points: list[dict[str, Any]]) -> None:
        self._points = points or []
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(640, 180)

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(40, 12, -12, -20)
        if rect.width() < 40 or rect.height() < 20:
            return

        grid_pen = QPen(QColor(C["line"]))
        faint_pen = QPen(QColor(C["faint"]))
        font = QFont()
        font.setPixelSize(10)
        painter.setFont(font)

        # horizontal grid + labels
        for tick in (0, 25, 50, 75, 100):
            y = rect.bottom() - (tick / 100.0) * rect.height()
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(faint_pen)
            painter.drawText(QRectF(0, y - 8, 34, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(tick))

        if not self._points:
            painter.setPen(faint_pen)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "нет данных")
            return

        n = len(self._points)

        def xy(i: int, value: float) -> QPointF:
            x = rect.left() if n == 1 else rect.left() + i * rect.width() / (n - 1)
            y = rect.bottom() - (value / 100.0) * rect.height()
            return QPointF(x, y)

        path_pts = [xy(i, float(p.get("winrate", 0.0))) for i, p in enumerate(self._points)]

        # area fill
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gold = QColor(C["gold"])
        top = QColor(gold)
        top.setAlpha(56)
        bottom = QColor(gold)
        bottom.setAlpha(0)
        gradient.setColorAt(0.0, top)
        gradient.setColorAt(1.0, bottom)

        area = QPainterPath()
        area.moveTo(path_pts[0].x(), rect.bottom())
        for pt in path_pts:
            area.lineTo(pt)
        area.lineTo(path_pts[-1].x(), rect.bottom())
        area.closeSubpath()
        painter.fillPath(area, gradient)

        # line
        painter.setPen(QPen(QColor(C["gold"]), 2))
        for i in range(len(path_pts) - 1):
            painter.drawLine(path_pts[i], path_pts[i + 1])

        # dots
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(C["gold"]))
        for pt in path_pts:
            painter.drawEllipse(pt, 3, 3)


_MONO = QFont()
_MONO.setFamily("monospace")


class NumericItem(QTableWidgetItem):
    """Sorts by numeric value instead of lexicographic text order."""

    def __lt__(self, other: QTableWidgetItem) -> bool:  # noqa: D105
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return self.text() < other.text()


def make_table(headers: list[str], numeric: set[int] | None = None) -> QTableWidget:
    """Bare, flat analytics table: no grid, no selection, sortable headers."""
    numeric = numeric or set()
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setShowGrid(False)
    table.setSortingEnabled(False)

    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setHighlightSections(False)
    for i in range(len(headers)):
        mode = (
            QHeaderView.ResizeMode.ResizeToContents
            if i in numeric
            else QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(i, mode)
    return table


def set_text(
    table: QTableWidget,
    row: int,
    col: int,
    text: str,
    mono: bool = False,
    right: bool = False,
    color: str | None = None,
    numeric: bool = False,
) -> None:
    item = NumericItem(str(text)) if numeric else QTableWidgetItem(str(text))
    if mono:
        item.setFont(_MONO)
    if right:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if color:
        item.setForeground(QColor(color))
    table.setItem(row, col, item)

