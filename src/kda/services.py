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

        # Enrich with hero thumbnails when the adapter can provide them.
        image = getattr(adapter, "hero_image", None)
        if callable(image):
            for row in data.get("heroes", []):
                row["img"] = image(row["hero_id"])
            for row in data.get("recent", []):
                row["img"] = image(row["hero_id"])
        return data

    def meta(self, game: str = "dota2") -> dict[str, Any]:
        return meta_hub.build_meta(self.adapter(game).heroes())

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
