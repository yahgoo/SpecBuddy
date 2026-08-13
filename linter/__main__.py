"""Allow `python -m linter` to run the SpecBuddy CLI compatibility entrypoint."""

from .claritygate import main

raise SystemExit(main())
