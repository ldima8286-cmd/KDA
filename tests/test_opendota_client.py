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
        "pro_pick": 10,
        "pro_win": 6,
        "pub_pick": 100,
        "pub_win": 55,
    }
]


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
        self.assertTrue(profile["heroes"][0]["img"].startswith("https://"))
        self.assertTrue(profile["recent"][0]["img"].startswith("https://"))
        service.close()
