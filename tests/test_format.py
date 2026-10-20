import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kda.format import (  # noqa: E402
    fmt_ago,
    fmt_dur,
    fmt_mark,
    game_mode_name,
    h_ratio,
    lobby_name,
    rank_name,
    rank_parts,
)


class FormatTests(unittest.TestCase):
    def test_rank_name(self):
        self.assertEqual(rank_name(None), "Без ранга")
        self.assertEqual(rank_name(10), "Herald")
        self.assertEqual(rank_name(11), "Herald 1")
        self.assertEqual(rank_name(53), "Legend 3")
        self.assertEqual(rank_name(80), "Immortal")
        self.assertEqual(rank_name(1), "—")  # invalid division digit

    def test_h_ratio(self):
        self.assertEqual(h_ratio(10, 2, 5), 7.5)
        self.assertEqual(h_ratio(0, 0, 0), 0.0)
        self.assertEqual(h_ratio(3, 10, 1), 0.4)

    def test_fmt_dur(self):
        self.assertEqual(fmt_dur(None), "—")
        self.assertEqual(fmt_dur(65), "1:05")
        self.assertEqual(fmt_dur(3600), "60:00")

    def test_fmt_ago(self):
        self.assertEqual(fmt_ago(None), "—")
        now = 1_700_000_000
        self.assertEqual(fmt_ago(now - 120, now=now), "2 мин")
        self.assertEqual(fmt_ago(now - 7200, now=now), "2 ч")
        self.assertEqual(fmt_ago(now - 172800, now=now), "2 дн")

    def test_fmt_mark(self):
        self.assertEqual(fmt_mark(None), "—")
        self.assertEqual(fmt_mark(0), "0:00")
        self.assertEqual(fmt_mark(95), "1:35")
        self.assertEqual(fmt_mark(-45), "-0:45")

    def test_rank_parts(self):
        self.assertEqual(rank_parts(None), (0, 0))
        self.assertEqual(rank_parts(53), (5, 3))
        self.assertEqual(rank_parts(80), (8, 0))
        self.assertEqual(rank_parts(1), (0, 0))

    def test_mode_name(self):
        self.assertEqual(game_mode_name(22), "All Draft")
        self.assertEqual(game_mode_name(23), "Turbo")
        self.assertEqual(game_mode_name(99), "режим 99")
        self.assertEqual(game_mode_name(22, {22: "custom"}), "custom")

    def test_lobby_name(self):
        self.assertEqual(lobby_name(7), "Ranked")
        self.assertEqual(lobby_name(999), "лобби 999")
