from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class IntegrationCliTests(unittest.TestCase):
    def test_full_pipeline_generates_report_for_ambiguous_sample(self) -> None:
        sample = "\n".join(
            [
                '- "The system should be fast when processing orders."',
                '- "Users should easily find their order status."',
                '- "The system should notify users appropriately when something changes."',
                '- "Admins can obviously override notifications if needed."',
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirements.md"
            report = Path(tmp) / "report.md"
            source.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-m", "linter.claritygate", str(source), "--out", str(report)],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, result.returncode)
            markdown = report.read_text(encoding="utf-8")
            self.assertIn("AMB-VAGUE-ADJ", markdown)
            self.assertIn("AMB-ESCAPE", markdown)
            self.assertIn("TACIT-UNREC", markdown)

    def test_lowercase_ears_rejection_lists_required_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirements.md"
            report = Path(tmp) / "report.md"
            source.write_text("- when an order changes, the system shall notify users.", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-m", "linter.claritygate", str(source), "--out", str(report)],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, result.returncode)
            self.assertIn("WHEN, WHILE, WHERE, IF, THEN, SHALL", report.read_text(encoding="utf-8"))

    def test_oblique_symbol_acceptance_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "requirements.md"
            report = Path(tmp) / "report.md"
            source.write_text("- THE System SHALL display symbol/sign status.", encoding="utf-8")

            subprocess.run(
                [sys.executable, "-m", "linter.claritygate", str(source), "--out", str(report)],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertIn("AMB-OBLIQUE", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
