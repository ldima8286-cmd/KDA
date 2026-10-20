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


class ComparePanel(QWidget):
    compareRequested = Signal(int, int)

    _ROWS = (
        ("Winrate (20)", lambda c: f"{c['summary']['winrate']}%", "up"),
        ("KDA", lambda c: f"{c['summary']['avg_kda']}", "up"),
        ("GPM", lambda c: f"{c['summary']['avg_gpm']:.0f}", "up"),
        ("XPM", lambda c: f"{c['summary']['avg_xpm']:.0f}", "up"),
        ("Сыграно (20)", lambda c: f"{c['summary']['matches']}", "up"),
        ("Ранг", lambda c: rank_name(c["player"].get("rank_tier")), None),
        ("Игр всего", lambda c: fmt_int((c["career"].get("wl") or {}).get("games") or 0), "up"),
        ("WR карьеры", lambda c: f"{c['career']['winrate']}%", "up"),
        ("KDA карьеры", lambda c: _num((c["career"].get("averages") or {}).get("kda")), "up"),
        ("GPM карьеры", lambda c: _num((c["career"].get("averages") or {}).get("gold_per_min")), "up"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("СРАВНЕНИЕ ИГРОКОВ")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        form = Panel("Head-to-head", "два account_id")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.input_a = QLineEdit()
        self.input_a.setPlaceholderText("account_id игрока A")
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("account_id игрока B")
        self.go = QPushButton("Сравнить")
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self._submit)
        row.addWidget(self.input_a, 1)
        row.addWidget(QLabel("VS"))
        row.addWidget(self.input_b, 1)
        row.addWidget(self.go)
        form.add_layout(row)
        outer.addWidget(form)

        self.status = QLabel("Введи два account_id и нажми «Сравнить».")
        self.status.setProperty("empty", True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.status)

        self.grid_panel = Panel("Метрики")
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(24)
        self.grid.setVerticalSpacing(12)
        self.grid_panel.add_layout(self.grid)
        outer.addWidget(self.grid_panel, 1)

        self._head_a = Avatar()
        self._head_b = Avatar()
        self._name_a = QLabel("A")
        self._name_a.setProperty("title", True)
        self._name_b = QLabel("B")
        self._name_b.setProperty("title", True)
        self.grid_panel.setVisible(False)

    def _submit(self) -> None:
        try:
            a = int(self.input_a.text().strip())
            b = int(self.input_b.text().strip())
        except ValueError:
            self.status.setText("Нужны числовые account_id.")
            return
        self.compareRequested.emit(a, b)

    def set_loading(self) -> None:
        self.status.setVisible(True)
        self.status.setText("загрузка игроков…")

    def set_result(self, data: dict[str, Any]) -> None:
        a, b = data["a"], data["b"]
        self.status.setVisible(False)
        self.grid_panel.setVisible(True)

        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._head_a.set_source(a["player"].get("avatar"))
        self._head_b.set_source(b["player"].get("avatar"))
        self._name_a.setText(a["player"].get("name") or str(a["player"].get("account_id")))
        self._name_b.setText(b["player"].get("name") or str(b["player"].get("account_id")))

        head = QHBoxLayout()
        head.addWidget(self._head_a)
        head.addWidget(self._name_a, 1)
        head.addWidget(self._head_b)
        head.addWidget(self._name_b, 1)
        self.grid.addLayout(head, 0, 0)

        for i, (label, getter, _mode) in enumerate(self._ROWS, start=1):
            va, vb = getter(a), getter(b)
            la = QLabel(va)
            la.setProperty("mono", True)
            la.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lb = QLabel(vb)
            lb.setProperty("mono", True)
            mid = QLabel(label.upper())
            mid.setProperty("statLabel", True)
            mid.setAlignment(Qt.AlignmentFlag.AlignCenter)

            na, nb = self._numeric(a, b, getter)
            if na > nb:
                la.setStyleSheet(f"color: {C['win']};")
            elif nb > na:
                lb.setStyleSheet(f"color: {C['win']};")

            self.grid.addWidget(la, i, 0)
            self.grid.addWidget(mid, i, 1)
            self.grid.addWidget(lb, i, 2)

    @staticmethod
    def _numeric(a: dict[str, Any], b: dict[str, Any], getter) -> tuple[float, float]:
        def to_num(c: dict[str, Any]) -> float:
            text = getter(c).replace("%", "")
            try:
                return float(text)
            except ValueError:
                return 0.0

        return to_num(a), to_num(b)
