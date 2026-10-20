#!/usr/bin/env bash
# Launch KDA (native Qt desktop app).
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi

PY=".venv/bin/python"
if ! "$PY" -c "import fastapi, uvicorn, httpx" >/dev/null 2>&1; then
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install -q -r requirements.txt
fi

export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m kda "$@"
