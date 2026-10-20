"""Dota 2 adapter backed by the public OpenDota API."""
from __future__ import annotations

from typing import Any

from ...analytics import skill_lab
from ...core.models import HeroMeta, Match, MatchDetail, Player
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
        self._icons: dict[int, str] | None = None
        self._items: dict[int, dict[str, str]] | None = None
        self._meta_constants: dict[str, dict[str, str]] = {}
        self._ability_names: dict[int, str] | None = None
        self._ability_meta: dict[int, dict[str, Any]] | None = None

    # --- lookups ---

    def _hero_map(self) -> dict[int, str]:
        if self._heroes is None:
            self._heroes = normalize.hero_index(self.client.heroes())
        return self._heroes

    def _hero_assets(self) -> tuple[dict[int, str], dict[int, str]]:
        if self._images is None or self._icons is None:
            images: dict[int, str] = {}
            icons: dict[int, str] = {}
            for row in self.client.hero_stats():
                hero_id = int(row.get("id") or 0)
                if url := normalize.img_url(row.get("img")):
                    images[hero_id] = url
                if url := normalize.img_url(row.get("icon")):
                    icons[hero_id] = url
            self._images, self._icons = images, icons
        return self._images, self._icons

    def hero_image(self, hero_id: int) -> str | None:
        return self._hero_assets()[0].get(hero_id)

    def hero_icon(self, hero_id: int) -> str | None:
        return self._hero_assets()[1].get(hero_id)

    def item_info(self, item_id: int) -> dict[str, str]:
        if self._items is None:
            table: dict[int, dict[str, str]] = {}
            for key, row in (self.client.constants("items") or {}).items():
                if not isinstance(row, dict):
                    continue
                table[int(row.get("id") or 0)] = {
                    "name": row.get("dname") or key,
                    "img": normalize.img_url(row.get("img")) or "",
                }
            self._items = table
        return self._items.get(item_id, {"name": "", "img": ""})

    def constants_map(self, name: str) -> dict[int, str]:
        if name not in self._meta_constants:
            raw = self.client.constants(name) or {}
            out: dict[int, str] = {}
            if isinstance(raw, dict):
                for key, row in raw.items():
                    if isinstance(row, dict):
                        label = row.get("name") or row.get("dname") or key
                    else:
                        label = str(row)
                    label = str(label)
                    for prefix in ("game_mode_", "game_modes_", "mode_"):
                        if label.startswith(prefix):
                            label = label[len(prefix) :]
                    label = label.replace("_", " ").strip().title()
                    try:
                        out[int(key)] = label
                    except (TypeError, ValueError):
                        continue
            self._meta_constants[name] = out
        return self._meta_constants[name]

    # --- queries ---

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

    def career_stats(self, account_id: int) -> dict[str, Any]:
        return {
            "wl": self.client.player_wl(account_id),
            "totals": self.client.player_totals(account_id),
            "heroes": self.client.player_heroes(account_id),
        }

    def match_detail(self, match_id: int) -> MatchDetail:
        heroes = self._hero_map()
        _, icons = self._hero_assets()
        return normalize.match_from_detail(self.client.match(match_id), heroes, icons)

    def request_parse(self, match_id: int) -> bool:
        return self.client.request_parse(match_id)

    def hero_detail(self, hero_id: int) -> dict[str, Any]:
        self._hero_map()
        images, icons = self._hero_assets()
        return {
            "hero_id": hero_id,
            "name": self._heroes.get(hero_id, str(hero_id)) if self._heroes else str(hero_id),
            "img": images.get(hero_id),
            "icon": icons.get(hero_id),
            "matchups": self.client.hero_matchups(hero_id),
            "durations": self.client.hero_durations(hero_id),
            "items": self.client.hero_items(hero_id),
        }

    def _ability_tables(self) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
        if self._ability_names is None or self._ability_meta is None:
            names: dict[int, str] = {}
            for key, value in (self.client.constants("ability_ids") or {}).items():
                try:
                    names[int(key)] = str(value)
                except (TypeError, ValueError):
                    continue
            by_name = {name: aid for aid, name in names.items()}
            meta: dict[int, dict[str, Any]] = {}
            for key, row in (self.client.constants("abilities") or {}).items():
                if not isinstance(row, dict):
                    continue
                ability_id = by_name.get(key)
                if ability_id is None:
                    continue
                meta[ability_id] = {
                    "dname": row.get("dname") or key,
                    "img": normalize.img_url(row.get("img")),
                }
            self._ability_names, self._ability_meta = names, meta
        return self._ability_names, self._ability_meta

    def hero_build(self, hero_id: int) -> dict[str, Any]:
        names, meta = self._ability_tables()
        return skill_lab.hero_build_from_raw(self.client.hero_skill_build(hero_id), names, meta)

    def hero_positions(self, hero_id: int) -> dict[str, Any]:
        """Pick share per lane position (1=carry ... 5=hard support)."""
        for row in self.client.hero_stats():
            if int(row.get("id") or 0) != int(hero_id):
                continue
            picks = [int(row.get(f"{p}_pick") or 0) for p in range(1, 6)]
            wins = [int(row.get(f"{p}_win") or 0) for p in range(1, 6)]
            total = sum(picks)
            positions = []
            for i, pos in enumerate(range(1, 6)):
                positions.append(
                    {
                        "position": pos,
                        "picks": picks[i],
                        "wins": wins[i],
                        "share": round(100.0 * picks[i] / total, 1) if total else 0.0,
                        "winrate": round(100.0 * wins[i] / picks[i], 1) if picks[i] else 0.0,
                    }
                )
            core = sum(picks[:3])
            support = sum(picks[3:])
            return {
                "total": total,
                "positions": positions,
                "core_share": round(100.0 * core / total, 1) if total else 0.0,
                "support_share": round(100.0 * support / total, 1) if total else 0.0,
            }
        return {"total": 0, "positions": [], "core_share": 0.0, "support_share": 0.0}

    def pro_matches(self) -> list[dict[str, Any]]:
        return self.client.pro_matches()
    def pro_players(self) -> list[dict[str, Any]]:
        return self.client.pro_players()

    def teams(self) -> list[dict[str, Any]]:
        return self.client.teams()

    def heroes(self) -> list[HeroMeta]:
        self._hero_map()
        stats = self.client.hero_stats()
        return normalize.meta_from_stats(stats, self._heroes)

    def close(self) -> None:
        self.client.close()
