"""Обзор: current meta at a glance (contested picks + top pub performers)."""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..widgets import Panel, hero_cell, make_table, set_text


class HomePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("ОБЗОР")
        kicker.setProperty("kicker", True)
        title = QLabel("Киберспорт-аналитика в одном месте")
        title.setProperty("title", True)
        subtitle = QLabel(
            "Найди игрока по нику или Steam ID в поиске сверху — откроется Skill Lab. "
            "Ниже — текущая мета Dota 2."
        )
        subtitle.setProperty("subtitle", True)
        subtitle.setWordWrap(True)
        outer.addWidget(kicker)
        outer.addWidget(title)
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 6, 0)
        content.setSpacing(14)

        self.contested = Panel("Самые контестуемые герои (Pro)")
        self._chips_host = QWidget()
        self._chips_grid = QGridLayout(self._chips_host)
        self._chips_grid.setContentsMargins(0, 0, 0, 0)
        self._chips_grid.setHorizontalSpacing(8)
        self._chips_grid.setVerticalSpacing(8)
        self.contested.add(self._chips_host)
        content.addWidget(self.contested)

        self.pubs = Panel("Топ по пабам", "pick rate")
        self._pub_table = make_table(["Герой", "Pick share", "Побед"], numeric={1, 2})
        self.pubs.add(self._pub_table)
        content.addWidget(self.pubs)

        content.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    # --- data ---

    def set_meta(self, meta: dict[str, Any]) -> None:
        contested = meta.get("pro_ranked") or []
        self.contested.note_label.setText(f"{meta.get('count', 0)} героев")

        while self._chips_grid.count():
            item = self._chips_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, hero in enumerate(contested[:8]):
            chip = QLabel(f"{hero['name']} · {hero['pro_winrate']}%")
            chip.setProperty("chip", True)
            self._chips_grid.addWidget(chip, i // 4, i % 4)
        self._chips_host.setVisible(bool(contested))

        top_pub = (meta.get("pub_ranked") or [])[:8]
        self._pub_table.setRowCount(len(top_pub))
        for row, hero in enumerate(top_pub):
            self._pub_table.setCellWidget(row, 0, hero_cell(hero.get("img"), hero["name"]))
            set_text(self._pub_table, row, 1, f"{hero['pub_pick_share']}%", mono=True, right=True)
            set_text(self._pub_table, row, 2, f"{hero['pub_winrate']}%", mono=True, right=True)
