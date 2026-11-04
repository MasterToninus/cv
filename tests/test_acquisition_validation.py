# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_acquisition_validation.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Prevent ambiguous CSV headers from replacing valid data.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Reject duplicate activity columns and preserve snapshots.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Verify that CSV header ambiguity cannot silently overwrite activity fields."""

import csv
import tempfile
import unittest
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch

from cvgen.acquisition import load_activities, refresh_activities


def duplicate_header_payload(column):
    """Build an otherwise valid CSV with one ambiguous repeated header."""
    columns = [
        "Type",
        "Start_Date",
        "Approx_Date",
        "Url",
        "Event_Title",
        "Organization",
        "Location",
        "Country",
    ]
    row = [
        "Invited Talk",
        "01-Feb-24",
        "February 2024",
        "https://example.org",
        "A talk",
        "A university",
        "A city",
        "Italy",
    ]
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow([*columns, column])
    # Even equal duplicate values must be rejected: accepting this structure
    # would also accept a later export whose duplicate columns disagree.
    writer.writerow([*row, row[columns.index(column)]])
    return stream.getvalue().encode("utf-8")


class ActivityHeaderValidationTests(unittest.TestCase):
    """Reject ambiguous inputs before they can replace the local snapshot."""

    def test_local_snapshot_rejects_duplicate_columns(self):
        for column in ("Type", "Start_Date", "Event_Title"):
            with (
                self.subTest(column=column),
                tempfile.TemporaryDirectory() as directory,
            ):
                source = Path(directory) / "activities.csv"
                source.write_bytes(duplicate_header_payload(column))
                with self.assertRaisesRegex(ValueError, "duplicate columns: " + column):
                    load_activities(source)

    def test_duplicate_columns_in_download_preserve_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "activities.csv"
            previous = b"known-good snapshot bytes"
            target.write_bytes(previous)
            with patch(
                "cvgen.acquisition.urllib.request.urlopen",
                return_value=BytesIO(duplicate_header_payload("Type")),
            ):
                with self.assertRaisesRegex(ValueError, "duplicate columns: Type"):
                    refresh_activities("https://example.org/activities.csv", target)
            self.assertEqual(target.read_bytes(), previous)
            self.assertEqual(list(Path(directory).iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
