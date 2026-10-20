"""Synchronous facade the desktop UI talks to.

Composes a game adapter with the analytics layer and owns cache invalidation,
so panels never call adapters or analytics directly.
"""
from __future__ import annotations

from typing import Any

from .adapters.base import GameAdapter
from .adapters.dota2 import Dota2Adapter
from .analytics import meta_hub, skill_lab

_DEFAULT_TTL = 600.0


class KdaService:
    def __init__(self, ttl: float = _DEFAULT_TTL) -> None:
        self._adapters: dict[str, GameAdapter] = {
            Dota2Adapter.slug: Dota2Adapter(ttl=ttl),
        }

    # --- registry ---

    @property
    def games(self) -> list[dict[str, str]]:
        return [{"slug": a.slug, "name": a.name} for a in self._adapters.values()]

    def adapter(self, game: str) -> GameAdapter:
        adapter = self._adapters.get(game)
        if adapter is None:
            raise KeyError(f"unknown game: {game!r}")
        return adapter

    # --- data ---

    def search(self, query: str, game: str = "dota2") -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.adapter(game).search(query)]

    def profile(self, account_id: int, game: str = "dota2", limit: int = 20) -> dict[str, Any]:
        adapter = self.adapter(game)
        player = adapter.player(account_id)
        matches = adapter.recent_matches(account_id, limit=limit)
        data = skill_lab.build_profile(player, matches)

        hero_icon = getattr(adapter, "hero_icon", None)
        if callable(hero_icon):
            for row in data.get("heroes", []):
                row["icon"] = hero_icon(row["hero_id"])
            for row in data.get("recent", []):
                row["icon"] = hero_icon(row["hero_id"])
        return data

    def career(self, account_id: int, game: str = "dota2") -> dict[str, Any]:
        adapter = self.adapter(game)
        raw = adapter.career_stats(account_id)
        images: dict[int, str] = {}
        hero_icon = getattr(adapter, "hero_icon", None)
        if callable(hero_icon):
            for row in raw.get("heroes", []):
                hero_id = int(row.get("hero_id") or 0)
                images[hero_id] = hero_icon(hero_id)
        return skill_lab.career_from_stats(raw, raw.get("heroes"), images)

    def match(self, match_id: int, game: str = "dota2") -> dict[str, Any]:
        adapter = self.adapter(game)
        detail = adapter.match_detail(match_id)
        data = skill_lab.match_summary(detail)

        item_info = getattr(adapter, "item_info", None)
        if callable(item_info):
            for side in ("radiant", "dire"):
                for row in data[side]:
                    row["item_meta"] = [item_info(i) for i in row["items"]]
        return data

    def request_parse(self, match_id: int, game: str = "dota2") -> bool:
        adapter = self.adapter(game)
        requester = getattr(adapter, "request_parse", None)
        return bool(requester(match_id)) if callable(requester) else False

    def hero_detail(self, hero_id: int, game: str = "dota2") -> dict[str, Any]:
        adapter = self.adapter(game)
        raw = adapter.hero_detail(hero_id)
        data = skill_lab.hero_from_raw(raw, self._hero_names(game))

        item_info = getattr(adapter, "item_info", None)
        if callable(item_info):
            for phase, ids in data["items"].items():
                data["items"][phase] = [item_info(i) for i in ids]

        iconer = getattr(adapter, "hero_icon", None)
        if callable(iconer):
            for row in data["matchups"]:
                row["icon"] = iconer(row["hero_id"])
        return data

    def pro_scene(self, game: str = "dota2") -> dict[str, Any]:
        adapter = self.adapter(game)
        matches = [skill_lab.pro_match_from_raw(m) for m in adapter.pro_matches()]
        teams = sorted(
            (skill_lab.team_from_raw(t) for t in adapter.teams()),
            key=lambda t: t["rating"],
            reverse=True,
        )
        players = [skill_lab.pro_player_from_raw(p) for p in adapter.pro_players()]
        return {"matches": matches, "teams": teams[:100], "players": players}

    def _hero_names(self, game: str) -> dict[int, str]:
        cached = getattr(self, "_hero_name_cache", None)
        if cached is None:
            try:
                cached = {h.hero_id: h.name for h in self.adapter(game).heroes()}
            except Exception:  # noqa: BLE001 - lookup is best-effort
                cached = {}
            self._hero_name_cache = cached
        return cached

    def meta(self, game: str = "dota2") -> dict[str, Any]:
        return meta_hub.build_meta(self.adapter(game).heroes())

    def game_modes(self, game: str = "dota2") -> dict[int, str]:
        adapter = self.adapter(game)
        mapper = getattr(adapter, "constants_map", None)
        return mapper("game_mode") if callable(mapper) else {}

    def regions(self, game: str = "dota2") -> dict[int, str]:
        adapter = self.adapter(game)
        mapper = getattr(adapter, "constants_map", None)
        return mapper("region") if callable(mapper) else {}

    # --- lifecycle ---

    def refresh(self) -> None:
        """Drop cached payloads so the next call pulls current data."""
        for adapter in self._adapters.values():
            client = getattr(adapter, "client", None)
            cache = getattr(client, "cache", None)
            if cache is not None:
                cache.clear()

    def close(self) -> None:
        for adapter in self._adapters.values():
            adapter.close()
