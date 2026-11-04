# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/industry.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Prepare the industry presentation from already-loaded CV data.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Prepare the industry presentation from already-loaded CV data."""

from __future__ import annotations

import re
from copy import deepcopy

DEFAULT_TITLEINFO = (
    "Former researcher in pure mathematics transitioning to tech, with interests "
    "in functional programming, quantum algorithms, high-performance computing, "
    "scientific programming and numerical simulations."
)
# Exact source titles express the reference CV's editorial selections; the
# optional YAML industry mapping can change them without duplicating records.
AWARD_TITLES = (
    "MSCA Seal of Excellence 2026",
    "Progetto avvio alla ricerca 2025",
    "Research Abroad Grant",
    "Premio di Studio e Laurea",
)
TRAINING_TITLES = (
    "Functional Programming and Domain-Specific Languages",
    "Scientific computing with Python",
    "Computational methods for the solution of Differential Equations",
    "Python for computational science",
    "Introduction to Scientific and Technical Computing in C++",
    "B2 General English Intensive course",
    "Introduction to Scientific Programming using GPGPU and CUDA",
)
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


def _long_month(value: str) -> str:
    """Expand numeric month/year labels and retain free-form date ranges."""
    match = re.fullmatch(r"(\d{1,2})/(\d{4})", str(value).strip())
    if match is None:
        # Exact day/month/year dates and descriptive ranges are already
        # valid display values; do not discard their additional precision.
        return value
    month, year = map(int, match.groups())
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month in CV entry date: {value}")
    return f"{_MONTHS[month - 1]} {year}"


def _brief_entry(entry: dict, *, long_date: bool = False) -> dict:
    """Adapt academic entries to the concise reference layout on a deep copy."""
    result = deepcopy(entry)
    # The combined education entries retain the same degree/curriculum facts,
    # while their separately structured thesis/supervisor details stay academic.
    info = str(result.get("info", "")).split(r"\par", 1)[0]
    info = re.sub(r"\\vspace\{[^{}]*\}", "", info).strip()
    if info.startswith(("Supervisors:", "Supervisor:")):
        info = ""
    result["info"] = info
    result["where"] = re.sub(
        r"\\vspace\{[^{}]*\}", "", str(result.get("where", ""))
    ).strip()
    if long_date:
        result["when"] = _long_month(result.get("when", ""))
    return result


def _count(rows: list[dict], label: str) -> int:
    """Read a shared processed counter rather than recounting raw records."""
    return next((int(row["value"]) for row in rows if row["type"] == label), 0)


def prepare_industry(data: dict) -> dict:
    """Select the reference's sections without duplicating its outdated facts.

    The optional ``industry`` mapping can replace the introductory prose and
    the award/training selections. Personal details, dates, scores and totals
    always use the shared current data. Inputs are never mutated.
    """
    options = data.get("industry", {})
    jobs = [
        _brief_entry(entry)
        for entry in data.get("currentjobs", []) + data.get("previousjobs", [])
    ]
    # edublended contains both degrees and courses; only actual diplomas
    # belong in Education, while technical courses are selected below.
    diploma_titles = {entry["what"] for entry in data.get("diplomas", [])}
    combined_education = data.get("edublended", data.get("diplomas", []))
    education = [
        _brief_entry(entry, long_date=True)
        for entry in combined_education
        if entry["what"] in diploma_titles
    ]

    selected_awards = set(options.get("award_titles", AWARD_TITLES))
    awards = [
        _brief_entry(entry, long_date=True)
        for entry in data.get("awd", [])
        if entry["what"] in selected_awards
    ]
    habilitations = [
        _brief_entry(entry, long_date=True) for entry in data.get("habil", [])
    ]
    # Keep the source layout's placement of habilitations among selected awards.
    honors = awards[:2] + habilitations + awards[2:]

    selected_training = set(options.get("training_titles", TRAINING_TITLES))
    training = [
        deepcopy(entry)
        for entry in data.get("schools", [])
        if entry["Event_Title"] in selected_training
    ]
    for entry in training:
        entry["Approx_Date"] = _long_month(entry["Approx_Date"])

    publications = _count(data.get("pubsnum", []), "Published Papers")
    courses = _count(data.get("teachnum", []), "Courses Taught")
    hours = _count(data.get("teachnum", []), "Teaching hours")
    # The shared legacy counter combines contributed talks and posters.
    # Keep that definition consistent across layouts rather than quietly
    # changing the industry total during presentation preparation.
    talks = sum(
        _count(data.get("talksnum", []), label)
        for label in (
            "Invited Talks",
            "Contributed Talks and Posters",
        )
    )
    site = str(data.get("site", "")).rstrip("/")
    publication_url = (
        ("https://orcid.org/" + data["orcid"]) if data.get("orcid") else site
    )
    academic_track = [
        {
            "type": "Scientific Publications",
            "value": publications,
            "url": publication_url,
        },
        {
            "type": "Courses Taught",
            "value": f"{courses} ({hours} hours)",
            "url": site + "/teaching/",
        },
        {
            "type": "Conference Talks",
            "value": talks,
            "url": site + "/research/#presentations",
        },
        {
            "type": "Conferences Organized",
            "value": _count(data.get("talksnum", []), "Conferences Organized"),
            "url": "",
        },
        {
            "type": "Research Stays",
            "value": _count(data.get("talksnum", []), "Research Stays"),
            "url": "",
        },
    ]
    return {
        "titleinfo": options.get("titleinfo", DEFAULT_TITLEINFO),
        "website_label": re.sub(r"^https?://", "", site),
        "work_experiences": jobs,
        "education": education,
        "honors": honors,
        "training": training,
        "academic_track": academic_track,
    }
