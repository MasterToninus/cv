# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : getactivities.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : not recorded; first tracked 2019-12-06
# |
# | Purpose           : Compatibility helpers for callers of the original data processor.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Compatibility helpers for callers of the original data processor.

Activities now come from the local snapshot. Network refresh is explicit in build.py.
Keep this root-level adapter for older imports; the reusable implementation
lives in the acquisition and processing stages under cvgen.
"""

from datetime import date
from pathlib import Path

from cvgen.acquisition import CSV_URL, load_activities, load_bibliography, load_config
from cvgen.processing import (
    process_activities,
    process_configuration,
    process_publications,
)

# CSV_URL remains an exported legacy name; these helpers do not download it.
# Their date.today() behavior is retained for compatibility. Reproducible
# documents use generate.py/build.py with one explicitly resolved date.
ROOT = Path(__file__).resolve().parent
BIBTEX_FILEPATH = ROOT / "data/publications.bib"
YAML_FILEPATH = ROOT / "data/cv.yaml"


def readmywebsite():
    """Keep the original helper name while reading the local activities snapshot."""
    return process_activities(
        load_activities(ROOT / "data/activities.csv"), date.today()
    )


def readmybibfile():
    """Return legacy publication counters using today, as existing callers expect."""
    return process_publications(load_bibliography(BIBTEX_FILEPATH), date.today())


def readmyconfigurations():
    """Expose the original configuration-summary API over the new pipeline."""
    return process_configuration(load_config(YAML_FILEPATH))
