"""Meta Hub: reformat hero statistics into a ranked, shareable view."""
from __future__ import annotations

import time
from typing import Any

from ..core.models import HeroMeta


def build_meta(heroes: list[HeroMeta]) -> dict[str, Any]:
    rows = [h.to_dict() for h in heroes]

    total_pro = sum(r["pro_pick"] for r in rows) or 1
    total_pub = sum(r["pub_pick"] for r in rows) or 1
    for r in rows:
        r["pro_pick_share"] = round(100.0 * r["pro_pick"] / total_pro, 3)
        r["pub_pick_share"] = round(100.0 * r["pub_pick"] / total_pub, 3)
        r["contested"] = r["pro_pick_share"] >= 1.0

    pro_ranked = sorted(rows, key=lambda r: (r["pro_pick"], r["pro_winrate"]), reverse=True)
    pub_ranked = sorted(rows, key=lambda r: (r["pub_pick"], r["pub_winrate"]), reverse=True)

    return {
        "updated_at": int(time.time()),
        "count": len(rows),
        "pro_ranked": pro_ranked,
        "pub_ranked": pub_ranked,
        "heroes": rows,
    }
