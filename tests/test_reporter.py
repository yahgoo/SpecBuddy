from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src.linter.evaluator import evaluate
from src.linter.models import Finding, RequirementRecord
from src.linter.reporter import print_summary, write_report


class ReporterTests(unittest.TestCase):
    def test_writes_markdown_report(self) -> None:
        records = [_record()]
        evaluation = evaluate(records, [_finding()])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.md"

            report = write_report("requirements.md", records, evaluation, out)

            self.assertTrue(out.exists())
            self.assertIn("SpecBuddy Quality Report", report.markdown)
            self.assertIn("AMB-VAGUE-ADJ", out.read_text(encoding="utf-8"))

    def test_prints_summary_to_stdout(self) -> None:
        records = [_record()]
        evaluation = evaluate(records, [])
        with tempfile.TemporaryDirectory() as tmp:
            report = write_report("requirements.md", records, evaluation, Path(tmp) / "report.md")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                print_summary(report, evaluation)

            self.assertIn("SpecBuddy scan complete", stdout.getvalue())

    def test_progress_indicator_only_for_more_than_twenty_requirements(self) -> None:
        records = [_record(line) for line in range(1, 22)]
        evaluation = evaluate(records, [])
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(stderr):
            write_report("requirements.md", records, evaluation, Path(tmp) / "report.md")

        self.assertIn("Scanning 21 requirement lines", stderr.getvalue())


def _record(line: int = 1) -> RequirementRecord:
    return RequirementRecord(line, "", "THE System SHALL display order status.")


def _finding() -> Finding:
    return Finding(
        line_number=1,
        type="unverifiable_adjective",
        severity="defect",
        message="message",
        suggested_rewrite="suggestion",
        check_id="AMB-VAGUE-ADJ",
        category="lexical",
    )


if __name__ == "__main__":
    unittest.main()
