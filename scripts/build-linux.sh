#!/usr/bin/env bash
# Build a self-contained Linux binary at dist/KDA (no Python needed to run it).
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then
    "$PY" -m venv .venv
fi

.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements-build.txt
.venv/bin/python -m PyInstaller --clean --noconfirm packaging/kda.spec

echo
echo "Built: $(pwd)/dist/KDA"
