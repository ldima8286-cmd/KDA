"""Обзор: a dense meta dashboard — KPI strip, contested picks, top pub performers."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_int
from ..theme import C
from ..widgets import HeroIcon, Panel, StatCard, hero_cell, make_table, row_id, set_row_id, set_text


class _HeroCard(QWidget):
    """Compact hero tile: icon + name + winrate with a pick-rate bar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("heroCard", True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(10)

        self.icon = HeroIcon()
        self.icon.setFixedSize(44, 44)
        lay.addWidget(self.icon)

        col = QVBoxLayout()
        col.setSpacing(3)
        self.name = QLabel("—")
        self.name.setProperty("heroName", True)
        self.meta = QLabel("—")
        self.meta.setProperty("statSub", True)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(4)
        self.bar.setRange(0, 100)
        col.addWidget(self.name)
        col.addWidget(self.meta)
        col.addWidget(self.bar)
        lay.addLayout(col, 1)

        self.wr = QLabel("—")
        self.wr.setProperty("mono", True)
        self.wr.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.wr)

    def set_hero(self, hero: dict[str, Any], pick_max: int) -> None:
        self.icon.set_source(hero.get("icon"))
        self.name.setText(hero["name"])
        picks = int(hero.get("pro_pick") or 0)
        self.meta.setText(f"{picks} пиков · Pro")
        share = int(picks / pick_max * 100) if pick_max else 0
        self.bar.setValue(share)
        wr = float(hero.get("pro_winrate") or 0)
        self.wr.setText(f"{wr:.0f}%")
        self.wr.setStyleSheet(f"color: {C['win'] if wr >= 50 else C['loss']};")


class HomePanel(QWidget):
    heroRequested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("ОБЗОР · ТЕКУЩАЯ МЕТА")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        # --- KPI strip ---
        kpis = QHBoxLayout()
        kpis.setSpacing(14)
        self.kpi_heroes = StatCard("Героев в мете", "—")
        self.kpi_contested = StatCard("Контест-пик (Pro)", "—", accent="accent")
        self.kpi_pub = StatCard("Лучший WR в пабах", "—", accent="teal")
        self.kpi_top = StatCard("Самый популярный", "—")
        for card in (self.kpi_heroes, self.kpi_contested, self.kpi_pub, self.kpi_top):
            kpis.addWidget(card, 1)
        outer.addLayout(kpis)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 6, 0)
        content.setSpacing(14)

        contested_panel = Panel("Контест-пики (Pro)", "клик по герою в Meta Hub")
        self._cards_host = QWidget()
        self._cards_grid = QGridLayout(self._cards_host)
        self._cards_grid.setContentsMargins(0, 0, 0, 0)
        self._cards_grid.setHorizontalSpacing(12)
        self._cards_grid.setVerticalSpacing(10)
        self._cards: list[_HeroCard] = []
        contested_panel.add(self._cards_host)
        content.addWidget(contested_panel)

        split = QHBoxLayout()
        split.setSpacing(14)

        self.pubs = Panel("Топ по пабам", "клик — открыть героя")
        self._pub_table = make_table(["Герой", "Доля пиков", "WR"], numeric={1, 2}, clickable=True, first_width=200)
        self._pub_table.rowClicked.connect(self._on_pub_clicked)
        self.pubs.add(self._pub_table)
        split.addWidget(self.pubs, 3)

        self.wr_panel = Panel("Самые побеждающие (пабы)", "клик — открыть героя")
        self._wr_table = make_table(["Герой", "WR", "Игр"], numeric={1, 2}, clickable=True, first_width=200)
        self._wr_table.rowClicked.connect(self._on_wr_clicked)
        self.wr_panel.add(self._wr_table)
        split.addWidget(self.wr_panel, 2)

        content.addLayout(split, 1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        for _ in range(8):
            card = _HeroCard()
            self._cards.append(card)

    # --- data ---

    def set_meta(self, meta: dict[str, Any]) -> None:
        contested = meta.get("pro_ranked") or []
        pubs = meta.get("pub_ranked") or []
        total = meta.get("count", 0)

        self.kpi_heroes.set_value(str(total), "в справочнике")
        if contested:
            top = contested[0]
            self.kpi_contested.set_value(top["name"], f"{fmt_int(top['pro_pick'])} пиков")
        else:
            self.kpi_contested.set_value("—")
        if pubs:
            best = max(pubs, key=lambda h: h.get("pub_winrate") or 0)
            self.kpi_pub.set_value(f"{best['pub_winrate']:.1f}%", best["name"])
            top_pub = max(pubs, key=lambda h: h.get("pub_pick") or 0)
            self.kpi_top.set_value(top_pub["name"], f"{top_pub['pub_pick_share']:.2f}% пиков")

        pick_max = max((int(h.get("pro_pick") or 0) for h in contested), default=0)
        show = contested[:8]
        while self._cards_grid.count():
            self._cards_grid.takeAt(0)
        for i, hero in enumerate(show):
            card = self._cards[i]
            card.set_hero(hero, pick_max)
            card.setVisible(True)
            self._cards_grid.addWidget(card, i // 2, i % 2)
        for i in range(len(show), len(self._cards)):
            self._cards[i].setVisible(False)

        top_pub = sorted(pubs, key=lambda h: h.get("pub_pick") or 0, reverse=True)[:10]
        self._pub_table.setRowCount(len(top_pub))
        for row, hero in enumerate(top_pub):
            set_row_id(self._pub_table, row, int(hero["hero_id"]))
            self._pub_table.setCellWidget(
                row, 0, hero_cell(hero.get("img"), hero["name"], icon_url=hero.get("icon"))
            )
            set_text(self._pub_table, row, 1, f"{hero['pub_pick_share']:.2f}%", mono=True, right=True)
            set_text(
                self._pub_table,
                row,
                2,
                f"{hero['pub_winrate']:.0f}%",
                mono=True,
                right=True,
                color=C["win"] if hero["pub_winrate"] >= 50 else C["loss"],
            )

        best_wr = sorted(pubs, key=lambda h: h["pub_winrate"], reverse=True)[:10]
        self._wr_table.setRowCount(len(best_wr))
        for row, hero in enumerate(best_wr):
            set_row_id(self._wr_table, row, int(hero["hero_id"]))
            self._wr_table.setCellWidget(
                row, 0, hero_cell(hero.get("img"), hero["name"], icon_url=hero.get("icon"))
            )
            set_text(
                self._wr_table,
                row,
                1,
                f"{hero['pub_winrate']:.0f}%",
                mono=True,
                right=True,
                color=C["win"],
            )
            set_text(self._wr_table, row, 2, fmt_int(hero['pub_pick']), mono=True, right=True)

    def _on_pub_clicked(self, row: int) -> None:
        hero_id = row_id(self._pub_table, row)
        if hero_id is not None:
            self.heroRequested.emit(hero_id)

    def _on_wr_clicked(self, row: int) -> None:
        hero_id = row_id(self._wr_table, row)
        if hero_id is not None:
            self.heroRequested.emit(hero_id)
