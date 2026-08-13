"""Tests for benchmark and evidence API routes."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import create_app

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
AMBIGUOUS_PATH = SAMPLES_DIR / "ambiguous-requirements.md"
CLEAN_PATH = SAMPLES_DIR / "clean-ears-requirements.md"


class BenchmarkTestBase(unittest.TestCase):
    """Base providing a TestClient with a temporary database."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test.db")
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self._tmpdir.cleanup()

    def _create_ambiguous_spec(self) -> dict:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        resp = self.client.post(
            "/api/specs",
            json={"filename": "ambiguous-requirements.md", "raw_text": raw_text},
        )
        self.assertEqual(resp.status_code, 201)
        return resp.json()

    def _create_clean_spec(self) -> dict:
        raw_text = CLEAN_PATH.read_text(encoding="utf-8")
        resp = self.client.post(
            "/api/specs",
            json={"filename": "clean-ears-requirements.md", "raw_text": raw_text},
        )
        self.assertEqual(resp.status_code, 201)
        return resp.json()


class BenchmarkRunTests(BenchmarkTestBase):
    """POST /api/benchmark/run"""

    def test_run_returns_structured_result(self) -> None:
        resp = self.client.post("/api/benchmark/run")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_cases", data)
        self.assertIn("true_positives", data)
        self.assertIn("false_positives", data)
        self.assertIn("false_negatives", data)
        self.assertIn("true_positive_ratio", data)
        self.assertIn("detection_coverage_ratio", data)
        self.assertIn("per_case", data)
        self.assertGreater(data["total_cases"], 0)
        self.assertIsInstance(data["true_positive_ratio"], float)
        self.assertIsInstance(data["detection_coverage_ratio"], float)


class BenchmarkResultsTests(BenchmarkTestBase):
    """GET /api/benchmark/results"""

    def test_results_returns_latest_run(self) -> None:
        # Run a benchmark first
        run_resp = self.client.post("/api/benchmark/run")
        self.assertEqual(run_resp.status_code, 200)

        # Fetch results
        resp = self.client.get("/api/benchmark/results")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIsNotNone(data["result"])
        result = data["result"]
        self.assertIn("total_cases", result)
        self.assertIn("true_positive_ratio", result)
        self.assertIn("detection_coverage_ratio", result)
        self.assertGreater(result["total_cases"], 0)

    def test_results_returns_none_when_no_runs(self) -> None:
        resp = self.client.get("/api/benchmark/results")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("result", data)
        self.assertIsNone(data["result"])


class EvidenceTests(BenchmarkTestBase):
    """GET /api/specs/{spec_id}/evidence"""

    def test_evidence_returns_scores_after_analysis(self) -> None:
        spec = self._create_ambiguous_spec()
        spec_id = spec["spec_id"]

        resp = self.client.get(f"/api/specs/{spec_id}/evidence")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["spec_id"], spec_id)
        self.assertIn("initial_score", data)
        self.assertIn("current_score", data)
        self.assertEqual(data["initial_score"], data["current_score"])
        self.assertIn("findings_resolved", data)
        self.assertEqual(data["findings_resolved"], 0)
        self.assertIn("questions_answered", data)
        self.assertEqual(data["questions_answered"], 0)
        self.assertIn("benchmark_available", data)

    def test_evidence_shows_improvement_after_rewrite(self) -> None:
        spec = self._create_ambiguous_spec()
        spec_id = spec["spec_id"]

        # Get initial evidence
        resp = self.client.get(f"/api/specs/{spec_id}/evidence")
        initial_data = resp.json()
        initial_score = initial_data["initial_score"]

        # Apply a rewrite to a finding line
        findings = spec["findings"]
        self.assertGreater(len(findings), 0)
        target_finding = findings[0]
        rewrite_text = target_finding["suggested_rewrite"] or "WHEN triggered, THE System SHALL perform action."

        rewrite_resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={
                "line_number": target_finding["line_number"],
                "rewritten_text": rewrite_text,
            },
        )
        self.assertEqual(rewrite_resp.status_code, 200)

        # Check evidence after rewrite
        resp = self.client.get(f"/api/specs/{spec_id}/evidence")
        after_data = resp.json()
        self.assertEqual(after_data["initial_score"], initial_score)
        # Current score should be >= initial since we applied a fix
        self.assertGreaterEqual(after_data["current_score"], initial_score)

    def test_evidence_includes_benchmark_metrics_after_run(self) -> None:
        spec = self._create_ambiguous_spec()
        spec_id = spec["spec_id"]

        # Run benchmark first
        self.client.post("/api/benchmark/run")

        resp = self.client.get(f"/api/specs/{spec_id}/evidence")
        data = resp.json()
        self.assertTrue(data["benchmark_available"])
        self.assertIsNotNone(data["true_positive_ratio_pct"])
        self.assertIsNotNone(data["detection_coverage_ratio_pct"])
        self.assertIsInstance(data["true_positive_ratio_pct"], float)
        self.assertIsInstance(data["detection_coverage_ratio_pct"], float)

    def test_evidence_returns_404_for_nonexistent_spec(self) -> None:
        resp = self.client.get("/api/specs/9999/evidence")
        self.assertEqual(resp.status_code, 404)

    def test_evidence_returns_null_benchmark_fields_when_no_run(self) -> None:
        spec = self._create_ambiguous_spec()
        spec_id = spec["spec_id"]

        resp = self.client.get(f"/api/specs/{spec_id}/evidence")
        data = resp.json()
        self.assertFalse(data["benchmark_available"])
        self.assertIsNone(data["true_positive_ratio_pct"])
        self.assertIsNone(data["detection_coverage_ratio_pct"])


if __name__ == "__main__":
    unittest.main()
