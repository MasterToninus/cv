# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_publications.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Verify complete, BibTeX-only publication-list generation.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Test grouping, editorial annotations, and independence.
# | 20261105  Miti/Codex   Check the Final Preparation section heading.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Checks for a standalone publication list sourced only from BibTeX."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest.mock import patch

from pybtex.database import BibliographyData, Entry, Person

import generate
from cvgen.acquisition import load_bibliography
from cvgen.helpers.formats import OUTPUT_STEMS, selected_formats
from cvgen.helpers.publications import prepare_publications
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 4)


class PublicationPreparationTests(unittest.TestCase):
    """Check grouping and citation options independently of a TeX compiler."""

    def test_every_type_is_visible_once_in_reverse_source_order_without_mutation(self):
        bibliography = BibliographyData(
            entries={
                "later-in-file": Entry("article"),
                "thesis": Entry("mastersthesis"),
                "first-preprint": Entry("preprint"),
                "earlier-date": Entry("book", fields={"year": "1999"}),
                "second-preprint": Entry("unpublished"),
                "work-in-progress": Entry("draft"),
                "unclassified": Entry("misc"),
            }
        )
        original = deepcopy(bibliography)
        sections = prepare_publications(bibliography)["publication_groups"]
        self.assertEqual(
            [section["title"] for section in sections],
            [
                "Published",
                "Theses",
                "Submitted to Peer-review",
                "Final Preparation",
                "Other Publications",
            ],
        )
        self.assertEqual(
            [[item["key"] for item in section["entries"]] for section in sections],
            [
                ["earlier-date", "later-in-file"],
                ["thesis"],
                ["second-preprint", "first-preprint"],
                ["work-in-progress"],
                ["unclassified"],
            ],
        )
        self.assertEqual(sections[1]["start"], 2)
        self.assertEqual(bibliography, original)

    def test_real_bibliography_includes_all_degrees_and_editorial_annotation(self):
        bibliography = load_bibliography(ROOT / "data/publications.bib")
        context = prepare_publications(bibliography)
        groups = context["publication_groups"]
        self.assertEqual([len(group["entries"]) for group in groups], [7, 3, 2, 3])
        rendered = render_cv(context, ROOT / "tmpl", AS_OF, format="publications")
        keys = re.findall(r"\\fullcite\{([^}]+)\}", rendered)
        self.assertEqual(len(keys), len(bibliography.entries))
        self.assertEqual(set(keys), set(bibliography.entries))
        self.assertEqual(
            keys,
            [
                "Luongo2025",
                "Miti2025",
                "Blacker2024",
                "Miti2024",
                "Miti2021c",
                "Miti2021a",
                "Miti2020",
                "Miti2021b",
                "Miti2015",
                "Miti2010",
                "Fiorenza2026",
                "Luongo2024",
                "Basu2026",
                "Miti2026",
                "DAgostino2026",
            ],
        )
        self.assertIn(r"\section*{Final Preparation}", rendered)
        self.assertNotIn(r"\section*{In Preparation}", rendered)
        self.assertIn(r"\setcounter{enumi}{7}", rendered)
        self.assertIn(
            r"\footnote{This is a reduced version of \cite{Luongo2024}", rendered
        )
        self.assertIn(r"\date{November 4, 2026}", rendered)
        self.assertEqual(context["max_name_count"], 4)
        for option in ("maxbibnames", "minbibnames", "maxcitenames", "mincitenames"):
            self.assertIn(f"{option}=4", rendered)

    def test_full_name_limits_follow_person_lists_without_an_arbitrary_cap(self):
        # Exceed the former limit of 99; a larger editor list also verifies
        # that the limit covers every person role, rather than authors alone.
        bibliography = BibliographyData(
            entries={
                "large-collaboration": Entry(
                    "article",
                    persons={
                        "author": [
                            Person(f"Author{number}, Given") for number in range(101)
                        ],
                    },
                ),
                "edited-volume": Entry(
                    "book",
                    persons={
                        "editor": [
                            Person(f"Editor{number}, Given") for number in range(103)
                        ],
                    },
                ),
            }
        )
        original = deepcopy(bibliography)
        context = prepare_publications(bibliography)
        self.assertEqual(context["max_name_count"], 103)
        self.assertEqual(bibliography, original)
        rendered = render_cv(context, ROOT / "tmpl", AS_OF, format="publications")
        for option in ("maxbibnames", "minbibnames", "maxcitenames", "mincitenames"):
            self.assertIn(f"{option}=103", rendered)

    def test_empty_bibliography_has_valid_positive_name_limits(self):
        self.assertEqual(prepare_publications(BibliographyData())["max_name_count"], 1)

    def test_annotations_are_data_driven_and_relative_bib_path_is_rendered(self):
        bibliography = BibliographyData(
            entries={
                "new-record": Entry(
                    "article",
                    fields={"annotation": r"An editorial note with \emph{context}."},
                ),
            }
        )
        rendered = render_cv(
            prepare_publications(bibliography),
            ROOT / "tmpl",
            AS_OF,
            bibliography_path="../../references/custom.bib",
            format="publications",
        )
        self.assertIn(
            r"\fullcite{new-record}\footnote{An editorial note with \emph{context}.}",
            rendered,
        )
        self.assertIn(r"\addbibresource{../../references/custom.bib}", rendered)
        self.assertNotIn("Luongo2025", rendered)
        self.assertNotIn("Other Publications", rendered)
        self.assertNotIn(r"\section*{Theses}", rendered)
        self.assertIn(r"\step[typesource=preprint, typetarget=unpublished]", rendered)
        self.assertIn(r"\step[typesource=draft, typetarget=unpublished]", rendered)


class PublicationGenerationTests(unittest.TestCase):
    """Exercise real file loading while forbidding unrelated data sources."""

    def test_generation_works_without_yaml_csv_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            # This isolated root contains only inputs this format may read;
            # the guards identify any accidental YAML or CSV acquisition.
            shutil.copyfile(
                ROOT / "data/publications.bib", root / "data/publications.bib"
            )
            shutil.copytree(ROOT / "tmpl", root / "tmpl")
            with (
                patch.object(generate, "ROOT", root),
                patch.object(
                    generate,
                    "load_config",
                    side_effect=AssertionError("unexpected YAML read"),
                ),
                patch.object(
                    generate,
                    "load_activities",
                    side_effect=AssertionError("unexpected CSV read"),
                ),
                patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("unexpected network"),
                ),
            ):
                destination = generate.generate(format="publications", as_of=AS_OF)
            self.assertEqual(destination, root / "gen/All-Publications.tex")
            self.assertEqual(
                len(
                    re.findall(r"\\fullcite\{", destination.read_text(encoding="utf-8"))
                ),
                15,
            )
            self.assertEqual(OUTPUT_STEMS["publications"], "All-Publications")
            self.assertIn("publications", selected_formats("all"))


class DefaultCommandLineTests(unittest.TestCase):
    """Verify both public scripts produce all four real TeX documents."""

    def test_both_commands_generate_four_real_sources_without_a_format_option(self):
        expected = {
            "Cv-Academic.tex",
            "Cv-Academic-Dossier.tex",
            "Cv-Industry.tex",
            "All-Publications.tex",
        }
        # Exercise actual entry points from outside the repository, without
        # mocking generation or requiring the TeX compiler for this test.
        environment = dict(os.environ, SOURCE_DATE_EPOCH="1793793600")
        for script, extra in (("generate.py", []), ("build.py", ["--tex-only"])):
            with (
                self.subTest(script=script),
                tempfile.TemporaryDirectory() as directory,
            ):
                target = Path(directory) / "output"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / script),
                        *extra,
                        "--output-dir",
                        str(target),
                    ],
                    cwd=directory,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual({path.name for path in target.glob("*.tex")}, expected)
                for name in expected:
                    document = (target / name).read_text(encoding="utf-8")
                    self.assertIn(r"\begin{document}", document)
                    self.assertNotIn("~{{", document)


if __name__ == "__main__":
    unittest.main()
