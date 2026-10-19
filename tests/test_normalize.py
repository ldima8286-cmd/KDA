import os
import sys
import unittest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))

from kda.adapters.dota2 import normalize  # noqa: E402


class NormalizeTest(unittest.TestCase):
    def test_player_from_raw(self):
        p = normalize.player_from_raw(
            42, {"profile": {"personaname": "Arteezy", "avatarfull": "http://a/x.jpg"}, "rank_tier": 80}
        )
        assert p.game == "dota2"
        assert p.name == "Arteezy"
        assert p.account_id == 42
        assert p.rank_tier == 80

    def test_recent_match_win_for_radiant(self):
        m = normalize.match_from_recent(
            7, {"match_id": 1, "player_slot": 3, "radiant_win": True, "kills": 5, "deaths": 2, "assists": 9}, "Anti-Mage"
        )
        assert m.players[0].win is True
        assert m.players[0].hero_name == "Anti-Mage"
        assert m.players[0].kda == 7.0

    def test_recent_match_loss_for_dire(self):
        m = normalize.match_from_recent(7, {"match_id": 2, "player_slot": 130, "radiant_win": True}, "Pudge")
        assert m.players[0].win is False

    def test_meta_winrate(self):
        stats = [{"id": 1, "localized_name": "Anti-Mage", "pro_pick": 10, "pro_win": 6, "pub_pick": 100, "pub_win": 55, "img": "/x.png"}]
        meta = normalize.meta_from_stats(stats, {1: "Anti-Mage"})[0]
        d = meta.to_dict()
        assert d["pro_winrate"] == 60.0
        assert d["pub_winrate"] == 55.0
        assert d["img"].startswith("https://cdn.cloudflare.steamstatic.com/")
