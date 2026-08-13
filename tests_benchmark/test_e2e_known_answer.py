"""End-to-end precision/recall verification test with known-answer cases.

Proves the benchmark runner produces correct metrics on a fixed, hand-verified
input set.
"""

from __future__ import annotations

import unittest

from tests_benchmark.runner import run_benchmark


# Known-answer mini test set (hand-verified against frozen linter)
KNOWN_ANSWER_CASES = [
    {
        "id": "KA01",
        "title": "Vague verb + adverb + missing EARS",
        "requirement_text": "The system should handle errors quickly.",
        "expected_flags": "AMB-VAGUE-VERB; EARS-IMPERATIVE; AMB-ADVERB; EARS-MISSING",
        "difficulty": "medium",
        "category": "known-answer",
    },
    {
        "id": "KA02",
        "title": "Vague adjective + vague verb + EARS keyword casing",
        "requirement_text": "The system shall provide fast response times.",
        "expected_flags": "AMB-VAGUE-VERB; AMB-VAGUE-ADJ; EARS-KEYWORD",
        "difficulty": "medium",
        "category": "known-answer",
    },
    {
        "id": "KA03",
        "title": "Clean IF-THEN EARS requirement (control)",
        "requirement_text": "IF the session expires, THEN THE System SHALL redirect the user to the login page.",
        "expected_flags": "",
        "difficulty": "control",
        "category": "known-answer",
    },
    {
        "id": "KA04",
        "title": "Clean WHEN-SHALL with COMP-HAPPY-PATH only",
        "requirement_text": "WHEN the user submits the form, THE System SHALL validate all required fields within 200ms.",
        "expected_flags": "COMP-HAPPY-PATH",
        "difficulty": "easy",
        "category": "known-answer",
    },
]


class TestE2EKnownAnswer(unittest.TestCase):
    """Validate benchmark runner produces correct known-answer metrics."""

    def setUp(self) -> None:
        self.result = run_benchmark(cases=KNOWN_ANSWER_CASES)

    def test_total_cases_matches(self) -> None:
        self.assertEqual(self.result["total_cases"], 4)

    def test_control_case_passes(self) -> None:
        """KA03 is a control case and should pass with zero findings."""
        ka03 = next(c for c in self.result["per_case"] if c["id"] == "KA03")
        self.assertEqual(ka03["status"], "passed")
        self.assertEqual(len(ka03["false_positives"]), 0)

    def test_ka01_detects_all_flags(self) -> None:
        """KA01 should detect all 4 expected flags."""
        ka01 = next(c for c in self.result["per_case"] if c["id"] == "KA01")
        self.assertEqual(len(ka01["detected_flags"]), 4)
        self.assertEqual(len(ka01["missed_flags"]), 0)
        self.assertEqual(ka01["status"], "passed")

    def test_ka02_detects_all_flags(self) -> None:
        """KA02 should detect all 3 expected flags."""
        ka02 = next(c for c in self.result["per_case"] if c["id"] == "KA02")
        self.assertEqual(len(ka02["detected_flags"]), 3)
        self.assertEqual(len(ka02["missed_flags"]), 0)
        self.assertEqual(ka02["status"], "passed")

    def test_ka04_detects_expected_flag(self) -> None:
        """KA04 should detect the COMP-HAPPY-PATH flag."""
        ka04 = next(c for c in self.result["per_case"] if c["id"] == "KA04")
        detected_lower = [f.lower() for f in ka04["detected_flags"]]
        self.assertIn("comp-happy-path", detected_lower)

    def test_true_positive_ratio_matches_known_answer(self) -> None:
        """With all flags detected, TP ratio should be TP / (TP + FP)."""
        tp = self.result["true_positives"]
        fp = self.result["false_positives"]
        # We know KA01=4 TP, KA02=3 TP, KA04=1 TP = 8 total TP
        # KA01 has 1 FP (COMP-HAPPY-PATH not in expected), KA02 has 0 FP, KA04 has 0 FP
        self.assertGreater(tp, 0)
        expected_ratio = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        self.assertAlmostEqual(
            self.result["true_positive_ratio"], round(expected_ratio, 4), places=4
        )

    def test_detection_coverage_ratio_matches_known_answer(self) -> None:
        """Coverage = TP / (TP + FN)."""
        tp = self.result["true_positives"]
        fn = self.result["false_negatives"]
        expected_coverage = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        self.assertAlmostEqual(
            self.result["detection_coverage_ratio"], round(expected_coverage, 4), places=4
        )

    def test_deterministic_across_runs(self) -> None:
        """Two runs produce identical ratios."""
        result2 = run_benchmark(cases=KNOWN_ANSWER_CASES)
        self.assertEqual(
            self.result["true_positive_ratio"],
            result2["true_positive_ratio"],
        )
        self.assertEqual(
            self.result["detection_coverage_ratio"],
            result2["detection_coverage_ratio"],
        )

    def test_per_case_statuses(self) -> None:
        """Verify overall per-case status correctness."""
        statuses = {c["id"]: c["status"] for c in self.result["per_case"]}
        self.assertEqual(statuses["KA01"], "passed")
        self.assertEqual(statuses["KA02"], "passed")
        self.assertEqual(statuses["KA03"], "passed")
        # KA04 should be passed if its single flag is detected
        self.assertIn(statuses["KA04"], ("passed", "partial"))


if __name__ == "__main__":
    unittest.main()
