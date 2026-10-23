"""Pro scene: recent professional matches, top teams and pro players."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_dur
from ..theme import C
from ..widgets import Panel, hero_cell, make_table, set_text


class ProPanel(QWidget):
    matchRequested = Signal(int)
    playerRequested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("PRO SCENE")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 6, 0)
        content.setSpacing(14)

        self._matches_panel = matches_panel = Panel("Последние про-матчи", "клик — открыть матч")
        self.matches_table = make_table(
            ["Команды", "Счёт", "Турнир", "Длит.", "Когда"],
            numeric={1, 3},
            clickable=True,
        )
        self.matches_table.rowClicked.connect(self._on_match_clicked)
        matches_panel.add(self.matches_table)
        content.addWidget(matches_panel, 3)

        split = QHBoxLayout()
        split.setSpacing(14)

        self._teams_panel = teams_panel = Panel("Топ команд", "по рейтингу")
        self.teams_table = make_table(
            ["Команда", "Рейтинг", "W / L", "WR"], numeric={1, 2, 3},
            first_width=240, row_height=46,
        )
        teams_panel.add(self.teams_table)
        split.addWidget(teams_panel, 1)

        self._players_panel = players_panel = Panel("Про-игроки", "клик — открыть профиль")
        self.players_table = make_table(
            ["Игрок", "Команда", "Страна"], numeric=set(), clickable=True,
            first_width=200, row_height=46,
        )
        self.players_table.rowClicked.connect(self._on_player_clicked)
        players_panel.add(self.players_table)
        split.addWidget(players_panel, 1)

        content.addLayout(split, 2)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self._match_ids: list[int] = []
        self._player_ids: list[int] = []
        self._game = "dota2"

    def set_game(self, game: str) -> None:
        self._game = game or "dota2"
        if self._game == "cs2":
            self._matches_panel.note_label.setText("нет публичных матчей без провайдера")
            self._teams_panel.note_label.setText("справочный снимок · не live")
        else:
            self._matches_panel.note_label.setText("клик — открыть матч")
            self._teams_panel.note_label.setText("по рейтингу")

    def set_scene(self, data: dict[str, Any]) -> None:
        matches = data.get("matches") or []
        self._match_ids = [int(m["match_id"]) for m in matches]
        self.matches_table.setRowCount(len(matches))
        for row, m in enumerate(matches):
            matchup = f"{m['radiant_name']} vs {m['dire_name']}"
            set_text(self.matches_table, row, 0, matchup)
            win_tag = "R" if m["radiant_win"] else "D"
            set_text(
                self.matches_table,
                row,
                1,
                f"{m['radiant_score']}:{m['dire_score']} ({win_tag})",
                mono=True,
                right=True,
                color=C["win"] if m["radiant_win"] else C["loss"],
            )
            set_text(self.matches_table, row, 2, m["league_name"] or "—")
            set_text(self.matches_table, row, 3, fmt_dur(m["duration"]), mono=True, right=True)
            when = (
                datetime.fromtimestamp(m["start_time"]).strftime("%d.%m %H:%M")
                if m["start_time"]
                else "—"
            )
            set_text(self.matches_table, row, 4, when, mono=True, right=True)

        teams = data.get("teams") or []
        self.teams_table.setRowCount(len(teams))
        for row, t in enumerate(teams):
            name = f"{t['name']} [{t['tag']}]" if t["tag"] else t["name"]
            self.teams_table.setCellWidget(
                row, 0, hero_cell(t.get("logo_url"), name, size=30)
            )
            set_text(self.teams_table, row, 1, t["rating"], mono=True, right=True)
            set_text(self.teams_table, row, 2, f"{t['wins']} / {t['losses']}", mono=True, right=True)
            set_text(self.teams_table, row, 3, f"{t['winrate']}%", mono=True, right=True,
                     color=C["win"] if t["winrate"] >= 50 else C["loss"])

        players = (data.get("players") or [])[:100]
        self._player_ids = [int(p["account_id"]) for p in players]
        self.players_table.setRowCount(len(players))
        for row, p in enumerate(players):
            self.players_table.setCellWidget(
                row, 0, hero_cell(p.get("avatar"), p["name"], size=30)
            )
            team = f"{p['team_name']} [{p['team_tag']}]" if p["team_tag"] else (p["team_name"] or "—")
            set_text(self.players_table, row, 1, team)
            set_text(self.players_table, row, 2, (p.get("country") or "—").upper(), mono=True)

    def _on_match_clicked(self, row: int) -> None:
        if 0 <= row < len(self._match_ids):
            self.matchRequested.emit(self._match_ids[row])

    def _on_player_clicked(self, row: int) -> None:
        if 0 <= row < len(self._player_ids):
            account_id = self._player_ids[row]
            if account_id:
                self.playerRequested.emit(account_id)
