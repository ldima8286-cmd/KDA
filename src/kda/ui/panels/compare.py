"""Head-to-head comparison of two players."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_int, rank_name
from ..theme import C
from ..widgets import Avatar, Panel, hero_cell, make_table, set_text


def _num(value: object) -> str:
    if value in (None, ""):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{int(number):,}" if number == int(number) else f"{number:,.1f}"


class _CompareRow(QWidget):
    """A single metric row: A value | label | B value, with a ratio bar."""

    def __init__(self, label: str, va: str, vb: str, na: float, nb: float,
                 higher_better: bool = True, lower_better: bool = False,
                 show_bar: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._va, self._vb = va, vb

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(4)

        head = QHBoxLayout()
        head.setSpacing(10)
        self._la = QLabel(va)
        self._la.setProperty("mono", True)
        self._la.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._lb = QLabel(vb)
        self._lb.setProperty("mono", True)
        self._lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mid = QLabel(label.upper())
        mid.setProperty("statLabel", True)
        mid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        a_wins = na > nb if not lower_better else na < nb
        b_wins = nb > na if not lower_better else nb < na
        if na != nb:
            if a_wins:
                self._la.setStyleSheet(f"color: {C['win']};")
            elif b_wins:
                self._lb.setStyleSheet(f"color: {C['win']};")

        head.addWidget(self._la, 1)
        head.addWidget(mid, 2)
        head.addWidget(self._lb, 1)
        outer.addLayout(head)

        if show_bar:
            bar = _RatioBar(na, nb)
            bar.setFixedHeight(6)
            outer.addWidget(bar)


class _RatioBar(QWidget):
    """Two-sided horizontal bar showing relative A:B strength."""

    def __init__(self, a: float, b: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._a = max(0.0, a)
        self._b = max(0.0, b)

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        mid = width / 2
        total = self._a + self._b
        if total <= 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(C["line"]))
            painter.drawRoundedRect(QRectF(0, 0, width, self.height()), 3, 3)
            return

        share_a = self._a / total
        col_a = QColor(C["teal"])
        col_b = QColor(C["win"])
        painter.setPen(Qt.PenStyle.NoPen)
        # left (A) grows leftward from center
        painter.setBrush(col_a)
        painter.drawRoundedRect(QRectF(mid - share_a * mid, 0, share_a * mid, self.height()), 3, 3)
        # right (B) grows rightward from center
        share_b = self._b / total
        painter.setBrush(col_b)
        painter.drawRoundedRect(QRectF(mid, 0, share_b * mid, self.height()), 3, 3)


class _DualTrendChart(QWidget):
    """Two win-rate trend lines (A teal, B green) on a shared 0-100 grid."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._a: list[dict[str, Any]] = []
        self._b: list[dict[str, Any]] = []
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, a: list[dict[str, Any]], b: list[dict[str, Any]]) -> None:
        self._a = a or []
        self._b = b or []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(34, 12, -12, -18)
        if rect.width() < 40 or rect.height() < 20:
            return

        font = QFont()
        font.setPixelSize(10)
        painter.setFont(font)
        grid_pen = QPen(QColor(C["line"]))
        faint_pen = QPen(QColor(C["faint"]))
        for tick in (0, 25, 50, 75, 100):
            y = rect.bottom() - (tick / 100.0) * rect.height()
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(faint_pen)
            painter.drawText(
                QRectF(0, y - 8, 30, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(tick),
            )

        n = max(len(self._a), len(self._b))
        if n == 0:
            painter.setPen(faint_pen)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "нет данных")
            return

        def xy(i: int, value: float) -> QPointF:
            x = rect.left() if n == 1 else rect.left() + i * rect.width() / (n - 1)
            y = rect.bottom() - (max(0.0, min(100.0, value)) / 100.0) * rect.height()
            return QPointF(x, y)

        def draw(series: list[dict[str, Any]], color: str) -> None:
            if not series:
                return
            pts = [xy(i, float(p.get("winrate", 0.0))) for i, p in enumerate(series)]
            painter.setPen(QPen(QColor(color), 2))
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            for pt in pts:
                painter.drawEllipse(pt, 2, 2)

        draw(self._a, C["teal"])
        draw(self._b, C["win"])


class _HeroPoolCard(QWidget):
    """Side-by-side hero pools for A and B, each a compact hero table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(18)

        self._ta = make_table(["Герой", "Игр", "WR"], numeric={1, 2}, first_width=200, row_height=44)
        self._tb = make_table(["Герой", "Игр", "WR"], numeric={1, 2}, first_width=200, row_height=44)
        for table, tag in ((self._ta, "A"), (self._tb, "B")):
            box = QVBoxLayout()
            box.setSpacing(6)
            label = QLabel(tag)
            label.setProperty("statLabel", True)
            box.addWidget(label)
            box.addWidget(table)
            outer.addLayout(box, 1)

    def set_data(self, a: list[dict[str, Any]], b: list[dict[str, Any]]) -> None:
        rows = max(len(a), len(b), 1)
        for table in (self._ta, self._tb):
            table.setFixedHeight(40 + rows * 44)
        for table, heroes in ((self._ta, a), (self._tb, b)):
            table.setRowCount(len(heroes))
            for row, hero in enumerate(heroes):
                table.setCellWidget(
                    row,
                    0,
                    hero_cell(hero.get("img"), str(hero.get("name") or hero.get("hero_id")),
                              icon_url=hero.get("icon")),
                )
                set_text(table, row, 1, fmt_int(hero.get("matches")), mono=True, right=True)
                wr = float(hero.get("winrate") or 0.0)
                set_text(
                    table, row, 2, f"{wr:.0f}%", mono=True, right=True,
                    color=C["win"] if wr >= 50 else C["loss"],
                )


class ComparePanel(QWidget):
    compareRequested = Signal(str, str)

    _ROWS = (
        ("Winrate (20)", lambda c: f"{c['summary']['winrate']}%", "up"),
        ("KDA", lambda c: f"{c['summary']['avg_kda']}", "up"),
        ("GPM", lambda c: f"{c['summary']['avg_gpm']:.0f}", "up"),
        ("XPM", lambda c: f"{c['summary']['avg_xpm']:.0f}", "up"),
        ("Убийства", lambda c: f"{c['summary'].get('avg_kills', 0):.1f}", "up"),
        ("Смерти", lambda c: f"{c['summary'].get('avg_deaths', 0):.1f}", "down"),
        ("Помощь", lambda c: f"{c['summary'].get('avg_assists', 0):.1f}", "up"),
        ("Часов", lambda c: f"{c['summary'].get('total_hours', 0):.1f}", "up"),
        ("Матчей (20)", lambda c: fmt_int(c['summary']['matches']), "up"),
        ("Ранг", lambda c: rank_name(c["player"].get("rank_tier")), None),
        ("Матчей всего", lambda c: fmt_int((c["career"].get("wl") or {}).get("games") or 0), "up"),
        ("WR карьеры", lambda c: f"{c['career']['winrate']}%", "up"),
        ("KDA карьеры", lambda c: _num((c["career"].get("averages") or {}).get("kda")), "up"),
        ("GPM карьеры", lambda c: _num((c["career"].get("averages") or {}).get("gold_per_min")), "up"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll)

        kicker = QLabel("HEAD-TO-HEAD")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        form = Panel("Сравнение игроков", "ник или account_id")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.input_a = QLineEdit()
        self.input_a.setPlaceholderText("Игрок A — ник или account_id")
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("Игрок B — ник или account_id")
        self.go = QPushButton("Сравнить")
        self.go.setProperty("primary", True)
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self._submit)
        vs = QLabel("VS")
        vs.setProperty("statLabel", True)
        row.addWidget(self.input_a, 1)
        row.addWidget(vs)
        row.addWidget(self.input_b, 1)
        row.addWidget(self.go)
        form.add_layout(row)
        outer.addWidget(form)

        self.status = QLabel("Введи ник или account_id двух игроков и нажми «Сравнить».")
        self.status.setProperty("empty", True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.status)

        self.head_panel = Panel()
        head_row = QHBoxLayout()
        head_row.setSpacing(16)
        self._head_a = Avatar()
        self._name_a = QLabel("A")
        self._name_a.setProperty("title", True)
        self._name_a.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._name_a.setMinimumWidth(60)
        vs_head = QLabel("VS")
        vs_head.setProperty("statLabel", True)
        self._name_b = QLabel("B")
        self._name_b.setProperty("title", True)
        self._name_b.setMinimumWidth(60)
        self._name_b.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._head_b = Avatar()
        head_row.addWidget(self._head_a)
        head_row.addWidget(self._name_a, 1)
        head_row.addWidget(vs_head)
        head_row.addWidget(self._name_b, 1)
        head_row.addWidget(self._head_b)
        self.head_panel.add_layout(head_row)
        self.head_panel.setVisible(False)
        outer.addWidget(self.head_panel)

        self.body = Panel("Метрики", "A ← бирюзовый · зелёный → B")
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)
        self.body.add_layout(self.rows_layout)
        self.body.setVisible(False)
        outer.addWidget(self.body)

        self.trend_panel = Panel("Форма", "винрейт за 20 игр · A бирюзовый · B зелёный")
        self.trend = _DualTrendChart()
        self.trend_panel.add(self.trend)
        self.trend_panel.setVisible(False)
        outer.addWidget(self.trend_panel)

        self.heroes_panel = Panel("Пул героев", "топ-5 по числу игр")
        self.heroes_card = _HeroPoolCard()
        self.heroes_panel.add(self.heroes_card)
        self.heroes_panel.setVisible(False)
        outer.addWidget(self.heroes_panel)

        outer.addStretch(1)

    def _submit(self) -> None:
        a = self.input_a.text().strip()
        b = self.input_b.text().strip()
        if not a or not b:
            self.status.setText("Заполни оба поля — ник или account_id.")
            return
        self.compareRequested.emit(a, b)

    def set_loading(self) -> None:
        self.status.setVisible(True)
        self.status.setText("загрузка игроков…")

    def set_error(self, message: str) -> None:
        self.status.setVisible(True)
        self.status.setText(message)

    def set_result(self, data: dict[str, Any]) -> None:
        a, b = data["a"], data["b"]
        self.status.setVisible(False)
        self.head_panel.setVisible(True)
        self.body.setVisible(True)
        self.trend_panel.setVisible(True)
        self.heroes_panel.setVisible(True)

        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._head_a.set_source(a["player"].get("avatar"))
        self._head_b.set_source(b["player"].get("avatar"))
        na = _name(a)
        nb = _name(b)
        self._name_a.setText(_elide(na))
        self._name_b.setText(_elide(nb))
        self._name_a.setToolTip(na)
        self._name_b.setToolTip(nb)

        for label, getter, mode in self._ROWS:
            va, vb = getter(a), getter(b)
            numa, numb = self._numeric(a, b, getter)
            row = _CompareRow(
                label, va, vb, numa, numb,
                higher_better=(mode == "up"), lower_better=(mode == "down"),
                show_bar=(mode is not None),
            )
            self.rows_layout.addWidget(row)
        self.rows_layout.addStretch(1)

        self.trend.set_data(a.get("trend") or [], b.get("trend") or [])
        self.heroes_card.set_data(
            (a.get("heroes") or [])[:5], (b.get("heroes") or [])[:5]
        )

    @staticmethod
    def _numeric(a: dict[str, Any], b: dict[str, Any], getter) -> tuple[float, float]:
        def to_num(c: dict[str, Any]) -> float:
            text = str(getter(c)).replace("%", "").replace(",", "").replace(" ", "").replace("\u2009", "")
            try:
                return float(text)
            except ValueError:
                return 0.0

        return to_num(a), to_num(b)


def _name(c: dict[str, Any]) -> str:
    return c["player"].get("name") or str(c["player"].get("account_id"))


def _elide(text: str, limit: int = 22) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
