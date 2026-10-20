"""Game adapter contract.

Each supported title implements this interface and returns the unified model,
so the analytics layer and UI stay game-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.models import HeroMeta, Match, Player


class GameAdapter(ABC):
    slug: str
    name: str

    @abstractmethod
    def search(self, query: str) -> list[Player]:
        ...

    @abstractmethod
    def player(self, account_id: int) -> Player:
        ...

    @abstractmethod
    def recent_matches(self, account_id: int, limit: int = 20) -> list[Match]:
        ...

    @abstractmethod
    def heroes(self) -> list[HeroMeta]:
        ...

    def close(self) -> None:
        return None
