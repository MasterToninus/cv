# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/rendering.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Render processed CV data without loading its sources or writing output.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | 20261105  Miti/Codex   Show the last position when no current job exists.
# | 20261105  Miti/Codex   Share optional information across academic layouts.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Render processed CV data without loading its sources or writing output."""

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .helpers.formats import OUTPUT_STEMS

_MONTH_NAMES = (
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


def render_cv(
    data: dict,
    template_dir: Path,
    as_of: date,
    bibliography_path: str = "../data/publications.bib",
    format: str = "current",
) -> str:
    """Render a layout from processed data without changing the shared context.

    Dates and bibliography locations are supplied by the caller. This
    function reads template files but neither reloads inputs nor writes
    the resulting TeX; generation owns that final filesystem boundary.
    """
    if format not in OUTPUT_STEMS:
        raise ValueError(f"Unknown CV format: {format}")
    # Custom delimiters avoid collisions with ordinary LaTeX braces.
    # Values are authored as LaTeX, so HTML autoescaping is inappropriate.
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        block_start_string="~{",
        block_end_string="}~",
        variable_start_string="~{{",
        variable_end_string="}}~",
        comment_start_string="~{#",
        comment_end_string="#}~",
    )
    # New layouts fail on missing fields; the current layout retains the
    # original undefined-value behavior to preserve its established rendering.
    if format == "publications":
        env.undefined = StrictUndefined
        return env.get_template("All-Publications_tmpl.tex").render(
            publication_groups=data["publication_groups"],
            max_name_count=data["max_name_count"],
            today_long=f"{_MONTH_NAMES[as_of.month - 1]} {as_of.day}, {as_of.year}",
            bibliography_path=bibliography_path,
        )
    if format == "industry":
        from .helpers.industry import prepare_industry

        env.undefined = StrictUndefined
        return env.get_template("Cv-Industry_tmpl.tex").render(
            cv=data,
            industry=prepare_industry(data),
            today=as_of.strftime("%d/%m/%y"),
            today_long=f"{_MONTH_NAMES[as_of.month - 1]} {as_of.day}, {as_of.year}",
        )
    if format == "academic-dossier":
        env.undefined = StrictUndefined
        return env.get_template("Cv-Academic-Dossier_tmpl.tex").render(
            cv=data,
            today=as_of.strftime("%d/%m/%y"),
            today_long=f"{_MONTH_NAMES[as_of.month - 1]} {as_of.day}, {as_of.year}",
            bibliography_path=bibliography_path,
        )
    # The YAML order assigns sections to the two cover columns or the
    # continuation body. Preserve both source order and the legacy placement.
    # As in the dossier, previous jobs are authored newest first. Promote the
    # latest only when a current-position slot exists, without changing the
    # shared employment lists used by the other formats.
    previous_jobs = data.get("previousjobs", [])
    promote_last_position = (
        not data.get("currentjobs")
        and bool(previous_jobs)
        and any(section[1] == "currentjobs" for section in data["order"])
    )
    bodies = ["", "", ""]
    section_template = env.get_template("helpers/section_tmpl.tex")
    for name, key, kind, column in data["order"]:
        contents = data[key]
        if key == "currentjobs":
            if promote_last_position:
                name, contents = "Last Position", previous_jobs[:1]
            elif not contents:
                continue
        elif key == "previousjobs":
            if promote_last_position:
                contents = contents[1:]
            # A sole previous job is already visible in Last Position; an
            # empty employment history does not need an empty section header.
            if not contents:
                continue
        section = section_template.render(name=name, contents=contents, kind=kind)
        bodies[column - 1 if column in (1, 2) else 2] += section

    # Full citations are emitted as TeX; Biber resolves them during compilation.
    publications_page = "\\block{Publications}"
    publication_types = (
        ("published", "Published"),
        ("thesis", "Theses"),
        ("preprints", "Preprints"),
        ("drafts", "In preparation"),
    )
    for kind, title in publication_types:
        publications = [entry for entry in data["pub_details"] if entry["type"] == kind]
        # An empty itemize is a LaTeX error. Categories can disappear when the
        # last draft is published or the bibliography is still being populated.
        if not publications:
            continue
        publications_page += f"\\subsection*{{{title}}}\n\\begin{{itemize}}\n"
        for publication in publications:
            publications_page += f"\\item \\fullcite{{{publication['key']}}}\n"
        publications_page += "\\end{itemize}\n"

    context = {
        key: data[key]
        for key in (
            "name",
            "phone",
            "email",
            "site",
            "github",
            "titleinfo",
            "pubsnum",
            "pub_details",
            "talksnum",
            "teachnum",
        )
    }
    return env.get_template("Cv-Academic_tmpl.tex").render(
        **context,
        coverstatement=data["coverstatement"] + "\\vspace{0.25em}",
        body1=bodies[0],
        body2=bodies[1],
        body3=bodies[2],
        additional_information=data.get("additional_information", []),
        today=as_of.strftime("%d/%m/%y"),
        publications_page=publications_page,
        bibliography_path=bibliography_path,
    )
