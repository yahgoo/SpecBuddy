"""Allow `python -m src.linter` for local development."""

from .claritygate import main

raise SystemExit(main())

