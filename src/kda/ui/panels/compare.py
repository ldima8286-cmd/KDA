"""Head-to-head comparison of two players."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_int, rank_name
from ..theme import C
from ..widgets import Avatar, Panel


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
                 higher_better: bool = True, parent: QWidget | None = None) -> None:
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

        if higher_better:
            if na > nb:
                self._la.setStyleSheet(f"color: {C['win']};")
            elif nb > na:
                self._lb.setStyleSheet(f"color: {C['win']};")

        head.addWidget(self._la, 1)
        head.addWidget(mid, 2)
        head.addWidget(self._lb, 1)
        outer.addLayout(head)

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


class ComparePanel(QWidget):
    compareRequested = Signal(str, str)

    _ROWS = (
        ("Winrate (20)", lambda c: f"{c['summary']['winrate']}", "up"),
        ("KDA", lambda c: f"{c['summary']['avg_kda']}", "up"),
        ("GPM", lambda c: f"{c['summary']['avg_gpm']:.0f}", "up"),
        ("XPM", lambda c: f"{c['summary']['avg_xpm']:.0f}", "up"),
        ("Игр (20)", lambda c: f"{c['summary']['matches']}", "up"),
        ("Ранг", lambda c: rank_name(c["player"].get("rank_tier")), None),
        ("Игр всего", lambda c: fmt_int((c["career"].get("wl") or {}).get("games") or 0), "up"),
        ("WR карьеры", lambda c: f"{c['career']['winrate']}", "up"),
        ("KDA карьеры", lambda c: _num((c["career"].get("averages") or {}).get("kda")), "up"),
        ("GPM карьеры", lambda c: _num((c["career"].get("averages") or {}).get("gold_per_min")), "up"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("HEAD-TO-HEAD")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        form = Panel("Compare two players", "ник или account_id")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.input_a = QLineEdit()
        self.input_a.setPlaceholderText("Игрок A — ник или account_id")
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("Игрок B — ник или account_id")
        self.go = QPushButton("Compare")
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

        self.status = QLabel("Введи ник или account_id двух игроков и нажми «Compare».")
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

        self.body = Panel("Метрики", "A ← синий · зелёный → B")
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)
        self.body.add_layout(self.rows_layout)
        self.body.setVisible(False)
        outer.addWidget(self.body, 1)

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
            row = _CompareRow(label, va, vb, numa, numb, higher_better=(mode == "up"))
            self.rows_layout.addWidget(row)
        self.rows_layout.addStretch(1)

    @staticmethod
    def _numeric(a: dict[str, Any], b: dict[str, Any], getter) -> tuple[float, float]:
        def to_num(c: dict[str, Any]) -> float:
            text = str(getter(c)).replace("%", "").replace(",", "")
            try:
                return float(text)
            except ValueError:
                return 0.0

        return to_num(a), to_num(b)


def _name(c: dict[str, Any]) -> str:
    return c["player"].get("name") or str(c["player"].get("account_id"))


def _elide(text: str, limit: int = 22) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
