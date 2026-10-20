"""Hero screen: matchup spread, winrate by game length and item popularity."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_int
from ..theme import C
from ..widgets import HeroIcon, Panel, TrendChart, item_cell, make_table, set_text

_PHASES = (
    ("start_game_items", "Старт"),
    ("early_game_items", "Ранняя игра"),
    ("mid_game_items", "Средняя игра"),
    ("late_game_items", "Поздняя игра"),
)


class HeroPanel(QWidget):
    backRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        head = QHBoxLayout()
        back = QPushButton("← Назад в Meta Hub")
        back.setProperty("ghost", True)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.backRequested.emit)
        head.addWidget(back)
        head.addStretch(1)
        self.hero_label = QLabel("—")
        self.hero_label.setProperty("handle", True)
        head.addWidget(self.hero_label)
        outer.addLayout(head)

        self.empty = QLabel("Герой не выбран.")
        self.empty.setProperty("empty", True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.empty)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 6, 0)
        content.setSpacing(14)

        title_panel = Panel()
        title_row = QHBoxLayout()
        title_row.setSpacing(16)
        self.hero_icon = HeroIcon()
        self.hero_icon.setFixedSize(48, 48)
        self.hero_name = QLabel("—")
        self.hero_name.setProperty("title", True)
        title_row.addWidget(self.hero_icon)
        title_row.addWidget(self.hero_name, 1)
        title_panel.add_layout(title_row)
        content.addWidget(title_panel)

        split = QHBoxLayout()
        split.setSpacing(14)

        dur_panel = Panel("Winrate по длине матча", "минуты")
        self.dur_chart = TrendChart()
        dur_panel.add(self.dur_chart)
        split.addWidget(dur_panel, 3)

        matchups_panel = Panel("Против кого")
        self.matchups_table = make_table(["Герой", "Игр", "WR"], numeric={1, 2})
        matchups_panel.add(self.matchups_table)
        split.addWidget(matchups_panel, 2)

        content.addLayout(split)

        items_panel = Panel("Популярные предметы")
        items_grid = QGridLayout()
        items_grid.setHorizontalSpacing(18)
        items_grid.setVerticalSpacing(10)
        self._item_rows: dict[str, QWidget] = {}
        for i, (key, label) in enumerate(_PHASES):
            lab = QLabel(label.upper())
            lab.setProperty("statLabel", True)
            host = QWidget()
            host_lay = QHBoxLayout(host)
            host_lay.setContentsMargins(0, 0, 0, 0)
            host_lay.setSpacing(4)
            host_lay.addStretch(1)
            self._item_rows[key] = host
            items_grid.addWidget(lab, i, 0)
            items_grid.addWidget(host, i, 1)
        items_panel.add_layout(items_grid)
        content.addWidget(items_panel)

        content.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self._body = scroll
        self._body.hide()

    def set_hero(self, data: dict[str, Any]) -> None:
        self.hero_label.setText(f"герой {data.get('hero_id')}")
        self.hero_name.setText(data.get("name") or "—")
        self.hero_icon.set_source(data.get("icon") or data.get("img"))

        durations = data.get("durations") or []
        self.dur_chart.set_points(
            [{"game": d["minute"], "winrate": d["winrate"]} for d in durations]
        )

        matchups = data.get("matchups") or []
        self.matchups_table.setRowCount(len(matchups))
        for row, mu in enumerate(matchups):
            self.matchups_table.setCellWidget(row, 0, self._matchup_cell(mu))
            set_text(self.matchups_table, row, 1, fmt_int(mu["games"]), mono=True, right=True)
            wr = mu["winrate"]
            set_text(
                self.matchups_table,
                row,
                2,
                f"{wr}%",
                mono=True,
                right=True,
                color=C["win"] if wr >= 50 else C["loss"],
            )

        items = data.get("items") or {}
        for key, _label in _PHASES:
            host = self._item_rows[key]
            lay = host.layout()
            while lay.count() > 1:
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            for meta in items.get(key) or []:
                lay.insertWidget(lay.count() - 1, self._item_tile(meta))

        self._body.show()
        self.empty.hide()

    @staticmethod
    def _matchup_cell(mu: dict[str, Any]) -> QWidget:
        from ..widgets import hero_cell

        return hero_cell(mu.get("icon"), mu["name"])

    @staticmethod
    def _item_tile(meta: dict[str, str]) -> QWidget:
        return item_cell([meta])

    def clear(self) -> None:
        self._body.hide()
        self.empty.show()
