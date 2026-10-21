"""Bundled offline reference data for Counter-Strike 2.

No public CS2 source gives live pro/match data without an API key, so the
adapter ships a curated, clearly-labelled reference set: the active map pool,
Premier rank bands, the main weapon classes and a snapshot of the top pro
teams. This keeps the Meta Hub and Pro Scene useful out of the box, and the
same shapes are reused when a live key is configured.
"""
from __future__ import annotations

from typing import Any

# --- Active Duty map pool (as of the 2026 rotation) ------------------------

MAPS: list[dict[str, Any]] = [
    {"name": "Ancient", "slug": "ancient", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Anubis", "slug": "anubis", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Dust2", "slug": "dust2", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Inferno", "slug": "inferno", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Mirage", "slug": "mirage", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Nuke", "slug": "nuke", "sites": ["A", "B"], "kind": "defusal"},
    {"name": "Train", "slug": "train", "sites": ["A", "B"], "kind": "defusal"},
]

# --- Premier rating bands (CS2 Premier mode) -------------------------------

PREMIER_RANKS: list[tuple[int, str, str]] = [
    (0, "Без ранга", "#5a6472"),
    (5000, "Silver I", "#9aa4b2"),
    (10000, "Silver II", "#a7b1bf"),
    (15000, "Silver III", "#b4bdca"),
    (20000, "Gold I", "#d9b45a"),
    (25000, "Gold II", "#e0bd68"),
    (30000, "Gold III", "#e6c676"),
    (35000, "Platinum I", "#7fc8d6"),
    (40000, "Platinum II", "#8bd0dd"),
    (45000, "Platinum III", "#97d8e4"),
    (50000, "Diamond I", "#6f8cff"),
    (55000, "Diamond II", "#7d97ff"),
    (60000, "Diamond III", "#8ba3ff"),
    (65000, "Master", "#b07bff"),
    (70000, "Master+", "#b986ff"),
    (75000, "Legendary", "#ff7bd0"),
    (80000, "Legendary+", "#ff86d5"),
    (85000, "Global Elite", "#ff5c5c"),
]

# --- Weapon classes (shape mirrors Dota item_info: id -> {name, img}) ------

WEAPONS: dict[int, str] = {
    1: "AK-47", 2: "M4A4", 3: "M4A1-S", 4: "AWP", 5: "Desert Eagle",
    6: "USP-S", 7: "Glock-18", 8: "P250", 9: "Tec-9", 10: "Five-SeveN",
    11: "Galil AR", 12: "FAMAS", 13: "SG 553", 14: "AUG", 15: "SSG 08",
    16: "MP9", 17: "MAC-10", 18: "MP5-SD", 19: "UMP-45", 20: "P90",
    21: "Negev", 22: "M249", 23: "Nova", 24: "XM1014", 25: "MAG-7",
    26: "High Explosive Grenade", 27: "Flashbang", 28: "Smoke Grenade",
    29: "Molotov", 30: "Incendiary Grenade", 31: "Decoy Grenade",
}

# --- Pro scene snapshot (offline reference) --------------------------------
# Ratings are a static reference ordering, not live; teams/leagues rotate each
# season. Attributed as a bundled snapshot in the UI.

PRO_TEAMS: list[dict[str, Any]] = [
    {"team_id": 1, "name": "Vitality", "tag": "VIT", "rating": 1000.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 2, "name": "Spirit", "tag": "SPR", "rating": 970.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 3, "name": "FaZe", "tag": "FaZe", "rating": 940.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 4, "name": "MOUZ", "tag": "MOUZ", "rating": 915.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 5, "name": "G2", "tag": "G2", "rating": 890.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 6, "name": "NAVI", "tag": "NAVI", "rating": 870.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 7, "name": "THE MONGOLZ", "tag": "MGLZ", "rating": 850.0, "wins": 0, "losses": 0, "region": "AS"},
    {"team_id": 8, "name": "Astralis", "tag": "AST", "rating": 830.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 9, "name": "Falcons", "tag": "FLC", "rating": 815.0, "wins": 0, "losses": 0, "region": "EU"},
    {"team_id": 10, "name": "Liquid", "tag": "TL", "rating": 800.0, "wins": 0, "losses": 0, "region": "NA"},
]

PRO_PLAYERS: list[dict[str, Any]] = [
    {"account_id": 1, "name": "ZywOo", "team_name": "Vitality", "team_tag": "VIT", "country_code": "FR", "is_pro": True},
    {"account_id": 2, "name": "donk", "team_name": "Spirit", "team_tag": "SPR", "country_code": "RU", "is_pro": True},
    {"account_id": 3, "name": "m0NESY", "team_name": "Falcons", "team_tag": "FLC", "country_code": "RU", "is_pro": True},
    {"account_id": 4, "name": "sh1ro", "team_name": "Spirit", "team_tag": "SPR", "country_code": "RU", "is_pro": True},
    {"account_id": 5, "name": "ropz", "team_name": "Vitality", "team_tag": "VIT", "country_code": "EE", "is_pro": True},
    {"account_id": 6, "name": "NiKo", "team_name": "Falcons", "team_tag": "FLC", "country_code": "BA", "is_pro": True},
    {"account_id": 7, "name": "donk", "team_name": "Spirit", "team_tag": "SPR", "country_code": "RU", "is_pro": True},
    {"account_id": 8, "name": "b1t", "team_name": "NAVI", "team_tag": "NAVI", "country_code": "UA", "is_pro": True},
    {"account_id": 9, "name": "flameZ", "team_name": "Vitality", "team_tag": "VIT", "country_code": "IL", "is_pro": True},
    {"account_id": 10, "name": "frozen", "team_name": "FaZe", "team_tag": "FaZe", "country_code": "SK", "is_pro": True},
]


def premier_rank(rating: int) -> str:
    label = PREMIER_RANKS[0][1]
    for threshold, name, _color in PREMIER_RANKS:
        if rating >= threshold:
            label = name
        else:
            break
    return label


def premier_color(rating: int) -> str:
    color = PREMIER_RANKS[0][2]
    for threshold, _name, c in PREMIER_RANKS:
        if rating >= threshold:
            color = c
        else:
            break
    return color


# --- Per-map reference played/winrates (clearly a snapshot, not live) -------
# Kept as illustrative meta so the Meta Hub has signal offline.
MAP_META: dict[str, dict[str, int]] = {
    "Ancient": {"picks": 820, "wins": 410},
    "Anubis": {"picks": 610, "wins": 300},
    "Dust2": {"picks": 1180, "wins": 596},
    "Inferno": {"picks": 1040, "wins": 520},
    "Mirage": {"picks": 1320, "wins": 656},
    "Nuke": {"picks": 900, "wins": 452},
    "Train": {"picks": 540, "wins": 268},
}
