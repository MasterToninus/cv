# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/clock.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Resolve one reference date for all stages of a reproducible build.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Resolve one reference date for all stages of a reproducible build."""

import os
from datetime import date, datetime, time, timezone


def resolve_date(value: str | None = None) -> date:
    """Prefer an explicit date, then the UTC epoch date, then the local day."""
    if value is not None:
        return date.fromisoformat(value)
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is not None:
        try:
            timestamp = int(epoch)
            if timestamp < 0:
                raise ValueError("negative timestamp")
            return datetime.fromtimestamp(timestamp, timezone.utc).date()
        except (ValueError, OverflowError, OSError) as error:
            raise ValueError(
                "SOURCE_DATE_EPOCH must be a non-negative Unix timestamp"
            ) from error
    return date.today()


def source_epoch(as_of: date, explicit_date: bool = False) -> str:
    """Keep a supplied epoch, or use noon UTC on the chosen reference date."""
    # An explicit --date overrides an inherited epoch; otherwise preserve the
    # supplied timestamp, not just its calendar day, for reproducible metadata.
    if not explicit_date and "SOURCE_DATE_EPOCH" in os.environ:
        resolve_date()
        return str(int(os.environ["SOURCE_DATE_EPOCH"]))
    # Noon UTC supplies one stable instant for a date-only request,
    # independent of the operating system timezone or daylight saving.
    timestamp = int(datetime.combine(as_of, time(12), timezone.utc).timestamp())
    if timestamp < 0:
        raise ValueError("A reproducible build date cannot precede 1970")
    return str(timestamp)
