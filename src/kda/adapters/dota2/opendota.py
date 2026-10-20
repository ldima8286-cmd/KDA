"""Thin synchronous client for the public OpenDota API (Dota 2).

No API key is required for the endpoints used here. Responses are cached with a
short TTL so relaunching the app (or switching panels) is instant; a fresh
launch clears the cache and pulls current data when online.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from ...core.cache import TTLCache

BASE = "https://api.opendota.com/api"


class OpenDotaError(RuntimeError):
    pass


class OpenDotaClient:
    def __init__(self, base: str = BASE, ttl: float = 300.0) -> None:
        self.base = base.rstrip("/")
        self.cache = TTLCache(ttl)
        self._client = httpx.Client(
            base_url=self.base,
            timeout=httpx.Timeout(30.0, read=90.0),
            headers={"User-Agent": "KDA/0.1 (+https://github.com)"},
        )

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, **params: Any) -> Any:
        key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = self._client.get(path, params=params)
                if resp.status_code == 429:
                    time.sleep(1.0 + attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                self.cache.set(key, data)
                return data
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(0.5 * (attempt + 1))
        raise OpenDotaError(f"GET {path} failed: {last_exc}")

    # --- high level ---

    def search(self, query: str) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        data = self._get("/search", q=query.strip())
        return data if isinstance(data, list) else []

    def player(self, account_id: int) -> dict[str, Any]:
        return self._get(f"/players/{account_id}")

    def matches(self, account_id: int, limit: int = 20) -> list[dict[str, Any]]:
        data = self._get(f"/players/{account_id}/matches", limit=limit)
        return data if isinstance(data, list) else []

    def recent_matches(self, account_id: int) -> list[dict[str, Any]]:
        # Rich last-20 feed: includes gold_per_min / xp_per_min / last_hits.
        data = self._get(f"/players/{account_id}/recentMatches")
        return data if isinstance(data, list) else []

    def player_heroes(self, account_id: int) -> list[dict[str, Any]]:
        """Career stats per hero (games/win/last_played)."""
        data = self._get(f"/players/{account_id}/heroes")
        return data if isinstance(data, list) else []

    def player_totals(self, account_id: int) -> list[dict[str, Any]]:
        """Career averages (kills/deaths/gpm/... sums with sample counts)."""
        data = self._get(f"/players/{account_id}/totals")
        return data if isinstance(data, list) else []

    def player_wl(self, account_id: int) -> dict[str, Any]:
        data = self._get(f"/players/{account_id}/wl")
        return data if isinstance(data, dict) else {}

    def match(self, match_id: int) -> dict[str, Any]:
        data = self._get(f"/matches/{match_id}")
        return data if isinstance(data, dict) else {}

    def request_parse(self, match_id: int) -> bool:
        """Ask OpenDota to parse a match. Returns True when the job was queued."""
        try:
            resp = self._client.post(f"/request/{match_id}")
            resp.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def hero_matchups(self, hero_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/heroes/{hero_id}/matchups")
        return data if isinstance(data, list) else []

    def hero_durations(self, hero_id: int) -> list[dict[str, Any]]:
        data = self._get(f"/heroes/{hero_id}/durations")
        return data if isinstance(data, list) else []

    def hero_items(self, hero_id: int) -> dict[str, Any]:
        data = self._get(f"/heroes/{hero_id}/itemPopularity")
        return data if isinstance(data, dict) else {}

    def pro_matches(self) -> list[dict[str, Any]]:
        data = self._get("/proMatches")
        return data if isinstance(data, list) else []

    def pro_players(self) -> list[dict[str, Any]]:
        data = self._get("/proPlayers")
        return data if isinstance(data, list) else []

    def teams(self) -> list[dict[str, Any]]:
        data = self._get("/teams")
        return data if isinstance(data, list) else []

    def heroes(self) -> list[dict[str, Any]]:
        data = self._get("/heroes")
        return data if isinstance(data, list) else []

    def hero_stats(self) -> list[dict[str, Any]]:
        data = self._get("/heroStats")
        return data if isinstance(data, list) else []

    # --- reference data ---

    def constants(self, name: str) -> Any:
        return self._get(f"/constants/{name}")
