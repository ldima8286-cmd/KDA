"""Thin synchronous client for the public OpenDota API (Dota 2).

No API key is required for the endpoints used here. Responses are cached with a
short TTL so relaunching the app (or switching panels) is instant; a fresh
launch clears the cache and pulls current data when online.
"""
from __future__ import annotations

import time
from datetime import datetime
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
        status: int | None = None
        attempts = 5
        for attempt in range(attempts):
            try:
                resp = self._client.get(path, params=params)
                status = resp.status_code
                if status == 429 or status >= 500:
                    # Rate limited or the origin is briefly down (Cloudflare
                    # 521/522/523) — back off and retry rather than surfacing
                    # a scary network error.
                    if attempt < attempts - 1:
                        time.sleep(1.0 * (2**attempt))
                        continue
                resp.raise_for_status()
                data = resp.json()
                self.cache.set(key, data)
                return data
            except httpx.HTTPError as exc:
                last_exc = exc
                code = getattr(getattr(exc, "response", None), "status_code", None)
                if code is not None and 400 <= code < 500 and code != 429:
                    # Client errors won't heal on retry — fail fast.
                    break
                if attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
        if status is not None and status >= 500:
            raise OpenDotaError(
                f"сервер OpenDota временно недоступен ({status}) — повторите позже"
            )
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

    def sql(self, query: str) -> list[dict[str, Any]]:
        """Run an SQL query through the public /explorer endpoint."""
        key = "explorer:" + query
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = self._client.get("/explorer", params={"sql": query})
                if resp.status_code == 429:
                    time.sleep(1.5 + attempt * 2)
                    continue
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("rows") or []
                self.cache.set(key, rows, ttl=1800.0)
                return rows
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(1.0 * (attempt + 1))
        raise OpenDotaError(f"explorer query failed: {last_exc}")

    def patches(self, limit: int = 4) -> list[dict[str, Any]]:
        """Recent patches (newest first) with raw and epoch dates.

        OpenDota tracks major versions (7.41); lettered sub-patches fall inside
        the same window, so filtering by the newest patch date keeps builds
        current without stale talents from older patches.
        """
        cached = self.cache.get("patches")
        if cached is not None:
            return cached[:limit]
        out: list[dict[str, Any]] = []
        try:
            raw = self._get("/constants/patch")
        except Exception:  # noqa: BLE001 - patches are best-effort
            raw = []
        for row in raw or []:
            if not isinstance(row, dict):
                continue
            date = str(row.get("date") or "")
            try:
                epoch = int(datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp())
            except ValueError:
                continue
            out.append(
                {"id": row.get("id"), "name": row.get("name"), "date": date, "epoch": epoch}
            )
        out.sort(key=lambda item: item["epoch"], reverse=True)
        self.cache.set("patches", out, ttl=6 * 3600.0)
        return out[:limit]

    def hero_skill_build(
        self, hero_id: int, sample: int = 8000, patches_back: int = 3
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Raw ability-upgrade arrays plus lane/gold, from parsed games.

        ``lane_role`` is 1=safe, 2=mid, 3=off, 4=jungle; ``gold_per_min`` lets
        us split core vs support within each lane. Rows are limited to the most
        recent patch so talents reflect the current game, not old rotations.
        """
        select = (
            "SELECT pm.ability_upgrades_arr, pm.lane_role, pm.gold_per_min "
            "FROM player_matches pm JOIN matches m ON m.match_id = pm.match_id "
        )
        try:
            recent = self.patches(limit=patches_back)
        except Exception:  # noqa: BLE001
            recent = []
        for patch in recent:
            query = (
                select
                + f"WHERE pm.hero_id = {int(hero_id)} "
                "AND pm.ability_upgrades_arr IS NOT NULL "
                f"AND m.start_time >= {int(patch['epoch'])} "
                f"LIMIT {int(sample)}"
            )
            rows = self.sql(query)
            if rows:
                return rows, str(patch["name"])
        query = (
            "SELECT ability_upgrades_arr, lane_role, gold_per_min FROM player_matches "
            f"WHERE hero_id = {int(hero_id)} AND ability_upgrades_arr IS NOT NULL "
            f"LIMIT {int(sample)}"
        )
        return self.sql(query), None
