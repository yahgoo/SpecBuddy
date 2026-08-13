from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.linter.loader import LoadError, load_requirements


class LoaderTests(unittest.TestCase):
    def test_loads_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.md"
            path.write_text("WHEN an order is placed THE System SHALL confirm it.", encoding="utf-8")

            self.assertIn("order", load_requirements(path))

    def test_rejects_missing_file(self) -> None:
        with self.assertRaisesRegex(LoadError, "not found"):
            load_requirements("does-not-exist.md")

    def test_rejects_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(LoadError, "not a file"):
                load_requirements(tmp)

    def test_rejects_non_utf8_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.md"
            path.write_bytes(b"\xff\xfe\x00\x00")

            with self.assertRaisesRegex(LoadError, "UTF-8"):
                load_requirements(path)


if __name__ == "__main__":
    unittest.main()
