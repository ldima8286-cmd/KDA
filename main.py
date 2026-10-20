"""Launcher entry point used by run scripts and PyInstaller builds."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from kda.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
