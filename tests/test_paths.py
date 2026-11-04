# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_paths.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Protect CLI path resolution when entry-point roots change.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Verify shared helpers retain dynamic root behavior.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Entry-point wrappers use the shared resolver with their current repository root."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
import generate


class EntryPointPathTests(unittest.TestCase):
    """Keep repository selection dynamic after the entry points are imported."""

    def test_rebinding_each_entry_point_root_redirects_only_relative_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            absolute = base / "external" / "custom.tex"
            for entry_point in (build, generate):
                # Rebinding twice catches a helper that captured the first
                # root in a default argument or a preconfigured partial.
                for folder in ("first-checkout", "second-checkout"):
                    with self.subTest(entry_point=entry_point.__name__, root=folder):
                        selected_root = base / folder
                        with patch.object(entry_point, "ROOT", selected_root):
                            self.assertEqual(
                                entry_point.project_path("gen/output.tex"),
                                selected_root / "gen/output.tex",
                            )
                            self.assertEqual(
                                entry_point.project_path(absolute), absolute
                            )


if __name__ == "__main__":
    unittest.main()
