"""Meta Hub: sortable hero meta table with a Pro / public-rankings toggle."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..widgets import Panel, hero_cell, make_table, row_id, set_row_id, set_text

_MODES = (("pro", "Pro"), ("pub", "Пабы"))

_LABELS = {
    "dota2": ("героев", "Герой"),
    "cs2": ("карт", "Карта"),
}


class MetaHubPanel(QWidget):
    heroRequested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._meta: dict[str, Any] = {}
        self._mode = "pro"
        self._game = "dota2"
        self._headers = ["Герой", "Pro pick", "Pro WR", "Pub pick", "Pub WR", "Роли"]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        kicker = QLabel("META HUB")
        kicker.setProperty("kicker", True)
        outer.addWidget(kicker)

        self._panel = Panel("Мета героев", "загрузка…")
        outer.addWidget(self._panel, 1)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for key, label in _MODES:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(btn)
            self._buttons[key] = btn
            toolbar.addWidget(btn)
        toolbar.addStretch(1)
        self._panel.add_layout(toolbar)

        self._table = make_table(
            list(self._headers),
            numeric={1, 2, 3, 4},
            clickable=True,
        )
        self._panel.add(self._table)
        group.buttonClicked.connect(self._on_mode_clicked)
        self._table.rowClicked.connect(self._on_row_clicked)

    def _on_row_clicked(self, row: int) -> None:
        hero_id = row_id(self._table, row)
        if hero_id is not None:
            self.heroRequested.emit(hero_id)

    # --- data ---

    def set_game(self, game: str) -> None:
        game = game or "dota2"
        if game == self._game:
            return
        self._game = game
        noun, subject = _LABELS.get(game, ("героев", "Герой"))
        roles = "Тип" if game == "cs2" else "Роли"
        pick = "Игр" if game == "cs2" else "Pro pick"
        pick_pub = "Игр" if game == "cs2" else "Pub pick"
        self._panel.title_label.setText("Мета карт" if game == "cs2" else "Мета героев")
        self._panel.note_label.setText(f"загрузка…")
        self._table.setHorizontalHeaderLabels(
            [subject, pick, "Pro WR", pick_pub, "Pub WR", roles]
        )
        self._table.setSortingEnabled(False)

    def set_meta(self, meta: dict[str, Any]) -> None:
        self._meta = meta or {}
        self._render()

    def _on_mode_clicked(self, button: QPushButton) -> None:
        self._mode = "pro" if button is self._buttons["pro"] else "pub"
        self._render()

    def _render(self) -> None:
        board_key = "pro_ranked" if self._mode == "pro" else "pub_ranked"
        rows = self._meta.get(board_key) or []
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(rows))

        for row, hero in enumerate(rows):
            # numeric cells keep plain values so NumericItem sorts correctly
            set_row_id(self._table, row, int(hero["hero_id"]))
            self._table.setCellWidget(
                row, 0, hero_cell(hero.get("img"), hero["name"], icon_url=hero.get("icon"))
            )
            set_text(self._table, row, 1, hero["pro_pick"], mono=True, right=True, numeric=True)
            set_text(self._table, row, 2, hero["pro_winrate"], mono=True, right=True, numeric=True)
            set_text(self._table, row, 3, hero["pub_pick"], mono=True, right=True, numeric=True)
            set_text(self._table, row, 4, hero["pub_winrate"], mono=True, right=True, numeric=True)
            set_text(self._table, row, 5, ", ".join(hero.get("roles") or []) or "—")

        if rows:
            self._table.setSortingEnabled(True)
            self._table.sortItems(1 if self._mode == "pro" else 3, Qt.SortOrder.DescendingOrder)

        noun = _LABELS.get(self._game, ("героев", "Герой"))[0]
        self._panel.note_label.setText(f"{self._meta.get('count', 0)} {noun}")
