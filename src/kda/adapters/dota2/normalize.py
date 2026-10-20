"""Normalise raw OpenDota payloads into the unified KDA model."""
from __future__ import annotations

from typing import Any

from ...core.models import HeroMeta, Match, MatchPlayer, Player


def player_from_raw(account_id: int, raw: dict[str, Any]) -> Player:
    profile = raw.get("profile") or {}
    return Player(
        game="dota2",
        account_id=account_id,
        name=profile.get("personaname") or str(account_id),
        avatar=profile.get("avatarfull"),
        country=profile.get("loccountrycode"),
        rank_tier=raw.get("rank_tier"),
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
            )
        )
    return out
