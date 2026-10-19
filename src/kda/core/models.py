"""Unified, game-agnostic domain model.

Every game adapter normalises its own data into these types, so analytics and
UI never need to know which title a match came from.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional


@dataclass
class Game:
    slug: str
    name: str


@dataclass
class Player:
    game: str
    account_id: int
    name: str
    avatar: Optional[str] = None
    country: Optional[str] = None
    rank_tier: Optional[int] = None
    profile_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatchPlayer:
    account_id: int
    hero_id: int
    hero_name: str = ""
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gpm: int = 0
    xpm: int = 0
    last_hits: int = 0
    net_worth: int = 0
    win: bool = False

    @property
    def kda(self) -> float:
        return (self.kills + self.assists) / max(self.deaths, 1)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kda"] = round(self.kda, 2)
        return data


@dataclass
class Match:
    game: str
    match_id: int
    start_time: int
    duration: int
    radiant_win: bool
    mode: Optional[int] = None
    lobby_type: Optional[int] = None
    players: List[MatchPlayer] = field(default_factory=list)


@dataclass
class HeroMeta:
    game: str
    hero_id: int
    name: str
    roles: List[str] = field(default_factory=list)
    pro_pick: int = 0
    pro_win: int = 0
    pub_pick: int = 0
    pub_win: int = 0
    img: Optional[str] = None

    @staticmethod
    def _rate(win: int, pick: int) -> float:
        return round(100.0 * win / pick, 2) if pick else 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pro_winrate"] = self._rate(self.pro_win, self.pro_pick)
        data["pub_winrate"] = self._rate(self.pub_win, self.pub_pick)
        return data
