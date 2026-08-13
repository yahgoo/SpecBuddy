"""Tests for backend.database and backend.main (Phase 1A).

Every test uses a temporary SQLite database via tempfile.TemporaryDirectory.
Tests never create, read, or modify the development specbuddy.db.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from backend.database import (
    connect,
    delete_all_rewrites,
    delete_rewrite,
    get_rewrites,
    get_spec,
    init_db,
    insert_spec,
    replace_findings,
    replace_requirements,
    upsert_rewrite,
)


class DatabaseTestBase(unittest.TestCase):
    """Base class providing a temporary database for each test."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test.db")
        init_db(self.db_path)
        self.conn = connect(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self._tmpdir.cleanup()


class SchemaTests(DatabaseTestBase):
    """Verify schema creation and structure."""

    def test_schema_creates_all_four_tables(self) -> None:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = sorted(row["name"] for row in cursor.fetchall())
        self.assertIn("specs", tables)
        self.assertIn("requirements", tables)
        self.assertIn("findings", tables)
        self.assertIn("rewrites", tables)

    def test_foreign_key_enforcement_active(self) -> None:
        """Inserting a requirement with a nonexistent spec_id must fail."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO requirements
                    (spec_id, line_number, raw_text, statement)
                VALUES (9999, 1, 'text', 'statement')
                """
            )


class SpecTests(DatabaseTestBase):
    """Verify insert_spec and get_spec."""

    def test_insert_and_get_spec(self) -> None:
        spec_id = insert_spec(self.conn, "test.md", "# Hello\n- Requirement")
        self.conn.commit()

        row = get_spec(self.conn, spec_id)
        self.assertIsNotNone(row)
        self.assertEqual(row["filename"], "test.md")
        self.assertEqual(row["raw_text"], "# Hello\n- Requirement")
        self.assertIsNotNone(row["created_at"])

    def test_get_spec_returns_none_for_missing(self) -> None:
        row = get_spec(self.conn, 9999)
        self.assertIsNone(row)

    def test_no_update_raw_text_helper_exists(self) -> None:
        """Confirm that backend.database does not expose an update function."""
        import backend.database as db_mod

        self.assertFalse(
            hasattr(db_mod, "update_raw_text"),
            "specs.raw_text must be immutable — no update helper allowed",
        )
        self.assertFalse(
            hasattr(db_mod, "update_spec"),
            "specs.raw_text must be immutable — no update helper allowed",
        )


class RewriteTests(DatabaseTestBase):
    """Verify rewrite CRUD operations."""

    def _make_spec(self) -> int:
        spec_id = insert_spec(self.conn, "spec.md", "line1\nline2\nline3")
        self.conn.commit()
        return spec_id

    def test_upsert_rewrite_inserts(self) -> None:
        spec_id = self._make_spec()
        upsert_rewrite(self.conn, spec_id, 2, "replaced line 2")
        self.conn.commit()

        rows = get_rewrites(self.conn, spec_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["line_number"], 2)
        self.assertEqual(rows[0]["rewritten_text"], "replaced line 2")

    def test_upsert_rewrite_replaces_same_line(self) -> None:
        spec_id = self._make_spec()
        upsert_rewrite(self.conn, spec_id, 2, "first version")
        self.conn.commit()
        upsert_rewrite(self.conn, spec_id, 2, "second version")
        self.conn.commit()

        rows = get_rewrites(self.conn, spec_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rewritten_text"], "second version")

    def test_delete_rewrite(self) -> None:
        spec_id = self._make_spec()
        upsert_rewrite(self.conn, spec_id, 1, "overlay")
        self.conn.commit()

        delete_rewrite(self.conn, spec_id, 1)
        self.conn.commit()

        rows = get_rewrites(self.conn, spec_id)
        self.assertEqual(len(rows), 0)

    def test_delete_all_rewrites_affects_only_target_spec(self) -> None:
        spec_a = self._make_spec()
        spec_b = insert_spec(self.conn, "other.md", "a\nb")
        self.conn.commit()

        upsert_rewrite(self.conn, spec_a, 1, "overlay A")
        upsert_rewrite(self.conn, spec_b, 1, "overlay B")
        self.conn.commit()

        delete_all_rewrites(self.conn, spec_a)
        self.conn.commit()

        self.assertEqual(len(get_rewrites(self.conn, spec_a)), 0)
        self.assertEqual(len(get_rewrites(self.conn, spec_b)), 1)


class ReplaceRequirementsTests(DatabaseTestBase):
    """Verify replace_requirements scoping."""

    def test_replace_requirements_affects_only_target_spec(self) -> None:
        spec_a = insert_spec(self.conn, "a.md", "text a")
        spec_b = insert_spec(self.conn, "b.md", "text b")
        self.conn.commit()

        recs_a = [
            {
                "line_number": 1,
                "raw_text": "req A",
                "statement": "req A",
                "section": None,
                "uppercase_keywords": ["SHALL"],
                "lowercase_keywords": [],
            }
        ]
        recs_b = [
            {
                "line_number": 1,
                "raw_text": "req B",
                "statement": "req B",
                "section": "Intro",
                "uppercase_keywords": [],
                "lowercase_keywords": ["shall"],
            }
        ]
        replace_requirements(self.conn, spec_a, recs_a)
        replace_requirements(self.conn, spec_b, recs_b)
        self.conn.commit()

        # Replace spec_a only
        new_recs = [
            {
                "line_number": 2,
                "raw_text": "new A",
                "statement": "new A",
                "section": None,
                "uppercase_keywords": [],
                "lowercase_keywords": [],
            }
        ]
        replace_requirements(self.conn, spec_a, new_recs)
        self.conn.commit()

        cur_a = self.conn.execute(
            "SELECT * FROM requirements WHERE spec_id = ?", (spec_a,)
        )
        rows_a = cur_a.fetchall()
        self.assertEqual(len(rows_a), 1)
        self.assertEqual(rows_a[0]["line_number"], 2)

        cur_b = self.conn.execute(
            "SELECT * FROM requirements WHERE spec_id = ?", (spec_b,)
        )
        rows_b = cur_b.fetchall()
        self.assertEqual(len(rows_b), 1)
        self.assertEqual(rows_b[0]["raw_text"], "req B")


class ReplaceFindingsTests(DatabaseTestBase):
    """Verify replace_findings scoping."""

    def test_replace_findings_affects_only_target_spec(self) -> None:
        spec_a = insert_spec(self.conn, "a.md", "text a")
        spec_b = insert_spec(self.conn, "b.md", "text b")
        self.conn.commit()

        finding = {
            "line_number": 1,
            "type": "defect",
            "severity": "error",
            "message": "vague",
            "suggested_rewrite": "be specific",
            "check_id": "AMB-VAGUE",
            "category": "lexical",
        }
        replace_findings(self.conn, spec_a, [finding])
        replace_findings(self.conn, spec_b, [finding])
        self.conn.commit()

        # Replace spec_a findings with empty
        replace_findings(self.conn, spec_a, [])
        self.conn.commit()

        cur_a = self.conn.execute(
            "SELECT * FROM findings WHERE spec_id = ?", (spec_a,)
        )
        self.assertEqual(len(cur_a.fetchall()), 0)

        cur_b = self.conn.execute(
            "SELECT * FROM findings WHERE spec_id = ?", (spec_b,)
        )
        self.assertEqual(len(cur_b.fetchall()), 1)


class TransactionRollbackTests(DatabaseTestBase):
    """Verify that rollback leaves no partial mutation."""

    def test_rollback_on_exception(self) -> None:
        spec_id = insert_spec(self.conn, "tx.md", "line1\nline2")
        self.conn.commit()

        # Begin a transaction that will fail partway through
        try:
            upsert_rewrite(self.conn, spec_id, 1, "overlay")
            # Force an error: violate foreign key on requirements
            self.conn.execute(
                """
                INSERT INTO requirements
                    (spec_id, line_number, raw_text, statement)
                VALUES (9999, 1, 'bad', 'bad')
                """
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()

        # The rewrite inserted before the error must be gone
        rows = get_rewrites(self.conn, spec_id)
        self.assertEqual(len(rows), 0)


class CreateAppTests(unittest.TestCase):
    """Verify create_app returns a FastAPI instance and initializes the DB."""

    def test_create_app_returns_fastapi_instance(self) -> None:
        from fastapi import FastAPI

        from backend.main import create_app

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "app_test.db")
            app = create_app(db_path)
            self.assertIsInstance(app, FastAPI)
            self.assertEqual(app.state.db_path, db_path)

    def test_create_app_lifespan_initializes_db(self) -> None:
        """Use the test client to trigger lifespan and verify schema exists."""
        from fastapi.testclient import TestClient

        from backend.main import create_app

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "lifespan_test.db")
            app = create_app(db_path)

            with TestClient(app):
                # After lifespan startup, the DB file should exist with tables
                self.assertTrue(os.path.exists(db_path))
                conn = connect(db_path)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = {row["name"] for row in cursor.fetchall()}
                conn.close()
                self.assertIn("specs", tables)
                self.assertIn("requirements", tables)
                self.assertIn("findings", tables)
                self.assertIn("rewrites", tables)


class RestartSafetyTests(unittest.TestCase):
    """Verify init_db is idempotent and restart-safe."""

    def test_init_db_succeeds_twice_on_same_database(self) -> None:
        """Calling init_db() twice on the same path must not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "restart.db")
            init_db(db_path)
            # Second call must succeed without error
            init_db(db_path)

    def test_all_four_tables_present_after_double_init(self) -> None:
        """All four tables remain present after two init_db() calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "restart.db")
            init_db(db_path)
            init_db(db_path)

            conn = connect(db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row["name"] for row in cursor.fetchall()}
            conn.close()
            self.assertIn("specs", tables)
            self.assertIn("requirements", tables)
            self.assertIn("findings", tables)
            self.assertIn("rewrites", tables)

    def test_data_persists_across_reinitialization(self) -> None:
        """Data inserted between two init_db() calls remains present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "restart.db")
            init_db(db_path)

            # Insert data
            conn = connect(db_path)
            spec_id = insert_spec(conn, "persist.md", "# Spec\n- Requirement")
            conn.commit()
            conn.close()

            # Re-initialize (simulates application restart)
            init_db(db_path)

            # Data must still be present
            conn = connect(db_path)
            row = get_spec(conn, spec_id)
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row["filename"], "persist.md")
            self.assertEqual(row["raw_text"], "# Spec\n- Requirement")

    def test_two_testclient_lifespans_on_same_database(self) -> None:
        """Two separate TestClient lifespans succeed on the same DB path."""
        from fastapi.testclient import TestClient

        from backend.main import create_app

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "dual_lifespan.db")

            # First lifespan
            app1 = create_app(db_path)
            with TestClient(app1) as client1:
                # Insert data during first lifespan
                conn = connect(db_path)
                spec_id = insert_spec(conn, "first.md", "first spec")
                conn.commit()
                conn.close()

            # Second lifespan (simulates server restart)
            app2 = create_app(db_path)
            with TestClient(app2) as client2:
                # Verify schema is intact and data persists
                conn = connect(db_path)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = {row["name"] for row in cursor.fetchall()}
                self.assertIn("specs", tables)
                self.assertIn("requirements", tables)
                self.assertIn("findings", tables)
                self.assertIn("rewrites", tables)

                row = get_spec(conn, spec_id)
                conn.close()
                self.assertIsNotNone(row)
                self.assertEqual(row["filename"], "first.md")


if __name__ == "__main__":
    unittest.main()
