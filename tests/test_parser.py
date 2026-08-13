from __future__ import annotations

import unittest

from src.linter.parser import parse_requirements


class ParserTests(unittest.TestCase):
    def test_extracts_requirement_lines_with_line_numbers(self) -> None:
        records = parse_requirements(
            "# Title\n\n"
            "Prose only.\n\n"
            "## Acceptance Criteria\n"
            "- WHEN an order is placed, THE System SHALL confirm it.\n"
        )

        self.assertEqual(1, len(records))
        self.assertEqual(6, records[0].line_number)
        self.assertIn("WHEN", records[0].uppercase_keywords)

    def test_detects_lowercase_ears_keywords(self) -> None:
        records = parse_requirements("- when an order is placed, the system shall confirm it.")

        self.assertEqual(("when", "shall"), records[0].lowercase_keywords)

    def test_tracks_current_section(self) -> None:
        records = parse_requirements(
            "## Functional Requirements\n"
            "- THE System SHALL validate input.\n"
            "\n"
            "## Goals\n"
            "- THE System SHALL be fast.\n"
        )

        self.assertEqual(2, len(records))
        self.assertEqual("functional requirements", records[0].section)
        self.assertEqual("goals", records[1].section)

    def test_detects_all_uppercase_ears_keywords(self) -> None:
        records = parse_requirements(
            "- WHILE the session is active, WHERE MFA is included, "
            "IF a timeout occurs THEN THE System SHALL reset the token.\n"
        )

        self.assertEqual(1, len(records))
        for kw in ("WHILE", "WHERE", "IF", "THEN", "SHALL"):
            self.assertIn(kw, records[0].uppercase_keywords)

    def test_skips_non_requirement_prose(self) -> None:
        records = parse_requirements(
            "# Introduction\n\n"
            "This document describes the project scope.\n"
            "It is intended for stakeholders.\n"
        )

        self.assertEqual(0, len(records))

    def test_extracts_ambiguous_non_ears_sample_lines(self) -> None:
        records = parse_requirements(
            '- "The system should be fast when processing orders."\n'
            '- "Users should easily find their order status."\n'
        )

        self.assertEqual(2, len(records))
        self.assertEqual("The system should be fast when processing orders.", records[0].statement)


if __name__ == "__main__":
    unittest.main()
