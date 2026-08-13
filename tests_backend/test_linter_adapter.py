"""Tests for backend.linter_adapter (Phase 1B).

Every test uses a temporary SQLite database.
Tests never create, read, or modify the development specbuddy.db.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.database import connect, init_db
from backend.linter_adapter import (
    analyze_spec,
    apply_rewrite,
    get_analysis,
    remove_rewrite,
    reset_rewrites,
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
AMBIGUOUS_PATH = SAMPLES_DIR / "ambiguous-requirements.md"
CLEAN_PATH = SAMPLES_DIR / "clean-ears-requirements.md"


class AdapterTestBase(unittest.TestCase):
    """Base providing a temporary database."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test.db")
        init_db(self.db_path)
        self.conn = connect(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self._tmpdir.cleanup()


class AnalyzeAmbiguousTests(AdapterTestBase):
    """Verify analysis of the ambiguous sample."""

    def test_ambiguous_returns_23_findings_score_0_refused(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)

        self.assertEqual(result["requirement_count"], 6)
        self.assertEqual(len(result["findings"]), 23)
        self.assertEqual(result["defects"], 21)
        self.assertEqual(result["clarifications"], 2)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["verdict"], "REFUSED")
        self.assertEqual(result["exit_code"], 2)

    def test_ambiguous_stores_requirements_and_findings(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]

        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM requirements WHERE spec_id = ?", (spec_id,)
        )
        self.assertEqual(cur.fetchone()["cnt"], 6)

        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM findings WHERE spec_id = ?", (spec_id,)
        )
        self.assertEqual(cur.fetchone()["cnt"], 23)

    def test_score_tier_verdict_not_stored_in_db(self) -> None:
        """No score/tier/verdict columns exist in any table."""
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)

        for table in ("specs", "requirements", "findings", "rewrites"):
            cur = self.conn.execute(f"PRAGMA table_info({table})")
            columns = {row["name"] for row in cur.fetchall()}
            self.assertNotIn("score", columns, f"score found in {table}")
            self.assertNotIn("tier", columns, f"tier found in {table}")
            self.assertNotIn("verdict", columns, f"verdict found in {table}")


class AnalyzeCleanTests(AdapterTestBase):
    """Verify analysis of the clean sample."""

    def test_clean_returns_0_findings_score_100_certified(self) -> None:
        raw_text = CLEAN_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "clean-ears-requirements.md", raw_text)

        self.assertEqual(result["requirement_count"], 3)
        self.assertEqual(len(result["findings"]), 0)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["verdict"], "CERTIFIED")
        self.assertEqual(result["exit_code"], 0)


class RewriteTests(AdapterTestBase):
    """Verify rewrite overlay behavior."""

    def test_rewrite_changes_only_targeted_line(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]

        # Pick the first requirement line
        first_req = result["requirements"][0]
        line_num = first_req["line_number"]
        original_line = raw_text.split("\n")[line_num - 1]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        result2 = apply_rewrite(self.conn, spec_id, line_num, new_text)

        # Effective markdown should have the new line
        effective_lines = result2["effective_markdown"].split("\n")
        self.assertEqual(effective_lines[line_num - 1], new_text)

        # Other lines unchanged
        raw_lines = raw_text.split("\n")
        for i, line in enumerate(raw_lines):
            if i != line_num - 1:
                self.assertEqual(effective_lines[i], line)

    def test_rewrite_transaction_rollback_on_failure(self) -> None:
        """If analysis fails mid-transaction, no partial mutation persists."""
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]
        first_req = result["requirements"][0]
        line_num = first_req["line_number"]

        # Count rewrites before
        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM rewrites WHERE spec_id = ?", (spec_id,)
        )
        before_count = cur.fetchone()["cnt"]

        # Attempt a rewrite on a non-requirement line should raise ValueError
        # and leave no partial state
        with self.assertRaises(ValueError):
            apply_rewrite(self.conn, spec_id, 9999, "bad rewrite")

        # Rewrites unchanged
        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM rewrites WHERE spec_id = ?", (spec_id,)
        )
        self.assertEqual(cur.fetchone()["cnt"], before_count)

    def test_remove_rewrite_restores_original(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]
        first_req = result["requirements"][0]
        line_num = first_req["line_number"]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        apply_rewrite(self.conn, spec_id, line_num, new_text)

        # Remove the rewrite
        result3 = remove_rewrite(self.conn, spec_id, line_num)
        self.assertEqual(result3["effective_markdown"], raw_text)
        self.assertEqual(len(result3["rewrites"]), 0)

    def test_reset_rewrites_restores_original(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]
        first_req = result["requirements"][0]
        line_num = first_req["line_number"]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        apply_rewrite(self.conn, spec_id, line_num, new_text)

        result3 = reset_rewrites(self.conn, spec_id)
        self.assertEqual(result3["effective_markdown"], raw_text)
        self.assertEqual(len(result3["rewrites"]), 0)
        self.assertEqual(len(result3["findings"]), 23)


class GetAnalysisTests(AdapterTestBase):
    """Verify get_analysis returns current state."""

    def test_get_analysis_returns_none_for_missing_spec(self) -> None:
        result = get_analysis(self.conn, 9999)
        self.assertIsNone(result)

    def test_get_analysis_reflects_rewrites(self) -> None:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        result = analyze_spec(self.conn, "ambiguous-requirements.md", raw_text)
        spec_id = result["spec_id"]
        first_req = result["requirements"][0]
        line_num = first_req["line_number"]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        apply_rewrite(self.conn, spec_id, line_num, new_text)

        # get_analysis should reflect the rewrite
        analysis = get_analysis(self.conn, spec_id)
        self.assertIsNotNone(analysis)
        self.assertEqual(len(analysis["rewrites"]), 1)
        effective_lines = analysis["effective_markdown"].split("\n")
        self.assertEqual(effective_lines[line_num - 1], new_text)


if __name__ == "__main__":
    unittest.main()
