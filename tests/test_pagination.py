# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_pagination.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Protect real PDF body content while suppressing empty academic shipouts.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Protect real PDF body content while suppressing empty academic shipouts."""

import subprocess
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
)

from cvgen.helpers.pagination import find_empty_body_pages

STEM = "Cv-Academic-Dossier"
CURRENT_STEM = "Cv-Academic"
HEADER_FOOTER = b"""
BT /F1 10 Tf 1 0 0 1 30 810 Tm (Curriculum Vitae) Tj ET
30 805 m 565 805 l S
BT /F1 8 Tf 1 0 0 1 30 25 Tm (Generated on November 4, 2026) Tj ET
BT /F1 8 Tf 1 0 0 1 540 25 Tm (5 / 18) Tj ET
"""


def stream(writer, payload):
    """Attach raw PDF drawing operators without relying on LaTeX fixtures."""
    result = DecodedStreamObject()
    result.set_data(payload)
    return writer._add_object(result)


def add_page(writer, body=b"", *, image=False, form=False, annotation=False):
    """Create an A4 page with margin furniture and optional body marks.

    Text, vector, XObject and annotation cases share the same coordinates so
    the tests isolate which content must prevent an empty-page classification.
    """
    page = writer.add_blank_page(width=595.276, height=841.89)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            ),
        }
    )
    if image or form:
        external = DecodedStreamObject()
        external[NameObject("/Type")] = NameObject("/XObject")
        if image:
            external.update(
                {
                    NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(1),
                    NameObject("/Height"): NumberObject(1),
                    NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                    NameObject("/BitsPerComponent"): NumberObject(8),
                }
            )
            external.set_data(b"\x00\x00\x00")
        else:
            external[NameObject("/Subtype")] = NameObject("/Form")
            external[NameObject("/BBox")] = ArrayObject(
                [NumberObject(n) for n in (0, 0, 1, 1)]
            )
            external.set_data(b"0 0 1 1 re f")
        resources[NameObject("/XObject")] = DictionaryObject(
            {NameObject("/Mark"): writer._add_object(external)}
        )
        body += b"q 60 0 0 60 100 400 cm /Mark Do Q\n"
    page[NameObject("/Resources")] = resources
    page[NameObject("/Contents")] = stream(writer, HEADER_FOOTER + body)
    if annotation:
        note = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Text"),
                NameObject("/Rect"): ArrayObject(
                    [FloatObject(n) for n in (100, 400, 120, 420)]
                ),
            }
        )
        page[NameObject("/Annots")] = ArrayObject([writer._add_object(note)])
    return page


class EmptyBodyDetectionTests(unittest.TestCase):
    """Protect sparse or graphical content using small synthetic PDF streams."""

    def detect(self, writer):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            writer.write(path)
            return find_empty_body_pages(path)

    def test_bare_and_header_footer_only_pages_are_empty(self):
        writer = PdfWriter()
        writer.add_blank_page(width=595.276, height=841.89)
        add_page(writer)
        add_page(writer, b"BT /F1 10 Tf 1 0 0 1 100 420 Tm (   ) Tj ET")
        self.assertEqual(self.detect(writer), (1, 2, 3))

    def test_one_word_and_a_short_last_page_are_real_body_content(self):
        writer = PdfWriter()
        add_page(writer, b"BT /F1 10 Tf 1 0 0 1 100 420 Tm (X) Tj ET")
        add_page(writer)
        add_page(writer, b"BT /F1 10 Tf 1 0 0 1 100 100 Tm (End.) Tj ET")
        self.assertEqual(self.detect(writer), (2,))

    def test_text_is_classified_after_its_page_transform(self):
        writer = PdfWriter()
        # Raw text coordinates suggest a header, but the translated text is in
        # the body and must remain. The second translation lands in the header.
        add_page(
            writer,
            b"q 1 0 0 1 0 -400 cm BT /F1 10 Tf 1 0 0 1 100 810 Tm (Body) Tj ET Q",
        )
        add_page(
            writer,
            b"q 1 0 0 1 0 600 cm BT /F1 10 Tf 1 0 0 1 100 210 Tm (Header) Tj ET Q",
        )
        self.assertEqual(self.detect(writer), (2,))

    def test_images_and_form_xobjects_are_preserved_conservatively(self):
        writer = PdfWriter()
        add_page(writer, image=True)
        add_page(writer, form=True)
        self.assertEqual(self.detect(writer), ())

    def test_rotated_or_slanted_text_crossing_a_margin_is_kept(self):
        writer = PdfWriter()
        # All anchors lie in a margin, but each run advances into the body.
        # Exercise both text and graphics matrices and both directions.
        for body in (
            b"BT /F1 10 Tf 0 1 -1 0 100 30 Tm (ABCDEFGHIJKLMNOPQRSTUVWXYZ) Tj ET",
            b"BT /F1 10 Tf 0 -1 1 0 100 810 Tm (ABCDEFGHIJKLMNOPQRSTUVWXYZ) Tj ET",
            b"BT /F1 10 Tf 1 .4 0 1 100 30 Tm (ABCDEFGHIJKLMNOPQRSTUVWXYZ) Tj ET",
            b"q 0 1 -1 0 100 30 cm BT /F1 10 Tf 1 0 0 1 0 0 Tm (ABCDEFGHIJKLMNOPQRSTUVWXYZ) Tj ET Q",
        ):
            add_page(writer, body)
        self.assertEqual(self.detect(writer), ())

    def test_body_vectors_are_kept_but_unpainted_paths_are_not_content(self):
        writer = PdfWriter()
        add_page(writer, b"100 350 80 20 re f")
        add_page(writer, b"100 350 80 20 re n")
        self.assertEqual(self.detect(writer), (2,))

    def test_body_annotations_are_preserved_conservatively(self):
        writer = PdfWriter()
        add_page(writer, annotation=True)
        self.assertEqual(self.detect(writer), ())


class AcademicBlankPageBuildTests(unittest.TestCase):
    """Test recompilation control separately from PDF content detection."""

    tools = {"pdflatex": "pdflatex", "biber": "biber"}

    def test_blank_pages_trigger_one_extra_compilation_round_and_stale_config_is_removed(
        self,
    ):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            pdf = output / (STEM + ".pdf")
            pdf.write_bytes(b"test result")
            skip = output / (STEM + ".skip.tex")
            skip.write_text("stale page selection", encoding="utf-8")
            config_present_during_commands = []

            def compiler(*args, **kwargs):
                # Presence during each pass proves stale page selections were
                # removed before the first round and generated only afterward.
                config_present_during_commands.append(skip.exists())
                return subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")

            with (
                patch("build.subprocess.run", side_effect=compiler) as run,
                patch(
                    "build.find_empty_body_pages", side_effect=[(5, 8), ()]
                ) as detector,
                patch("sys.stdout", new_callable=StringIO),
            ):
                self.assertEqual(
                    build.compile_pdf(output, self.tools, "1793793600", stem=STEM), pdf
                )
            self.assertEqual(run.call_count, 8)
            self.assertEqual(detector.call_count, 2)
            self.assertTrue(
                all(call.args[0] == pdf for call in detector.call_args_list)
            )
            self.assertEqual(config_present_during_commands, [False] * 4 + [True] * 4)
            configuration = skip.read_text(encoding="utf-8")
            self.assertNotIn("stale page selection", configuration)
            self.assertIn("5", configuration)
            self.assertIn("8", configuration)

    def test_remaining_empty_pages_fail_instead_of_silently_publishing_them(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / (STEM + ".pdf")).write_bytes(b"test result")
            success = subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")
            with (
                patch("build.subprocess.run", return_value=success) as run,
                patch("build.find_empty_body_pages", side_effect=[(5,), (7,)]),
                patch("sys.stdout", new_callable=StringIO),
            ):
                with self.assertRaises(RuntimeError):
                    build.compile_pdf(output, self.tools, "1793793600", stem=STEM)
            self.assertEqual(run.call_count, 8)

    def test_nonempty_dossier_does_not_gain_an_unnecessary_second_round(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / (STEM + ".pdf")).write_bytes(b"test result")
            success = subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")
            with (
                patch("build.subprocess.run", return_value=success) as run,
                patch("build.find_empty_body_pages", return_value=()) as detector,
                patch("sys.stdout", new_callable=StringIO),
            ):
                build.compile_pdf(output, self.tools, "1793793600", stem=STEM)
            self.assertEqual(run.call_count, 4)
            detector.assert_called_once()
            self.assertFalse((output / (STEM + ".skip.tex")).exists())

    def test_current_format_is_not_subject_to_academic_page_suppression(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / (CURRENT_STEM + ".pdf")).write_bytes(b"test result")
            success = subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")
            with (
                patch("build.subprocess.run", return_value=success) as run,
                patch(
                    "build.find_empty_body_pages",
                    side_effect=AssertionError("must not inspect current format"),
                ) as detector,
                patch("sys.stdout", new_callable=StringIO),
            ):
                build.compile_pdf(output, self.tools, "1793793600")
            self.assertEqual(run.call_count, 4)
            detector.assert_not_called()

    def test_clean_removes_shipout_config_but_preserves_unrelated_tex(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            skip = output / (STEM + ".skip.tex")
            unrelated = output / "notes.skip.tex"
            skip.write_text("generated", encoding="utf-8")
            unrelated.write_text("keep", encoding="utf-8")
            build.clean(output)
            self.assertFalse(skip.exists())
            self.assertTrue(unrelated.is_file())


if __name__ == "__main__":
    unittest.main()
