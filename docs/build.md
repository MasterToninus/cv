# Architecture and build details

## Pipeline

The command-line entry points coordinate three stages:

1. `cvgen/acquisition.py` reads YAML, CSV, and BibTeX. Its explicit refresh operation is the only network acquisition step.
2. `cvgen/processing.py` assembles presentation data, activity categories, publication groups, and counters without fetching data or writing files.
3. `cvgen/rendering.py` selects a Jinja template and returns LaTeX. `generate.py` writes the result; `build.py` owns tool checks, compilation, and generated-file cleanup.

Supporting modules are grouped under `cvgen/helpers/`: `clock.py` resolves the build date, `formats.py` holds format/output names, `paths.py` resolves repository-relative paths, `industry.py` selects industry presentation data, `publications.py` groups bibliography-only records, and `pagination.py` detects empty pages conservatively. Internal imports use this package, for example `cvgen.helpers.clock` and `cvgen.helpers.publications`. The root-level `getactivities.py` remains a small compatibility adapter for older callers; new code uses the pipeline stages and their helper package.

`cvgen/helpers/formats.py` is the shared registry of all four documents and the command-line default, `all`. Both `python build.py` and `python generate.py` use this default; Make explicitly selects its `all` target. Selecting one document requires `--format` (or `make FORMAT=...`). Both entry points use the path resolver in `cvgen/helpers/paths.py`, so relative arguments are interpreted from the repository root when invoked from another working directory.

The `publications` format bypasses YAML and activities: acquisition loads only `data/publications.bib`, `cvgen/helpers/publications.py` prepares its groups, and Jinja renders `tmpl/All-Publications_tmpl.tex`. Citation keys come from the bibliography entries, rather than a manually maintained selection. Its output is `gen/All-Publications.tex/pdf`.

The four main Jinja templates remain directly under `tmpl/`. Shared sections and entry macros live under `tmpl/helpers/` and are loaded through paths such as `helpers/section_tmpl.tex` and `helpers/academic_macros.tex` relative to the template directory.

The original academic layout preserves its existing activity order, categories, counters, and publication grouping. The dossier uses the same processed data, including the separate `edu` and `diplomas` lists. Industry-specific selections are derived without changing the shared mapping. Sorting or classification changes should be reviewed as content changes.

## Toolchain

Install the exact Python dependencies in [`requirements.txt`](../requirements.txt). It includes the runtime and transitive pins used for the build. The optional `Pipfile` is not a locked replacement for those pins.

TeX Live or MiKTeX must provide `pdflatex` and `biber` on `PATH`. An industry-only build needs only `pdflatex`:

```sh
python build.py --check-tools --format industry
```

The templates use packages including `fontawesome`, `academicons`, `biblatex` with the IEEE style, `geometry`, `hyperref`, `fancyhdr`, `lastpage`, `tabularx`, and `enumitem`. The dossier also uses `tcolorbox`, `orcidlink`, and `titlesec`. No system Make, Perl, or `latexmk` is required.

## Reproducibility

Use an explicit reference date:

```sh
python build.py --date 2026-11-04
```

The date controls generated dates, scheduled-event labels, and experience counters. `--date` takes precedence over `SOURCE_DATE_EPOCH` and fixes the TeX build epoch to noon UTC on that date. Without it, a supplied `SOURCE_DATE_EPOCH` supplies the date and epoch; otherwise the build uses today's date and noon UTC.

For repeatable results, retain the same source files, activities snapshot, reference date, Python dependencies, and TeX/font versions. Byte-for-byte PDF reproduction depends on the TeX toolchain and fonts as well as the versioned inputs. Ordinary generation reads local data; refreshes are deliberate, separate operations.

## Compilation and logs

Each invocation regenerates the selected sources. Academic formats and the standalone publication list run `pdflatex`, `biber`, and two further `pdflatex` passes. Industry runs three `pdflatex` passes without Biber. A failed command stops the build. Logs are written beside each output as `<stem>.build.log`.

If compilation or PDF verification fails, the previous PDF is restored. When no previous PDF exists, an incomplete new PDF is removed. TeX sources, auxiliary files, and logs remain available for diagnosis.

For the dossier, `pypdf` checks the completed PDF for pages containing only headers and footers. If any are found, the build writes `Cv-Academic-Dossier.skip.tex` and repeats compilation to suppress those pages within LaTeX. This keeps the layout of retained pages and updates links, table of contents, page numbers, and totals. Body text, drawings, images, and body annotations retain a page, including a short final page. Every normal build discards the previous skip list and detects pages again.

The dossier preserves the reference's cover, contact labels, link borders, title sizes, columns, tables, and spacing commands. It keeps the original three-entry table of contents and selection of eight computer skills; referees and exam supervision remain omitted. The address box reads `address` from `data/cv.yaml`. Updated text lengths can still change pagination.

Existing layout or bibliography-driver warnings may appear even when compilation succeeds. Consult the log when reviewing a change; a successful exit alone does not replace visual inspection.

## GitHub Actions

The [Build CV PDFs workflow](../.github/workflows/build-cv.yml) runs on pushes to `master`, pull requests targeting `master`, and manual dispatch. It uses Ubuntu 24.04 and Python 3.11, installs the exact runtime pins, runs the test suite, and invokes the normal `python build.py` entry point. It does not refresh activities or compile tailored application documents.

Its TeX packages are installed from Ubuntu: `biber`, `cm-super`, `texlive-bibtex-extra`, `texlive-fonts-extra`, `texlive-fonts-recommended`, and `texlive-latex-extra`. These provide the template fonts, IEEE bibliography style, and dossier packages. `SOURCE_DATE_EPOCH` comes from the checked-out commit's committer timestamp, including the tested merge commit on pull requests. The date is therefore fixed to the source rather than the runner's clock. Ubuntu package revisions can change; matching the exact PDF bytes also requires matching the TeX installation.

All Actions are official GitHub Actions pinned to full commit SHAs. The token has only `contents: read`, and checkout does not persist credentials. The workflow does not push, publish a release, or modify the inputs. New runs cancel an older run for the same ref.

After all four PDFs compile and pass a text/readability check, each PDF is uploaded as its own artifact: `Cv-Academic`, `Cv-Academic-Dossier`, `Cv-Industry`, and `All-Publications`. Each ZIP contains only that document's PDF. The run summary provides direct GitHub download links. PDF artifacts have a 90-day retention; failed-build logs are uploaded separately as `Cv-Build-Logs` for 7 days when available.

The [README download links](../README.md#download-generated-pdfs) open successful runs on `master`. Select the latest run and its artifact; GitHub requires signing in to download. Direct artifact URLs contain the run and artifact IDs and expire with the artifact, so they cannot be hardcoded as permanent links to the latest build. No third-party download service is used. Artifacts become available only after the workflow is pushed and succeeds on GitHub.

## Output cleanup

`python build.py --clean` removes only known generated CV files in the selected output directory. It does not recursively delete the directory or tailored documents.

Cleaning also recognizes the previous capitalization of dossier and publication-list filenames on case-sensitive filesystems. Bibliography inputs (`*.bib`) remain visible to Git; only generated `*-blx.bib` helper files are ignored.

The current academic output is `Cv-Academic.tex/pdf`. After its replacement PDF compiles successfully, the build removes products and logs using the legacy stems `cv` and `Cv-Academic-Home`. A failed compilation preserves them. Cleaning also recognizes those legacy names.

## Optional Make commands

The Makefile delegates to the same Python scripts:

| Command | Operation |
| --- | --- |
| `make` | Generate and compile all four documents |
| `make tex` | Generate TeX only |
| `make clean` | Remove known generated CV files |
| `make refresh-activities` | Refresh the local activities snapshot |
| `make check` | Check compilation tools |
| `make test` | Run the test suite |
| `make format` | Apply isort and Black to all Python sources, after installing `requirements-dev.txt` |
| `make format-check` | Check Python import order and formatting without editing files |

Use `make DATE=2026-11-04` to fix the reference date, `make FORMAT=academic-dossier` to select a layout, or `make PYTHON=python` to select the Python command.

[Back to the repository guide](../README.md)
