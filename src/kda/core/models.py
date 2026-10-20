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
    leaderboard_rank: Optional[int] = None
    profile_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatchPlayer:
    account_id: int
    hero_id: int
    hero_name: str = ""
    hero_icon: Optional[str] = None
    personaname: Optional[str] = None
    player_slot: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gpm: int = 0
    xpm: int = 0
    last_hits: int = 0
    denies: int = 0
    hero_damage: int = 0
    tower_damage: int = 0
    hero_healing: int = 0
    level: int = 0
    net_worth: int = 0
    items: List[int] = field(default_factory=list)
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
    patch: Optional[int] = None
    region: Optional[int] = None
    radiant_score: int = 0
    dire_score: int = 0
    players: List[MatchPlayer] = field(default_factory=list)

    def team(self, radiant: bool) -> List[MatchPlayer]:
        return [p for p in self.players if (p.player_slot < 128) == radiant]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["radiant_team"] = [p.to_dict() for p in self.team(True)]
        data["dire_team"] = [p.to_dict() for p in self.team(False)]
        return data


@dataclass
class PickBan:
    is_pick: bool
    hero_id: int
    team: int
    order: int = 0
    hero_name: str = ""


@dataclass
class Objective:
    time: int
    kind: str
    label: str = ""
    team: Optional[int] = None


@dataclass
class MatchDetail:
    """A parsed match: ten-player scoreboard plus the game's event timeline."""

    game: str
    match: Match
    picks_bans: List[PickBan] = field(default_factory=list)
    objectives: List[Objective] = field(default_factory=list)
    gold_adv: List[int] = field(default_factory=list)
    xp_adv: List[int] = field(default_factory=list)
    has_parsed: bool = False
    parsed_data: bool = False


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
    icon: Optional[str] = None

    @staticmethod
    def _rate(win: int, pick: int) -> float:
        return round(100.0 * win / pick, 2) if pick else 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pro_winrate"] = self._rate(self.pro_win, self.pro_pick)
        data["pub_winrate"] = self._rate(self.pub_win, self.pub_pick)
        return data
