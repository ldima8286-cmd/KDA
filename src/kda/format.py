"""Small display formatters shared by the panels (pure functions, testable)."""
from __future__ import annotations

import time

_RANK_NAMES = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]


def fmt_int(value: float | int | None) -> str:
    return "—" if value in (None, "") else f"{int(value):,}"


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
