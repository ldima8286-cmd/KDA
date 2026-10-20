"""Normalise raw OpenDota payloads into the unified KDA model."""
from __future__ import annotations

from typing import Any

from ...core.models import HeroMeta, Match, MatchDetail, MatchPlayer, Objective, PickBan, Player


def player_from_raw(account_id: int, raw: dict[str, Any]) -> Player:
    profile = raw.get("profile") or {}
    return Player(
        game="dota2",
        account_id=account_id,
        name=profile.get("personaname") or str(account_id),
        avatar=profile.get("avatarfull"),
        country=profile.get("loccountrycode"),
        rank_tier=raw.get("rank_tier"),
        leaderboard_rank=raw.get("leaderboard_rank"),
        profile_url=profile.get("profileurl"),
    )


def _won(player_slot: int, radiant_win: bool) -> bool:
    is_radiant = player_slot < 128
    return radiant_win if is_radiant else not radiant_win


def match_from_recent(account_id: int, raw: dict[str, Any], hero_name: str = "") -> Match:
    radiant_win = bool(raw.get("radiant_win"))
    slot = int(raw.get("player_slot") or 0)
    participant = MatchPlayer(
        account_id=account_id,
        hero_id=int(raw.get("hero_id") or 0),
        hero_name=hero_name,
        kills=int(raw.get("kills") or 0),
        deaths=int(raw.get("deaths") or 0),
        assists=int(raw.get("assists") or 0),
        gpm=int(raw.get("gold_per_min") or 0),
        xpm=int(raw.get("xp_per_min") or 0),
        last_hits=int(raw.get("last_hits") or 0),
        net_worth=int(raw.get("net_worth") or 0),
        win=_won(slot, radiant_win),
    )
    return Match(
        game="dota2",
        match_id=int(raw.get("match_id") or 0),
        start_time=int(raw.get("start_time") or 0),
        duration=int(raw.get("duration") or 0),
        radiant_win=radiant_win,
        mode=raw.get("game_mode"),
        lobby_type=raw.get("lobby_type"),
        players=[participant],
    )


def hero_index(heroes_raw: list[dict[str, Any]]) -> dict[int, str]:
    return {int(h["id"]): h.get("localized_name") or h.get("name") or str(h["id"]) for h in heroes_raw}


def hero_index_name(heroes: dict[int, str] | None, row: dict[str, Any]) -> str:
    if not heroes:
        return ""
    return heroes.get(int(row.get("hero_id") or 0), "")


def img_url(raw_img: str | None) -> str | None:
    """OpenDota returns Steam CDN paths; make them absolute."""
    if not raw_img:
        return None
    text = str(raw_img)
    if text.startswith("http"):
        return text
    return "https://cdn.cloudflare.steamstatic.com" + text


def match_from_detail(
    raw: dict[str, Any],
    heroes: dict[int, str] | None = None,
    icons: dict[int, str] | None = None,
) -> MatchDetail:
    """Normalise a fully parsed /matches/{id} payload into a scoreboard + timeline."""
    heroes = heroes or {}
    icons = icons or {}
    radiant_win = bool(raw.get("radiant_win"))

    players: list[MatchPlayer] = []
    for row in raw.get("players") or []:
        hero_id = int(row.get("hero_id") or 0)
        items = [int(row.get(f"item_{i}") or 0) for i in range(6)]
        neutral = int(row.get("item_neutral") or 0)
        if neutral:
            items.append(neutral)
        players.append(
            MatchPlayer(
                account_id=int(row.get("account_id") or 0),
                hero_id=hero_id,
                hero_name=heroes.get(hero_id) or str(hero_id),
                hero_icon=icons.get(hero_id),
                personaname=row.get("personaname"),
                player_slot=int(row.get("player_slot") or 0),
                kills=int(row.get("kills") or 0),
                deaths=int(row.get("deaths") or 0),
                assists=int(row.get("assists") or 0),
                gpm=int(row.get("gold_per_min") or 0),
                xpm=int(row.get("xp_per_min") or 0),
                last_hits=int(row.get("last_hits") or 0),
                denies=int(row.get("denies") or 0),
                hero_damage=int(row.get("hero_damage") or 0),
                tower_damage=int(row.get("tower_damage") or 0),
                hero_healing=int(row.get("hero_healing") or 0),
                level=int(row.get("level") or 0),
                net_worth=int(row.get("net_worth") or row.get("total_gold") or 0),
                items=items,
                win=_won(int(row.get("player_slot") or 0), radiant_win),
            )
        )

    match = Match(
        game="dota2",
        match_id=int(raw.get("match_id") or 0),
        start_time=int(raw.get("start_time") or 0),
        duration=int(raw.get("duration") or 0),
        radiant_win=radiant_win,
        mode=raw.get("game_mode"),
        lobby_type=raw.get("lobby_type"),
        patch=raw.get("patch"),
        region=raw.get("region"),
        radiant_score=int(raw.get("radiant_score") or 0),
        dire_score=int(raw.get("dire_score") or 0),
        players=players,
    )

    picks_bans = [
        PickBan(
            is_pick=bool(pb.get("is_pick")),
            hero_id=int(pb.get("hero_id") or 0),
            team=int(pb.get("team") or 0),
            order=int(pb.get("order") or 0),
            hero_name=heroes.get(int(pb.get("hero_id") or 0), ""),
        )
        for pb in raw.get("picks_bans") or []
    ]

    objectives = [_objective(entry, heroes) for entry in raw.get("objectives") or []]

    od = raw.get("od_data") or {}
    return MatchDetail(
        game="dota2",
        match=match,
        picks_bans=picks_bans,
        objectives=objectives,
        has_parsed=bool(od.get("has_parsed")),
        parsed_data=True,
    )


_OBJECTIVE_LABELS = {
    "CHAT_MESSAGE_FIRSTBLOOD": "Первая кровь",
    "CHAT_MESSAGE_ROSHAN_KILL": "Рошан убит",
    "CHAT_MESSAGE_AEGIS": "Эгида",
    "CHAT_MESSAGE_AEGIS_STOLEN": "Эгида украдена",
    "CHAT_MESSAGE_COURIER_LOST": "Курьер потерян",
    "CHAT_MESSAGE_COURIER_KILL": "Курьер убит",
    "CHAT_MESSAGE_BUYBACK": "Выкуп",
    "CHAT_MESSAGE_EFFIGY_KILL": "Эффигия",
    "CHAT_MESSAGE_MINIBOSS_KILL": "Мини-босс",
    "CHAT_MESSAGE_GLYPH_USED": "Глиф",
    "building_kill": "Строение разрушено",
}


def _objective(entry: dict[str, Any], heroes: dict[int, str]) -> Objective:
    kind = str(entry.get("type") or entry.get("event") or "")
    label = _OBJECTIVE_LABELS.get(kind, kind.replace("CHAT_MESSAGE_", "").replace("_", " ").lower())

    if kind == "building_kill":
        unit = str(entry.get("unit") or "")
        if unit.startswith("npc_dota_hero_"):
            slug = unit[len("npc_dota_hero_") :]
            label = f"Строение снесено · {_pretty_slug(slug, heroes)}"
        else:
            label = f"Строение снесено · {_building_name(str(entry.get('key') or ''))}"

    team: int | None = None
    if "team" in entry:
        team = int(entry["team"])
    elif "player_slot" in entry:
        team = 0 if int(entry["player_slot"]) < 128 else 1

    return Objective(time=int(entry.get("time") or 0), kind=kind, label=label, team=team)


def _pretty_slug(slug: str, heroes: dict[int, str]) -> str:
    for name in heroes.values():
        if name.lower().replace(" ", "").replace("-", "") == slug.replace("_", ""):
            return name
    return slug.replace("_", " ").title()


def _building_name(key: str) -> str:
    if not key:
        return "здание"
    tail = key.rsplit("_", 1)[-1].replace("badguys", "dire").replace("goodguys", "radiant")
    return {
        "tower1": "T1",
        "tower2": "T2",
        "tower3": "T3",
        "tower4": "T4",
        "melee": "бараки (melee)",
        "ranged": "бараки (ranged)",
        "healers": "бараки (healers)",
        "filler": "башня",
    }.get(tail, tail)


def meta_from_stats(
    stats_raw: list[dict[str, Any]],
    heroes: dict[int, str] | None = None,
) -> list[HeroMeta]:
    heroes = heroes or {}
    out: list[HeroMeta] = []
    for row in stats_raw:
        hero_id = int(row.get("id") or 0)
        out.append(
            HeroMeta(
                game="dota2",
                hero_id=hero_id,
                name=heroes.get(hero_id) or row.get("localized_name") or str(hero_id),
                roles=list(row.get("roles") or []),
                pro_pick=int(row.get("pro_pick") or 0),
                pro_win=int(row.get("pro_win") or 0),
                pub_pick=int(row.get("pub_pick") or 0),
                pub_win=int(row.get("pub_win") or 0),
                img=img_url(row.get("img")),
                icon=img_url(row.get("icon")),
            )
        )
    return out
