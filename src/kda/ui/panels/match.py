"""Match viewer: full ten-player scoreboard, draft and the event timeline."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...format import fmt_dur, fmt_int, fmt_mark, game_mode_name, lobby_name
from ..theme import C
from ..widgets import ClickableTable, Panel, item_cell, make_table, set_text


class MatchPanel(QWidget):
    backRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        head = QHBoxLayout()
        back = QPushButton("← Назад к профилю")
        back.setProperty("ghost", True)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.backRequested.emit)
        head.addWidget(back)
        head.addStretch(1)
        self.match_label = QLabel("—")
        self.match_label.setProperty("handle", True)
        head.addWidget(self.match_label)
        outer.addLayout(head)

        self.empty = QLabel("Матч не выбран.")
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

        self.result_panel = Panel()
        result_row = QHBoxLayout()
        result_row.setSpacing(18)
        self.radiant_score = QLabel("—")
        self.radiant_score.setProperty("teamRadiant", True)
        self.result_mid = QLabel("—")
        self.result_mid.setProperty("title", True)
        self.dire_score = QLabel("—")
        self.dire_score.setProperty("teamDire", True)
        result_row.addWidget(self.radiant_score)
        result_row.addWidget(self.result_mid, 1)
        result_row.addWidget(self.dire_score)
        self.result_panel.add_layout(result_row)
        self.meta_line = QLabel("")
        self.meta_line.setProperty("handle", True)
        self.result_panel.add(self.meta_line)
        content.addWidget(self.result_panel)

        self.radiant_panel = Panel("Radiant")
        self.radiant_table = self._scoreboard()
        self.radiant_panel.add(self.radiant_table)
        content.addWidget(self.radiant_panel)

        self.dire_panel = Panel("Dire")
        self.dire_table = self._scoreboard()
        self.dire_panel.add(self.dire_table)
        content.addWidget(self.dire_panel)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)

        draft_panel = Panel("Драфт")
        self.draft_table = make_table(["#", "Team", "Пик / бан", "Герой"], numeric={0})
        self.draft_table.setMinimumHeight(320)
        draft_panel.add(self.draft_table)
        bottom.addWidget(draft_panel, 1)

        timeline_panel = Panel("Хронология", "весь процесс игры")
        self.timeline_table = make_table(["Время", "Событие"], numeric={0})
        self.timeline_table.setMinimumHeight(320)
        timeline_panel.add(self.timeline_table)
        bottom.addWidget(timeline_panel, 2)

        content.addLayout(bottom)
        content.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self._body = scroll
        self._body.hide()

    @staticmethod
    def _scoreboard() -> ClickableTable:
        return make_table(
            ["Игрок", "Ур.", "K / D / A", "LH / DN", "GPM", "XPM", "Net", "Урон", "Предметы"],
            numeric={1, 2, 3, 4, 5, 6, 7},
        )

    def set_match(self, data: dict[str, Any]) -> None:
        radiant_win = data["radiant_win"]
        winner = "RADIANT" if radiant_win else "DIRE"
        self.radiant_score.setText(f"RADIANT · {data['radiant_score']}")
        self.dire_score.setText(f"{data['dire_score']} · DIRE")
        self.result_mid.setText(f"{winner} ПОБЕДА")
        self.match_label.setText(f"матч {data['match_id']}")

        when = datetime.fromtimestamp(data["start_time"]).strftime("%d.%m.%Y %H:%M") if data["start_time"] else "—"
        parsed = "распарсен" if data.get("has_parsed") else "не распарсен · хронология ограничена"
        self.meta_line.setText(
            f"{when} · {fmt_dur(data['duration'])} · {game_mode_name(data.get('mode'))} · "
            f"{lobby_name(data.get('lobby_type'))} · патч {data.get('patch') or '—'} · {parsed}"
        )

        self._fill_team(self.radiant_table, data.get("radiant") or [])
        self._fill_team(self.dire_table, data.get("dire") or [])
        self._fill_draft(data.get("picks_bans") or [])
        self._fill_timeline(data.get("objectives") or [])

        self._body.show()
        self.empty.hide()

    def _fill_team(self, table: ClickableTable, rows: list[dict[str, Any]]) -> None:
        table.setRowCount(len(rows))
        for row, p in enumerate(rows):
            name = p.get("personaname") or (f"id {p['account_id']}" if p.get("account_id") else "—")
            label = QLabel(f"{name}  ·  {p['hero_name']}")
            label.setProperty("heroName", True)
            table.setCellWidget(row, 0, label)
            set_text(table, row, 1, p["level"], mono=True, right=True)
            set_text(table, row, 2, f"{p['kills']} / {p['deaths']} / {p['assists']}", mono=True, right=True)
            set_text(table, row, 3, f"{p['last_hits']} / {p['denies']}", mono=True, right=True)
            set_text(table, row, 4, fmt_int(p["gpm"]), mono=True, right=True)
            set_text(table, row, 5, fmt_int(p["xpm"]), mono=True, right=True)
            set_text(table, row, 6, fmt_int(p["net_worth"]), mono=True, right=True)
            set_text(table, row, 7, fmt_int(p["hero_damage"]), mono=True, right=True)
            table.setCellWidget(row, 8, item_cell(p.get("item_meta") or []))

    def _fill_draft(self, picks: list[dict[str, Any]]) -> None:
        self.draft_table.setRowCount(len(picks))
        for row, pb in enumerate(picks):
            set_text(self.draft_table, row, 0, row + 1, mono=True, right=True)
            team = "Radiant" if pb["team"] == 0 else "Dire"
            set_text(
                self.draft_table,
                row,
                1,
                team,
                color=C["win"] if pb["team"] == 0 else C["loss"],
            )
            set_text(
                self.draft_table,
                row,
                2,
                "Пик" if pb["is_pick"] else "Бан",
                color=C["ink"] if pb["is_pick"] else C["muted"],
            )
            set_text(self.draft_table, row, 3, pb.get("hero_name") or f"hero #{pb['hero_id']}")

    def _fill_timeline(self, objectives: list[dict[str, Any]]) -> None:
        self.timeline_table.setRowCount(len(objectives))
        for row, obj in enumerate(objectives):
            set_text(self.timeline_table, row, 0, fmt_mark(obj["time"]), mono=True, right=True)
            team = obj.get("team")
            color = C["win"] if team == 0 else C["loss"] if team == 1 else None
            set_text(self.timeline_table, row, 1, obj["label"], color=color)

    def clear(self) -> None:
        self._body.hide()
        self.empty.show()
