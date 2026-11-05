# LaTeX CV Generator

[![CV build](https://img.shields.io/github/actions/workflow/status/MasterToninus/cv/build-cv.yml?branch=master&event=push&label=CV%20build&logo=github&style=flat)](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml)
[![Link check](https://img.shields.io/github/actions/workflow/status/MasterToninus/cv/check-links.yml?branch=master&event=workflow_run&label=links&logo=github&style=flat)](https://github.com/MasterToninus/cv/actions/workflows/check-links.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white&style=flat)](docs/build.md#quick-start)
[![Four PDF formats](https://img.shields.io/badge/PDF-4%20formats-2e7d32?style=flat)](#download-generated-pdfs)

Generate Antonio Michele Miti's academic CV, academic dossier, industry CV, and complete publication list from shared YAML, CSV, and BibTeX data using Python, Jinja2, and LaTeX.

Visit [my webpage](https://www.antoniomiti.it/) for the [published CV](https://www.dropbox.com/scl/fi/w6l4vkwenl8780v0kewal/cv.pdf?dl=0&rlkey=dggzb4t7h76nsqts71qt80oyi&st=kvtie7my).

## Download generated PDFs

Open the [latest successful builds on `master`](https://github.com/MasterToninus/cv/actions/workflows/build-cv.yml?query=branch%3Amaster+is%3Asuccess), select the newest run, and download the matching artifact:

| Document | Artifact |
| --- | --- |
| Academic CV | `Cv-Academic.pdf` |
| Academic dossier | `Cv-Academic-Dossier.pdf` |
| Industry CV | `Cv-Industry.pdf` |
| Complete publication list | `All-Publications.pdf` |
| All four PDFs in one ZIP | `Cv-All-PDFs` |

The four individual artifacts download directly as PDFs; `Cv-All-PDFs` downloads as a ZIP containing all four. Official GitHub downloads require signing in; artifacts are retained for 90 days. The [link-check workflow](https://github.com/MasterToninus/cv/actions/workflows/check-links.yml) publishes a separate `Cv-Link-Report` with broken and unverified URLs.

## Repository layout

| Folder | Contents |
| --- | --- |
| [`data/`](data/README.md) | Shared CV data and bibliography |
| [`cvgen/`](cvgen/README.md) | Acquisition, processing, rendering, and helpers |
| [`tmpl/`](tmpl/README.md) | Main Jinja/LaTeX templates and shared macros |
| [`tests/`](tests/README.md) | Regression and behavior checks |
| [`hand-tailored/`](hand-tailored/README.md) | Independently maintained standalone sources |
| [`ai-tailored/`](ai-tailored/README.md) | Application-specific sources prepared with AI assistance |
| [`old-tailored/`](old-tailored/README.md) | Historical and reference documents |

## Documentation

- [Setup, compilation, testing, and link checking](docs/build.md)
- [Data contract](docs/data.md) and [template reference](docs/templates.md)
- [Documentation index](docs/README.md), [agent instructions](AGENTS.md), and [roadmap](docs/roadmap.md)

Early versions by [VittorioErba](https://github.com/vittorioerba), inspired by [bamos/cv](https://github.com/bamos/cv). ChatGPT assisted with code structure and documentation.
