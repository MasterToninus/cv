# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/processing.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Transform already-loaded CV data without reading files or accessing the network.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Transform already-loaded CV data without reading files or accessing the network."""

from __future__ import annotations

import warnings
from copy import deepcopy
from datetime import date, timedelta

from pybtex.database import BibliographyData

PHD_DEFENSE_DATE = date(2021, 4, 1)
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
_MONTH_NUMBERS = {name.lower(): number for number, name in enumerate(_MONTHS, 1)}
_MONTH_NUMBERS.update(
    {name[:3].lower(): number for number, name in enumerate(_MONTHS, 1)}
)


def parse_start_date(value: str) -> date:
    """Parse the CSV's English day-month-year independently of OS locale."""
    day, month, year = value.split("-")
    number = int(year)
    # Match strptime('%y'): 00..68 mean 2000..2068; 69..99 mean 1969..1999.
    if len(year) == 2:
        number += 2000 if number <= 68 else 1900
    return date(number, _MONTH_NUMBERS[month.lower()], int(day))


def format_approximate_date(value: str) -> str:
    """Convert an English month/year label to the CV's numeric display format."""
    month, year = value.split()
    parsed = date(int(year), _MONTH_NUMBERS[month.lower()], 1)
    return f"{parsed.month:02d}/{parsed.year:04d}"


def process_activities(rows: list[dict[str, str]], as_of: date) -> dict:
    """Preserve the legacy activity order, categories, counts, and date horizon."""
    schools, conferences, talks = [], [], []
    unused = set()
    talksnum = [
        {"type": "Invited Talks", "value": 0},
        {"type": "Contributed Talks and Posters", "value": 0},
        {"type": "Attended Conferences", "value": 0},
    ]
    school_types = {
        "Training Course",
        "Ph.D. Course",
        "School",
        "Summer school",
        "Master Course",
        "Reading Course",
        "Industry Course",
    }
    talk_types = {"Invited Talk", "Contributed Talk", "Poster"}
    conference_types = {"Workshop", "Conference"}
    limit = as_of + timedelta(days=200)

    for original in rows:
        # Enrich a copy: callers may render another layout from the same rows.
        item = dict(original)
        event = item["Type"]
        start = parse_start_date(item["Start_Date"])
        item["Url"] = item["Url"].replace("%", "\\%").replace("#", "\\#")
        item["Scheduled"] = "(scheduled)" if start > as_of else ""
        item["Approx_Date"] = format_approximate_date(item["Approx_Date"])

        # Counts intentionally include all source rows, as in the existing CV.
        if event == "Invited Talk":
            talksnum[0]["value"] += 1
        elif event in {"Contributed Talk", "Poster"}:
            talksnum[1]["value"] += 1
        elif event in {"Workshop", "Conference", "School"}:
            talksnum[2]["value"] += 1

        if event not in school_types | talk_types | conference_types:
            unused.add(event)
        # Original start times are midnight and the legacy cutoff is today's
        # current time + 200 days: include the complete cutoff date explicitly.
        if start <= limit:
            if event in conference_types:
                conferences.append(item)
            elif event in school_types:
                schools.append(item)
            elif event in talk_types:
                talks.append(item)

    if unused:
        warnings.warn(
            "The following event types are not categorized: "
            + ", ".join(sorted(unused))
            + ". Please review and categorize these event types.",
            UserWarning,
            stacklevel=2,
        )

    # Deliberately do not sort: sorting would change the current CV's content.
    return {
        "schools": list(reversed(schools)),
        "conferences": list(reversed(conferences)),
        "talks": list(reversed(talks)),
        "talksnum": talksnum,
    }


def process_publications(bibliography: BibliographyData, as_of: date) -> dict:
    """Keep the existing publication grouping, citation order, and totals."""
    pubsnum = [
        {"type": "Published Papers", "value": 0},
        {"type": "Preprints", "value": 0},
        {"type": "Drafts in Preparation", "value": 0},
    ]
    details = []
    for key, entry in bibliography.entries.items():
        kind = entry.type.lower()
        detail = {"key": key, "type": kind}
        if kind in {"article", "book", "inproceedings", "proceedings"}:
            pubsnum[0]["value"] += 1
            detail["type"] = "published"
        elif kind in {"unpublished", "preprint"}:
            pubsnum[1]["value"] += 1
            detail["type"] = "preprints"
        elif kind == "draft":
            pubsnum[2]["value"] += 1
            detail["type"] = "drafts"
        elif kind in {"phdthesis", "mastersthesis"}:
            detail["type"] = "thesis"
        details.append(detail)
    # This historical label measures elapsed time since the PhD defence,
    # not the sum of employment contracts or time excluding career breaks.
    # Preserve the legacy whole-365-day counter rather than introducing a
    # different anniversary calculation during the rendering refactor.
    pubsnum.append(
        {
            "type": "Postdoctoral experience (years)",
            "value": (as_of - PHD_DEFENSE_DATE).days // 365,
        }
    )
    return {"pubsnum": pubsnum, "pub_details": details}


def process_configuration(config: dict) -> list[dict]:
    """Derive the existing teaching, organization, and research-stay totals."""
    # These totals count configured records. In particular, org includes
    # courses/seminar series as well as conferences; the existing labels
    # and classifications are preserved pending an editorial data decision.
    courses = config.get("teach", [])
    return [
        {"type": "Conferences Organized", "value": len(config.get("org", []))},
        {"type": "Courses Taught", "value": len(courses)},
        {
            "type": "Teaching hours",
            "value": sum(course.get("load", 0) for course in courses),
        },
        {"type": "Research Stays", "value": len(config.get("visit", []))},
    ]


def assemble_cv(
    config: dict,
    activities: list[dict[str, str]],
    bibliography: BibliographyData,
    as_of: date,
) -> dict:
    """Build a render context, leaving all input objects unchanged."""
    # Templates receive one independent context; nested YAML lists remain
    # unchanged when derived counters and activity collections are added.
    data = deepcopy(config)
    data.update(process_activities(activities, as_of))
    data.update(process_publications(bibliography, as_of))
    teaching = process_configuration(config)
    communication_types = {"Conferences Organized", "Research Stays"}
    data["talksnum"].extend(
        item for item in teaching if item["type"] in communication_types
    )
    data["teachnum"] = [
        item for item in teaching if item["type"] not in communication_types
    ]
    return data
