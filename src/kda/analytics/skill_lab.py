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


def _is_talent(ability_id: int, ability_names: dict[int, str]) -> bool:
    name = ability_names.get(ability_id, "")
    return name.startswith("special_bonus") or ability_id >= 7000


def _humanize_ability(key: str) -> str:
    text = key
    if text.startswith("special_bonus_unique_"):
        text = text[len("special_bonus_unique_"):]
        return "Talent: " + text.replace("_", " ").strip().title()
    if text.startswith("special_bonus_"):
        text = text[len("special_bonus_"):]
        return "Talent: " + text.replace("_", " ").strip().title()
    for prefix in ("npc_dota_hero_", "dota_hero_"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    parts = text.split("_")
    return " ".join(parts[1:]).title() if len(parts) > 1 else text.title()


def _clean_talent(text: str) -> str:
    import re

    cleaned = re.sub(r"\{[svm]:[^}]*\}", "?", text)
    return cleaned.strip() or "Talent"


LANE_NAMES = {1: "safe", 2: "mid", 3: "off", 4: "jungle"}
CORE_GPM = 450


def _lane_role_of(row: dict) -> str:
    lane = row.get("lane_role")
    try:
        lane = int(lane)
    except (TypeError, ValueError):
        return "unknown"
    return LANE_NAMES.get(lane, "unknown")


def _is_core(row: dict) -> bool:
    try:
        return int(row.get("gold_per_min") or 0) >= CORE_GPM
    except (TypeError, ValueError):
        return False


def _aggregate(
    rows: list[dict],
    ability_names: dict[int, str],
    ability_meta: dict[int, dict],
) -> dict:
    level_counts: list[dict[int, int]] = [defaultdict(int) for _ in range(18)]
    talent_counts: dict[int, dict[int, int]] = {10: defaultdict(int), 15: defaultdict(int),
                                                20: defaultdict(int), 25: defaultdict(int)}
    games = 0

    for row in rows:
        arr = row.get("ability_upgrades_arr") or []
        if not arr:
            continue
        games += 1
        skill_slot = 0
        for ability_id in arr:
            ability_id = int(ability_id)
            if _is_talent(ability_id, ability_names):
                hero_level = skill_slot + 1
                if hero_level in talent_counts:
                    talent_counts[hero_level][ability_id] += 1
                continue
            if skill_slot < 18:
                level_counts[skill_slot][ability_id] += 1
            skill_slot += 1

    order = []
    for level in range(18):
        counts = level_counts[level]
        if not counts:
            order.append(None)
            continue
        top_id = max(counts, key=counts.get)
        order.append(
            {
                "level": level + 1,
                "ability_id": top_id,
                "name": _humanize_ability(ability_names.get(top_id, str(top_id))),
                "img": (ability_meta.get(top_id) or {}).get("img"),
                "picks": counts[top_id],
                "share": round(100.0 * counts[top_id] / games, 1) if games else 0.0,
            }
        )

    talents = []
    for tier in (10, 15, 20, 25):
        counts = talent_counts[tier]
        if not counts:
            continue
        total = sum(counts.values())
        options = []
        for ability_id, picks in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:2]:
            meta = ability_meta.get(ability_id) or {}
            dname = meta.get("dname")
            if dname:
                label = _clean_talent(str(dname))
            else:
                raw = ability_names.get(ability_id, "")
                label = _humanize_ability(raw) if raw else f"Talent #{ability_id}"
            options.append(
                {
                    "ability_id": ability_id,
                    "name": label,
                    "img": meta.get("img"),
                    "picks": picks,
                    "share": round(100.0 * picks / total, 1) if total else 0.0,
                }
            )
        talents.append({"tier": tier, "options": options})

    return {"games": games, "order": order, "talents": talents}


def hero_build_from_raw(
    rows: list[dict],
    ability_names: dict[int, str],
    ability_meta: dict[int, dict],
) -> dict:
    """Skill order and talents overall plus a lane/role breakdown.

    Players often take a hero on an off-role, so we return the overall build
    alongside per-lane (safe/mid/off) and per-role (core/support) slices. Each
    slice carries its own match count so the UI can flag small samples.
    """
    overall = _aggregate(rows, ability_names, ability_meta)

    groups: dict[str, dict] = {}
    for lane in ("safe", "mid", "off"):
        lane_rows = [r for r in rows if _lane_role_of(r) == lane]
        if lane_rows:
            groups[lane] = _aggregate(lane_rows, ability_names, ability_meta)
        core_rows = [r for r in lane_rows if _is_core(r)]
        support_rows = [r for r in lane_rows if not _is_core(r)]
        if core_rows:
            groups[f"{lane}_core"] = _aggregate(core_rows, ability_names, ability_meta)
        if support_rows:
            groups[f"{lane}_support"] = _aggregate(support_rows, ability_names, ability_meta)

    core_rows = [r for r in rows if _is_core(r)]
    support_rows = [r for r in rows if not _is_core(r)]
    if core_rows:
        groups["core"] = _aggregate(core_rows, ability_names, ability_meta)
    if support_rows:
        groups["support"] = _aggregate(support_rows, ability_names, ability_meta)

    return {"games": overall["games"], "order": overall["order"],
            "talents": overall["talents"], "groups": groups}


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
        "gold_adv": list(detail.gold_adv),
        "xp_adv": list(detail.xp_adv),
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


def hero_from_raw(raw: dict, heroes: dict[int, str] | None = None) -> dict:
    """Shape a hero's matchups, duration winrate and item popularity."""
    heroes = heroes or {}

    matchups = []
    ranked = sorted(raw.get("matchups") or [], key=lambda m: m.get("games_played", 0), reverse=True)
    for row in ranked[:12]:
        other = int(row.get("hero_id") or 0)
        games = int(row.get("games_played") or 0)
        wins = int(row.get("wins") or 0)
        matchups.append(
            {
                "hero_id": other,
                "name": heroes.get(other, f"hero #{other}"),
                "games": games,
                "wins": wins,
                "winrate": round(100.0 * wins / games, 1) if games else 0.0,
            }
        )

    duration_bins = []
    for row in sorted(raw.get("durations") or [], key=lambda e: int(e.get("duration_bin") or 0)):
        games = int(row.get("games_played") or 0)
        wins = int(row.get("wins") or 0)
        if not games:
            continue
        duration_bins.append(
            {
                "minute": int(row.get("duration_bin") or 0) // 60,
                "games": games,
                "wins": wins,
                "winrate": round(100.0 * wins / games, 1),
            }
        )

    items_raw = raw.get("items") or {}
    items: dict[str, list[int]] = {}
    for phase in ("start_game_items", "early_game_items", "mid_game_items", "late_game_items"):
        bucket = items_raw.get(phase) or {}
        if isinstance(bucket, dict):
            picked = sorted(bucket.items(), key=lambda kv: kv[1], reverse=True)[:8]
            items[phase] = [int(k) for k, _ in picked]

    return {
        "hero_id": raw.get("hero_id"),
        "name": raw.get("name"),
        "img": raw.get("img"),
        "icon": raw.get("icon"),
        "matchups": matchups,
        "durations": duration_bins,
        "items": items,
    }


def pro_match_from_raw(raw: dict) -> dict:
    return {
        "match_id": int(raw.get("match_id") or 0),
        "start_time": int(raw.get("start_time") or 0),
        "duration": int(raw.get("duration") or 0),
        "radiant_name": raw.get("radiant_name") or "Radiant",
        "dire_name": raw.get("dire_name") or "Dire",
        "radiant_win": bool(raw.get("radiant_win")),
        "radiant_score": int(raw.get("radiant_score") or 0),
        "dire_score": int(raw.get("dire_score") or 0),
        "league_name": raw.get("league_name") or "",
    }


def team_from_raw(raw: dict) -> dict:
    wins = int(raw.get("wins") or 0)
    losses = int(raw.get("losses") or 0)
    games = wins + losses
    return {
        "team_id": int(raw.get("team_id") or 0),
        "name": raw.get("name") or f"team {raw.get('team_id')}",
        "tag": raw.get("tag") or "",
        "rating": round(float(raw.get("rating") or 0), 1),
        "wins": wins,
        "losses": losses,
        "winrate": round(100.0 * wins / games, 1) if games else 0.0,
        "logo_url": raw.get("logo_url"),
    }


def pro_player_from_raw(raw: dict) -> dict:
    return {
        "account_id": int(raw.get("account_id") or 0),
        "name": raw.get("name") or raw.get("personaname") or f"player {raw.get('account_id')}",
        "personaname": raw.get("personaname") or "",
        "team_name": raw.get("team_name") or "",
        "team_tag": raw.get("team_tag") or "",
        "country": raw.get("country_code") or raw.get("loccountrycode"),
        "avatar": raw.get("avatarfull"),
        "is_pro": bool(raw.get("is_pro")),
    }
