# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/dates.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-05
# |
# | Purpose           : Format entry dates consistently without changing source precision.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261105  Miti/Codex   Standardize month/year dates in generated CV entries.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Format entry dates consistently without changing source precision."""

from __future__ import annotations

import re
from datetime import date

_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_NUMERIC_DATE = r"(?:\d{1,2}/)?\d{1,2}/\d{4}"
_ENTRY_DATE = re.compile(
    rf"(?P<start>{_NUMERIC_DATE})"
    rf"(?:\s*(?:--|[-–—])\s*(?P<end>{_NUMERIC_DATE}|Now|Present))?"
)


def _month_label(value: str, *, long_month: bool) -> str:
    """Validate the full recorded date before hiding its day in the display."""
    if value in {"Now", "Present"}:
        return value
    parts = [int(part) for part in value.split("/")]
    day, month, year = parts if len(parts) == 3 else [1, *parts]
    try:
        parsed = date(year, month, day)
    except ValueError as error:
        raise ValueError(f"Invalid CV entry date: {value}") from error
    if long_month:
        return f"{_MONTHS[parsed.month - 1]} {parsed.year:04d}"
    return f"{parsed.month:02d}/{parsed.year:04d}"


def format_entry_date(value: str, *, long_month: bool = False) -> str:
    """Present numeric entry dates at month precision and normalize ranges.

    Full dates remain available in YAML and the shared render context.
    Descriptive labels are retained verbatim; this filter is not applied
    to birth dates, document dates, or bibliography metadata. Industry
    degree and award entries can retain their established named-month style.
    """
    match = _ENTRY_DATE.fullmatch(value.strip())
    if match is None:
        return value
    start = _month_label(match["start"], long_month=long_month)
    if match["end"] is None:
        return start
    end = _month_label(match["end"], long_month=long_month)
    return f"{start} -- {end}"
