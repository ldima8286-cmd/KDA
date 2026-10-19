"""Thin async client for the public OpenDota API (Dota 2).

No API key is required for the endpoints used here. Responses are cached with a
short TTL so the UI can poll freely without hammering the service.
"""
from __future__ import annotations

import asyncio
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
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base,
                timeout=httpx.Timeout(30.0),
                headers={"User-Agent": "KDA/0.1 (+https://github.com)"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, **params: Any) -> Any:
        key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        client = await self._http()
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = await client.get(path, params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(1.0 + attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                self.cache.set(key, data)
                return data
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                await asyncio.sleep(0.5 * (attempt + 1))
        raise OpenDotaError(f"GET {path} failed: {last_exc}")

    # --- high level ---

    async def search(self, query: str) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        data = await self._get("/search", q=query.strip())
        return data if isinstance(data, list) else []

    async def player(self, account_id: int) -> dict[str, Any]:
        return await self._get(f"/players/{account_id}")

    async def matches(self, account_id: int, limit: int = 20) -> list[dict[str, Any]]:
        data = await self._get(f"/players/{account_id}/matches", limit=limit)
        return data if isinstance(data, list) else []

    async def recent_matches(self, account_id: int) -> list[dict[str, Any]]:
        # Rich last-20 feed: includes gold_per_min / xp_per_min / last_hits.
        data = await self._get(f"/players/{account_id}/recentMatches")
        return data if isinstance(data, list) else []

    async def heroes(self) -> list[dict[str, Any]]:
        data = await self._get("/heroes")
        return data if isinstance(data, list) else []

    async def hero_stats(self) -> list[dict[str, Any]]:
        data = await self._get("/heroStats")
        return data if isinstance(data, list) else []
