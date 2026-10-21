import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kda.analytics import meta_hub, skill_lab  # noqa: E402
from kda.core.models import HeroMeta, Match, MatchPlayer, Player  # noqa: E402


def _match(mid, hero_id, win, k=0, d=0, a=0, duration=1800, start=1_700_000_000):
    return Match(
        game="dota2",
        match_id=mid,
        start_time=start,
        duration=duration,
        radiant_win=win,
        players=[
            MatchPlayer(
                account_id=1, hero_id=hero_id, hero_name=f"h{hero_id}",
                kills=k, deaths=d, assists=a, win=win,
            )
        ],
    )


class SkillLabTests(unittest.TestCase):
    def test_build_profile_aggregates(self):
        p = Player(game="dota2", account_id=1, name="P", rank_tier=60)
        matches = [
            _match(1, 1, True, k=10, d=2, a=5),
            _match(2, 1, False, k=4, d=6, a=3),
            _match(3, 2, True, k=8, d=1, a=8),
        ]
        profile = skill_lab.build_profile(p, matches)

        self.assertEqual(profile["summary"]["matches"], 3)
        self.assertEqual(profile["summary"]["wins"], 2)
        self.assertEqual(profile["summary"]["winrate"], 66.7)
        self.assertEqual(profile["summary"]["total_hours"], 1.5)
        self.assertEqual(profile["heroes"][0]["hero_id"], 1)
        self.assertEqual(profile["heroes"][0]["matches"], 2)
        self.assertEqual(len(profile["trend"]), 1)


class MetaHubTests(unittest.TestCase):
    def test_build_meta_shares_and_ranking(self):
        heroes = [
            HeroMeta(game="dota2", hero_id=1, name="A", pro_pick=10, pro_win=6, pub_pick=100, pub_win=55),
            HeroMeta(game="dota2", hero_id=2, name="B", pro_pick=30, pro_win=12, pub_pick=50, pub_win=30),
        ]
        meta = meta_hub.build_meta(heroes)
        self.assertEqual(meta["count"], 2)
        self.assertEqual(meta["pro_ranked"][0]["hero_id"], 2)

    def test_hero_build_from_raw_groups(self):
        names = {5003: "antimage_mana_break", 5004: "antimage_blink", 6012: "special_bonus_unique_antimage",
                6353: "special_bonus_unique_antimage_2"}
        meta = {5003: {"dname": "Mana Break", "img": "x"}}
        rows = [
            {"ability_upgrades_arr": [5003, 5004, 5003, 5004, 5005, 5003, 5004, 5005, 5005, 6012], "lane_role": 1, "gold_per_min": 600},
            {"ability_upgrades_arr": [5003, 5004, 5003, 5004, 5005, 5003, 5004, 5005, 5005, 6353], "lane_role": 1, "gold_per_min": 350},
            {"ability_upgrades_arr": [5003, 5004, 5003, 5004, 5005, 5003, 5004, 5005, 5005, 6012], "lane_role": 2, "gold_per_min": 550},
        ]
        out = skill_lab.hero_build_from_raw(rows, names, meta)
        self.assertEqual(out["games"], 3)
        self.assertIn("groups", out)
        self.assertIn("safe_core", out["groups"])
        self.assertIn("safe_support", out["groups"])
        self.assertIn("mid", out["groups"])
        self.assertEqual(out["groups"]["safe_core"]["games"], 1)
        self.assertEqual(out["groups"]["safe_support"]["games"], 1)
        self.assertEqual(out["groups"]["core"]["games"], 2)
