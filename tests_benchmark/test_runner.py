"""Unit tests for tests_benchmark.runner.

Follows the pattern in tests_backend/test_linter_adapter.py.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from tests_benchmark.runner import run_benchmark, _load_cases, _validate_case

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
_DISTILLATION_PATH = _DATA_DIR / "distillation-test-cases.json"
_ADVERSARIAL_PATH = _DATA_DIR / "adversarial-sg-sme-cases.json"


class TestLoadDistillationCases(unittest.TestCase):
    """Test loading existing distillation cases produces expected structured output."""

    def test_distillation_cases_load_successfully(self) -> None:
        result = run_benchmark(distillation_path=_DISTILLATION_PATH, adversarial_path=Path("/nonexistent.json"))
        self.assertGreater(result["total_cases"], 0)
        self.assertIn("per_case", result)
        self.assertIn("true_positive_ratio", result)
        self.assertIn("detection_coverage_ratio", result)
        for case in result["per_case"]:
            self.assertIn("id", case)
            self.assertIn("status", case)
            self.assertIn(case["status"], ("passed", "partial", "failed", "errored"))


class TestLoadAdversarialCases(unittest.TestCase):
    """Test loading adversarial cases succeeds (non-zero case count, UTF-8 chars)."""

    def test_adversarial_cases_load_with_utf8(self) -> None:
        result = run_benchmark(distillation_path=Path("/nonexistent.json"), adversarial_path=_ADVERSARIAL_PATH)
        self.assertGreater(result["total_cases"], 0)
        # Verify UTF-8 content survived: at least one case title or requirement has non-ASCII
        has_non_ascii = False
        for case in result["per_case"]:
            if any(ord(c) > 127 for c in case.get("title", "")):
                has_non_ascii = True
                break
        self.assertTrue(has_non_ascii, "Expected at least one case with non-ASCII chars")


class TestControlCase(unittest.TestCase):
    """Test a known control case passes (zero findings → passed)."""

    def test_control_case_passes_with_no_findings(self) -> None:
        control_case = {
            "id": "CTRL01",
            "title": "Clean EARS requirement with nominal and unwanted behavior",
            "requirement_text": (
                "WHEN the user submits the form, THE System SHALL save the record within 2 seconds.\n"
                "IF the save operation fails, THEN THE System SHALL return error code 500 to the user within 1 second."
            ),
            "expected_flags": "none expected",
            "difficulty": "control",
            "category": "test",
        }
        result = run_benchmark(cases=[control_case])
        self.assertEqual(result["total_cases"], 1)
        case_result = result["per_case"][0]
        self.assertEqual(case_result["status"], "passed", f"Control case failed with FPs: {case_result.get('false_positives')}")
        self.assertEqual(case_result["false_positives"], [])


class TestExceptionIsolation(unittest.TestCase):
    """Test exception isolation: a crashing case is marked errored, remaining cases unaffected."""

    def test_errored_case_does_not_affect_others(self) -> None:
        good_case = {
            "id": "GOOD01",
            "title": "Normal case",
            "requirement_text": "The system should handle errors quickly.",
            "expected_flags": "vague adverb",
            "difficulty": "easy",
            "category": "test",
        }
        # Patch parse_requirements to raise on specific text
        original_parse = None

        def patched_parse(text):
            if "CRASH_TRIGGER" in text:
                raise RuntimeError("Simulated crash")
            from src.linter.parser import parse_requirements as _orig
            return _orig(text)

        crash_case = {
            "id": "CRASH01",
            "title": "Crashing case",
            "requirement_text": "CRASH_TRIGGER this will fail.",
            "expected_flags": "something",
            "difficulty": "medium",
            "category": "test",
        }

        with patch("tests_benchmark.runner.parse_requirements", side_effect=patched_parse):
            result = run_benchmark(cases=[crash_case, good_case])

        self.assertEqual(result["total_cases"], 2)
        crash_result = result["per_case"][0]
        good_result = result["per_case"][1]
        self.assertEqual(crash_result["status"], "errored")
        self.assertIsNotNone(crash_result["error"])
        # Good case still processed normally
        self.assertIn(good_result["status"], ("passed", "partial", "failed"))
        self.assertIsNone(good_result["error"])


class TestEmptyFile(unittest.TestCase):
    """Test empty file produces zero totals + warning."""

    def test_empty_cases_returns_zero_totals(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = run_benchmark(cases=[])

        self.assertEqual(result["total_cases"], 0)
        self.assertEqual(result["true_positives"], 0)
        self.assertEqual(result["false_positives"], 0)
        self.assertEqual(result["false_negatives"], 0)
        self.assertEqual(result["true_positive_ratio"], 0.0)
        self.assertEqual(result["detection_coverage_ratio"], 0.0)
        self.assertTrue(len(result["warnings"]) > 0)

    def test_nonexistent_file_returns_zero_totals(self) -> None:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = run_benchmark(
                distillation_path=Path("/nonexistent1.json"),
                adversarial_path=Path("/nonexistent2.json"),
            )
        self.assertEqual(result["total_cases"], 0)


class TestMalformedEntry(unittest.TestCase):
    """Test malformed entry skipped with warning, other cases processed."""

    def test_malformed_entry_skipped(self) -> None:
        malformed = {"id": "MAL01", "title": "Missing fields"}  # no requirement_text or expected_flags
        good_case = {
            "id": "GOOD02",
            "title": "Valid case",
            "requirement_text": "The system should handle errors properly.",
            "expected_flags": "vague adverb",
            "difficulty": "easy",
            "category": "test",
        }

        result = run_benchmark(cases=[malformed, good_case])
        self.assertEqual(result["total_cases"], 1)  # only good case processed
        self.assertTrue(any("MAL01" in w for w in result["warnings"]))


class TestDeterministic(unittest.TestCase):
    """Test deterministic: two consecutive runs produce identical ratios."""

    def test_two_runs_same_ratios(self) -> None:
        result1 = run_benchmark()
        result2 = run_benchmark()
        self.assertEqual(result1["true_positive_ratio"], result2["true_positive_ratio"])
        self.assertEqual(result1["detection_coverage_ratio"], result2["detection_coverage_ratio"])
        self.assertEqual(result1["total_cases"], result2["total_cases"])


class TestPerformance(unittest.TestCase):
    """Test total execution under 10 seconds."""

    def test_benchmark_completes_within_10_seconds(self) -> None:
        start = time.time()
        run_benchmark()
        elapsed = time.time() - start
        self.assertLess(elapsed, 10.0, f"Benchmark took {elapsed:.2f}s, exceeds 10s limit")


if __name__ == "__main__":
    unittest.main()
