"""Tiny async TTL cache used to be polite to public APIs."""
from __future__ import annotations

import time
from typing import Any, Dict, Tuple


class TTLCache:
    def __init__(self, ttl: float = 300.0) -> None:
        self.ttl = ttl
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        expires, value = entry
        if time.time() > expires:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._store[key] = (time.time() + (ttl if ttl is not None else self.ttl), value)

    def clear(self) -> None:
        self._store.clear()
