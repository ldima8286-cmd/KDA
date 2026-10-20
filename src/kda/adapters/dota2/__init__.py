"""Dota 2 adapter backed by the public OpenDota API."""
from __future__ import annotations

from ...core.models import HeroMeta, Match, Player
from ..base import GameAdapter
from . import normalize
from .opendota import OpenDotaClient


class Dota2Adapter(GameAdapter):
    slug = "dota2"
    name = "Dota 2"

    def __init__(self, ttl: float = 300.0) -> None:
        self.client = OpenDotaClient(ttl=ttl)
        self._heroes: dict[int, str] | None = None
        self._images: dict[int, str] | None = None

    def _hero_map(self) -> dict[int, str]:
        if self._heroes is None:
            self._heroes = normalize.hero_index(self.client.heroes())
        return self._heroes

    def hero_image(self, hero_id: int) -> str | None:
        if self._images is None:
            self._images = {
                int(row.get("id") or 0): url
                for row in self.client.hero_stats()
                if (url := normalize.img_url(row.get("img")))
            }
        return self._images.get(hero_id)

    def search(self, query: str) -> list[Player]:
        raw = self.client.search(query)
        return [
            Player(
                game=self.slug,
                account_id=int(item.get("account_id") or 0),
                name=item.get("personaname") or str(item.get("account_id")),
                avatar=item.get("avatarfull"),
            )
            for item in raw
            if item.get("account_id")
        ]

    def player(self, account_id: int) -> Player:
        return normalize.player_from_raw(account_id, self.client.player(account_id))

    def recent_matches(self, account_id: int, limit: int = 20) -> list[Match]:
        self._hero_map()
        raw = self.client.recent_matches(account_id)
        return [
            normalize.match_from_recent(account_id, row, normalize.hero_index_name(self._heroes, row))
            for row in raw[:limit]
        ]

    def heroes(self) -> list[HeroMeta]:
        self._hero_map()
        stats = self.client.hero_stats()
        return normalize.meta_from_stats(stats, self._heroes)

    def close(self) -> None:
        self.client.close()
