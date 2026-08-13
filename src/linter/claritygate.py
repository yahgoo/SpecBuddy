"""SpecBuddy CLI orchestration for the five-stage linter pipeline."""

from __future__ import annotations

import argparse
import sys

from .evaluator import evaluate
from .loader import LoadError, load_requirements
from .parser import parse_requirements
from .reporter import print_summary, write_report
from .rule_engine import run_checks


def run(input_path: str, out_path: str = "specbuddy-report.md") -> int:
    text = load_requirements(input_path)
    records = parse_requirements(text)
    findings = run_checks(records)
    evaluation = evaluate(records, findings)
    report = write_report(input_path, records, evaluation, out_path)
    print_summary(report, evaluation)
    return evaluation.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan requirements.md for SpecBuddy quality issues.")
    parser.add_argument("path", help="Path to a requirements.md file")
    parser.add_argument("--out", default="specbuddy-report.md", help="Markdown report output path")
    args = parser.parse_args(argv)

    try:
        return run(args.path, args.out)
    except LoadError as exc:
        print(f"SpecBuddy load error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
