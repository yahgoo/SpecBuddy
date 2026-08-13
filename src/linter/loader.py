"""Loader stage: read a requirements file as UTF-8 text."""

from __future__ import annotations

from pathlib import Path


class LoadError(Exception):
    """Raised when SpecBuddy cannot load a requirements file."""


def load_requirements(path: str | Path) -> str:
    """Read a requirements file, rejecting missing and non-UTF-8 inputs clearly."""

    source = Path(path)
    if not source.exists():
        raise LoadError(f"Input file not found: {source}")
    if not source.is_file():
        raise LoadError(f"Input path is not a file: {source}")

    try:
        return source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise LoadError(f"Input file must be UTF-8 text: {source}") from exc
    except OSError as exc:
        raise LoadError(f"Unable to read input file {source}: {exc}") from exc
