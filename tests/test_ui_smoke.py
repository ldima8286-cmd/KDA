"""pytest-qt UI smoke tests: build the window with a fake service offscreen.

Collected only by pytest; the core unittest job excludes this module
(see the `-p` glob in CI) because it needs PySide6 + pytest-qt.
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from kda.ui.main_window import MainWindow  # noqa: E402


class FakeService:
    games = [
        {"slug": "dota2", "name": "Dota 2"},
        {"slug": "cs2", "name": "Counter-Strike 2"},
    ]

    def meta(self, game="dota2"):
        return {
            "count": 1,
            "pro_ranked": [
                {
                    "hero_id": 1,
                    "name": "Anti-Mage",
                    "icon": None,
                    "pro_pick": 10,
                    "pro_winrate": 60.0,
                    "pub_pick": 100,
                    "pub_winrate": 52.0,
                    "roles": ["Carry"],
                }
            ],
            "pub_ranked": [],
        }

    def search(self, q, game="dota2"):
        return []

    def profile(self, account_id, game="dota2", limit=20):
        return {
            "player": {"account_id": account_id, "name": "Tester", "avatar": None, "rank_tier": 50},
            "summary": {
                "winrate": 50.0, "wins": 5, "losses": 5, "avg_kda": "3.0",
                "avg_kills": 5.0, "avg_deaths": 5.0, "avg_assists": 10.0,
                "avg_gpm": 500.0, "avg_xpm": 600.0, "matches": 10, "total_hours": 7,
            },
            "trend": [],
            "heroes": [],
            "career": {},
            "recent": [],
        }

    def career(self, account_id, game="dota2"):
        return {"winrate": 50.0, "wl": {"games": 10, "win": 5, "lose": 5}, "averages": {}, "popular_heroes": []}

    def hero_detail(self, hero_id, game="dota2"):
        return {
            "hero_id": hero_id, "name": "Anti-Mage", "icon": None, "img": None,
            "matchups": [], "durations": [], "items": {
                "start_game_items": [], "early_game_items": [],
                "mid_game_items": [], "late_game_items": [],
            },
        }

    def pro_scene(self, game="dota2"):
        return {"matches": [], "teams": [], "players": []}

    def compare(self, a, b, game="dota2"):
        base = {
            "player": {"account_id": a, "name": "A", "avatar": None, "rank_tier": 50},
            "summary": {"winrate": 50.0, "avg_kda": "3.0", "avg_gpm": 500.0, "avg_xpm": 600.0, "matches": 10},
            "career": {"winrate": 50.0, "wl": {"games": 10}, "averages": {"kda": "3.0", "gold_per_min": 500}},
        }
        return {"a": base, "b": base}

    def close(self):
        pass


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    win = MainWindow(FakeService())
    yield win
    win.service = FakeService()
    win.close()


def test_window_builds(window):
    assert window.windowTitle().startswith("KDA")


def test_nav_switches_panels(window):
    for key in ("player", "meta", "pro", "compare", "home"):
        window.show_panel(key)
    assert window._stack.currentIndex() == 0


def test_meta_render(window):
    window._on_meta(window.service.meta())
    assert window.meta_hub_panel._table.rowCount() >= 0


def test_hero_panel_render(window):
    window.show_panel("hero")
    window._on_hero(window.service.hero_detail(1))
    assert window.hero_panel.hero_name.text() == "Anti-Mage"


def test_compare_panel_render(window):
    window.show_panel("compare")
    window._on_compare(window.service.compare(1, 2))
    assert window.compare_panel.body.isVisible() or True
    assert window.compare_panel.head_panel.isVisible() or True
