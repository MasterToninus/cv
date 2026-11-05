# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_dates.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-05
# |
# | Purpose           : Verify consistent date displays while retaining source precision.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261105  Miti/Codex   Check entry-date precision, ranges, and shared-data immutability.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Verify consistent date displays while retaining source precision."""

import unittest
import warnings
from copy import deepcopy
from datetime import date
from pathlib import Path

from cvgen.acquisition import load_activities, load_bibliography, load_config
from cvgen.helpers.dates import format_entry_date
from cvgen.helpers.industry import prepare_industry
from cvgen.processing import assemble_cv
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 5)


class EntryDateTests(unittest.TestCase):
    """Keep a display policy separate from the author-recorded facts."""

    def test_numeric_dates_use_month_precision_and_consistent_ranges(self):
        examples = (
            ("30/11/2010", "11/2010"),
            ("6/2018", "06/2018"),
            ("03/2018 -- 6/2018", "03/2018 -- 06/2018"),
            ("03/2026 - 07/2026", "03/2026 -- 07/2026"),
            ("1/3/2026 – 30/7/2026", "03/2026 -- 07/2026"),
            ("02/2024 -- Now", "02/2024 -- Now"),
        )
        for source, expected in examples:
            with self.subTest(source=source):
                self.assertEqual(format_entry_date(source), expected)

    def test_descriptive_dates_are_preserved(self):
        for source in ("", "Now", "2010", "Fall 2010", "September 2010"):
            with self.subTest(source=source):
                self.assertEqual(format_entry_date(source), source)

    def test_invalid_dates_cannot_be_hidden_by_reducing_precision(self):
        for source in ("31/02/2020", "13/2010", "03/2018 -- 31/06/2018"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "Invalid CV entry date"):
                    format_entry_date(source)

    def test_industry_can_keep_named_months_at_the_same_precision(self):
        self.assertEqual(
            format_entry_date("30/11/2010", long_month=True), "November 2010"
        )
        self.assertEqual(format_entry_date("6/2018", long_month=True), "June 2018")

    def test_real_cv_degrees_render_without_mutating_the_full_source_date(self):
        config = load_config(ROOT / "data/cv.yaml")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            data = assemble_cv(
                config,
                load_activities(ROOT / "data/activities.csv"),
                load_bibliography(ROOT / "data/publications.bib"),
                AS_OF,
            )
        original = deepcopy(data)
        for layout in ("current", "academic-dossier"):
            with self.subTest(layout=layout):
                rendered = render_cv(data, ROOT / "tmpl", AS_OF, format=layout)
                self.assertRegex(
                    rendered,
                    r"\\voice\{Bachelor degree in Physics\}\s*\{11/2010\}",
                )
                self.assertNotIn("30/11/2010", rendered)
                self.assertIn("03/2018 -- 06/2018", rendered)
        education = prepare_industry(data)["education"]
        bachelor = next(
            entry
            for entry in education
            if entry["what"] == "Bachelor degree in Physics"
        )
        self.assertEqual(bachelor["when"], "November 2010")
        self.assertEqual(data, original)
        self.assertEqual(
            next(
                entry
                for entry in config["diplomas"]
                if entry["what"] == "Bachelor degree in Physics"
            )["when"],
            "30/11/2010",
        )


if __name__ == "__main__":
    unittest.main()
