"""FastAPI application factory for SpecBuddy backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS, DEFAULT_DB_PATH
from backend.database import init_db
from backend.routes import router


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize the database schema on application startup."""
    init_db(app.state.db_path)
    yield


def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    """Create and return a configured FastAPI application instance.

    The database path is injectable for testing.  The schema is initialized
    during the application lifespan (startup).  No server is started by this
    function.
    """
    app = FastAPI(
        title="SpecBuddy",
        version="0.2.0",
        lifespan=_lifespan,
    )
    app.state.db_path = db_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app
