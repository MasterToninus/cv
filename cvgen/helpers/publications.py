# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/publications.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Group BibTeX records for a standalone publication list.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Add automatic publication-list presentation.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Prepare publication-list sections directly from loaded BibTeX records."""

from pybtex.database import BibliographyData

_SECTIONS = (
    ("Published", {"article", "book", "inproceedings", "proceedings"}, True),
    ("Theses", {"phdthesis", "mastersthesis"}, True),
    ("Submitted to Peer-review", {"preprint", "unpublished"}, False),
    ("In Preparation", {"draft"}, False),
)


def prepare_publications(bibliography: BibliographyData) -> dict:
    """Keep every record once, reversing its source order within each section.

    ``annotation`` is optional trusted LaTeX from the local bibliography. It
    carries editorial footnotes without encoding publication keys in Python
    or Jinja2. Unrecognized entry types remain visible in an extra section.
    """
    sections = [
        {"title": title, "numbered": numbered, "start": 0, "entries": []}
        for title, _, numbered in _SECTIONS
    ]
    other = {
        "title": "Other Publications",
        "numbered": False,
        "start": 0,
        "entries": [],
    }
    # BibLaTeX name limits must remain positive even for an empty source.
    max_name_count = 1
    for key, entry in bibliography.entries.items():
        # Full citations use citation-name limits, distinct from bibliography
        # limits. Cover every person list, including editors, without a fixed
        # cap that could silently truncate a future large collaboration.
        max_name_count = max(
            max_name_count,
            max((len(names) for names in entry.persons.values()), default=1),
        )
        target = next(
            (
                section
                for section, (_, kinds, _) in zip(sections, _SECTIONS)
                if entry.type.lower() in kinds
            ),
            other,
        )
        target["entries"].append(
            {
                "key": key,
                "annotation": entry.fields.get("annotation", ""),
            }
        )
    # Continue the numbered sequence from Published through Theses, as in the
    # reference. Other groups use bullets and do not consume that counter.
    counter = 0
    for section in sections:
        # The supplied list presents the reverse of each BibTeX group; this
        # preserves that editorial order without imposing a date/key sort.
        section["entries"].reverse()
        if section["numbered"]:
            section["start"] = counter
            counter += len(section["entries"])
    if other["entries"]:
        other["entries"].reverse()
        sections.append(other)
    return {"publication_groups": sections, "max_name_count": max_name_count}
