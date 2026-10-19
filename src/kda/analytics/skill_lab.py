"""Skill Lab: turn a player's recent matches into a cross-queryable profile."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..core.models import Match, Player

BUCKET = 5


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def build_profile(player: Player, matches: list[Match]) -> dict[str, Any]:
    parts = [m.players[0] for m in matches if m.players]
    wins = sum(1 for p in parts if p.win)
    total = len(parts)

    hero_stats: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"hero_id": 0, "name": "", "matches": 0, "wins": 0, "kda": []}
    )
    for p in parts:
        bucket = hero_stats[p.hero_id]
        bucket["hero_id"] = p.hero_id
        bucket["name"] = p.hero_name or str(p.hero_id)
        bucket["matches"] += 1
        bucket["wins"] += int(p.win)
        bucket["kda"].append(p.kda)

    heroes = []
    for bucket in hero_stats.values():
        heroes.append(
            {
                "hero_id": bucket["hero_id"],
                "name": bucket["name"],
                "matches": bucket["matches"],
                "wins": bucket["wins"],
                "winrate": round(100.0 * bucket["wins"] / bucket["matches"], 1),
                "avg_kda": _avg(bucket["kda"]),
            }
        )
    heroes.sort(key=lambda h: (h["matches"], h["winrate"]), reverse=True)

    recent = [
        {
            "match_id": m.match_id,
            "hero_id": m.players[0].hero_id,
            "hero_name": m.players[0].hero_name or str(m.players[0].hero_id),
            "win": m.players[0].win,
            "kills": m.players[0].kills,
            "deaths": m.players[0].deaths,
            "assists": m.players[0].assists,
            "kda": round(m.players[0].kda, 2),
            "gpm": m.players[0].gpm,
            "xpm": m.players[0].xpm,
            "duration": m.duration,
            "start_time": m.start_time,
        }
        for m in matches
    ]

    # Rolling win-rate trend (win=1, loss=0) in buckets of BUCKET matches.
    trend: list[dict[str, Any]] = []
    for start in range(0, len(parts), BUCKET):
        chunk = parts[start : start + BUCKET]
        trend.append(
            {
                "game": start + len(chunk),
                "winrate": round(100.0 * sum(1 for p in chunk if p.win) / len(chunk), 1),
            }
        )

    return {
        "player": player.to_dict(),
        "summary": {
            "matches": total,
            "wins": wins,
            "losses": total - wins,
            "winrate": round(100.0 * wins / total, 1) if total else 0.0,
            "avg_kills": _avg([p.kills for p in parts]),
            "avg_deaths": _avg([p.deaths for p in parts]),
            "avg_assists": _avg([p.assists for p in parts]),
            "avg_kda": _avg([p.kda for p in parts]),
            "avg_gpm": _avg([p.gpm for p in parts]),
            "avg_xpm": _avg([p.xpm for p in parts]),
            "total_hours": round(sum(m.duration for m in matches) / 3600.0, 1),
        },
        "heroes": heroes,
        "recent": recent,
        "trend": trend,
    }
