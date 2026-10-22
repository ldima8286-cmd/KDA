"""Skill Lab: a single player's dossier — winrate, KDA, GPM/XPM, heroes, form."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...analytics.skill_lab import BUCKET
from ...format import fmt_ago, fmt_dur, fmt_int, fmt_k, rank_name
from ..theme import C
from ..widgets import (
    Avatar,
    Panel,
    RankBadge,
    StatCard,
    TrendChart,
    hero_cell,
    make_table,
    set_text,
)


class SkillLabPanel(QWidget):
    matchRequested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("SKILL LAB")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        self.empty = QLabel("Найди игрока в поиске сверху — ник или Steam ID.")
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

        # --- player head ---
        head = Panel()
        head_row = QHBoxLayout()
        head_row.setSpacing(16)
        self.avatar = Avatar()
        id_box = QVBoxLayout()
        id_box.setSpacing(3)
        self.name_label = QLabel("—")
        self.name_label.setProperty("title", True)
        self.handle = QLabel("")
        self.handle.setProperty("handle", True)
        id_box.addWidget(self.name_label)
        id_box.addWidget(self.handle)
        id_box.addStretch(1)
        head_row.addWidget(self.avatar)
        head_row.addLayout(id_box, 1)

        rank_box = QVBoxLayout()
        rank_box.setSpacing(4)
        rank_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rank_badge = RankBadge()
        self.rank_chip = QLabel("")
        self.rank_chip.setProperty("rank", True)
        self.rank_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rank_box.addWidget(self.rank_badge, 0, Qt.AlignmentFlag.AlignRight)
        rank_box.addWidget(self.rank_chip, 0, Qt.AlignmentFlag.AlignRight)
        head_row.addLayout(rank_box)
        head.add_layout(head_row)
        content.addWidget(head)

        # --- stat cards ---
        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.card_wr = StatCard("Winrate (20)", "—")
        self.card_kda = StatCard("Средний KDA", "—")
        self.card_gpm = StatCard("GPM", "—", accent="accent")
        self.card_played = StatCard("Сыграно", "—")
        for card in (self.card_wr, self.card_kda, self.card_gpm, self.card_played):
            cards.addWidget(card, 1)
        content.addLayout(cards)

        # --- trend + best heroes ---
        split = QHBoxLayout()
        split.setSpacing(14)

        chart_panel = Panel("Динамика winrate", f"окно {BUCKET} игр")
        self.chart = TrendChart()
        chart_panel.add(self.chart)
        split.addWidget(chart_panel, 3)

        heroes_panel = Panel("Лучшие герои", "по последним матчам")
        self.heroes_table = make_table(["Герой", "Игр", "WR", "KDA"], numeric={1, 2, 3})
        heroes_panel.add(self.heroes_table)
        split.addWidget(heroes_panel, 2)

        content.addLayout(split)

        # --- career ---
        career_panel = Panel("Карьера", "вся история аккаунта")
        career_grid = QGridLayout()
        career_grid.setHorizontalSpacing(28)
        career_grid.setVerticalSpacing(14)
        self._career_values: dict[str, QLabel] = {}
        specs = [
            ("games", "Игр"),
            ("winrate", "Winrate"),
            ("kda", "KDA"),
            ("gpm", "GPM"),
            ("xpm", "XPM"),
            ("last_hits", "Добивания"),
            ("hero_damage", "Урон по героям"),
            ("tower_damage", "Урон по строениям"),
        ]
        for i, (key, label) in enumerate(specs):
            box = QVBoxLayout()
            box.setSpacing(2)
            lab = QLabel(label.upper())
            lab.setProperty("statLabel", True)
            val = QLabel("—")
            val.setProperty("mono", True)
            box.addWidget(lab)
            box.addWidget(val)
            self._career_values[key] = val
            career_grid.addLayout(box, i // 4, i % 4)
        career_panel.add_layout(career_grid)

        popular_head = QLabel("ПОПУЛЯРНЫЕ ГЕРОИ · ЗА ВСЮ ИСТОРИЮ")
        popular_head.setProperty("sectionLabel", True)
        career_panel.add(popular_head)
        self.popular_table = make_table(["Герой", "Игр", "W / L", "WR"], numeric={1, 2, 3})
        self.popular_table.setMaximumHeight(230)
        career_panel.add(self.popular_table)
        content.addWidget(career_panel)

        # --- recent matches ---
        recent_panel = Panel("Последние матчи", "клик — открыть матч")
        self.recent_table = make_table(
            ["Герой", "Итог", "K / D / A", "GPM / XPM", "Длит.", "Когда"],
            numeric={2, 3, 4, 5},
            clickable=True,
        )
        self.recent_table.rowClicked.connect(self._on_recent_clicked)
        recent_panel.add(self.recent_table)
        content.addWidget(recent_panel)

        content.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self._body = scroll
        self._body.hide()
        self._recent_ids: list[int] = []

    # --- data ---

    def set_profile(self, profile: dict[str, Any]) -> None:
        player = profile["player"]
        summary = profile["summary"]

        self.avatar.set_source(player.get("avatar"))
        self.name_label.setText(player.get("name") or str(player.get("account_id")))
        country = player.get("country")
        self.handle.setText(f"account_id {player.get('account_id')}" + (f" · {country}" if country else ""))
        self.rank_badge.set_rank(player.get("rank_tier"), player.get("leaderboard_rank"))
        self.rank_chip.setText(rank_name(player.get("rank_tier")))

        self.card_wr.set_value(
            f"{summary['winrate']}%",
            f"{summary['wins']}W · {summary['losses']}L",
        )
        self.card_kda.set_value(
            f"{summary['avg_kda']}",
            f"{summary['avg_kills']} / {summary['avg_deaths']} / {summary['avg_assists']}",
        )
        self.card_gpm.set_value(f"{summary['avg_gpm']:.0f}", f"XPM {summary['avg_xpm']:.0f}")
        self.card_played.set_value(f"{summary['matches']}", f"{summary['total_hours']} ч в игре")

        self.chart.set_points(profile.get("trend") or [])

        heroes = (profile.get("heroes") or [])[:12]
        self.heroes_table.setRowCount(len(heroes))
        for row, hero in enumerate(heroes):
            self.heroes_table.setCellWidget(
                row, 0, hero_cell(hero.get("img"), hero["name"], icon_url=hero.get("icon"))
            )
            set_text(self.heroes_table, row, 1, hero["matches"], mono=True, right=True)
            set_text(self.heroes_table, row, 2, f"{hero['winrate']}%", mono=True, right=True)
            set_text(self.heroes_table, row, 3, hero["avg_kda"], mono=True, right=True)

        self._set_career(profile.get("career") or {})

        recent = profile.get("recent") or []
        self._recent_ids = [int(m["match_id"]) for m in recent]
        self.recent_table.setRowCount(len(recent))
        for row, match in enumerate(recent):
            self.recent_table.setCellWidget(
                row,
                0,
                hero_cell(match.get("img"), match["hero_name"], icon_url=match.get("icon")),
            )
            set_text(
                self.recent_table,
                row,
                1,
                "Победа" if match["win"] else "Поражение",
                color=C["win"] if match["win"] else C["loss"],
            )
            set_text(
                self.recent_table,
                row,
                2,
                f"{match['kills']} / {match['deaths']} / {match['assists']}",
                mono=True,
                right=True,
            )
            set_text(
                self.recent_table,
                row,
                3,
                f"{fmt_k(match['gpm'])} / {fmt_k(match['xpm'])}",
                mono=True,
                right=True,
            )
            set_text(self.recent_table, row, 4, fmt_dur(match["duration"]), mono=True, right=True)
            set_text(self.recent_table, row, 5, fmt_ago(match["start_time"]), mono=True, right=True)

        self._body.show()
        self.empty.hide()

    def set_career(self, career: dict[str, Any]) -> None:
        self._set_career(career)

    def _set_career(self, career: dict[str, Any]) -> None:
        averages = career.get("averages") or {}
        wl = career.get("wl") or {}
        games = wl.get("games") or 0

        self._career_values["games"].setText(fmt_int(games) if games else "—")
        self._career_values["winrate"].setText(
            f"{career['winrate']}%  ·  {wl.get('win', 0)}W / {wl.get('lose', 0)}L" if games else "—"
        )
        for key, field in (
            ("kda", "kda"),
            ("gpm", "gold_per_min"),
            ("xpm", "xp_per_min"),
            ("last_hits", "last_hits"),
            ("hero_damage", "hero_damage"),
            ("tower_damage", "tower_damage"),
        ):
            value = averages.get(field)
            self._career_values[key].setText(fmt_int(value) if value else "—")

        popular = career.get("popular_heroes") or []
        self.popular_table.setRowCount(len(popular))
        for row, hero in enumerate(popular):
            label = hero.get("name") or f"#{hero['hero_id']}"
            self.popular_table.setCellWidget(row, 0, hero_cell(hero.get("img"), label))
            set_text(self.popular_table, row, 1, fmt_int(hero["games"]), mono=True, right=True)
            set_text(self.popular_table, row, 2, f"{hero['wins']} / {hero['lost']}", mono=True, right=True)
            set_text(self.popular_table, row, 3, f"{hero['winrate']}%", mono=True, right=True)

    def _on_recent_clicked(self, row: int) -> None:
        if 0 <= row < len(self._recent_ids):
            self.matchRequested.emit(self._recent_ids[row])

    def clear(self) -> None:
        self._body.hide()
        self.empty.show()

