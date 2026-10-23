"""CS2 adapter.

Live data comes from the Steam Web API (free key in ``KDA_STEAM_KEY``): player
profiles and vanity resolution. CS2 exposes no public match history or pick/win
statistics without a commercial data provider, so the meta/pro-scene surfaces
are served from a clearly-labelled bundled snapshot (see ``data``). This keeps
the Meta Hub and Pro Scene meaningful out of the box and lets a live
provider be plugged in later without touching the UI.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from ...core.cache import TTLCache
from ...core.models import HeroMeta, Match, Player
from ..base import GameAdapter
from . import data as cs2data

_STEAM_API = "https://api.steampowered.com"
_REFERENCE_NOTE = "bundled reference snapshot"

# Re-exported reference data / helpers for callers and tests.
_MAPS = cs2data.MAPS
_PREMIER_RANKS = cs2data.PREMIER_RANKS
premier_rank = cs2data.premier_rank
premier_color = cs2data.premier_color


class SteamClient:
    def __init__(self, key: str | None = None, ttl: float = 300.0) -> None:
        self.key = key if key is not None else os.environ.get("KDA_STEAM_KEY", "")
        self.cache = TTLCache(ttl=ttl)
        self._client = httpx.Client(base_url=_STEAM_API, timeout=httpx.Timeout(20.0))

    @property
    def available(self) -> bool:
        return bool(self.key)

    def _get(self, path: str, **params: Any) -> Any:
        if not self.key:
            raise RuntimeError("KDA_STEAM_KEY is not set")
        params["key"] = self.key
        key = path + repr(sorted(params.items()))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        response = self._client.get(path, params=params)
        response.raise_for_status()
        data = response.json()
        self.cache.set(key, data)
        return data

    def player_summaries(self, steam_id: int) -> dict[str, Any]:
        return self._get("/ISteamUser/GetPlayerSummaries/v2/", steamids=steam_id)

    def resolve_vanity(self, vanity: str) -> dict[str, Any]:
        return self._get("/ISteamUser/ResolveVanityURL/v1/", vanityurl=vanity)

    def close(self) -> None:
        self._client.close()


class CS2Adapter(GameAdapter):
    slug = "cs2"
    name = "Counter-Strike 2"

    def __init__(self, ttl: float = 300.0) -> None:
        self.client = SteamClient(ttl=ttl)

    @property
    def live(self) -> bool:
        return self.client.available

    def hero_image(self, hero_id: int) -> str | None:
        return None

    def hero_icon(self, hero_id: int) -> str | None:
        return None

    def item_info(self, item_id: int) -> dict[str, str]:
        name = cs2data.WEAPONS.get(item_id)
        return {"name": name or "", "img": ""}

    def constants_map(self, name: str) -> dict[int, str]:
        if name in ("map", "maps"):
            return {i + 1: m["name"] for i, m in enumerate(cs2data.MAPS)}
        if name in ("weapon", "weapons"):
            return dict(cs2data.WEAPONS)
        return {}

    def search(self, query: str) -> list[Player]:
        text = (query or "").strip()
        if not text:
            return []
        if text.isdigit() and len(text) >= 6:
            return [self.player(int(text))]
        if not self.live:
            raise RuntimeError(
                "Поиск игроков CS2 требует ключа Steam (KDA_STEAM_KEY). "
                f"Доступна офлайн-мета: {_REFERENCE_NOTE}."
            )
        raw = self.client.resolve_vanity(text)
        steam_id = raw.get("response", {}).get("steamid")
        if not steam_id:
            return []
        return [self.player(int(steam_id))]

    def player(self, account_id: int) -> Player:
        if self.live:
            raw = self.client.player_summaries(account_id)
            players = raw.get("response", {}).get("players") or [{}]
            info = players[0]
            return Player(
                game=self.slug,
                account_id=account_id,
                name=info.get("personaname") or str(account_id),
                avatar=info.get("avatarfull"),
                country=info.get("loccountrycode"),
                profile_url=info.get("profileurl"),
            )
        return Player(game=self.slug, account_id=account_id, name=str(account_id))

    def recent_matches(self, account_id: int, limit: int = 20) -> list[Match]:
        return []

    def career_stats(self, account_id: int) -> dict[str, Any]:
        return {"totals": [], "wl": {}, "heroes": []}

    def player_stats(self, account_id: int) -> dict[str, Any]:
        return {"player": self.player(account_id).to_dict()}

    def heroes(self) -> list[HeroMeta]:
        rows: list[HeroMeta] = []
        for i, m in enumerate(cs2data.MAPS, start=1):
            meta = cs2data.MAP_META.get(m["name"], {})
            picks = int(meta.get("picks") or 0)
            wins = int(meta.get("wins") or 0)
            rows.append(
                HeroMeta(
                    game=self.slug,
                    hero_id=i,
                    name=m["name"],
                    roles=list(m.get("sites") or []),
                    pro_pick=picks,
                    pro_win=wins,
                    pub_pick=picks,
                    pub_win=wins,
                )
            )
        return rows

    def pro_matches(self) -> list[dict[str, Any]]:
        return []

    def pro_players(self) -> list[dict[str, Any]]:
        return [dict(p) for p in cs2data.PRO_PLAYERS]

    def teams(self) -> list[dict[str, Any]]:
        return [dict(t) for t in cs2data.PRO_TEAMS]

    def close(self) -> None:
        self.client.close()
