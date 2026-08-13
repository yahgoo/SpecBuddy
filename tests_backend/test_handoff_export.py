"""Tests for the handoff export endpoint (Task 4 + Task 9 e2e).

Covers happy path, rewrites, unresolved findings, all resolved,
zero requirements, missing spec 404, refused verdict, metadata fields,
response latency, and end-to-end section verification.
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import create_app

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
AMBIGUOUS_PATH = SAMPLES_DIR / "ambiguous-requirements.md"
CLEAN_PATH = SAMPLES_DIR / "clean-ears-requirements.md"


class HandoffExportTestBase(unittest.TestCase):
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

    def _create_spec(self, filename: str, raw_text: str) -> dict:
        resp = self.client.post(
            "/api/specs",
            json={"filename": filename, "raw_text": raw_text},
        )
        self.assertEqual(resp.status_code, 201)
        return resp.json()

    def _create_ambiguous_spec(self) -> dict:
        raw_text = AMBIGUOUS_PATH.read_text(encoding="utf-8")
        return self._create_spec("ambiguous-requirements.md", raw_text)

    def _create_clean_spec(self) -> dict:
        raw_text = CLEAN_PATH.read_text(encoding="utf-8")
        return self._create_spec("clean-ears-requirements.md", raw_text)

    def _export(self, spec_id: int) -> "tuple[int, dict]":
        resp = self.client.post(
            f"/api/specs/{spec_id}/handoff-export",
            json={},
        )
        return resp.status_code, resp.json()


class HandoffExportHappyPathTests(HandoffExportTestBase):
    """Happy path: create spec, export, verify sections and metadata."""

    def test_export_clean_spec_returns_200_with_all_sections(self) -> None:
        created = self._create_clean_spec()
        spec_id = created["spec_id"]

        status, data = self._export(spec_id)
        self.assertEqual(status, 200)

        md = data["markdown_document"]

        # All four required sections present
        self.assertIn("## Certified Spec", md)
        self.assertIn("## Acceptance Criteria", md)
        self.assertIn("## Unresolved Questions", md)
        self.assertIn("## Implementation Tasks", md)

    def test_export_metadata_fields(self) -> None:
        created = self._create_clean_spec()
        spec_id = created["spec_id"]

        status, data = self._export(spec_id)
        self.assertEqual(status, 200)

        # Required response fields
        self.assertEqual(data["spec_id"], spec_id)
        self.assertEqual(data["filename"], "clean-ears-requirements.md")
        self.assertIsInstance(data["score"], int)
        self.assertIn(data["verdict"], ("CERTIFIED", "REFUSED"))
        self.assertIsInstance(data["exported_at"], str)
        self.assertTrue(len(data["exported_at"]) > 0)
        self.assertIsInstance(data["markdown_document"], str)

    def test_export_metadata_in_markdown_header(self) -> None:
        created = self._create_clean_spec()
        spec_id = created["spec_id"]

        _, data = self._export(spec_id)
        md = data["markdown_document"]

        # Metadata header fields
        self.assertIn("clean-ears-requirements.md", md)
        self.assertIn("Score", md)
        self.assertIn("Verdict", md)


class HandoffExportWithRewritesTests(HandoffExportTestBase):
    """Export reflects applied rewrites in the certified spec."""

    def test_certified_spec_reflects_rewrite(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        # Apply a rewrite to the first requirement line
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]
        new_text = "- WHEN a user logs in, THE System SHALL authenticate within 2 seconds."

        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": new_text},
        )
        self.assertEqual(resp.status_code, 200)

        _, data = self._export(spec_id)
        md = data["markdown_document"]

        # The rewritten text should appear in the certified spec section
        self.assertIn(new_text, md)


class HandoffExportUnresolvedTests(HandoffExportTestBase):
    """Unresolved questions section lists findings."""

    def test_unresolved_findings_listed(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        _, data = self._export(spec_id)
        md = data["markdown_document"]

        # Ambiguous spec has findings — unresolved section should list them
        self.assertIn("## Unresolved Questions", md)
        # Should contain line references and check IDs
        self.assertIn("Line", md.split("## Unresolved Questions")[1])

    def test_all_resolved_shows_no_open_questions(self) -> None:
        created = self._create_clean_spec()
        spec_id = created["spec_id"]

        _, data = self._export(spec_id)
        md = data["markdown_document"]

        # Clean spec has no findings — should show "no open questions"
        unresolved_section = md.split("## Unresolved Questions")[1].split("##")[0]
        self.assertIn("no open questions", unresolved_section.lower())


class HandoffExportZeroRequirementsTests(HandoffExportTestBase):
    """Zero-requirement specs produce a valid document."""

    def test_zero_requirements_export(self) -> None:
        # A spec with no parseable requirement lines
        raw_text = "# Just a heading\n\nSome paragraph text with no bullet requirements.\n"
        created = self._create_spec("empty.md", raw_text)
        spec_id = created["spec_id"]

        status, data = self._export(spec_id)
        self.assertEqual(status, 200)

        md = data["markdown_document"]
        self.assertIn("## Certified Spec", md)
        self.assertIn("## Acceptance Criteria", md)
        self.assertIn("## Unresolved Questions", md)
        self.assertIn("## Implementation Tasks", md)


class HandoffExportMissingSpecTests(HandoffExportTestBase):
    """Missing spec returns 404."""

    def test_missing_spec_returns_404(self) -> None:
        resp = self.client.post(
            "/api/specs/9999/handoff-export",
            json={},
        )
        self.assertEqual(resp.status_code, 404)


class HandoffExportRefusedVerdictTests(HandoffExportTestBase):
    """Refused specs still export successfully."""

    def test_refused_spec_exports_with_unresolved_findings(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        # Confirm it's refused
        self.assertEqual(created["verdict"], "REFUSED")

        status, data = self._export(spec_id)
        self.assertEqual(status, 200)
        self.assertEqual(data["verdict"], "REFUSED")

        # Unresolved questions should be populated
        md = data["markdown_document"]
        unresolved_section = md.split("## Unresolved Questions")[1].split("##")[0]
        self.assertIn("Line", unresolved_section)


class HandoffExportLatencyTests(HandoffExportTestBase):
    """Response latency must be under 200ms for specs under 200 lines."""

    def test_response_within_200ms(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        start = time.perf_counter()
        status, _ = self._export(spec_id)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(status, 200)
        self.assertLess(elapsed_ms, 200, f"Export took {elapsed_ms:.1f}ms, exceeds 200ms limit")


class HandoffExportEndToEndTests(HandoffExportTestBase):
    """End-to-end verification: exported Markdown contains all four sections
    with correct content structure (Task 9)."""

    def test_e2e_all_sections_with_content(self) -> None:
        """Full path: create → export → assert all section headers and content."""
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        status, data = self._export(spec_id)
        self.assertEqual(status, 200)

        md = data["markdown_document"]

        # Section 1: Certified Spec with effective spec text
        self.assertIn("## Certified Spec", md)
        certified_section = md.split("## Certified Spec")[1].split("## Acceptance Criteria")[0]
        # Should contain actual spec content (not empty)
        self.assertTrue(len(certified_section.strip()) > 0)

        # Section 2: Acceptance Criteria with EARS-formatted criteria
        self.assertIn("## Acceptance Criteria", md)
        criteria_section = md.split("## Acceptance Criteria")[1].split("## Unresolved Questions")[0]
        self.assertTrue(len(criteria_section.strip()) > 0)

        # Section 3: Unresolved Questions
        self.assertIn("## Unresolved Questions", md)
        unresolved_section = md.split("## Unresolved Questions")[1].split("## Implementation Tasks")[0]
        self.assertTrue(len(unresolved_section.strip()) > 0)

        # Section 4: Implementation Tasks with line-referenced tasks
        self.assertIn("## Implementation Tasks", md)
        tasks_section = md.split("## Implementation Tasks")[1]
        # Should contain line references like "[Line N]"
        self.assertIn("[Line", tasks_section)

        # Metadata header
        self.assertIn(data["filename"], md)
        self.assertIn(str(data["score"]), md)
        self.assertIn(data["verdict"], md)

    def test_e2e_extra_fields_ignored(self) -> None:
        """Extra fields in request body are silently ignored."""
        created = self._create_clean_spec()
        spec_id = created["spec_id"]

        resp = self.client.post(
            f"/api/specs/{spec_id}/handoff-export",
            json={"unexpected_field": "ignored_value", "another": 123},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("markdown_document", data)


if __name__ == "__main__":
    unittest.main()
