# LaTeX CV Generator

Generate Antonio Michele Miti's academic CV, academic dossier, industry CV, and standalone publication list from local data. Python and Jinja2 render the LaTeX sources; pdfLaTeX compiles the PDFs, with Biber for the academic formats and publication list.

View the [published CV (PDF)](https://www.dropbox.com/scl/fi/w6l4vkwenl8780v0kewal/cv.pdf?dl=0&rlkey=dggzb4t7h76nsqts71qt80oyi&st=kvtie7my) linked from [my webpage](https://www.antoniomiti.it/).

## Download generated PDFs

The [Build CV PDFs workflow](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml) runs the tests and compiles all four documents on pushes to `master`, pull requests targeting `master`, or a manual **Run workflow** request.

Open the [successful builds on `master`](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess), choose the latest run, and download the matching artifact from its **Artifacts** section or the links in its summary:

| Generated document | Artifact download page |
| --- | --- |
| Academic CV | [Cv-Academic](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess) |
| Academic dossier | [Cv-Academic-Dossier](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess) |
| Industry CV | [Cv-Industry](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess) |
| Complete publication list | [All-Publications](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess) |

Each artifact is a ZIP containing the corresponding PDF. Downloads use GitHub only and require signing in. Artifacts are retained for 90 days, subject to repository retention settings; run the workflow again if they expire. These links become usable after the workflow has been pushed and its first successful run has completed. They open the successful-run list because GitHub's direct artifact URLs change for every run.

The reference date is the source commit's UTC date, so rerunning the same commit retains its date. Builds use the committed data without refreshing the website snapshot. See [CI details](docs/build.md#github-actions).

## Quick start

Requirements: Python 3.10 or later, and TeX Live or MiKTeX with `pdflatex` and `biber` on `PATH`.

```sh
git clone https://github.com/MasterToninus/cv.git
cd cv
python -m venv .venv
```

Activate the environment:

- PowerShell: `.venv\Scripts\Activate.ps1`
- POSIX shell: `. .venv/bin/activate`

Then install the pinned dependencies, check the toolchain, and build:

```sh
python -m pip install -r requirements.txt
python build.py --check-tools
python build.py
```

The default command builds all four documents in `gen/`. Use `python generate.py` for all four TeX sources without compiling, or `make` as an optional build wrapper. No format option is needed. To fix the reference date, use `python build.py --date 2026-11-04` or set `SOURCE_DATE_EPOCH`; otherwise today's date is used.

The generator uses local inputs and works offline. A TeX installation may need network access for its initial package setup. Make, Perl, `latexmk`, Scopus credentials, and `pybliometrics` are not required.

## Generated documents

`python build.py` generates and compiles all four formats:

| Format option | LaTeX source | PDF |
| --- | --- | --- |
| `current` | `gen/Cv-Academic.tex` | `gen/Cv-Academic.pdf` |
| `academic-dossier` | `gen/Cv-Academic-Dossier.tex` | `gen/Cv-Academic-Dossier.pdf` |
| `industry` | `gen/Cv-Industry.tex` | `gen/Cv-Industry.pdf` |
| `publications` | `gen/All-Publications.tex` | `gen/All-Publications.pdf` |

The capitalization in these filenames is intentional. `current` remains the command-line/API name of the academic format; its output is named `Cv-Academic`.

```sh
python build.py --format current
python build.py --format academic-dossier
python build.py --format industry
python build.py --format publications
python build.py --tex-only
python build.py --output-dir gen-review --date 2026-11-04
python build.py --clean
```

Every build regenerates the selected TeX sources. Each document has its own auxiliary files and `*.build.log`. The academic dossier preserves the reference's style and postal-address box, uses updated local data, and automatically suppresses pages with no body content. The industry format compiles without Biber.

The `publications` format reads only `data/publications.bib`; it does not load YAML or activities. It automatically includes the bibliography entries in published, theses, submitted, and in-preparation groups, using the standalone reference's layout without a hardcoded list of citation keys.

Treat `gen/` as disposable output: edit the data or templates, then rebuild. The build does not compile the standalone documents in the tailored folders. See [build details](docs/build.md) for reproducibility, compilation passes, legacy output cleanup, and Make commands.

## What to edit

| Change | Location |
| --- | --- |
| Personal information, employment, education, sections, and format options | [`data/cv.yaml`](data/cv.yaml) |
| Publications and citation keys | [`data/publications.bib`](data/publications.bib) |
| Activities snapshot | [`data/activities.csv`](data/activities.csv) |
| Layout and reusable LaTeX/Jinja macros | [`tmpl/`](tmpl/README.md) |
| Data loading, transformations, and rendering | [`cvgen/`](cvgen/) |
| Shared Python support and format-specific presentation helpers | [`cvgen/helpers/`](cvgen/helpers/) |
| Reusable Jinja sections and entry macros | [`tmpl/helpers/`](tmpl/helpers/) |
| Standalone application-specific variants | [`hand-tailored/`](hand-tailored/README.md), [`ai-tailored/`](ai-tailored/README.md) |
| Historical/reference CVs and the extracted ERC CV | [`old-tailored/`](old-tailored/README.md) |

Normal generation never downloads the activities. Refresh the snapshot explicitly:

```sh
python build.py --refresh-activities
```

The download has a timeout and is validated before replacement. Failure preserves the previous snapshot. Review the CSV diff and rebuild before keeping an update. See [data documentation](data/README.md) for the input contract.

## Repository structure

```text
cv/
├── .github/workflows/
│   └── build-cv.yml          # Test, compile, and upload all four PDFs
├── data/                    # Shared, versioned CV inputs
├── cvgen/                   # The three pipeline stages
│   ├── acquisition.py
│   ├── processing.py
│   ├── rendering.py
│   └── helpers/             # Python support modules
│       ├── __init__.py
│       ├── clock.py         # Reference date and reproducible build epoch
│       ├── formats.py       # Format registry and default selection
│       ├── industry.py      # Industry presentation data
│       ├── pagination.py    # Conservative empty-page detection
│       ├── paths.py         # Shared repository-relative path resolution
│       └── publications.py  # Bibliography-only presentation data
├── tmpl/
│   ├── Cv-Academic_tmpl.tex
│   ├── Cv-Academic-Dossier_tmpl.tex
│   ├── Cv-Industry_tmpl.tex
│   ├── All-Publications_tmpl.tex
│   └── helpers/             # Reusable Jinja sections and macros
│       ├── academic_macros.tex
│       ├── industry_macros.tex
│       └── section_tmpl.tex
├── tests/                   # Regression and behavior checks
├── generate.py              # Generate TeX only; reusable Python entry point
├── build.py                 # Generate and compile PDFs; maintenance commands
├── getactivities.py         # Small compatibility adapter for older callers
├── Makefile                 # Optional wrapper around Python commands
├── requirements.txt         # Authoritative pinned build dependencies
├── Pipfile                  # Optional Pipenv package declarations
├── gen/                     # Generated files; ignored by Git
├── hand-tailored/            # Independently maintained standalone sources
├── ai-tailored/              # AI-assisted application document sources
├── old-tailored/             # Historical and reference documents
└── docs/                    # Build documentation, author confirmations, reviews
```

The three CVs share acquisition and processing, then select a renderer. The publication list follows a separate bibliography-only path. Tailored and archived documents remain independent snapshots. Their contents do not automatically enter the generated CVs.

For a new application, follow the [CV-tailoring workflow](AGENTS.md#tailoring-a-cv-for-a-position): validate YAML and `getactivities`, regenerate the current CV, and adapt a copy of its generated TeX in `ai-tailored/`.

Python support modules live in `cvgen/helpers/`; reusable template fragments live in `tmpl/helpers/`. The root keeps the two command-line entry points and the legacy `getactivities.py` adapter.

See the [documentation index](docs/README.md), [template contracts](tmpl/README.md), and the [roadmap](docs/roadmap.md).

## Development and verification

```sh
python -m unittest discover -s tests -v
python build.py --date 2026-11-04
```

The tests cover the processing pipeline, format selection, build behavior, dossier pagination, and the original academic-content regression. After a template or data change, inspect the affected PDFs as well. Review intentional content changes before updating any expected regression fingerprint.

Python sources use four-space indentation, Black formatting, and isort import ordering, configured in `pyproject.toml`. The optional development tools are separate from the runtime dependencies:

```sh
python -m pip install -r requirements-dev.txt
python -m isort build.py generate.py getactivities.py cvgen tests
python -m black build.py generate.py getactivities.py cvgen tests
python -m isort --check-only build.py generate.py getactivities.py cvgen tests
python -m black --check build.py generate.py getactivities.py cvgen tests
```

With GNU Make, `make format` and `make format-check` run those same commands. The default `make` target still generates and compiles all four documents.

The generator can also run independently:

```sh
python generate.py --date 2026-11-04
python generate.py --format academic-dossier --date 2026-11-04
python generate.py --format publications --date 2026-11-04
python generate.py --format current --output gen/Cv-Academic.tex
```

Both CLIs default to `--format all`; the Python `generate()` API defaults to one `current` document. `--output` selects a filename for a single format, while `--output-dir` selects a shared directory. Paths passed to the scripts are relative to the repository, so the scripts can be invoked by full path from another working directory.

## Acknowledgments

- Early versions due to [VittorioErba](https://github.com/vittorioerba).
- Inspired by [bamos/cv](https://github.com/bamos/cv).
- Thanks to ChatGPT for help improving documentation and code structure.

AI document names follow the [shared naming convention](AGENTS.md#ai-document-filenames-and-versions); their [review notes](docs/ai-tailored/README.md) live under `docs/ai-tailored/`. Historical document prefixes record their [first Git introduction](docs/document-origins.md).
