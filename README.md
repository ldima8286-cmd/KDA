# KDA — esports intelligence

A local, self-contained esports analytics workstation. One dark, data-dense
interface over multiple games, starting with **Dota 2** (powered by the public
[OpenDota](https://docs.opendota.com/) API — no key required).

> The app runs entirely on your machine: a small FastAPI server + a hand-built
> web UI, wrapped in a Qt shell. No accounts, no telemetry, no cloud.

## Highlights

- **Skill Lab** — search any player by name or Steam `account_id` and get a
  full dossier: win rate, KDA, GPM/XPM, hero pool, a win-rate trend chart and
  the latest matches.
- **Meta Hub** — current hero meta with pro and pub pick/win rates, filterable
  and sortable.
- **Universal Engine** — a game-agnostic core (`Player` / `Match` / `HeroMeta`
  models + `GameAdapter` interface). Dota 2 is the first adapter; more games
  plug into the same UI without touching it.
- **Offline-friendly** — every upstream response is cached with a short TTL, so
  navigation is instant and the app keeps working through brief network blips.

## Screens

The UI follows a dark, dense esports aesthetic (Dota 2 client + HLTV tables +
Linear/Vercel surfaces). All charts are hand-rolled SVG — no external CDNs, no
font downloads.

## Quick start

Requirements: Python 3.11+ (3.13 recommended).

```bash
git clone https://github.com/ldima8286-cmd/KDA.git
cd KDA
./run.sh          # Linux/macOS
run.bat           # Windows
```

`run.sh` / `run.bat` create a virtual environment, install dependencies and
launch the app. The Qt shell opens a native window with the UI embedded; if
`QtWebEngine` is unavailable it falls back to opening your default browser.

### Manual / headless

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m kda
```

Server-only (useful on a headless box; open the printed URL from another
machine after port-forwarding):

```bash
PYTHONPATH=src .venv/bin/python -m uvicorn kda.server.app:app --host 127.0.0.1 --port 8000
```

If `QtWebEngine` fails to import on Linux, install your distro's Kerberos
runtime (`libkrb5`, e.g. `krb5-libs` / `libgssapi-krb5-2`).

## HTTP API

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | Liveness + available games |
| `GET /api/games` | Registered game adapters |
| `GET /api/search?game=dota2&q=<name\|id>` | Player search |
| `GET /api/players/{account_id}?game=dota2&limit=20` | Full Skill Lab profile |
| `GET /api/meta?game=dota2` | Meta Hub hero stats |

## Architecture

```
src/kda/
  core/            models.py (unified entities) · cache.py (TTL cache)
  adapters/
    base.py        GameAdapter interface
    dota2/         opendota.py (HTTP client) · normalize.py · __init__.py
  analytics/       skill_lab.py · meta_hub.py   (game-agnostic analysis)
  server/          app.py (FastAPI factory) · routes.py
  web/             index.html · style.css · app.js
  app.py           Qt shell (server thread + QWebEngineView)
```

The engine is deliberately split: **adapters** fetch and normalise game data
into the shared model, **analytics** compute insights from the model, and the
**UI** never talks to a game API directly. That keeps every future game a
matter of writing one adapter.

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Roadmap

- More games (CS2, League of Legends) via new adapters.
- Draft/lineup analysis and head-to-head comparisons.
- Local history + offline snapshots (SQLite).
- Exportable match reports.

## Disclaimer

KDA is an unofficial project. Dota 2 data comes from OpenDota and the Steam
Web API; KDA is not affiliated with or endorsed by Valve.

## License

MIT — see [LICENSE](LICENSE).
