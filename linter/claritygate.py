"""Forward `python -m linter.claritygate` to the src-layout implementation."""

from src.linter.claritygate import main, run


if __name__ == "__main__":
    raise SystemExit(main())

