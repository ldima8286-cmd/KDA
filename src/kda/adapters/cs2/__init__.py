"""CS2 adapter backed by the Steam Web API (requires a free API key).

Set the key in the environment as ``KDA_STEAM_KEY``. Without a key the adapter
still serves a bundled offline reference (maps and Premier ranks) so the Meta
Hub works, but live player data is unavailable.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from ...core.cache import TTLCache
from ...core.models import HeroMeta, Match, MatchPlayer, Player
from ..base import GameAdapter

_STEAM_API = "https://api.steampowered.com"

_PREMIER_RANKS = [
    (0, "Без ранга"),
    (5000, "Silver I"),
    (10000, "Silver II"),
    (15000, "Silver III"),
    (20000, "Gold I"),
    (25000, "Gold II"),
    (30000, "Gold III"),
    (35000, "Platinum I"),
    (40000, "Platinum II"),
    (45000, "Platinum III"),
    (50000, "Diamond I"),
    (55000, "Diamond II"),
    (60000, "Diamond III"),
    (65000, "Master"),
    (70000, "Master+"),
    (75000, "Legendary"),
    (80000, "Legendary+"),
    (85000, "Global Elite"),
]

_MAPS = [
    "Ancient", "Anubis", "Dust2", "Inferno", "Mirage",
    "Nuke", "Overpass", "Train", "Vertigo",
]


def premier_rank(rating: int) -> str:
    label = _PREMIER_RANKS[0][1]
    for threshold, name in _PREMIER_RANKS:
        if rating >= threshold:
            label = name
        else:
            break
    return label


class SteamClient:
    def __init__(self, key: str | None = None, ttl: float = 300.0) -> None:
        self.key = key if key is not None else os.environ.get("KDA_STEAM_KEY", "")
        self.cache = TTLCache(ttl=ttl)
        self._client = httpx.Client(base_url=_STEAM_API, timeout=httpx.Timeout(20.0))

    def _get(self, path: str, **params: Any) -> Any:
        if not self.key:
            raise RuntimeError("KDA_STEAM_KEY is not set")
        params["key"] = self.key
        cached = self.cache.get(path + repr(sorted(params.items())))
        if cached is not None:
            return cached
        response = self._client.get(path, params=params)
        response.raise_for_status()
        data = response.json()
        self.cache.set(path + repr(sorted(params.items())), data)
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

    # --- queries ---

    def search(self, query: str) -> list[Player]:
        raw = self.client.resolve_vanity(query)
        steam_id = raw.get("response", {}).get("steamid")
        if not steam_id:
            return []
        return [self.player(int(steam_id))]

    def player(self, account_id: int) -> Player:
        raw = self.client.player_summaries(account_id)
        players = raw.get("response", {}).get("players") or [{}]
        info = players[0]
        return Player(
            game=self.slug,
            account_id=account_id,
            name=info.get("personaname") or str(account_id),
            avatar=info.get("avatarfull"),
        )

    def recent_matches(self, account_id: int, limit: int = 20) -> list[Match]:
        # Live CS2 match history is not exposed by the Steam Web API.
        return []

    def heroes(self) -> list[HeroMeta]:
        return [
            HeroMeta(
                game=self.slug,
                hero_id=i + 1,
                name=name,
                roles=["map"],
                pro_pick=0,
                pro_win=0,
                pub_pick=0,
                pub_win=0,
            )
            for i, name in enumerate(_MAPS)
        ]

    def player_stats(self, account_id: int) -> dict[str, Any]:
        return {"player": self.player(account_id).to_dict()}

    def close(self) -> None:
        self.client.close()
