from __future__ import annotations

import unittest

from src.linter.evaluator import evaluate
from src.linter.models import Finding, RequirementRecord


class EvaluatorTests(unittest.TestCase):
    def test_certifies_clean_findings(self) -> None:
        result = evaluate([_record()], [])

        self.assertEqual("CERTIFIED", result.verdict)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(100, result.score)
        self.assertEqual("Agent Ready", result.tier)

    def test_refuses_on_lowercase_ears(self) -> None:
        result = evaluate([_record()], [_finding("lowercase_ears_keyword", "defect")])

        self.assertEqual("REFUSED", result.verdict)
        self.assertEqual(2, result.exit_code)

    def test_scores_defects_and_clarifications(self) -> None:
        result = evaluate(
            [_record()],
            [
                _finding("vague_verb", "defect"),
                _finding("tacit_knowledge", "clarification"),
            ],
        )

        self.assertEqual(88, result.score)
        self.assertEqual(1, result.defects)
        self.assertEqual(1, result.clarifications)


def _record() -> RequirementRecord:
    return RequirementRecord(1, "", "THE System SHALL display order status.")


def _finding(type_: str, severity: str) -> Finding:
    return Finding(
        line_number=1,
        type=type_,
        severity=severity,
        message="message",
        suggested_rewrite="suggestion",
        check_id="TEST",
        category="test",
    )


if __name__ == "__main__":
    unittest.main()
