from __future__ import annotations

import unittest

from src.linter.parser import parse_requirements
from src.linter.rule_engine import (
    check_adverbs,
    check_ears_keyword_casing,
    check_ears_missing_keyword,
    check_ears_pattern,
    check_ears_singularity,
    check_escape_clauses,
    check_implementation_leakage,
    check_non_mandatory_imperatives,
    check_oblique_symbols,
    check_passive_voice,
    check_pronouns,
    check_tacit_knowledge,
    check_vague_adjectives,
    check_vague_verbs,
    run_checks,
)


def record(line: str):
    return parse_requirements(f"- {line}")[0]


class RuleEngineTests(unittest.TestCase):
    def assert_flags(self, check, line: str) -> None:
        self.assertTrue(check(record(line)), line)

    def assert_clean(self, check, line: str) -> None:
        self.assertFalse(check(record(line)), line)

    def test_vague_verbs(self) -> None:
        self.assert_flags(check_vague_verbs, "THE System SHALL support order lookup.")
        self.assert_clean(check_vague_verbs, "THE System SHALL display order status within 2 seconds.")

    def test_vague_adjectives(self) -> None:
        findings = check_vague_adjectives(record("THE System SHALL be user-friendly."))
        self.assertTrue(findings)
        self.assertIn("measurable", findings[0].suggested_rewrite)
        self.assert_clean(check_vague_adjectives, "THE System SHALL respond within 2 seconds.")

    def test_non_mandatory_imperatives(self) -> None:
        self.assert_flags(check_non_mandatory_imperatives, "The system should notify users.")
        self.assert_clean(check_non_mandatory_imperatives, "THE System SHALL notify users.")

    def test_adverbs(self) -> None:
        self.assert_flags(check_adverbs, "Users should easily find order status.")
        self.assert_clean(check_adverbs, "THE System SHALL show order status within 2 seconds.")

    def test_passive_voice(self) -> None:
        self.assert_flags(check_passive_voice, "THE System SHALL ensure orders are processed.")
        self.assert_clean(check_passive_voice, "THE System SHALL process orders.")

    def test_pronouns(self) -> None:
        self.assert_flags(check_pronouns, "THE System SHALL show it.")
        self.assert_clean(check_pronouns, "WHEN a user opens an order, THE System SHALL show its status.")

    def test_oblique_symbols(self) -> None:
        self.assert_flags(check_oblique_symbols, "THE System SHALL display the symbol/sign.")
        self.assert_clean(check_oblique_symbols, "THE System SHALL display the symbol.")

    def test_escape_clauses(self) -> None:
        self.assert_flags(check_escape_clauses, "THE System SHALL notify users as appropriate.")
        self.assert_clean(check_escape_clauses, "THE System SHALL notify users within 1 minute.")

    def test_ears_keyword_casing(self) -> None:
        self.assert_flags(check_ears_keyword_casing, "when an order changes, the system shall notify users.")
        self.assert_clean(check_ears_keyword_casing, "WHEN an order changes, THE System SHALL notify users.")

    def test_missing_ears_keyword(self) -> None:
        self.assert_flags(check_ears_missing_keyword, "Users should find their order status.")
        self.assert_clean(check_ears_missing_keyword, "THE System SHALL display order status.")

    def test_ears_singularity(self) -> None:
        self.assert_flags(check_ears_singularity, "THE System SHALL notify users and SHALL log the event.")
        self.assert_clean(check_ears_singularity, "THE System SHALL notify users.")

    def test_ears_pattern(self) -> None:
        self.assert_flags(check_ears_pattern, "Users SHALL receive order status.")
        self.assert_clean(check_ears_pattern, "WHEN an order changes, THE System SHALL notify users.")

    def test_tacit_knowledge(self) -> None:
        self.assert_flags(check_tacit_knowledge, "Admins can obviously override notifications.")
        self.assert_clean(check_tacit_knowledge, "THE System SHALL allow admins to override notifications after approval.")

    def test_implementation_leakage(self) -> None:
        self.assert_flags(check_implementation_leakage, "THE System SHALL use SQL database storage.")
        self.assert_clean(check_implementation_leakage, "THE System SHALL store order status for 90 days.")

    def test_happy_path_only_detection(self) -> None:
        findings = run_checks(parse_requirements("- WHEN an order changes, THE System SHALL notify users."))
        self.assertTrue(any(f.type == "missing_unwanted_behavior" for f in findings))

    def test_happy_path_detection_skips_when_if_then_exists(self) -> None:
        findings = run_checks(
            parse_requirements(
                "- WHEN an order changes, THE System SHALL notify users.\n"
                "- IF notification delivery fails, THEN THE System SHALL retry within 1 minute."
            )
        )
        self.assertFalse(any(f.type == "missing_unwanted_behavior" for f in findings))

    def test_required_ambiguous_sample_flags_each_line(self) -> None:
        records = parse_requirements(
            '- "The system should be fast when processing orders."\n'
            '- "Users should easily find their order status."\n'
            '- "The system should notify users appropriately when something changes."\n'
            '- "Admins can obviously override notifications if needed."\n'
        )
        findings = run_checks(records)
        flagged_lines = {finding.line_number for finding in findings}

        self.assertEqual({1, 2, 3, 4}, flagged_lines)


if __name__ == "__main__":
    unittest.main()
