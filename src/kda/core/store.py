"""SQLite snapshot store: keeps the last known payload per key for offline use."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class SnapshotStore:
    """Persists JSON payloads keyed by a string, so the app can show stale data offline."""

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            path = Path.home() / ".cache" / "kda" / "snapshots.db"
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS snapshots "
            "(key TEXT PRIMARY KEY, payload TEXT NOT NULL, saved_at REAL NOT NULL)"
        )
        self._conn.commit()

    def save(self, key: str, payload: Any) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO snapshots (key, payload, saved_at) VALUES (?, ?, ?)",
            (key, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        self._conn.commit()

    def load(self, key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload, saved_at FROM snapshots WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        payload, saved_at = row
        try:
            value = json.loads(payload)
        except (TypeError, ValueError):
            return None
        return {"value": value, "saved_at": saved_at}

    def keys(self) -> list[str]:
        return [r[0] for r in self._conn.execute("SELECT key FROM snapshots")]

    def clear(self) -> None:
        self._conn.execute("DELETE FROM snapshots")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
