# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_positions.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-05
# |
# | Purpose           : Preserve employment facts while displaying a last-position fallback.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261105  Miti/Codex   Verify current/last position selection across academic layouts.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Check employment headings, dates, deduplication, and input immutability."""

import unittest
import warnings
from copy import deepcopy
from datetime import date
from pathlib import Path

from cvgen.acquisition import load_activities, load_bibliography, load_config
from cvgen.processing import assemble_cv
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 4)
ACADEMIC_FORMATS = ("current", "academic-dossier")


class EmploymentRenderingTests(unittest.TestCase):
    """Exercise real templates with distinct jobs rather than an empty-heading mock."""

    @classmethod
    def setUpClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cls.context = assemble_cv(
                load_config(ROOT / "data/cv.yaml"),
                load_activities(ROOT / "data/activities.csv"),
                load_bibliography(ROOT / "data/publications.bib"),
                AS_OF,
            )

    def employment(self):
        """Keep presentation fields realistic and make each job independently visible."""
        data = deepcopy(self.context)
        sample = data["previousjobs"][0]
        data["currentjobs"] = []
        data["previousjobs"] = [
            dict(
                sample, what="Latest completed role sentinel", when="02/2024 -- 04/2026"
            ),
            dict(
                sample,
                what="Earlier completed role sentinel",
                when="10/2022 -- 01/2024",
            ),
        ]
        return data

    def render(self, data, format):
        return render_cv(data, ROOT / "tmpl", AS_OF, format=format)

    def test_empty_current_shows_latest_completed_job_once_with_original_dates(self):
        data = self.employment()
        original = deepcopy(data)
        for format in ACADEMIC_FORMATS:
            with self.subTest(format=format):
                rendered = self.render(data, format)
                self.assertIn(r"\block{Last Position}", rendered)
                self.assertNotIn(r"\block{Current Position}", rendered)
                for title in (
                    "Latest completed role sentinel",
                    "Earlier completed role sentinel",
                ):
                    self.assertEqual(rendered.count(title), 1)
                self.assertLess(
                    rendered.index("Latest completed role sentinel"),
                    rendered.index(r"\block{Work Experience}"),
                )
                self.assertRegex(
                    rendered,
                    r"\\voice\{Latest completed role sentinel\}\s*\{02/2024 -- 04/2026\}",
                )
                self.assertEqual(data, original)

    def test_current_job_keeps_its_heading_and_preserves_every_previous_job(self):
        data = self.employment()
        data["currentjobs"] = [
            dict(
                data["previousjobs"][0],
                what="Current role sentinel",
                when="05/2026 -- Now",
            )
        ]
        original = deepcopy(data)
        for format in ACADEMIC_FORMATS:
            with self.subTest(format=format):
                rendered = self.render(data, format)
                self.assertIn(r"\block{Current Position}", rendered)
                self.assertNotIn(r"\block{Last Position}", rendered)
                for title in (
                    "Current role sentinel",
                    "Latest completed role sentinel",
                    "Earlier completed role sentinel",
                ):
                    self.assertEqual(rendered.count(title), 1)
                self.assertRegex(
                    rendered,
                    r"\\voice\{Current role sentinel\}\s*\{05/2026 -- Now\}",
                )
                self.assertEqual(data, original)

    def test_no_jobs_omit_empty_employment_headings(self):
        data = self.employment()
        data["previousjobs"] = []
        for format in ACADEMIC_FORMATS:
            with self.subTest(format=format):
                rendered = self.render(data, format)
                for heading in ("Current Position", "Last Position", "Work Experience"):
                    self.assertNotIn(r"\block{" + heading + "}", rendered)

    def test_a_single_previous_job_does_not_leave_an_empty_work_experience(self):
        data = self.employment()
        data["previousjobs"] = data["previousjobs"][:1]
        for format in ACADEMIC_FORMATS:
            with self.subTest(format=format):
                rendered = self.render(data, format)
                self.assertIn(r"\block{Last Position}", rendered)
                self.assertNotIn(r"\block{Work Experience}", rendered)
                self.assertEqual(rendered.count("Latest completed role sentinel"), 1)

    def test_omitting_the_current_slot_does_not_drop_the_latest_work_entry(self):
        data = self.employment()
        data["order"] = [entry for entry in data["order"] if entry[1] != "currentjobs"]
        original = deepcopy(data)
        rendered = self.render(data, "current")
        self.assertNotIn(r"\block{Last Position}", rendered)
        self.assertIn(r"\block{Work Experience}", rendered)
        self.assertEqual(rendered.count("Latest completed role sentinel"), 1)
        self.assertEqual(rendered.count("Earlier completed role sentinel"), 1)
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
