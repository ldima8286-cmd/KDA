"""HTTP routes: a thin, game-agnostic surface over the adapters and analytics."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..adapters.base import GameAdapter
from ..adapters.dota2 import Dota2Adapter
from ..analytics import meta_hub, skill_lab

router = APIRouter()

_ADAPTERS: dict[str, GameAdapter] = {
    Dota2Adapter.slug: Dota2Adapter(),
}


def get_adapter(game: str) -> GameAdapter:
    adapter = _ADAPTERS.get(game)
    if adapter is None:
        raise HTTPException(status_code=404, detail=f"unknown game: {game!r}")
    return adapter


async def close_adapters() -> None:
    for adapter in _ADAPTERS.values():
        await adapter.aclose()


@router.get("/api/health")
async def health() -> dict:
    return {"ok": True, "games": list(_ADAPTERS.keys())}


@router.get("/api/games")
async def games() -> list[dict]:
    return [{"slug": a.slug, "name": a.name} for a in _ADAPTERS.values()]


@router.get("/api/search")
async def search(q: str = Query(..., min_length=1), game: str = "dota2") -> dict:
    adapter = get_adapter(game)
    results = await adapter.search(q)
    return {"game": game, "results": [p.to_dict() for p in results]}


@router.get("/api/players/{account_id}")
async def player_profile(
    account_id: int,
    game: str = "dota2",
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    adapter = get_adapter(game)
    player = await adapter.player(account_id)
    matches = await adapter.recent_matches(account_id, limit=limit)
    return skill_lab.build_profile(player, matches)


@router.get("/api/meta")
async def meta(game: str = "dota2") -> dict:
    heroes = await get_adapter(game).heroes()
    return meta_hub.build_meta(heroes)
