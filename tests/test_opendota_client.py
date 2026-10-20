import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx  # noqa: E402

from kda.adapters.dota2 import Dota2Adapter  # noqa: E402
from kda.adapters.dota2.opendota import OpenDotaClient  # noqa: E402
from kda.services import KdaService  # noqa: E402

PROFILE = {
    "profile": {"personaname": "TestPlayer", "avatarfull": "http://a/x.jpg"},
    "rank_tier": 53,
}

RECENT = [
    {
        "match_id": 11,
        "player_slot": 1,
        "radiant_win": True,
        "hero_id": 1,
        "kills": 5,
        "deaths": 2,
        "assists": 10,
        "gold_per_min": 400,
        "xp_per_min": 500,
        "duration": 1800,
        "start_time": 1_700_000_000,
    }
]

HERO_STATS = [
    {
        "id": 1,
        "localized_name": "Anti-Mage",
        "roles": ["Carry"],
        "img": "/apps/570/images/1.jpg",
        "icon": "/apps/570/icons/1.jpg",
        "pro_pick": 10,
        "pro_win": 6,
        "pub_pick": 100,
        "pub_win": 55,
    }
]

MATCH = {
    "match_id": 11,
    "start_time": 1_700_000_000,
    "duration": 1800,
    "radiant_win": True,
    "game_mode": 22,
    "lobby_type": 7,
    "patch": 60,
    "region": 8,
    "radiant_score": 30,
    "dire_score": 12,
    "od_data": {"has_parsed": True},
    "picks_bans": [
        {"is_pick": True, "hero_id": 1, "team": 0, "order": 0},
        {"is_pick": False, "hero_id": 2, "team": 1, "order": 1},
    ],
    "objectives": [
        {"time": 52, "type": "CHAT_MESSAGE_FIRSTBLOOD", "player_slot": 1},
        {"time": 600, "type": "building_kill", "key": "npc_dota_goodguys_tower1_mid", "player_slot": 1},
    ],
    "players": [
        {
            "account_id": 42,
            "personaname": "TestPlayer",
            "player_slot": 1,
            "hero_id": 1,
            "kills": 5,
            "deaths": 2,
            "assists": 10,
            "gold_per_min": 400,
            "xp_per_min": 500,
            "last_hits": 120,
            "denies": 8,
            "hero_damage": 12345,
            "tower_damage": 300,
            "hero_healing": 0,
            "level": 22,
            "net_worth": 9000,
            "item_0": 63,
        },
    ],
}

CAREER = {
    "/players/42/wl": {"win": 88, "lose": 12},
    "/players/42/totals": [
        {"field": "kills", "n": 100, "sum": 500},
        {"field": "gold_per_min", "n": 100, "sum": 40000},
    ],
    "/players/42/heroes": [
        {"hero_id": 1, "games": 10, "win": 7, "last_played": 1_700_000_000},
    ],
}


def make_client(routes: dict[str, object]) -> OpenDotaClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path not in routes:
            return httpx.Response(404, json={"error": "not found"})
        return httpx.Response(200, json=routes[path])

    client = OpenDotaClient(base="http://test")
    client._client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler))
    return client


class AdapterOfflineTests(unittest.TestCase):
    def _adapter(self, routes: dict[str, object]) -> Dota2Adapter:
        adapter = Dota2Adapter()
        adapter.client = make_client(routes)
        return adapter

    def test_search_player_matches_and_meta(self):
        adapter = self._adapter(
            {
                "/search": [{"account_id": 42, "personaname": "TestPlayer"}],
                "/players/42": PROFILE,
                "/players/42/recentMatches": RECENT,
                "/heroes": [{"id": 1, "localized_name": "Anti-Mage"}],
                "/heroStats": HERO_STATS,
            }
        )

        found = adapter.search("test")
        self.assertEqual(found[0].account_id, 42)
        self.assertEqual(found[0].name, "TestPlayer")

        player = adapter.player(42)
        self.assertEqual(player.name, "TestPlayer")
        self.assertEqual(player.rank_tier, 53)

        matches = adapter.recent_matches(42)
        self.assertEqual(matches[0].players[0].win, True)
        self.assertEqual(matches[0].players[0].hero_name, "Anti-Mage")
        self.assertEqual(matches[0].players[0].gpm, 400)

        heroes = adapter.heroes()
        self.assertEqual(heroes[0].img, "https://cdn.cloudflare.steamstatic.com/apps/570/images/1.jpg")

    def test_http_errors_become_opendota_error(self):
        from kda.adapters.dota2.opendota import OpenDotaError

        adapter = self._adapter({})
        with self.assertRaises(OpenDotaError):
            adapter.search("nope")

    def test_match_detail_and_career(self):
        adapter = self._adapter(
            {
                "/matches/11": MATCH,
                "/heroes": [{"id": 1, "localized_name": "Anti-Mage"}],
                "/heroStats": HERO_STATS,
                **CAREER,
            }
        )

        detail = adapter.match_detail(11)
        self.assertEqual(detail.match.radiant_score, 30)
        self.assertEqual(len(detail.picks_bans), 2)
        self.assertTrue(detail.has_parsed)
        self.assertEqual(detail.match.players[0].hero_name, "Anti-Mage")
        self.assertEqual(detail.match.players[0].items[0], 63)
        self.assertEqual(len(detail.match.players[0].items), 6)
        self.assertIn("Первая кровь", [o.label for o in detail.objectives])

        career = adapter.career_stats(42)
        self.assertEqual(career["wl"]["win"], 88)
        self.assertEqual(career["heroes"][0]["games"], 10)

    def test_hero_icon_and_item_lookup(self):
        adapter = self._adapter(
            {
                "/heroStats": HERO_STATS,
                "/constants/items": {
                    "power_treads": {"id": 63, "dname": "Power Treads", "img": "/apps/items/pt.png"}
                },
            }
        )
        self.assertEqual(
            adapter.hero_icon(1),
            "https://cdn.cloudflare.steamstatic.com/apps/570/icons/1.jpg",
        )
        info = adapter.item_info(63)
        self.assertEqual(info["name"], "Power Treads")
        self.assertTrue(info["img"].startswith("https://"))


class ServiceOfflineTests(unittest.TestCase):
    def test_profile_is_built_and_enriched(self):
        service = KdaService()
        adapter = Dota2Adapter()
        adapter.client = make_client(
            {
                "/players/42": PROFILE,
                "/players/42/recentMatches": RECENT,
                "/heroes": [{"id": 1, "localized_name": "Anti-Mage"}],
                "/heroStats": HERO_STATS,
            }
        )
        service._adapters["dota2"] = adapter

        profile = service.profile(42)
        self.assertEqual(profile["summary"]["matches"], 1)
        self.assertEqual(profile["summary"]["winrate"], 100.0)
        self.assertEqual(profile["heroes"][0]["name"], "Anti-Mage")
        self.assertTrue(profile["heroes"][0]["icon"].startswith("https://"))
        self.assertTrue(profile["recent"][0]["icon"].startswith("https://"))
        service.close()

    def test_career_and_match_facade(self):
        service = KdaService()
        adapter = Dota2Adapter()
        adapter.client = make_client(
            {
                "/matches/11": MATCH,
                "/heroes": [{"id": 1, "localized_name": "Anti-Mage"}],
                "/heroStats": HERO_STATS,
                "/constants/items": {
                    "power_treads": {"id": 63, "dname": "Power Treads", "img": "/apps/items/pt.png"}
                },
                **CAREER,
            }
        )
        service._adapters["dota2"] = adapter

        career = service.career(42)
        self.assertEqual(career["wl"]["games"], 100)
        self.assertEqual(career["averages"]["gold_per_min"], 400.0)
        self.assertEqual(career["popular_heroes"][0]["winrate"], 70.0)
        self.assertTrue(career["popular_heroes"][0]["img"].startswith("https://"))

        match = service.match(11)
        self.assertEqual(match["radiant_score"], 30)
        self.assertIn("Первая кровь", [o["label"] for o in match["objectives"]])
        self.assertEqual(match["radiant"][0]["item_meta"][0]["name"], "Power Treads")
        service.close()

    def test_career_from_stats_pure(self):
        from kda.analytics.skill_lab import career_from_stats

        career = career_from_stats(
            {"wl": {"win": 3, "lose": 1}, "totals": [{"field": "kills", "n": 4, "sum": 8}], "heroes": []}
        )
        self.assertEqual(career["winrate"], 75.0)
        self.assertEqual(career["averages"]["kills"], 2.0)
