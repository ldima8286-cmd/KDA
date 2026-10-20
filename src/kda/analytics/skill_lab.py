"""Skill Lab: turn a player's recent matches into a cross-queryable profile."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..core.models import Match, MatchDetail, Player

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


def career_from_stats(
    raw: dict,
    heroes: list[dict] | None = None,
    images: dict[int, str] | None = None,
) -> dict:
    """Turn /players/{id}/wl + totals + heroes into a career summary."""
    images = images or {}
    totals = raw.get("totals") or []
    wl = raw.get("wl") or {}

    averages = {}
    for row in totals:
        field = row.get("field")
        n = int(row.get("n") or 0)
        if field and n:
            averages[field] = round(float(row.get("sum") or 0) / n, 2)

    wins = int(wl.get("win") or 0)
    losses = int(wl.get("lose") or 0)
    games = wins + losses

    popular = []
    for row in (heroes or [])[:10]:
        played = int(row.get("games") or 0)
        if not played:
            continue
        hero_id = int(row.get("hero_id") or 0)
        won = int(row.get("win") or 0)
        popular.append(
            {
                "hero_id": hero_id,
                "games": played,
                "wins": won,
                "lost": played - won,
                "winrate": round(100.0 * won / played, 1),
                "img": images.get(hero_id),
                "last_played": int(row.get("last_played") or 0),
            }
        )

    return {
        "wl": {"win": wins, "lose": losses, "games": games},
        "winrate": round(100.0 * wins / games, 1) if games else 0.0,
        "averages": averages,
        "popular_heroes": popular,
    }


def match_summary(detail: MatchDetail) -> dict:
    """Structure a parsed match for the viewer panel."""
    match = detail.match

    def player_row(p) -> dict:
        return {
            "account_id": p.account_id,
            "personaname": p.personaname,
            "hero_id": p.hero_id,
            "hero_name": p.hero_name,
            "hero_icon": p.hero_icon,
            "player_slot": p.player_slot,
            "kills": p.kills,
            "deaths": p.deaths,
            "assists": p.assists,
            "kda": round(p.kda, 2),
            "gpm": p.gpm,
            "xpm": p.xpm,
            "last_hits": p.last_hits,
            "denies": p.denies,
            "hero_damage": p.hero_damage,
            "tower_damage": p.tower_damage,
            "hero_healing": p.hero_healing,
            "level": p.level,
            "net_worth": p.net_worth,
            "items": list(p.items),
            "win": p.win,
        }

    return {
        "match_id": match.match_id,
        "start_time": match.start_time,
        "duration": match.duration,
        "radiant_win": match.radiant_win,
        "mode": match.mode,
        "lobby_type": match.lobby_type,
        "patch": match.patch,
        "region": match.region,
        "radiant_score": match.radiant_score,
        "dire_score": match.dire_score,
        "has_parsed": detail.has_parsed,
        "picks_bans": [
            {
                "hero_id": pb.hero_id,
                "hero_name": pb.hero_name or f"hero #{pb.hero_id}",
                "is_pick": pb.is_pick,
                "team": pb.team,
            }
            for pb in detail.picks_bans
        ],
        "objectives": [
            {"time": o.time, "kind": o.kind, "label": o.label, "team": o.team}
            for o in detail.objectives
        ],
        "radiant": [player_row(p) for p in match.team(True)],
        "dire": [player_row(p) for p in match.team(False)],
    }
