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
    QButtonGroup,
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

_TALENT_TIERS = (10, 15, 20, 25)


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
        self.positions_label = QLabel("")
        self.positions_label.setProperty("statLabel", True)
        title_row.addWidget(self.positions_label)
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

        build_panel = Panel("Раскачка способностей", "порядок по уровням")
        filt = QHBoxLayout()
        filt.setSpacing(6)
        filt.addStretch(1)
        self._lane_group = QButtonGroup(self)
        self._lane_group.setExclusive(True)
        for key, label in (("all", "Все"), ("safe", "Сайд"), ("mid", "Мид"), ("off", "Оффлейн")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("ghost", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("role_key", key)
            self._lane_group.addButton(btn)
            filt.addWidget(btn)
        self._lane_group.buttons()[0].setChecked(True)
        self._role_group = QButtonGroup(self)
        self._role_group.setExclusive(True)
        for key, label in (("all", "Все роли"), ("core", "Кора"), ("support", "Саппорт")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("ghost", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("role_key", key)
            self._role_group.addButton(btn)
            filt.addWidget(btn)
        self._role_group.buttons()[0].setChecked(True)
        self._lane_group.buttonClicked.connect(lambda *_: self._apply_build_filter())
        self._role_group.buttonClicked.connect(lambda *_: self._apply_build_filter())
        build_panel.add_layout(filt)

        build_grid = QGridLayout()
        build_grid.setHorizontalSpacing(10)
        build_grid.setVerticalSpacing(8)
        self._build_grid = build_grid
        self._build_container = QWidget()
        self._build_container.setLayout(build_grid)
        build_panel.add(self._build_container)

        self._build_note = QLabel("Нет данных")
        self._build_note.setProperty("empty", True)
        build_panel.add(self._build_note)
        content.addWidget(build_panel)

        talents_panel = Panel("Таланты", "самые популярные")
        t_filt = QHBoxLayout()
        t_filt.setSpacing(6)
        t_filt.addStretch(1)
        self._talent_lane = QButtonGroup(self)
        self._talent_lane.setExclusive(True)
        for key, label in (("all", "Все"), ("safe", "Сайд"), ("mid", "Мид"), ("off", "Оффлейн")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("ghost", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("role_key", key)
            self._talent_lane.addButton(btn)
            t_filt.addWidget(btn)
        self._talent_lane.buttons()[0].setChecked(True)
        self._talent_role = QButtonGroup(self)
        self._talent_role.setExclusive(True)
        for key, label in (("all", "Все роли"), ("core", "Кора"), ("support", "Саппорт")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("ghost", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("role_key", key)
            self._talent_role.addButton(btn)
            t_filt.addWidget(btn)
        self._talent_role.buttons()[0].setChecked(True)
        self._talent_lane.buttonClicked.connect(lambda *_: self._apply_build_filter())
        self._talent_role.buttonClicked.connect(lambda *_: self._apply_build_filter())
        talents_panel.add_layout(t_filt)

        talents_grid = QGridLayout()
        talents_grid.setHorizontalSpacing(18)
        talents_grid.setVerticalSpacing(10)
        self._talent_boxes: dict[int, QWidget] = {}
        self._talent_labels: dict[int, QLabel] = {}
        self._talent_bars: dict[int, object] = {}
        for row, tier in enumerate(_TALENT_TIERS):
            tier_lab = QLabel(f"Тир {tier}")
            tier_lab.setProperty("panelTitle", True)
            talents_grid.addWidget(tier_lab, row, 0, 1, 2)
            for col in (0, 1):
                box = QWidget()
                box.setProperty("role", "panel2")
                lay = QHBoxLayout(box)
                lay.setContentsMargins(10, 8, 10, 8)
                lay.setSpacing(10)
                name = QLabel("—")
                name.setWordWrap(True)
                lay.addWidget(name, 1)
                share = QLabel("0%")
                share.setProperty("mono", True)
                lay.addWidget(share)
                self._talent_boxes[(tier, col)] = box
                self._talent_labels[(tier, col)] = name
                box.hide()
                talents_grid.addWidget(box, row + 1, col)
        talents_panel.add_layout(talents_grid)
        self._talents_note = QLabel("Нет данных")
        self._talents_note.setProperty("empty", True)
        talents_panel.add(self._talents_note)
        content.addWidget(talents_panel)

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

        positions = data.get("positions") or {}
        if positions.get("total"):
            self.positions_label.setText(
                f"кора · {positions.get('core_share', 0)}%    саппорт · "
                f"{positions.get('support_share', 0)}%"
            )
            self.positions_label.show()
        else:
            self.positions_label.hide()

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

        self._build_data = data.get("build") or {}
        self._apply_build_filter()

        self._body.show()
        self.empty.hide()

    def _checked_key(self, group: QButtonGroup) -> str:
        btn = group.checkedButton()
        if btn is None:
            return "all"
        return btn.property("role_key") or "all"

    def _group_key(self) -> str:
        lane = self._checked_key(self._lane_group)
        role = self._checked_key(self._role_group)
        if role == "all":
            return lane if lane != "all" else "all"
        if lane == "all":
            return role
        return f"{lane}_{role}"

    def _apply_build_filter(self) -> None:
        build = getattr(self, "_build_data", {}) or {}
        groups = build.get("groups") or {}
        key = self._group_key()
        data_b = groups.get(key) if key != "all" else None
        if data_b is None and key != "all":
            lane = self._checked_key(self._lane_group)
            if lane != "all":
                data_b = groups.get(lane)
        if data_b is None:
            data_b = build
        self._fill_build_grid(data_b.get("order") or [], data_b)
        self._fill_talents_grid(data_b.get("talents") or [])

    def _fill_build_grid(self, order: list[dict[str, Any]], build: dict[str, Any]) -> None:
        grid = self._build_grid
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        entries = [e for e in order if e]
        games = build.get("games") or 0
        self._build_note.setVisible(not entries)
        if games:
            self._build_note.setText(f"На основе {fmt_int(games)} матчей")
        else:
            self._build_note.setText("Нет данных")
        for idx, entry in enumerate(entries):
            tile = self._ability_tile(entry)
            grid.addWidget(tile, idx // 9, idx % 9)

    def _fill_talents_grid(self, talents: list[dict[str, Any]]) -> None:
        by_tier = {t["tier"]: t.get("options") or [] for t in talents}
        any_data = False
        for tier in _TALENT_TIERS:
            for col in (0, 1):
                box = self._talent_boxes[(tier, col)]
                name = self._talent_labels[(tier, col)]
                options = by_tier.get(tier) or []
                if col < len(options):
                    opt = options[col]
                    any_data = True
                    name.setText(opt.get("name") or "—")
                    box.setToolTip(f"{opt.get('picks', 0)} взятий · {opt.get('share', 0)}%")
                    box.show()
                else:
                    box.hide()
        self._talents_note.setVisible(not any_data)

    @staticmethod
    def _ability_tile(entry: dict[str, Any]) -> QWidget:
        from ..widgets import ItemIcon

        host = QWidget()
        box = QVBoxLayout(host)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        icon = ItemIcon(entry.get("img"), tip=f"{entry['name']} · ур. {entry['level']}")
        box.addWidget(icon, 0, Qt.AlignmentFlag.AlignHCenter)
        label = QLabel(str(entry["level"]))
        label.setProperty("statLabel", True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(label)
        return host

    @staticmethod
    def _talent_tile(opt: dict[str, Any]) -> QWidget:
        host = QWidget()
        box = QHBoxLayout(host)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        name = QLabel(opt.get("name") or "—")
        name.setWordWrap(True)
        box.addWidget(name, 1)
        share = QLabel(f"{opt.get('share', 0)}%")
        share.setProperty("statLabel", True)
        box.addWidget(share)
        return host

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
