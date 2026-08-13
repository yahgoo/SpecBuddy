"""Runtime configuration for the SpecBuddy backend."""

from __future__ import annotations

import os


DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", "specbuddy.db")


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


CORS_ORIGINS = _split_csv(
    os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
)
