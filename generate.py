#!/usr/bin/env python3
# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : generate.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : not recorded; first tracked 2019-09-05
# |
# | Purpose           : Generate the CV from local inputs; importing this module performs no I/O.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Generate the CV from local inputs; importing this module performs no I/O."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

from jinja2 import TemplateError

from cvgen.acquisition import load_activities, load_bibliography, load_config
from cvgen.helpers.clock import resolve_date
from cvgen.helpers.formats import (
    DEFAULT_FORMAT,
    FORMAT_CHOICES,
    OUTPUT_STEMS,
    selected_formats,
)
from cvgen.helpers.paths import resolve_project_path
from cvgen.helpers.publications import prepare_publications
from cvgen.processing import assemble_cv
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parent


def project_path(value: str | Path) -> Path:
    """Resolve CLI paths from the repository, independent of the caller's cwd."""
    # Keep this wrapper for existing callers while sharing the path policy.
    return resolve_project_path(value, root=ROOT)


def generate(
    ext: str = "tex",
    *,
    output: str | Path | None = None,
    activities: str | Path = "data/activities.csv",
    as_of: date | None = None,
    format: str = "current",
) -> Path:
    """Acquire, process, and render one document using an explicit build date.

    Keep the single-layout API default for existing Python callers; the CLI
    expands its own ``all`` default into separate calls to this function.
    """
    if ext != "tex":
        raise ValueError("Only the tex output format is supported")
    if format not in OUTPUT_STEMS:
        raise ValueError(f"Unknown CV format: {format}")
    as_of = as_of if as_of is not None else resolve_date()
    destination = project_path(
        output if output is not None else f"gen/{OUTPUT_STEMS[format]}.tex"
    )
    bibliography = ROOT / "data/publications.bib"
    # File I/O belongs to acquisition; processing receives loaded objects and
    # one shared date, so templates never fetch data or consult the clock.
    bibliography_data = load_bibliography(bibliography)
    if format == "publications":
        # A standalone list depends only on its BibTeX source, not CV data or
        # the activities snapshot. Entry types determine the visible sections.
        data = prepare_publications(bibliography_data)
    else:
        data = assemble_cv(
            load_config(ROOT / "data/cv.yaml"),
            load_activities(project_path(activities)),
            bibliography_data,
            as_of,
        )
    # TeX resolves bibliography paths from the output directory, not ROOT.
    try:
        bibliography_path = Path(
            os.path.relpath(bibliography, destination.parent)
        ).as_posix()
    except ValueError:  # An explicitly selected output on a different Windows drive.
        bibliography_path = bibliography.as_posix()
    document = render_cv(data, ROOT / "tmpl", as_of, bibliography_path, format=format)
    # Generation is the write boundary: earlier stages only return data
    # or text, so validation/rendering errors do not leave partial TeX.
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8", newline="\n")
    return destination


def main(argv: list[str] | None = None) -> int:
    """Generate the selected layouts and return a shell-friendly exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date", help="CV reference date, YYYY-MM-DD (or SOURCE_DATE_EPOCH)"
    )
    parser.add_argument(
        "--activities", default="data/activities.csv", help="Local CSV snapshot"
    )
    parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default=DEFAULT_FORMAT,
        help="Document format (default: all four)",
    )
    parser.add_argument("--output-dir", default="gen", help="Output directory")
    parser.add_argument(
        "--output", help="Output TeX filename (requires a single --format)"
    )
    args = parser.parse_args(argv)
    if args.output is not None and args.format == "all":
        parser.error("--output requires a single --format; use --output-dir for all")
    try:
        # Resolve once: a multi-layout invocation must use the same date.
        as_of = resolve_date(args.date)
        for format in selected_formats(args.format):
            destination = (
                args.output
                if args.output is not None
                else project_path(args.output_dir) / f"{OUTPUT_STEMS[format]}.tex"
            )
            output = generate(
                output=destination,
                activities=args.activities,
                as_of=as_of,
                format=format,
            )
            print(f"Generated {output}")
    except (OSError, ValueError, KeyError, csv.Error, TemplateError) as error:
        print(f"Generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
