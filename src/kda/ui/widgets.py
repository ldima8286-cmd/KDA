"""Reusable KDA widgets: panels, stat cards, hero icons and the trend chart."""
from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
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


def _round_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    """Return a copy of the pixmap with rounded corners and transparency."""
    if pixmap.isNull() or radius <= 0:
        return pixmap
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    rect = QRectF(0, 0, pixmap.width(), pixmap.height())
    path.addRoundedRect(rect, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded


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
            self.title_label = title_label
        else:
            self.note_label = QLabel()
            self.note_label.hide()
            self.title_label = QLabel()
            self.title_label.hide()

        self._root.addLayout(self._content)

    def add(self, widget: QWidget) -> None:
        self._content.addWidget(widget)

    def add_layout(self, layout) -> None:  # noqa: ANN001 - Qt layout type varies
        self._content.addLayout(layout)


class HeroIcon(QLabel):
    """Hero thumbnail, loaded asynchronously by URL.

    Prefers the 32x32 square ``icon`` asset; the wide ``img`` banner is cropped
    to a square by aspect, never stretched.
    """

    SIZE = 40

    def __init__(self, url: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = self.SIZE
        self.setProperty("heroIcon", True)
        self.setFixedSize(self._size, self._size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._url = url
        cache = ImageCache.instance()
        cache.loaded.connect(self._on_loaded)
        self.set_source(url)

    def resize_icon(self, size: int) -> None:
        self._size = size
        self.setFixedSize(size, size)
        cached = ImageCache.instance().cached(self._url)
        if cached is not None:
            self.setPixmap(self._cover(cached))

    def _cover(self, pixmap: QPixmap) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        side = min(pixmap.width(), pixmap.height())
        x = (pixmap.width() - side) // 2
        y = (pixmap.height() - side) // 2
        cropped = pixmap.copy(x, y, side, side).scaled(
            self._size,
            self._size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        return _round_pixmap(cropped, max(4, self._size // 5))

    def set_source(self, url: str | None) -> None:
        self._url = url
        cache = ImageCache.instance()
        cached = cache.cached(url)
        if cached is not None:
            self.setPixmap(self._cover(cached))
        else:
            self.clear()
            cache.request(url)

    def _on_loaded(self, url: str, pixmap: QPixmap) -> None:
        if url == self._url:
            self.setPixmap(self._cover(pixmap))


class Avatar(HeroIcon):
    """Player avatar: same async loader, larger square."""

    SIZE = 64

    def __init__(self, url: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(url, parent)
        self._size = self.SIZE
        self.setProperty("heroIcon", False)
        self.setProperty("avatar", True)
        self.setFixedSize(self._size, self._size)
        self.set_source(url)


class ItemIcon(QFrame):
    """Small square item tile, async-loaded; shows a slot placeholder when empty."""

    SIZE = 32

    def __init__(self, url: str | None = None, tip: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("itemIcon", True)
        self.setFixedSize(self.SIZE, self.SIZE)
        if tip:
            self.setToolTip(tip)

        self._label = QLabel(self)
        self._label.setGeometry(0, 0, self.SIZE, self.SIZE)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if url:
            cache = ImageCache.instance()
            cached = cache.cached(url)
            if cached is not None:
                self._label.setPixmap(self._scaled(cached))
            else:
                cache.loaded.connect(self._on_loaded)
                self._url = url
                cache.request(url)
        else:
            self._url = ""

    def _scaled(self, pixmap: QPixmap) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        side = min(pixmap.width(), pixmap.height())
        x = (pixmap.width() - side) // 2
        y = (pixmap.height() - side) // 2
        cropped = pixmap.copy(x, y, side, side)
        if cropped.width() <= self.SIZE:
            scaled = cropped.scaled(
                self.SIZE,
                self.SIZE,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            scaled = cropped.scaled(
                self.SIZE,
                self.SIZE,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        return _round_pixmap(scaled, max(3, self.SIZE // 6))

    def _on_loaded(self, url: str, pixmap: QPixmap) -> None:
        if url == self._url:
            self._label.setPixmap(self._scaled(pixmap))


class RankBadge(QWidget):
    """Painter-drawn rank medal driven by a Dota rank_tier (division + stars)."""

    _COLORS = [
        ("#8a95a5", "#c3ccd8"),  # Herald
        ("#9a6b2f", "#d59a4a"),  # Guardian
        ("#3f7d8c", "#6fb7c6"),  # Crusader
        ("#4a6f9c", "#7ba3d1"),  # Archon
        ("#5b8a63", "#86c092"),  # Legend
        ("#6a5aa0", "#a08fd8"),  # Ancient
        ("#9c4a4a", "#d98080"),  # Divine
        ("#b8892e", "#f0c063"),  # Immortal
    ]
    _LABELS = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._division = 0
        self._star = 0
        self._leaderboard: int | None = None
        self.setFixedSize(46, 46)
        self.setToolTip("Без ранга")

    def set_rank(self, tier: int | None, leaderboard: int | None = None) -> None:
        if not tier:
            self._division, self._star = 0, 0
        else:
            division, star = divmod(int(tier), 10)
            if 1 <= division <= 8:
                self._division, self._star = division, min(star, 5)
            else:
                self._division, self._star = 0, 0
        self._leaderboard = leaderboard
        if self._division:
            text = f"{self._LABELS[self._division - 1]} {self._star}"
            if leaderboard:
                text += f" · лидерборд #{leaderboard}"
        else:
            text = "Без ранга"
        self.setToolTip(text)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        cx, cy, r = 23.0, 23.0, 19.0
        if not self._division:
            painter.setBrush(QColor(C["panel3"]))
            painter.setPen(QPen(QColor(C["line2"]), 1.5))
            painter.drawEllipse(QPointF(cx, cy), r, r)
            painter.setPen(QColor(C["faint"]))
            font = QFont()
            font.setPixelSize(18)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "—")
            return

        dark, light = self._COLORS[self._division - 1]

        ring = QRadialGradient(cx, cy - 4, r * 1.5)
        ring.setColorAt(0.0, QColor(light))
        ring.setColorAt(1.0, QColor(dark))
        painter.setBrush(ring)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.setPen(QPen(QColor(0, 0, 0, 90), 1.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r - 0.8, r - 0.8)
        painter.drawEllipse(QPointF(cx, cy), r - 5.5, r - 5.5)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#12100b"))
        star_r = 6.3
        painter.drawEllipse(QPointF(cx, cy), star_r, star_r)

        if self._star:
            self._draw_stars(painter, cx, cy, self._star)
        else:
            painter.setPen(QColor(light))
            font = QFont("monospace")
            font.setPixelSize(11)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self._division))

    @staticmethod
    def _draw_stars(painter: QPainter, cx: float, cy: float, count: int) -> None:
        path = QPainterPath()
        outer, inner = 5.4, 2.3
        points = []
        for i in range(10):
            angle = -90 + i * 36
            radius = outer if i % 2 == 0 else inner
            x = radius * math.cos(math.radians(angle))
            y = radius * math.sin(math.radians(angle))
            points.append((cx + x, cy + y))
        path.moveTo(*points[0])
        for pt in points[1:]:
            path.lineTo(*pt)
        path.closeSubpath()
        painter.setBrush(QColor("#f2d489"))
        painter.drawPath(path)


def item_cell(metas: list[dict[str, str]], limit: int = 6) -> QWidget:
    """Row of item tiles (six by default) plus the neutral slot."""
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(4, 2, 4, 2)
    lay.setSpacing(3)
    for meta in (metas or [])[:limit]:
        lay.addWidget(ItemIcon(meta.get("img") or None, meta.get("name") or ""))
    lay.addStretch(1)
    return wrap


def set_row_id(table: QTableWidget, row: int, value: int) -> None:
    """Stash an id on a row so it survives sorting; read it with row_id()."""
    item = QTableWidgetItem()
    item.setData(Qt.ItemDataRole.UserRole, int(value))
    table.setItem(row, 0, item)


def row_id(table: QTableWidget, row: int) -> int | None:
    item = table.item(row, 0)
    if item is None:
        return None
    value = item.data(Qt.ItemDataRole.UserRole)
    return int(value) if value is not None else None


def hero_cell(
    url: str | None,
    name: str,
    size: int = HeroIcon.SIZE,
    icon_url: str | None = None,
) -> QWidget:
    """Icon + name row used inside table cells.

    ``icon_url`` (the square 32x32 asset) is preferred over the wide banner
    ``url`` because a square crop of a landscape banner can lose the portrait.
    """
    # Dota serves a wide 256x144 banner at .../heroes/<name>.png and a square
    # 32x32 portrait at .../heroes/icons/<name>.png. A centre-crop of the wide
    # banner can clip the portrait, so always derive the square asset when the
    # caller only passed the banner.
    if not icon_url and url and "/heroes/" in url and "/heroes/icons/" not in url:
        icon_url = url.replace("/heroes/", "/heroes/icons/")
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(8, 5, 8, 5)
    lay.setSpacing(11)
    icon = HeroIcon(icon_url or url)
    icon.resize_icon(size)
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


class AdvantageChart(QWidget):
    """Signed line chart for radiant gold/xp advantage (positive = radiant)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._series: list[tuple[str, list[int], str]] = []
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_series(self, series: list[tuple[str, list[int], str]]) -> None:
        """series: list of (label, values, colour)."""
        self._series = [(label, vals or [], colour) for label, vals, colour in series if vals]
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(720, 200)

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(56, 12, -12, -20)
        if rect.width() < 40 or rect.height() < 20:
            return

        faint_pen = QPen(QColor(C["faint"]))
        font = QFont()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.setPen(faint_pen)

        peak = 1
        length = 0
        for _, vals, _ in self._series:
            peak = max(peak, max((abs(v) for v in vals), default=0))
            length = max(length, len(vals))

        if length < 2:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "нет данных парсинга")
            return

        mid_y = rect.center().y()

        def xy(i: int, value: float) -> QPointF:
            x = rect.left() + i * rect.width() / (length - 1)
            y = mid_y - (value / peak) * (rect.height() / 2.0)
            return QPointF(x, y)

        painter.setPen(QPen(QColor(C["line2"]), 1))
        painter.drawLine(QPointF(rect.left(), mid_y), QPointF(rect.right(), mid_y))
        painter.setPen(faint_pen)
        painter.drawText(
            QRectF(0, mid_y - 8, 50, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "0",
        )
        painter.drawText(
            QRectF(0, rect.top() - 6, 50, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"+{peak // 1000}k" if peak >= 1000 else f"+{peak}",
        )
        painter.drawText(
            QRectF(0, rect.bottom() - 10, 50, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"-{peak // 1000}k" if peak >= 1000 else f"-{peak}",
        )

        for _label, vals, colour in self._series:
            pts = [xy(i, float(v)) for i, v in enumerate(vals)]
            painter.setPen(QPen(QColor(colour), 2))
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

        lx = rect.left() + 6
        for label, _vals, colour in self._series:
            painter.setPen(QPen(QColor(colour), 2))
            painter.drawLine(QPointF(lx, rect.top() + 4), QPointF(lx + 16, rect.top() + 4))
            painter.setPen(faint_pen)
            painter.drawText(QPointF(lx + 22, rect.top() + 8), label)
            lx += 120


class NumericItem(QTableWidgetItem):
    """Sorts by numeric value instead of lexicographic text order."""

    def __lt__(self, other: QTableWidgetItem) -> bool:  # noqa: D105
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return self.text() < other.text()


class ClickableTable(QTableWidget):
    """Table that emits the clicked row so panels can open a detail view."""

    rowClicked = Signal(int)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cellClicked.connect(lambda row, _col: self.rowClicked.emit(row))


def make_table(
    headers: list[str],
    numeric: set[int] | None = None,
    clickable: bool = False,
    row_height: int = 52,
) -> QTableWidget:
    """Bare, flat analytics table: no grid, no selection, sortable headers."""
    numeric = numeric or set()
    table = ClickableTable(0, len(headers)) if clickable else QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
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

