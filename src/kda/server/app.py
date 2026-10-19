"""FastAPI application factory.

The app powers the local API and serves the bundled web UI, which the Qt shell
embeds via QWebEngineView.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import routes

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await routes.close_adapters()


def create_app() -> FastAPI:
    app = FastAPI(title="KDA", version="0.1.0", lifespan=lifespan)
    app.include_router(routes.router)

    if WEB_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(str(WEB_DIR / "index.html"))

    return app


app = create_app()
