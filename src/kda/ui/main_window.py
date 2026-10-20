"""KDA main window: nav rail, player search, and the three analysis panels."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..services import KdaService
from . import workers
from .panels import HomePanel, MetaHubPanel, SkillLabPanel
from .theme import C

_NAV = (("home", "Обзор"), ("player", "Skill Lab"), ("meta", "Meta Hub"))


class MainWindow(QMainWindow):
    def __init__(self, service: KdaService) -> None:
        super().__init__()
        self.service = service
        self._meta: dict | None = None

        self.setWindowTitle("KDA — esports intelligence")
        self.resize(1360, 880)
        self.setMinimumSize(1000, 640)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_rail())

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_topbar())
        main_layout.addWidget(self._build_stack(), 1)
        root.addWidget(main, 1)

        self.setCentralWidget(central)

        # Pull current data as soon as the window is up (TTL cache is cold on
        # every launch, so this always hits the API when online).
        QTimer.singleShot(0, self.refresh)

    # ---------- chrome ----------

    def _build_rail(self) -> QFrame:
        rail = QFrame()
        rail.setProperty("role", "rail")
        rail.setFixedWidth(224)

        lay = QVBoxLayout(rail)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setSpacing(18)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        brand = QLabel("KDA")
        brand.setProperty("brand", True)
        brand_sub = QLabel("ESPORTS INTELLIGENCE")
        brand_sub.setProperty("brandSub", True)
        brand_box.addWidget(brand)
        brand_box.addWidget(brand_sub)
        lay.addLayout(brand_box)

        self._nav_buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for key, label in _NAV:
            btn = QPushButton(label)
            btn.setProperty("nav", True)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(btn)
            self._nav_buttons[key] = btn
            lay.addWidget(btn)
            btn.clicked.connect(lambda _=False, k=key: self.show_panel(k))
        self._nav_buttons["home"].setChecked(True)

        lay.addStretch(1)

        chip = QLabel(f'<span style="color:{C["teal"]}">●</span>&nbsp; Dota 2')
        chip.setProperty("chip", True)
        lay.addWidget(chip)

        self._refresh_btn = QPushButton("Обновить данные")
        self._refresh_btn.setProperty("ghost", True)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._force_refresh)
        lay.addWidget(self._refresh_btn)

        return rail

    def _build_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setFixedHeight(62)

        lay = QHBoxLayout(topbar)
        lay.setContentsMargins(26, 12, 26, 12)
        lay.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Steam ID или ник игрока — Enter")
        self._search.setClearButtonEnabled(True)
        self._search.returnPressed.connect(self._on_search)
        lay.addWidget(self._search, 1)

        go = QPushButton("Найти")
        go.setProperty("primary", True)
        go.setCursor(Qt.CursorShape.PointingHandCursor)
        go.clicked.connect(self._on_search)
        lay.addWidget(go)

        self._status = QLabel("запуск…")
        self._status.setProperty("status", True)
        self._status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._status)

        return topbar

    def _build_stack(self) -> QStackedWidget:
        self.home_panel = HomePanel()
        self.skill_lab_panel = SkillLabPanel()
        self.meta_hub_panel = MetaHubPanel()

        stack = QStackedWidget()
        stack.addWidget(self.home_panel)      # index 0
        stack.addWidget(self.skill_lab_panel)  # index 1
        stack.addWidget(self.meta_hub_panel)   # index 2
        self._stack = stack
        return stack

    # ---------- status ----------

    def set_status(self, text: str, kind: str = "idle") -> None:
        props = {"idle": "status", "busy": "statusBusy", "ok": "statusOk", "err": "statusErr"}
        for prop in props.values():
            self._status.setProperty(prop, prop == props[kind])
        self._status.setText(text)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    # ---------- navigation ----------

    def show_panel(self, key: str) -> None:
        index = {"home": 0, "player": 1, "meta": 2}[key]
        self._stack.setCurrentIndex(index)
        self._nav_buttons[key].setChecked(True)

    # ---------- data ----------

    def refresh(self) -> None:
        self.set_status("обновление данных…", "busy")
        self._refresh_btn.setEnabled(False)
        workers.submit(self.service.meta, self._on_meta, self._on_error, self._refresh_done)

    def _force_refresh(self) -> None:
        self.service.refresh()
        self.refresh()

    def _refresh_done(self) -> None:
        self._refresh_btn.setEnabled(True)

    def _on_meta(self, meta: dict) -> None:
        self._meta = meta
        self.home_panel.set_meta(meta)
        self.meta_hub_panel.set_meta(meta)
        stamp = datetime.now().strftime("%H:%M")
        self.set_status(f"данные обновлены · {stamp}", "ok")

    def _on_error(self, message: str) -> None:
        self.set_status(f"нет соединения: {message[:60]}", "err")

    def _on_search(self) -> None:
        query = self._search.text().strip()
        if not query:
            return
        self.set_status("поиск…", "busy")
        if query.isdigit():
            self._load_profile(int(query))
            return
        workers.submit(
            self.service.search,
            self._on_search_results,
            self._on_error,
            None,
            query,
        )

    def _on_search_results(self, results: list) -> None:
        if not results:
            self.set_status("игрок не найден", "err")
            return
        self._load_profile(int(results[0]["account_id"]))

    def _load_profile(self, account_id: int) -> None:
        self.show_panel("player")
        self.set_status("загрузка игрока…", "busy")
        workers.submit(
            self.service.profile,
            self._on_profile,
            self._on_error,
            None,
            account_id,
        )

    def _on_profile(self, profile: dict) -> None:
        self.skill_lab_panel.set_profile(profile)
        name = profile["player"].get("name") or str(profile["player"].get("account_id"))
        self.set_status(f"профиль загружен · {name}", "ok")

    # ---------- lifecycle ----------

    def closeEvent(self, event) -> None:  # noqa: N802, ARG002
        self.service.close()
        super().closeEvent(event)
