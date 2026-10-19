"""Game adapter contract.

Each supported title implements this interface and returns the unified model,
so the analytics layer and UI stay game-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..core.models import HeroMeta, Match, Player


class GameAdapter(ABC):
    slug: str
    name: str

    @abstractmethod
    async def search(self, query: str) -> list[Player]:
        ...

    @abstractmethod
    async def player(self, account_id: int) -> Player:
        ...

    @abstractmethod
    async def recent_matches(self, account_id: int, limit: int = 20) -> list[Match]:
        ...

    @abstractmethod
    async def heroes(self) -> list[HeroMeta]:
        ...

    async def aclose(self) -> None:
        return None
