"""Small display formatters shared by the panels (pure functions, testable)."""
from __future__ import annotations

import time

_RANK_NAMES = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]

_GAME_MODES = {
    0: "Unknown",
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    11: "Mid Only",
    12: "Least Played",
    13: "Limited Heroes",
    16: "Captains Draft",
    18: "Ability Draft",
    19: "Event",
    20: "All Random Deathmatch",
    21: "1v1 Mid",
    22: "All Draft",
    23: "Turbo",
}

_LOBBY_TYPES = {
    -1: "Invalid",
    0: "Public",
    1: "Practice",
    2: "Tournament",
    3: "Tutorial",
    4: "Co-op Bots",
    5: "Team Match",
    6: "Solo Queue",
    7: "Ranked",
    8: "1v1 Mid",
    9: "Battle Cup",
}


def fmt_int(value: float | int | None) -> str:
    return "—" if value in (None, "") else f"{int(value):,}".replace(",", "\u2009")


def fmt_k(value: float | int | None) -> str:
    if not value:
        return "0"
    v = float(value)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}k"
    return f"{v:.0f}"


def fmt_dur(seconds: int | None) -> str:
    if not seconds:
        return "—"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}:{sec:02d}"


def fmt_mark(seconds: int | None) -> str:
    """In-game clock, signed (e.g. -1:30 for pre-horn events)."""
    if seconds is None:
        return "—"
    sec = int(seconds)
    sign = "-" if sec < 0 else ""
    minutes, rem = divmod(abs(sec), 60)
    return f"{sign}{minutes}:{rem:02d}"


def fmt_ago(start_time: int | None, now: float | None = None) -> str:
    if not start_time:
        return "—"
    delta = int((now if now is not None else time.time()) - start_time)
    if delta < 3600:
        return f"{max(1, delta // 60)} мин"
    if delta < 86400:
        return f"{delta // 3600} ч"
    return f"{delta // 86400} дн"


def h_ratio(kills: int, deaths: int, assists: int) -> float:
    return round((kills + assists) / max(deaths, 1), 2)


def rank_name(tier: int | None) -> str:
    if not tier:
        return "Без ранга"
    division, star = divmod(int(tier), 10)
    if not 1 <= division <= len(_RANK_NAMES):
        return "—"
    base = _RANK_NAMES[division - 1]
    return f"{base} {star}" if star else base


def rank_parts(tier: int | None) -> tuple[int, int]:
    """(division 1..8, star 0..5); (0, 0) when unranked/invalid."""
    if not tier:
        return 0, 0
    division, star = divmod(int(tier), 10)
    if not 1 <= division <= len(_RANK_NAMES):
        return 0, 0
    return division, min(star, 5)


def game_mode_name(mode: int | None, table: dict[int, str] | None = None) -> str:
    if mode is None:
        return "—"
    if table and int(mode) in table:
        return table[int(mode)]
    return _GAME_MODES.get(int(mode), f"режим {mode}")


def lobby_name(lobby: int | None) -> str:
    if lobby is None:
        return "—"
    return _LOBBY_TYPES.get(int(lobby), f"лобби {lobby}")

