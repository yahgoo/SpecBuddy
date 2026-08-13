"""Tests for backend.routes (Phase 1B).

Every test uses a temporary SQLite database via TestClient.
Tests never create, read, or modify the development specbuddy.db.
"""

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


class RouteTestBase(unittest.TestCase):
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


class CreateSpecRouteTests(RouteTestBase):
    """POST /api/specs"""

    def test_create_ambiguous_spec(self) -> None:
        data = self._create_ambiguous_spec()
        self.assertEqual(data["requirement_count"], 6)
        self.assertEqual(len(data["findings"]), 23)
        self.assertEqual(data["score"], 0)
        self.assertEqual(data["verdict"], "REFUSED")
        self.assertIn("report_markdown", data)
        self.assertIn("spec_id", data)

    def test_create_clean_spec(self) -> None:
        raw_text = CLEAN_PATH.read_text(encoding="utf-8")
        resp = self.client.post(
            "/api/specs",
            json={"filename": "clean-ears-requirements.md", "raw_text": raw_text},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["requirement_count"], 3)
        self.assertEqual(len(data["findings"]), 0)
        self.assertEqual(data["score"], 100)
        self.assertEqual(data["verdict"], "CERTIFIED")

    def test_empty_filename_returns_422(self) -> None:
        resp = self.client.post(
            "/api/specs",
            json={"filename": "  ", "raw_text": "some text"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_empty_raw_text_returns_422(self) -> None:
        resp = self.client.post(
            "/api/specs",
            json={"filename": "test.md", "raw_text": "  "},
        )
        self.assertEqual(resp.status_code, 422)


class GetSpecRouteTests(RouteTestBase):
    """GET /api/specs/{spec_id}"""

    def test_get_existing_spec(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        resp = self.client.get(f"/api/specs/{spec_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["spec_id"], spec_id)
        self.assertEqual(len(data["findings"]), 23)

    def test_get_missing_spec_returns_404(self) -> None:
        resp = self.client.get("/api/specs/9999")
        self.assertEqual(resp.status_code, 404)


class RewriteRouteTests(RouteTestBase):
    """POST /api/specs/{spec_id}/rewrites"""

    def test_apply_rewrite(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": new_text},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["rewrites"]), 1)
        self.assertIn("effective_markdown", data)

    def test_rewrite_with_newline_returns_400(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": "line1\nline2"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_rewrite_with_carriage_return_returns_400(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": "line1\rline2"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_rewrite_empty_text_returns_422(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": "   "},
        )
        self.assertEqual(resp.status_code, 422)

    def test_rewrite_missing_spec_returns_404(self) -> None:
        resp = self.client.post(
            "/api/specs/9999/rewrites",
            json={"line_number": 1, "rewritten_text": "new text"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_rewrite_out_of_range_line_returns_404(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": 9999, "rewritten_text": "new text"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_rewrite_non_requirement_line_returns_422(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]

        # Line 1 is typically a heading, not a requirement
        resp = self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": 1, "rewritten_text": "new text"},
        )
        self.assertEqual(resp.status_code, 422)


class DeleteRewriteRouteTests(RouteTestBase):
    """DELETE /api/specs/{spec_id}/rewrites/{line_number}"""

    def test_delete_one_rewrite(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        # Apply then delete
        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": new_text},
        )

        resp = self.client.delete(f"/api/specs/{spec_id}/rewrites/{line_num}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["rewrites"]), 0)

    def test_delete_rewrite_missing_spec_returns_404(self) -> None:
        resp = self.client.delete("/api/specs/9999/rewrites/1")
        self.assertEqual(resp.status_code, 404)


class DeleteAllRewritesRouteTests(RouteTestBase):
    """DELETE /api/specs/{spec_id}/rewrites"""

    def test_delete_all_rewrites(self) -> None:
        created = self._create_ambiguous_spec()
        spec_id = created["spec_id"]
        first_req = created["requirements"][0]
        line_num = first_req["line_number"]

        new_text = "- WHEN an order is submitted, THE System SHALL display confirmation within 2 seconds."
        self.client.post(
            f"/api/specs/{spec_id}/rewrites",
            json={"line_number": line_num, "rewritten_text": new_text},
        )

        resp = self.client.delete(f"/api/specs/{spec_id}/rewrites")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["rewrites"]), 0)
        self.assertEqual(len(data["findings"]), 23)

    def test_delete_all_rewrites_missing_spec_returns_404(self) -> None:
        resp = self.client.delete("/api/specs/9999/rewrites")
        self.assertEqual(resp.status_code, 404)


class ResponseConstraintTests(RouteTestBase):
    """Verify response constraints."""

    def test_no_mission_state_in_response(self) -> None:
        data = self._create_ambiguous_spec()
        self.assertNotIn("missions", data)
        self.assertNotIn("mission", data)

    def test_report_markdown_present(self) -> None:
        data = self._create_ambiguous_spec()
        self.assertIn("report_markdown", data)
        self.assertIn("SpecBuddy Quality Report", data["report_markdown"])
        self.assertIn("REFUSED", data["report_markdown"])


if __name__ == "__main__":
    unittest.main()
