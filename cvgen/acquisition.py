# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/acquisition.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Read local CV inputs and explicitly refresh the activities snapshot.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Read local CV inputs and explicitly refresh the activities snapshot."""

from __future__ import annotations

import csv
import io
import os
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path

import yaml
from pybtex.database import BibliographyData, parse_file
from pybtex.exceptions import PybtexError

from .processing import format_approximate_date, parse_start_date

CSV_URL = "http://antoniomiti.it/data/activities.csv"
ACTIVITY_COLUMNS = frozenset(
    {
        "Type",
        "Start_Date",
        "Approx_Date",
        "Url",
        "Event_Title",
        "Organization",
        "Location",
        "Country",
    }
)


def load_config(path: Path) -> dict:
    """Read CV configuration, without fetching or modifying other inputs.

    Values may contain intentional LaTeX. This stage checks the outer
    mapping and reports YAML syntax errors; presentation stays downstream.
    """
    try:
        with Path(path).open(encoding="utf-8") as source:
            config = yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML configuration {path}: {error}") from error
    if not isinstance(config, dict):
        raise ValueError(f"CV configuration must contain a YAML mapping: {path}")
    return config


def _parse_activities(payload: bytes) -> list[dict[str, str]]:
    """Validate the CSV structure before accepting a local or downloaded input."""
    # Website exports may contain a UTF-8 BOM; the semicolon is part of the
    # source format and must not depend on locale-specific CSV defaults.
    reader = csv.DictReader(
        io.StringIO(payload.decode("utf-8-sig"), newline=""),
        delimiter=";",
        strict=True,
    )
    columns = reader.fieldnames or ()
    # DictReader otherwise silently keeps only the last repeated column,
    # allowing a malformed export to replace a valid snapshot with lost data.
    duplicate_columns = sorted(
        name for name, count in Counter(columns).items() if count > 1
    )
    if duplicate_columns:
        raise ValueError(
            "Activities CSV has duplicate columns: " + ", ".join(duplicate_columns)
        )
    missing = ACTIVITY_COLUMNS - set(columns)
    if missing:
        raise ValueError(
            "Activities CSV is missing columns: " + ", ".join(sorted(missing))
        )

    rows = []
    for row in reader:
        # DictReader uses a None key for surplus cells and None values for
        # missing cells. Reject both instead of shifting or losing fields.
        if None in row or any(value is None for value in row.values()):
            raise ValueError(
                f"Activities CSV has an invalid row at line {reader.line_num}"
            )
        if any(not row[key].strip() for key in ("Type", "Start_Date", "Approx_Date")):
            raise ValueError(
                f"Activities CSV has an empty type or date at line {reader.line_num}"
            )
        try:
            parse_start_date(row["Start_Date"])
            format_approximate_date(row["Approx_Date"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Activities CSV has an invalid date at line {reader.line_num}"
            ) from error
        rows.append(row)
    if not rows:
        raise ValueError("Activities CSV contains no records")
    return rows


def load_activities(path: Path) -> list[dict[str, str]]:
    """Read the versioned CSV snapshot. Normal generation never needs the network."""
    return _parse_activities(Path(path).read_bytes())


def load_bibliography(path: Path) -> BibliographyData:
    """Read bibliographic entries in the source file's original order."""
    try:
        return parse_file(str(path))
    except PybtexError as error:
        raise ValueError(f"Invalid bibliography {path}: {error}") from error


def refresh_activities(url: str, path: Path, timeout: float = 30) -> None:
    """Replace a snapshot atomically, only after a successful validated download."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = response.read()
    # Reject malformed downloads before touching the known-good snapshot.
    _parse_activities(payload)

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # The temporary file shares the destination filesystem so os.replace
        # can publish a complete snapshot atomically, including on Windows.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=destination.name + ".",
            delete=False,
        ) as target:
            temporary = Path(target.name)
            target.write(payload)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
