"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI

from runback_server.api import flows, hooks, replay, runners, runs


def create_app() -> FastAPI:
    app = FastAPI(title="Runback", version="0.0.0")
    app.include_router(hooks.router, prefix="/api/hooks", tags=["hooks"])
    app.include_router(flows.router, prefix="/api/flows", tags=["flows"])
    app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
    app.include_router(replay.router, prefix="/api", tags=["replay"])
    app.include_router(runners.router, prefix="/api/runners", tags=["runners"])
    return app


app = create_app()
