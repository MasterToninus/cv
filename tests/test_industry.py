# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_industry.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Industry output uses current shared facts and a pdfLaTeX-only build.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Industry output uses current shared facts and a pdfLaTeX-only build."""

import importlib
import shutil
import subprocess
import tempfile
import unittest
import warnings
from copy import deepcopy
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cvgen.acquisition import load_activities, load_bibliography, load_config
from cvgen.helpers.industry import prepare_industry
from cvgen.processing import assemble_cv
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 4)
INDUSTRY_STEM = "Cv-Industry"


class IndustryDataAndRenderingTests(unittest.TestCase):
    """Adapt shared facts into the industry layout without changing the inputs."""

    @classmethod
    def setUpClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cls.data = assemble_cv(
                load_config(ROOT / "data/cv.yaml"),
                load_activities(ROOT / "data/activities.csv"),
                load_bibliography(ROOT / "data/publications.bib"),
                AS_OF,
            )

    def test_preparation_does_not_mutate_inputs_or_return_shared_job_objects(self):
        data = deepcopy(self.data)
        original = deepcopy(data)
        prepared = prepare_industry(data)
        self.assertEqual(data, original)
        prepared["work_experiences"][0]["what"] = "Changed derived entry"
        self.assertEqual(data, original)

    def test_real_data_uses_finished_job_dates_and_all_current_work_entries(self):
        prepared = prepare_industry(self.data)
        expected_jobs = self.data["currentjobs"] + self.data["previousjobs"]
        self.assertEqual(
            [(entry["what"], entry["when"]) for entry in prepared["work_experiences"]],
            [(entry["what"], entry["when"]) for entry in expected_jobs],
        )
        self.assertIn("04/2026", prepared["work_experiences"][0]["when"])
        self.assertEqual(len(prepared["education"]), 3)
        self.assertEqual(len(prepared["training"]), 7)
        self.assertFalse(
            any("career" in entry["what"].lower() for entry in prepared["education"])
        )

    def test_academic_track_counts_are_derived_instead_of_copied_from_the_reference(
        self,
    ):
        prepared = prepare_industry(self.data)
        self.assertCountEqual(
            [row["value"] for row in prepared["academic_track"]],
            [7, "5 (58 hours)", 37, 4, 12],
        )
        self.assertFalse(
            any("grant" in row["type"].lower() for row in prepared["academic_track"])
        )

        # Deliberately unrealistic sentinels expose counters accidentally
        # copied from the reference CV rather than the processed context.
        changed = deepcopy(self.data)
        for row in changed["pubsnum"]:
            if row["type"] == "Published Papers":
                row["value"] = 99
        for row in changed["teachnum"]:
            row["value"] = 9 if row["type"] == "Courses Taught" else 123
        values = {
            "Invited Talks": 11,
            "Contributed Talks and Posters": 22,
            "Conferences Organized": 6,
            "Research Stays": 17,
        }
        for row in changed["talksnum"]:
            if row["type"] in values:
                row["value"] = values[row["type"]]
        result = prepare_industry(changed)
        self.assertCountEqual(
            [row["value"] for row in result["academic_track"]],
            [99, "9 (123 hours)", 33, 6, 17],
        )

    def test_rendering_uses_updated_contacts_profile_and_roles_without_a_bibliography(
        self,
    ):
        data = deepcopy(self.data)
        data.update(
            name={"first": "IndustrySentinel", "last": "Dynamic"},
            email="industry@example.test",
            phone="12345",
            site="https://example.test/industry",
            industry={"titleinfo": "Dynamic industry summary sentinel."},
        )
        data["currentjobs"] = [
            dict(data["previousjobs"][0], what="Current industry role sentinel")
        ]
        original = deepcopy(data)
        rendered = render_cv(data, ROOT / "tmpl", AS_OF, format="industry")
        for value in (
            "IndustrySentinel",
            "industry@example.test",
            "12345",
            "Dynamic industry summary sentinel.",
            "Current industry role sentinel",
        ):
            with self.subTest(value=value):
                self.assertIn(value, rendered)
        self.assertNotIn(r"\fullcite", rendered)
        self.assertNotIn(r"\addbibresource", rendered)
        self.assertNotIn("biblatex", rendered)
        self.assertNotIn("~{{", rendered)
        self.assertNotIn("~{", rendered)
        self.assertEqual(data, original)


class IndustryGenerationAndBuildTests(unittest.TestCase):
    """Keep Industry selectable and independent of the academic Biber job."""

    def test_generator_names_the_separate_industry_tex_without_fetching(self):
        module = importlib.import_module("generate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("data", "tmpl"):
                shutil.copytree(ROOT / folder, root / folder)
            with (
                patch.object(module, "ROOT", root),
                patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("unexpected network"),
                ),
                warnings.catch_warnings(),
            ):
                warnings.simplefilter("ignore", UserWarning)
                output = module.generate(format="industry", as_of=AS_OF)
            self.assertEqual(output, root / "gen" / (INDUSTRY_STEM + ".tex"))
            self.assertTrue(output.is_file())
            self.assertFalse((root / "gen/Cv-Academic.tex").exists())

    def test_industry_only_build_does_not_require_biber(self):
        import build

        module = importlib.import_module("generate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch(
                    "build.shutil.which",
                    side_effect=lambda name: "pdflatex" if name == "pdflatex" else None,
                ) as which,
                patch.object(
                    module, "generate", return_value=root / (INDUSTRY_STEM + ".tex")
                ) as generate,
                patch(
                    "build.compile_pdf", return_value=root / (INDUSTRY_STEM + ".pdf")
                ) as compile_pdf,
                patch("sys.stdout", new_callable=StringIO),
            ):
                self.assertEqual(
                    build.main(
                        [
                            "--format",
                            "industry",
                            "--date",
                            "2026-11-04",
                            "--output-dir",
                            str(root),
                        ]
                    ),
                    0,
                )
            self.assertEqual(
                [call.args[0] for call in which.call_args_list], ["pdflatex"]
            )
            self.assertEqual(generate.call_args.kwargs["format"], "industry")
            self.assertEqual(compile_pdf.call_args.kwargs["stem"], INDUSTRY_STEM)

    def test_industry_compilation_runs_three_latex_passes_without_biber_or_page_suppression(
        self,
    ):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            pdf = output / (INDUSTRY_STEM + ".pdf")
            pdf.write_bytes(b"new industry output")
            previous_home = output / "cv.pdf"
            previous_home.write_bytes(b"previous home output")
            success = subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")
            with (
                patch("build.subprocess.run", return_value=success) as run,
                patch(
                    "build.find_empty_body_pages",
                    side_effect=AssertionError("industry is not an academic shipout"),
                ) as detector,
                patch("sys.stdout", new_callable=StringIO),
            ):
                self.assertEqual(
                    build.compile_pdf(
                        output,
                        {"pdflatex": "pdflatex"},
                        "1793793600",
                        stem=INDUSTRY_STEM,
                    ),
                    pdf,
                )
            self.assertEqual(run.call_count, 3)
            self.assertTrue(
                all(call.args[0][0] == "pdflatex" for call in run.call_args_list)
            )
            self.assertTrue(
                all(
                    call.args[0][-1] == INDUSTRY_STEM + ".tex"
                    for call in run.call_args_list
                )
            )
            detector.assert_not_called()
            self.assertEqual(previous_home.read_bytes(), b"previous home output")
            self.assertTrue((output / (INDUSTRY_STEM + ".build.log")).is_file())


if __name__ == "__main__":
    unittest.main()
