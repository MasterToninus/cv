# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_pipeline.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Offline checks for data acquisition and the preserved CV semantics.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Offline checks for data acquisition and the preserved CV semantics."""

import csv
import hashlib
import importlib
import locale
import os
import sys
import tempfile
import unittest
import warnings
from contextlib import contextmanager
from copy import deepcopy
from datetime import date
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from pybtex.database import BibliographyData, Entry

from cvgen import acquisition, processing

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2024, 2, 15)
COLUMNS = (
    "Type",
    "Start_Date",
    "Approx_Date",
    "Url",
    "Event_Title",
    "Organization",
    "Location",
    "Country",
)


def activity(kind="Invited Talk", start="01-Feb-24", title="A talk", **changes):
    """Return one complete CSV record with only the fields under test replaced."""
    row = {
        "Type": kind,
        "Start_Date": start,
        "Approx_Date": "February 2024",
        "Url": "https://example.org/talk?q=10%23#details",
        "Event_Title": title,
        "Organization": "A university",
        "Location": "A city",
        "Country": "Italy",
    }
    row.update(changes)
    return row


def csv_bytes(rows):
    """Encode fixtures with the website snapshot's real delimiter and quoting."""
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


@contextmanager
def in_directory(path):
    """Restore the process working directory even when an assertion fails."""
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


class AcquisitionTests(unittest.TestCase):
    """Use real temporary files and simulated downloads to check atomic refresh."""

    def test_local_csv_handles_bom_unicode_and_quoted_semicolons(self):
        row = activity(title="Geometry; algebra — Università")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "activities.csv"
            source.write_bytes(b"\xef\xbb\xbf" + csv_bytes([row]))
            self.assertEqual(acquisition.load_activities(source), [row])

    def test_refresh_writes_valid_snapshot_without_changing_downloaded_bytes(self):
        payload = csv_bytes([activity()])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "activities.csv"
            target.write_bytes(b"previous snapshot")
            with patch(
                "cvgen.acquisition.urllib.request.urlopen",
                return_value=BytesIO(payload),
            ) as download:
                acquisition.refresh_activities(
                    "https://example.org/activities.csv", target, timeout=7
                )
            download.assert_called_once_with(
                "https://example.org/activities.csv", timeout=7
            )
            self.assertEqual(target.read_bytes(), payload)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_failed_refresh_preserves_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "activities.csv"
            target.write_bytes(b"previous snapshot")
            with patch(
                "cvgen.acquisition.urllib.request.urlopen",
                side_effect=URLError("offline"),
            ):
                with self.assertRaises(URLError):
                    acquisition.refresh_activities(
                        "https://example.org/activities.csv", target
                    )
            self.assertEqual(target.read_bytes(), b"previous snapshot")
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_invalid_download_preserves_existing_snapshot(self):
        invalid_payloads = [
            b"<!doctype html><title>Maintenance</title>",
            csv_bytes([]),
            csv_bytes([activity(start="not-a-date")]),
        ]
        for payload in invalid_payloads:
            with (
                self.subTest(payload=payload),
                tempfile.TemporaryDirectory() as directory,
            ):
                target = Path(directory) / "activities.csv"
                target.write_bytes(b"previous snapshot")
                with patch(
                    "cvgen.acquisition.urllib.request.urlopen",
                    return_value=BytesIO(payload),
                ):
                    with self.assertRaises(ValueError):
                        acquisition.refresh_activities(
                            "https://example.org/activities.csv", target
                        )
                self.assertEqual(target.read_bytes(), b"previous snapshot")
                self.assertEqual(list(Path(directory).iterdir()), [target])


class ProcessingTests(unittest.TestCase):
    """Preserve established classifications, counters and input immutability."""

    def test_preserves_legacy_reverse_order_and_does_not_mutate_rows(self):
        rows = [
            activity(start="05-Feb-24", title="first"),
            activity(start="01-Feb-24", title="second"),
        ]
        original = deepcopy(rows)
        result = processing.process_activities(rows, AS_OF)
        self.assertEqual(
            [row["Event_Title"] for row in result["talks"]], ["second", "first"]
        )
        self.assertEqual(rows, original)
        self.assertEqual(result["talks"][0]["Approx_Date"], "02/2024")
        self.assertEqual(
            result["talks"][0]["Url"], r"https://example.org/talk?q=10\%23\#details"
        )

    def test_preserves_future_count_and_scheduled_event_rules(self):
        # Established counters include all rows, while displayed event lists
        # apply the 200-day horizon. Keep those two behaviors distinct.
        rows = [
            activity(start="01-Mar-24", title="soon", Approx_Date="March 2024"),
            activity(start="01-Jan-25", title="distant", Approx_Date="January 2025"),
            activity(kind="School", title="school"),
        ]
        result = processing.process_activities(rows, AS_OF)
        self.assertEqual(
            result["talksnum"],
            [
                {"type": "Invited Talks", "value": 2},
                {"type": "Contributed Talks and Posters", "value": 0},
                {"type": "Attended Conferences", "value": 1},
            ],
        )
        self.assertEqual([row["Event_Title"] for row in result["talks"]], ["soon"])
        self.assertEqual(result["talks"][0]["Scheduled"], "(scheduled)")
        self.assertEqual(result["schools"][0]["Scheduled"], "")
        self.assertEqual(result["conferences"], [])

    def test_english_dates_work_under_an_italian_locale(self):
        original = locale.setlocale(locale.LC_TIME)
        try:
            for candidate in (
                "Italian_Italy.1252",
                "it_IT.UTF-8",
                "it_IT.utf8",
                "it_IT",
            ):
                try:
                    locale.setlocale(locale.LC_TIME, candidate)
                    break
                except locale.Error:
                    continue
            else:
                self.skipTest("An Italian locale is not installed")
            result = processing.process_activities([activity()], AS_OF)
            self.assertEqual(result["talks"][0]["Approx_Date"], "02/2024")
        finally:
            locale.setlocale(locale.LC_TIME, original)

    def test_publication_categories_and_experience_are_preserved(self):
        kinds = [
            "article",
            "book",
            "inproceedings",
            "proceedings",
            "unpublished",
            "preprint",
            "draft",
            "phdthesis",
            "mastersthesis",
            "misc",
        ]
        bibliography = BibliographyData(entries={kind: Entry(kind) for kind in kinds})
        result = processing.process_publications(bibliography, AS_OF)
        self.assertEqual(
            result["pubsnum"],
            [
                {"type": "Published Papers", "value": 4},
                {"type": "Preprints", "value": 2},
                {"type": "Drafts in Preparation", "value": 1},
                {"type": "Postdoctoral experience (years)", "value": 2},
            ],
        )
        self.assertEqual([item["key"] for item in result["pub_details"]], kinds)
        self.assertEqual(
            [item["type"] for item in result["pub_details"]],
            [
                "published",
                "published",
                "published",
                "published",
                "preprints",
                "preprints",
                "drafts",
                "thesis",
                "thesis",
                "misc",
            ],
        )

    def test_assembly_moves_summary_rows_without_mutating_inputs(self):
        config = {"org": [{}, {}], "teach": [{"load": 10}, {}], "visit": [{}, {}, {}]}
        rows = [activity()]
        original_config, original_rows = deepcopy(config), deepcopy(rows)
        result = processing.assemble_cv(config, rows, BibliographyData(), AS_OF)
        self.assertEqual(
            result["talksnum"][-2:],
            [
                {"type": "Conferences Organized", "value": 2},
                {"type": "Research Stays", "value": 3},
            ],
        )
        self.assertEqual(
            result["teachnum"],
            [
                {"type": "Courses Taught", "value": 2},
                {"type": "Teaching hours", "value": 10},
            ],
        )
        self.assertEqual(config, original_config)
        self.assertEqual(rows, original_rows)


class ImportAndRenderingTests(unittest.TestCase):
    """Keep imports inert and rendering deterministic against approved data."""

    def test_importing_generate_does_not_load_data_download_or_write_output(self):
        sys.modules.pop("generate", None)
        try:
            with tempfile.TemporaryDirectory() as directory, in_directory(directory):
                with (
                    patch(
                        "urllib.request.urlopen",
                        side_effect=AssertionError("unexpected network"),
                    ),
                    patch.object(
                        acquisition,
                        "load_config",
                        side_effect=AssertionError("unexpected YAML read"),
                    ),
                    patch.object(
                        acquisition,
                        "load_activities",
                        side_effect=AssertionError("unexpected CSV read"),
                    ),
                    patch.object(
                        acquisition,
                        "load_bibliography",
                        side_effect=AssertionError("unexpected bibliography read"),
                    ),
                ):
                    importlib.import_module("generate")
                self.assertEqual(list(Path(directory).iterdir()), [])
        finally:
            # Imports bind patched acquisition functions; discard this instance.
            sys.modules.pop("generate", None)

    def test_rendering_uses_the_supplied_date_and_template_directory(self):
        from cvgen.rendering import render_cv

        data = {
            "name": {"first": "Test", "last": "Person"},
            "phone": "123",
            "email": "test@example.org",
            "site": "https://example.org",
            "github": "test",
            "titleinfo": "A researcher",
            "coverstatement": "Research statement.",
            "order": [],
            "pubsnum": [],
            "pub_details": [],
            "talksnum": [],
            "teachnum": [],
        }
        with tempfile.TemporaryDirectory() as directory, in_directory(directory):
            rendered = render_cv(data, ROOT / "tmpl", AS_OF)
            repeated = render_cv(data, ROOT / "tmpl", AS_OF)
        self.assertEqual(rendered, repeated)
        self.assertIn("Test Person", rendered)
        self.assertIn("15/02/24", rendered)
        self.assertIn(r"\addbibresource{../data/publications.bib}", rendered)
        self.assertNotRegex(rendered, r"\\begin\{itemize\}\s*\\end\{itemize\}")

    def test_versioned_snapshot_matches_the_approved_cv(self):
        from cvgen.rendering import render_cv

        as_of = date(2026, 11, 4)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            data = processing.assemble_cv(
                acquisition.load_config(ROOT / "data/cv.yaml"),
                acquisition.load_activities(ROOT / "data/activities.csv"),
                acquisition.load_bibliography(ROOT / "data/publications.bib"),
                as_of,
            )
        rendered = render_cv(data, ROOT / "tmpl", as_of).replace("\r\n", "\n")
        # Header metadata is editorial; preserve the original rendered TeX,
        # including whitespace and inline comments, outside full comment lines.
        # This baseline includes the author-approved data corrections recorded
        # in docs/confirmed-data.md. Review further intentional content changes.
        content = "\n".join(
            line for line in rendered.splitlines() if not line.lstrip().startswith("%")
        )
        # Do not regenerate this expectation merely because the test fails:
        # first inspect the CV diff and obtain approval for factual changes.
        self.assertEqual(
            hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "31b88271381e7aaf0e8f104bcbd80f414a1eb10f4ecf61c9d722b661c954d885",
        )


if __name__ == "__main__":
    unittest.main()
