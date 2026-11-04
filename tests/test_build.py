# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_build.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Checks for reproducible dates and failure-safe build orchestration.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Checks for reproducible dates and failure-safe build orchestration."""

import subprocess
import tempfile
import unittest
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import build
from cvgen.helpers.clock import resolve_date, source_epoch

CURRENT_STEM = "Cv-Academic"
LEGACY_CURRENT_STEMS = ("cv", "Cv-Academic-Home")


class ClockTests(unittest.TestCase):
    """Keep visible dates and TeX timestamps tied to the same UTC epoch."""

    def test_explicit_date_overrides_even_an_invalid_environment_epoch(self):
        with patch.dict("os.environ", {"SOURCE_DATE_EPOCH": "invalid"}):
            as_of = resolve_date("2024-02-15")
            self.assertEqual(as_of, date(2024, 2, 15))
            epoch = source_epoch(as_of, explicit_date=True)
        self.assertEqual(
            epoch, str(int(datetime(2024, 2, 15, 12, tzinfo=timezone.utc).timestamp()))
        )

    def test_environment_epoch_uses_utc_date_and_keeps_exact_timestamp(self):
        # Near midnight: the local date in Europe/Rome differs from UTC.
        epoch = str(int(datetime(2024, 2, 15, 23, 30, tzinfo=timezone.utc).timestamp()))
        with patch.dict("os.environ", {"SOURCE_DATE_EPOCH": epoch}):
            as_of = resolve_date()
            self.assertEqual(as_of, date(2024, 2, 15))
            self.assertEqual(source_epoch(as_of), epoch)

    def test_invalid_epoch_is_reported_before_building(self):
        for epoch in ("invalid", "", "9" * 100):
            with (
                self.subTest(epoch=epoch),
                patch.dict("os.environ", {"SOURCE_DATE_EPOCH": epoch}),
            ):
                with self.assertRaisesRegex(ValueError, "SOURCE_DATE_EPOCH"):
                    resolve_date()


class BuildTests(unittest.TestCase):
    """Simulate compiler outcomes while checking actual output-file effects."""

    def test_missing_tools_fail_before_generation_changes_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with (
                patch("build.shutil.which", return_value=None),
                patch(
                    "generate.generate", side_effect=AssertionError("must not generate")
                ) as generate,
                patch("sys.stderr", new_callable=StringIO) as error,
            ):
                result = build.main(
                    ["--date", "2024-02-15", "--output-dir", str(output)]
                )
            self.assertEqual(result, 1)
            self.assertFalse(output.exists())
            generate.assert_not_called()
            self.assertIn("pdflatex, biber", error.getvalue())

    def test_biber_failure_stops_compilation_and_retains_diagnostic_log(self):
        results = [
            subprocess.CompletedProcess([], 0, stdout=b"first LaTeX pass\n"),
            subprocess.CompletedProcess([], 1, stdout=b"invalid bibliography\n"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with (
                patch("build.subprocess.run", side_effect=results) as run,
                patch("sys.stdout", new_callable=StringIO),
                patch("sys.stderr", new_callable=StringIO),
            ):
                with self.assertRaisesRegex(RuntimeError, "biber.*failed"):
                    build.compile_pdf(
                        output, {"pdflatex": "pdflatex", "biber": "biber"}, "1707998400"
                    )
            self.assertEqual(run.call_count, 2)
            transcript = (output / (CURRENT_STEM + ".build.log")).read_text(
                encoding="utf-8"
            )
            self.assertIn("first LaTeX pass", transcript)
            self.assertIn("invalid bibliography", transcript)
            self.assertFalse((output / (CURRENT_STEM + ".pdf")).exists())

    def test_compilation_timeout_stops_and_saves_partial_output(self):
        timeout = subprocess.TimeoutExpired(
            "pdflatex", 120, output=b"partial compiler output\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with (
                patch("build.subprocess.run", side_effect=timeout) as run,
                patch("sys.stdout", new_callable=StringIO),
            ):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    build.compile_pdf(
                        output, {"pdflatex": "pdflatex", "biber": "biber"}, "1707998400"
                    )
            self.assertEqual(run.call_count, 1)
            self.assertIn(
                "partial compiler output",
                (output / (CURRENT_STEM + ".build.log")).read_text(encoding="utf-8"),
            )

    def test_biber_failure_restores_previous_pdf_or_removes_a_partial_first_build(self):
        # LaTeX can write a provisional PDF before Biber fails. The fake
        # compiler must actually overwrite the file to exercise rollback.
        for previous in (None, b"previous complete PDF"):
            with (
                self.subTest(previous=previous),
                tempfile.TemporaryDirectory() as directory,
            ):
                output = Path(directory)
                pdf = output / (CURRENT_STEM + ".pdf")
                if previous is not None:
                    pdf.write_bytes(previous)

                def compiler(command, **kwargs):
                    if Path(command[0]).name == "pdflatex":
                        pdf.write_bytes(b"provisional first-pass PDF")
                        return subprocess.CompletedProcess(
                            command, 0, stdout=b"first LaTeX pass\n"
                        )
                    return subprocess.CompletedProcess(
                        command, 1, stdout=b"invalid bibliography\n"
                    )

                with (
                    patch("build.subprocess.run", side_effect=compiler) as run,
                    patch("sys.stdout", new_callable=StringIO),
                    patch("sys.stderr", new_callable=StringIO),
                ):
                    with self.assertRaisesRegex(RuntimeError, "biber.*failed"):
                        build.compile_pdf(
                            output,
                            {"pdflatex": "pdflatex", "biber": "biber"},
                            "1793793600",
                        )
                self.assertEqual(run.call_count, 2)
                if previous is None:
                    self.assertFalse(pdf.exists())
                else:
                    self.assertEqual(pdf.read_bytes(), previous)
                self.assertIn(
                    "invalid bibliography",
                    (output / (CURRENT_STEM + ".build.log")).read_text(
                        encoding="utf-8"
                    ),
                )

    def test_timeout_restores_previous_pdf_or_removes_a_partial_first_build(self):
        # A failed first build has no complete PDF to restore, so its partial
        # output must disappear instead of looking like a usable deliverable.
        for previous in (None, b"previous complete PDF"):
            with (
                self.subTest(previous=previous),
                tempfile.TemporaryDirectory() as directory,
            ):
                output = Path(directory)
                pdf = output / (CURRENT_STEM + ".pdf")
                if previous is not None:
                    pdf.write_bytes(previous)

                def compiler(command, **kwargs):
                    pdf.write_bytes(b"interrupted partial PDF")
                    raise subprocess.TimeoutExpired(
                        command, 120, output=b"partial compiler output\n"
                    )

                with (
                    patch("build.subprocess.run", side_effect=compiler),
                    patch("sys.stdout", new_callable=StringIO),
                ):
                    with self.assertRaisesRegex(RuntimeError, "timed out"):
                        build.compile_pdf(
                            output,
                            {"pdflatex": "pdflatex", "biber": "biber"},
                            "1793793600",
                        )
                if previous is None:
                    self.assertFalse(pdf.exists())
                else:
                    self.assertEqual(pdf.read_bytes(), previous)
                self.assertIn(
                    "partial compiler output",
                    (output / (CURRENT_STEM + ".build.log")).read_text(
                        encoding="utf-8"
                    ),
                )

    def test_clean_preserves_unrelated_files_and_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generated = [
                output / name
                for name in ("cv.tex", "cv.pdf", "cv.aux", "cv.run.xml", "build.log")
            ]
            generated += [
                output / (CURRENT_STEM + suffix)
                for suffix in (".tex", ".pdf", ".aux", ".run.xml", ".build.log")
            ]
            generated += [
                output / ("Cv-Academic-Home" + suffix)
                for suffix in (".tex", ".pdf", ".aux", ".build.log")
            ]
            preserved = [
                output / name for name in ("notes.txt", "other.tex", "cv.notes")
            ]
            nested = output / "notes"
            nested.mkdir()
            # A matching basename below another directory is not a build
            # product in output_dir and must survive the non-recursive clean.
            preserved.append(nested / "cv.tex")
            for path in generated + preserved:
                path.write_text("keep or remove", encoding="utf-8")
            build.clean(output)
            build.clean(output)
            build.clean(output / "absent")
            self.assertTrue(all(not path.exists() for path in generated))
            self.assertTrue(all(path.is_file() for path in preserved))

    def test_both_legacy_current_names_are_removed_only_after_successful_replacement(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            legacy = [
                output / (stem + suffix)
                for stem in LEGACY_CURRENT_STEMS
                for suffix in (".tex", ".pdf", ".aux", ".build.log")
            ]
            legacy.append(output / "build.log")
            for path in legacy:
                path.write_bytes(b"previous output")
            new_pdf = output / (CURRENT_STEM + ".pdf")
            new_pdf.write_bytes(b"replacement output")
            failure = subprocess.CompletedProcess([], 1, stdout=b"compiler failed\n")
            with (
                patch("build.subprocess.run", return_value=failure),
                patch("sys.stdout", new_callable=StringIO),
                patch("sys.stderr", new_callable=StringIO),
            ):
                with self.assertRaises(RuntimeError):
                    build.compile_pdf(
                        output, {"pdflatex": "pdflatex", "biber": "biber"}, "1707998400"
                    )
            self.assertTrue(
                all(path.read_bytes() == b"previous output" for path in legacy)
            )

            success = subprocess.CompletedProcess([], 0, stdout=b"compiler succeeded\n")
            with (
                patch("build.subprocess.run", return_value=success),
                patch("sys.stdout", new_callable=StringIO),
            ):
                result = build.compile_pdf(
                    output, {"pdflatex": "pdflatex", "biber": "biber"}, "1707998400"
                )
            self.assertEqual(result, new_pdf)
            self.assertEqual(new_pdf.read_bytes(), b"replacement output")
            self.assertTrue(all(not path.exists() for path in legacy))

    def test_clean_recognizes_previous_capitalization_without_touching_other_files(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generated = [
                output / name
                for name in (
                    "cv-Academic-Dossier.tex",
                    "Cv-Academic-Dossier.pdf",
                    "all-publications.tex",
                    "All-Publications.pdf",
                    "all-publications.build.log",
                    "cv-Academic-Dossier.skip.tex",
                )
            ]
            unrelated = output / "all-publications.notes"
            # Known filenames used as directories are never traversed/deleted.
            preserved_directory = output / "All-Publications.aux"
            preserved_directory.mkdir()
            for path in [*generated, unrelated]:
                path.write_text("sample", encoding="utf-8")
            build.clean(output)
            self.assertTrue(all(not path.exists() for path in generated))
            self.assertTrue(unrelated.is_file())
            self.assertTrue(preserved_directory.is_dir())


if __name__ == "__main__":
    unittest.main()
