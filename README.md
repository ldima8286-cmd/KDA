# KDA — esports intelligence

A native desktop analytics workstation for competitive games, starting with
**Dota 2** (public [OpenDota](https://docs.opendota.com/) API — no key required).

One dark, data-dense interface: a Qt shell over a small Python engine. No web
server, no browser, no accounts — the app talks to the API directly and pulls
fresh data on every launch when you are online.

## Highlights

- **Skill Lab** — search any player by nickname or Steam `account_id` and get a
  full dossier: rank medal, win rate, KDA, GPM/XPM, a rolling win-rate trend
  chart, the latest matches, **career totals** (games, winrate, averages) and
  **popular heroes** across the whole account history.
- **Match viewer** — click any recent game to open the full picture: ten-player
  scoreboard (net worth, hero damage, items), the draft (picks/bans) and, for
  parsed matches, an event timeline of the whole game (first blood, towers,
  Roshan, aegis, courier kills).
- **Meta Hub** — current hero meta with pro and pub pick/win rates; sortable
  columns and a Pro / public-rankings toggle.
- **Hero screen** — click any hero for matchup spread, win rate by game length,
  popular items per phase, **skill build by lane + role** (core/support) with
  sample counts and small-sample warnings, and **talents** (10/15/20/25).
- **Universal Engine** — a game-agnostic core (`Player` / `Match` / `HeroMeta`
  models + `GameAdapter` interface). Dota 2 is the first adapter; more games
  plug in without touching the UI.
- **Fresh on launch, polite offline** — a short TTL cache keeps navigation
  instant; every launch starts cold and pulls current data, and the refresh
  button forces a re-pull. Networking runs off the UI thread, so the window
  never freezes.

## Counter-Strike 2

CS2 is the second adapter, exercising the Universal Engine end-to-end. The app
switches games from the header combo; the Meta Hub and Pro Scene both adapt
their labels and content (maps instead of heroes, teams instead of Dota
leagues).

- **Meta Hub** — the active-duty map pool as a sortable table (plays / win
  rate / type), served from a clearly-labelled bundled reference snapshot.
- **Pro Scene** — a top-teams and pro-players reference snapshot. CS2 exposes
  no public match feed, so the match list is intentionally empty offline.
- **Live player profiles** — set a free Steam Web API key to resolve and show
  real Steam profiles: export `KDA_STEAM_KEY` before launching. Without a key
  the adapter runs fully offline (maps, Premier rank bands, weapons).

> CS2 has no open, keyless match-history or pick/win API. Live pro-scene data
> requires a commercial provider; the adapter is written so one can be plugged
> in later without touching the UI.

## Screens

The UI is a dark esports aesthetic (Dota 2 client + HLTV analytics tables).
The win-rate trend chart is hand-drawn with QPainter — no charting dependency.

## Quick start

### Download (one click)

Prebuilt binaries for Linux and Windows are attached to every
[GitHub Release](https://github.com/ldima8286-cmd/KDA/releases). No Python
toolchain required:

- **Linux** — `KDA-linux-x86_64.tar.gz`: extract, then run `./KDA`
  (`chmod +x KDA` if your file manager dropped the executable bit).
- **Windows** — `KDA-windows-x86_64.zip`: extract, then double-click `KDA.exe`.

### Run from source

Requirements: Python 3.11+ (3.13 recommended).

```bash
git clone https://github.com/ldima8286-cmd/KDA.git
cd KDA
./run.sh          # Linux/macOS
run.bat           # Windows
```

`run.sh` / `run.bat` create a virtual environment, install dependencies and
launch the app.

### Manual

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m kda
```

### Build the binary yourself

```bash
./scripts/build-linux.sh      # -> dist/KDA
scripts\build-windows.bat     # -> dist\KDA.exe
```

Both scripts create/refresh `.venv`, install `requirements-build.txt` and run
PyInstaller with `packaging/kda.spec`, producing a single self-contained
executable (`onefile`). CI does the same on every `v*` tag and attaches the
binaries to the release.

> **Linux note:** hero thumbnails and avatars load through `QtNetwork`, which
> links against Kerberos on some distros. If icons do not appear, install your
> runtime (`krb5-libs` / `libgssapi-krb5-2`). The app still runs without it,
> just without images.

## Architecture

```
main.py            launcher entry point (run scripts + PyInstaller)
packaging/kda.spec PyInstaller spec (onefile, Linux + Windows)
scripts/           build-linux.sh · build-windows.bat
.github/workflows/ ci.yml (tests) · release.yml (binaries on v* tags)
src/kda/
  core/            models.py (unified entities) · cache.py (TTL cache)
  adapters/
    base.py        GameAdapter interface
    dota2/         opendota.py (sync HTTP client) · normalize.py
  analytics/       skill_lab.py · meta_hub.py   (game-agnostic analysis)
  format.py        display formatters (no Qt, unit-tested)
  services.py      KdaService — facade the UI talks to
  ui/
    theme.py       dark palette as a Qt stylesheet
    workers.py     run blocking calls off the UI thread
    images.py      async thumbnail loader with pixmap cache
    widgets.py     panels, stat cards, tables, trend chart
    panels/        home.py · skill_lab.py · match.py · meta_hub.py
    main_window.py nav rail + player search + panel stack
  app.py           QApplication bootstrap
```

Adapters fetch and normalise game data into the shared model, analytics compute
insights from the model, and the UI never talks to a game API directly. Adding
a title means writing one adapter.

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Covers the normalisation pipeline, analytics aggregates, formatters, the
sync OpenDota client (offline via `httpx.MockTransport`) and the service
facade.

## Roadmap

- More games (League of Legends, Valorant) via new adapters — CS2 ships.
- Draft/lineup analysis and head-to-head comparisons.
- Local history + offline snapshots (SQLite).
- Exportable match reports.

## Disclaimer

KDA is an unofficial project. Dota 2 data comes from OpenDota and the Steam
Web API; KDA is not affiliated with or endorsed by Valve.

## License

MIT — see [LICENSE](LICENSE).
