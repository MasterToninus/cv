# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_academic_dossier.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Offline checks for the academic dossier and selection of CV output formats.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Offline checks for the academic dossier and selection of CV output formats."""

import importlib
import re
import shutil
import subprocess
import tempfile
import unittest
import warnings
from copy import deepcopy
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cvgen.acquisition import load_activities, load_bibliography, load_config
from cvgen.processing import assemble_cv
from cvgen.rendering import render_cv

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 4)
ACADEMIC_STEM = "Cv-Academic-Dossier"
CURRENT_STEM = "Cv-Academic"
INDUSTRY_STEM = "Cv-Industry"
PUBLICATIONS_STEM = "All-Publications"


def reference_source():
    """Find the archived typography reference independently of generated files."""
    # Keep the fixture independent of whether manual sources are archived.
    for directory in ("old-tailored", "hand-tailored"):
        path = ROOT / directory / "2025-Cv-Dossier-Publications.tex"
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise AssertionError("The original academic dossier source is missing")


def without_comments(document):
    """Ignore editorial notes when inspecting the reference's visible content."""
    return "\n".join(
        line for line in document.splitlines() if not line.lstrip().startswith("%")
    )


def macro_definition(document, name):
    """Extract a complete reference macro, including nested TeX argument groups."""
    declaration = re.search(
        r"\\newcommand\{\\" + re.escape(name) + r"\}(?:\[[^\]]*\])*", document
    )
    if declaration is None:
        raise AssertionError(f"Missing LaTeX macro: {name}")
    start = document.index("{", declaration.end())
    depth = 0
    for index in range(start, len(document)):
        if document[index] == "{":
            depth += 1
        elif document[index] == "}":
            depth -= 1
            if depth == 0:
                return re.sub(r"\s+", "", document[declaration.start() : index + 1])
    raise AssertionError(f"Unclosed LaTeX macro: {name}")


class AcademicDossierRenderingTests(unittest.TestCase):
    """Protect reference typography while allowing data-driven substitutions."""

    @classmethod
    def setUpClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cls.data = assemble_cv(
                load_config(ROOT / "data/cv.yaml"),
                load_activities(ROOT / "data/activities.csv"),
                load_bibliography(ROOT / "data/publications.bib"),
                AS_OF,
            )

    def render(self, data=None, **kwargs):
        return render_cv(
            self.data if data is None else data,
            ROOT / "tmpl",
            AS_OF,
            format="academic-dossier",
            **kwargs,
        )

    def test_dossier_contains_the_reference_sections_in_academic_order(self):
        rendered = self.render()
        sections = (
            r"\addcontentsline{toc}{section}{Resume}",
            r"\block{Work Experience}",
            r"\block{Education}",
            r"\blockNp{Diplomas}",
            r"\section*{Teaching \& Administrative Activities}",
            r"\section*{Research Activities}",
            r"\block{Publications}",
            r"\block{Research Stays}",
            r"\blockNp{Talks \& Communications}",
            r"\block{Workshops \& Conferences}",
            r"\block{Post-Graduate Training}",
        )
        # Summary tables also contain labels such as "Research Stays"; inspect
        # heading commands rather than the first occurrence of those words.
        positions = [rendered.index(section) for section in sections]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(rendered.index(r"\tableofcontents"), positions[0])
        self.assertNotIn("~{{", rendered)
        self.assertNotIn("~{", rendered)

    def test_reference_typography_and_entry_primitives_are_preserved(self):
        reference = reference_source()
        rendered = self.render()
        reference_preamble = reference.split(r"\begin{document}", 1)[0]
        preamble, body = rendered.split(r"\begin{document}", 1)
        # These definitions control the original heading rules, paragraph
        # spacing, 90/10 activity columns, and filled/remainder skill bars.
        for name in (
            "crule",
            "progbar",
            "block",
            "Block",
            "blockNp",
            "longvoice",
            "voice",
            "skill",
            "skillbar",
            "txt",
        ):
            with self.subTest(macro=name):
                self.assertEqual(
                    macro_definition(preamble, name),
                    macro_definition(reference_preamble, name),
                )
        packages = lambda source: [
            re.sub(r"\s+", "", package)
            for package in re.findall(r"\\usepackage(?:\[[^\]]*\])?\{[^}]+\}", source)
        ]
        self.assertEqual(packages(preamble), packages(reference_preamble))
        expected_titleformat = reference_preamble[
            reference_preamble.index(
                r"\titleformat{\section}"
            ) : reference_preamble.index(r"\title{Curriculum Vitae}")
        ]
        self.assertIn(
            re.sub(r"\s+", "", expected_titleformat), re.sub(r"\s+", "", preamble)
        )
        self.assertEqual(
            re.findall(r"\\begin\{tcolorbox\}(?:\[[^\]]*\])?", body),
            [r"\begin{tcolorbox}"] * 2,
        )
        self.assertNotIn(r"\dossierchapter", rendered)
        self.assertNotIn(r"\hypersetup{colorlinks=true", rendered)

    def test_original_contents_and_page_breaks_are_not_expanded_into_new_chapters(self):
        rendered = self.render()
        body = rendered.split(r"\begin{document}", 1)[1]
        entries = re.findall(r"\\addcontentsline\{toc\}\{section\}\{([^}]+)\}", body)
        self.assertEqual(
            entries,
            ["Resume", "Teaching and Administrative Activities", "Research Activities"],
        )
        activities = body.split(r"\blockNp{Talks \& Communications}", 1)[1]
        self.assertIn(r"\block{Workshops \& Conferences}", activities)
        self.assertIn(r"\block{Post-Graduate Training}", activities)
        self.assertNotRegex(activities, r"\\(?:newpage|clearpage|blockNp)\b")

    def test_original_skill_selection_and_omitted_sections_are_preserved(self):
        reference = reference_source()
        reference_body = without_comments(reference.split(r"\begin{document}", 1)[1])
        body = self.render().split(r"\begin{document}", 1)[1]
        skill_labels = lambda source: re.findall(r"\\skillbar\s*\{([^}]+)\}", source)
        self.assertEqual(len(skill_labels(reference_body)), 8)
        self.assertEqual(skill_labels(body), skill_labels(reference_body))
        self.assertNotIn(r"\block{Referees}", body)
        self.assertNotIn("Exams supervision", body)

    def test_every_publication_is_cited_once_in_its_existing_group_order(self):
        rendered = self.render()
        expected = [
            publication["key"]
            for kind in ("published", "thesis", "preprints", "drafts")
            for publication in self.data["pub_details"]
            if publication["type"] == kind
        ]
        self.assertEqual(len(expected), 15)
        self.assertEqual(re.findall(r"\\fullcite\{([^}]+)\}", rendered), expected)

    def test_profile_and_contacts_are_rendered_from_current_data(self):
        data = deepcopy(self.data)
        data.update(
            name={"first": "TemplateSentinel", "last": "Dynamic"},
            email="dossier@example.test",
            phone="12345",
            orcid="0000-0000-0000-0001",
            site="https://example.test/dossier",
            github="dossier-user",
            titleinfo="Dynamic profile sentinel.",
            address=["Dynamic institute sentinel", "Dynamic postal address sentinel"],
            coverstatement="Dynamic research statement sentinel.",
            keywords=["Dynamic keyword sentinel"],
        )
        rendered = self.render(data, bibliography_path="../../references/library.bib")
        for value in (
            "TemplateSentinel",
            "DYNAMIC",
            "dossier@example.test",
            "12345",
            "https://example.test/dossier",
            "dossier-user",
            "Dynamic profile sentinel.",
            "Dynamic research statement sentinel.",
            "Dynamic institute sentinel",
            "Dynamic postal address sentinel",
            "Dynamic keyword sentinel",
            "November 4, 2026",
        ):
            with self.subTest(value=value):
                self.assertIn(value, rendered)
        self.assertIn(r"\addbibresource{../../references/library.bib}", rendered)
        self.assertIn(
            r"\href{https://orcid.org/0000-0000-0000-0001}{0000-0000-0000-0001}",
            rendered,
        )
        # Personal details, including the cover address, come from the supplied
        # data rather than being fixed in the template.
        self.assertNotIn("Antonio Michele MITI", rendered)
        self.assertNotIn("Piazzale Aldo Moro", rendered)
        self.assertNotIn("00185 Roma", rendered)
        self.assertNotIn(
            "Postdoctoral researcher in mathematics specializing", rendered
        )

    def test_both_academic_layouts_omit_empty_publication_groups(self):
        groups = (
            ("published", "Published"),
            ("thesis", "Theses"),
            ("preprints", "Preprints"),
            ("drafts", "In preparation"),
        )
        for format in ("current", "academic-dossier"):
            # None removes every group; each other case removes only one.
            # A category can become empty naturally when its last draft moves.
            for omitted in (None, *(kind for kind, _ in groups)):
                with self.subTest(format=format, omitted=omitted):
                    data = deepcopy(self.data)
                    data["pub_details"] = [
                        entry
                        for entry in data["pub_details"]
                        if omitted is not None and entry["type"] != omitted
                    ]
                    rendered = render_cv(data, ROOT / "tmpl", AS_OF, format=format)
                    self.assertNotRegex(
                        rendered, r"\\begin\{itemize\}\s*\\end\{itemize\}"
                    )
                    for kind, title in groups:
                        heading = rf"\subsection*{{{title}}}"
                        if omitted is None or kind == omitted:
                            self.assertNotIn(heading, rendered)
                        else:
                            self.assertIn(heading, rendered)

    def test_activity_order_and_input_data_are_preserved(self):
        data = deepcopy(self.data)
        sample = deepcopy(data["talks"][0])
        data["talks"] = [
            dict(sample, Event_Title=title)
            for title in (
                "First activity sentinel",
                "Second activity sentinel",
            )
        ]
        original = deepcopy(data)
        rendered = self.render(data)
        self.assertLess(
            rendered.index("First activity sentinel"),
            rendered.index("Second activity sentinel"),
        )
        self.assertEqual(data, original)

    def test_link_urls_escape_special_characters_once_without_mutating_data(self):
        raw_url = "https://example.test/award?grant=one&rate=10%25#details"
        escaped_url = r"https://example.test/award?grant=one\&rate=10\%25\#details"
        results = []
        for url in (raw_url, escaped_url):
            with self.subTest(url=url):
                data = deepcopy(self.data)
                data["awd"] = [
                    dict(
                        data["awd"][0],
                        what="Escaping regression sentinel",
                        where="Test institution",
                        url=url,
                    )
                ]
                original = deepcopy(data)
                rendered = self.render(data)
                hrefs = re.findall(
                    r"\\voice\s*\{Escaping regression sentinel\}\s*\{[^}]*\}\s*\{Test institution\}\s*\{([^}]+)\}",
                    rendered,
                )
                self.assertEqual(hrefs, [escaped_url])
                self.assertNotIn(r"\\", hrefs[0])
                self.assertEqual(data, original)
                results.append(rendered)
        self.assertEqual(results[0], results[1])

    def test_current_or_last_position_is_not_duplicated_in_work_experience(self):
        data = deepcopy(self.data)
        sample = deepcopy(data["previousjobs"][0])
        data["previousjobs"] = [
            dict(sample, what=title)
            for title in (
                "Last position sentinel",
                "Earlier position sentinel",
            )
        ]
        data["currentjobs"] = []
        rendered = self.render(data)
        self.assertIn(r"\block{Last Position}", rendered)
        self.assertNotIn(r"\block{Current Position}", rendered)
        self.assertEqual(rendered.count("Last position sentinel"), 1)
        self.assertEqual(rendered.count("Earlier position sentinel"), 1)

        data["currentjobs"] = [dict(sample, what="Current position sentinel")]
        rendered = self.render(data)
        self.assertIn(r"\block{Current Position}", rendered)
        self.assertNotIn(r"\block{Last Position}", rendered)
        for title in (
            "Current position sentinel",
            "Last position sentinel",
            "Earlier position sentinel",
        ):
            self.assertEqual(rendered.count(title), 1)

    def test_explicit_current_format_matches_the_legacy_default(self):
        default = render_cv(self.data, ROOT / "tmpl", AS_OF)
        explicit = render_cv(self.data, ROOT / "tmpl", AS_OF, format="current")
        self.assertEqual(default, explicit)

    def test_unknown_format_fails_instead_of_silently_rendering_a_different_cv(self):
        with self.assertRaises(ValueError):
            render_cv(self.data, ROOT / "tmpl", AS_OF, format="unknown")


class AcademicDossierGenerationTests(unittest.TestCase):
    """Check API filenames, isolated inputs and CLI selection without network I/O."""

    def test_default_api_generates_the_exact_academic_output_name(self):
        module = importlib.import_module("generate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("data", "tmpl"):
                shutil.copytree(ROOT / folder, root / folder)
            with (
                patch.object(module, "ROOT", root),
                patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("unexpected network"),
                ),
                warnings.catch_warnings(),
            ):
                warnings.simplefilter("ignore", UserWarning)
                destination = module.generate(as_of=AS_OF)
            self.assertEqual(destination, root / "gen" / (CURRENT_STEM + ".tex"))
            self.assertTrue(destination.is_file())
            self.assertFalse((root / "gen/cv.tex").exists())
            self.assertFalse((root / "gen/Cv-Academic-Home.tex").exists())

    def test_selected_dossier_generates_a_separate_tex_file_without_network(self):
        module = importlib.import_module("generate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("data", "tmpl"):
                shutil.copytree(ROOT / folder, root / folder)
            with (
                patch.object(module, "ROOT", root),
                patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("unexpected network"),
                ),
                warnings.catch_warnings(),
            ):
                warnings.simplefilter("ignore", UserWarning)
                destination = module.generate(format="academic-dossier", as_of=AS_OF)
            self.assertEqual(destination, root / "gen" / (ACADEMIC_STEM + ".tex"))
            rendered = destination.read_text(encoding="utf-8")
            self.assertIn(r"\tableofcontents", rendered)
            self.assertIn(r"\addbibresource{../data/publications.bib}", rendered)
            self.assertFalse((root / "gen" / (CURRENT_STEM + ".tex")).exists())

    def test_generator_cli_defaults_to_all_formats_and_accepts_single_output(self):
        module = importlib.import_module("generate")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = (
                (
                    ["--date", "2026-11-04", "--output-dir", str(root)],
                    ["current", "academic-dossier", "industry", "publications"],
                    [
                        root / (CURRENT_STEM + ".tex"),
                        root / (ACADEMIC_STEM + ".tex"),
                        root / (INDUSTRY_STEM + ".tex"),
                        root / (PUBLICATIONS_STEM + ".tex"),
                    ],
                ),
                (
                    [
                        "--date",
                        "2026-11-04",
                        "--format",
                        "academic-dossier",
                        "--output",
                        str(root / "custom.tex"),
                    ],
                    ["academic-dossier"],
                    [root / "custom.tex"],
                ),
            )
            for arguments, expected_formats, expected_outputs in cases:
                with (
                    self.subTest(arguments=arguments),
                    patch.object(
                        module, "generate", side_effect=lambda **kw: Path(kw["output"])
                    ) as generate,
                    patch("sys.stdout", new_callable=StringIO),
                ):
                    self.assertEqual(module.main(arguments), 0)
                self.assertEqual(
                    [call.kwargs["format"] for call in generate.call_args_list],
                    expected_formats,
                )
                self.assertEqual(
                    [Path(call.kwargs["output"]) for call in generate.call_args_list],
                    expected_outputs,
                )
                self.assertTrue(
                    all(
                        call.kwargs["as_of"] == AS_OF
                        for call in generate.call_args_list
                    )
                )

    def test_one_explicit_output_cannot_overwrite_multiple_formats(self):
        module = importlib.import_module("generate")
        with (
            patch.object(module, "generate") as generate,
            patch("sys.stderr", new_callable=StringIO),
        ):
            with self.assertRaises(SystemExit) as error:
                module.main(["--format", "all", "--output", "same.tex"])
        self.assertEqual(error.exception.code, 2)
        generate.assert_not_called()


class AcademicDossierBuildTests(unittest.TestCase):
    """Inspect orchestration commands; rendering is covered independently above."""

    def test_build_selects_all_documents_by_default_and_can_compile_only_the_dossier(
        self,
    ):
        import build

        module = importlib.import_module("generate")
        tools = {"pdflatex": "pdflatex", "biber": "biber"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for selection, formats, stems in (
                (
                    [],
                    ["current", "academic-dossier", "industry", "publications"],
                    [CURRENT_STEM, ACADEMIC_STEM, INDUSTRY_STEM, PUBLICATIONS_STEM],
                ),
                (
                    ["--format", "academic-dossier"],
                    ["academic-dossier"],
                    [ACADEMIC_STEM],
                ),
            ):
                with (
                    self.subTest(selection=selection),
                    patch("build.check_tools", return_value=tools),
                    patch.object(
                        module, "generate", side_effect=lambda **kw: Path(kw["output"])
                    ) as generate,
                    patch(
                        "build.compile_pdf", return_value=root / "example.pdf"
                    ) as compile_pdf,
                    patch("sys.stdout", new_callable=StringIO),
                ):
                    self.assertEqual(
                        build.main(
                            [
                                "--date",
                                "2026-11-04",
                                "--output-dir",
                                str(root),
                                *selection,
                            ]
                        ),
                        0,
                    )
                self.assertEqual(
                    [call.kwargs["format"] for call in generate.call_args_list], formats
                )
                self.assertEqual(
                    [call.kwargs["stem"] for call in compile_pdf.call_args_list], stems
                )

    def test_dossier_compilation_uses_its_own_tex_biber_job_and_log(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / (ACADEMIC_STEM + ".pdf")).write_bytes(b"existing test result")
            result = subprocess.CompletedProcess([], 0, stdout=b"compiler output\n")
            with (
                patch("build.subprocess.run", return_value=result) as run,
                patch("build.find_empty_body_pages", return_value=()),
                patch("sys.stdout", new_callable=StringIO),
            ):
                pdf = build.compile_pdf(
                    root,
                    {"pdflatex": "pdflatex", "biber": "biber"},
                    "1793793600",
                    stem=ACADEMIC_STEM,
                )
            self.assertEqual(pdf, root / (ACADEMIC_STEM + ".pdf"))
            self.assertEqual(
                [call.args[0][-1] for call in run.call_args_list],
                [
                    ACADEMIC_STEM + ".tex",
                    ACADEMIC_STEM,
                    ACADEMIC_STEM + ".tex",
                    ACADEMIC_STEM + ".tex",
                ],
            )
            self.assertTrue((root / (ACADEMIC_STEM + ".build.log")).is_file())
            self.assertFalse((root / "build.log").exists())

    def test_clean_removes_all_known_families_and_keeps_other_tex_files(self):
        import build

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = [
                root / (stem + suffix)
                for stem in (
                    CURRENT_STEM,
                    ACADEMIC_STEM,
                    INDUSTRY_STEM,
                    PUBLICATIONS_STEM,
                    "cv",
                    "Cv-Academic-Home",
                )
                for suffix in (".tex", ".pdf", ".bcf", ".toc")
            ]
            generated += [
                root / "build.log",
                *[
                    root / (stem + ".build.log")
                    for stem in (
                        CURRENT_STEM,
                        ACADEMIC_STEM,
                        INDUSTRY_STEM,
                        PUBLICATIONS_STEM,
                    )
                ],
            ]
            preserved = root / "reference.tex"
            for target in [*generated, preserved]:
                target.write_text("sample", encoding="utf-8")
            build.clean(root)
            self.assertTrue(all(not target.exists() for target in generated))
            self.assertTrue(preserved.is_file())


if __name__ == "__main__":
    unittest.main()
