# Template reference

The three CV layouts share the same YAML, activities snapshot, bibliography, processed counters, and explicit reference date. The standalone publication layout reads only the bibliography. Templates change presentation; they do not fetch data or edit the inputs.

| Format | Main template | Supporting template |
| --- | --- | --- |
| `current` | `Cv-Academic_tmpl.tex` | `helpers/section_tmpl.tex` |
| `academic-dossier` | `Cv-Academic-Dossier_tmpl.tex` | `helpers/academic_macros.tex` |
| `industry` | `Cv-Industry_tmpl.tex` | `helpers/industry_macros.tex` |
| `publications` | `All-Publications_tmpl.tex` | — |

Generate all four with `python generate.py --date 2026-11-04`, or select one `--format`, such as `academic-dossier`, `industry`, or `publications`. `python build.py` also compiles all four PDFs. Output names are `gen/Cv-Academic.tex`, `gen/Cv-Academic-Dossier.tex`, `gen/Cv-Industry.tex`, and `gen/All-Publications.tex`, with matching PDF names. A successful compilation of the `current` layout removes legacy `cv.*` and `Cv-Academic-Home.*` outputs and their logs; a failed compilation preserves them.

Main document templates live at the top level of `tmpl/`. Reusable sections and macros live in `tmpl/helpers/`; Jinja import and loader paths use the `helpers/` prefix relative to this template directory. Python presentation helpers are grouped separately under `cvgen/helpers/`.

## Jinja syntax for LaTeX

The renderer configures delimiters that do not collide with normal LaTeX braces:

| Purpose | Syntax |
| --- | --- |
| Value | `~{{ expression }}~` |
| Statement | `~{ if condition }~ ... ~{ endif }~` |
| Comment | `~{# comment #}~` |

Standard Jinja filters, loops, macros, imports, and whitespace controls remain available. Data values already contain intentional LaTeX commands, so the renderer does not HTML-escape them. A new data field must use valid LaTeX, just like the existing YAML fields.

## Current layout

The existing renderer passes the original `name`, contacts, profile, rendered `body1`/`body2`/`body3`, publication text, counters, `today`, and `bibliography_path` to `Cv-Academic_tmpl.tex`. `helpers/section_tmpl.tex` receives `name`, `contents`, and `kind`, following `cv.yaml`'s `order` list. Its output is protected by an approved-content regression test. When the configured current-position section has no current job, the renderer shows the first previous job as Last Position, with its original dates, and removes that entry from the following Work Experience block. If both lists are empty, the empty position heading is omitted. This presentation fallback does not modify the YAML or claim that an ended appointment is current.

## Academic dossier

The main dossier template receives:

- `cv`: the complete processed CV mapping. Original YAML keys such as `edu` and `diplomas` are retained, alongside `talks`, `schools`, `conferences`, `pub_details`, `pubsnum`, `talksnum`, and `teachnum`.
- `today`: the selected reference date formatted as `dd/mm/yy`.
- `today_long`: the same date in the original English long form, for example `November 4, 2026`, independently of the operating-system locale.
- `bibliography_path`: the BibTeX path relative to the chosen output directory.

Use fields instead of copying personal information from the reference document:

```tex
\textbf{~{{ cv.name.first }}~ ~{{ cv.name.last | upper }}~}
\addbibresource{~{{ bibliography_path }}~}

~{ if cv.currentjobs }~
~{{ academic.voices('Current Position', cv.currentjobs) }}~
~{ elif cv.previousjobs }~
~{{ academic.voices('Last Position', cv.previousjobs[:1]) }}~
~{ endif }~
```

The template imports `helpers/academic_macros.tex` as `academic`. Its reusable macros are:

| Macro | Input and output |
| --- | --- |
| `voice(entry)` | One YAML entry with `what`, `when`, `where`, `url`, `info` |
| `voices(title, entries)` | An original-style block heading and its entries; empty lists are omitted |
| `numbers(entries)` | A summary table from `{type, value}` rows |
| `activities(entries)` | Detailed activities from the processed CSV rows |
| `publications(details)` | Four citation groups from `{key, type}` records |

For example, to expose an existing YAML list in a new dossier section:

```tex
~{{ academic.voices('Research Stays', cv.visit) }}~
```

The dossier follows this order:

1. Cover with contacts, keywords, and table of contents.
2. Resume, current or last position, languages, the eight skills selected in the reference, work experience, and `edu`.
3. Separate `diplomas`, habilitations, and awards.
4. Teaching and administration, with the organization count in its summary.
5. Research profile, publication/communications counts, bibliography, and research stays.
6. Talks, conferences, and postgraduate training.

When there is no current job, the first previous job is displayed as Last Position and excluded from the subsequent Work Experience list. The original order, activity selection, counters, and publication groups remain controlled by the processing layer. Dates and citation keys are never fixed in the template.

The LaTeX preamble and the `block`, `blockNp`, `voice`, `longvoice`, `skill`, and `skillbar` commands match the supplied reference. Use those commands rather than introducing alternative section styles. Only Resume, Teaching and Administrative Activities, and Research Activities are added to the table of contents. Diplomas and Talks use `blockNp`; Workshops and Post-Graduate Training continue normally with `block`. Referees and exam supervision stay omitted as in the reference.

The cover keeps the original two-column contact box, including the postal address supplied by the `address` list in `data/cv.yaml`. Each list item is rendered on a separate line. An absent or empty list retains the original space without address text. Optional `keyword_heading`, `publication_archive`, and `bibliometrics_url` fields can override the reference's publication/keyword metadata; the author identifier and website use current CV fields.

The dossier uses `tcolorbox`, `orcidlink`, and `titlesec` in addition to the existing LaTeX packages. It retains the original IEEE bibliography behavior, without driver aliases or modified itemize spacing. Bibliography, table of contents, and page totals are resolved by Biber and the repeated LaTeX passes in the build. Local Jinja whitespace controls prevent loops from adding unintended LaTeX paragraphs while retaining the original paragraph breaks after headings.

Run `python -m unittest discover -s tests -v` after template changes. For layout changes, compile and visually inspect the affected PDF pages as well.

The dossier reads an optional `\jobname.skip.tex` file generated by the build after checking which PDF pages contain no body content. Its shipout hook suppresses only those empty pages and adjusts logical numbering. It does not change the original spacing commands or reflow the retained pages. `make clean` and `python build.py --clean` remove this generated file; normal builds discard any previous list before detecting pages again.

### Additional information

The two academic templates share `helpers/additional_information.tex`. It renders the optional author-supplied LaTeX paragraphs after Honors & Awards in the dossier and as the final block in the generic Academic CV. The dossier reads `cv.additional_information`; the generic renderer supplies `additional_information` from the same YAML field.

The shared block places `\vfill` before its unnumbered `\block{Additional Information}` heading. Its horizontal rule, large bold type, and spacing match neighboring blocks. Mathematical `\cdot` item markers and zero list `topsep`/`partopsep` avoid extra space between the heading and list; compact item and paragraph spacing is retained. Missing or empty data emits neither the block nor its spacer. It does not add a table-of-contents entry and is not rendered in Industry or All-Publications. See the [YAML field contract](data.md#optional-additional-information).

## Industry

The industry template receives the same `cv`, `today`, and `today_long` values, plus `industry`, the presentation mapping returned by the pure `cvgen.helpers.industry.prepare_industry(cv)` helper. This helper selects work experience, education, honors, and training from the updated shared data without changing those inputs. Its academic-track figures are derived from the current publication, teaching, communications, organization, and research-stay counts rather than copied from the reference document.

The optional `industry` mapping in `data/cv.yaml` can override `titleinfo`, `award_titles`, and `training_titles`. The latter two lists select existing award and training titles; their dates and descriptions still come from the shared data.

The template imports `helpers/industry_macros.tex` for its entries and summary tables. It does not use BibLaTeX citation commands or a Biber job. Build just this document with `python build.py --format industry`; its output is `gen/Cv-Industry.pdf`.

## Publications

`All-Publications_tmpl.tex` reproduces the standalone layout of `old-tailored/2020-All-Publications.tex`, while deriving every citation key from `data/publications.bib`. The `publications` format bypasses CV YAML and activity loading; editing the bibliography is enough to update this document.

The pure helper in `cvgen/helpers/publications.py` groups entries by BibTeX type:

| Section | Entry types |
| --- | --- |
| Published | `article`, `book`, `inproceedings`, `proceedings` |
| Theses | `phdthesis`, `mastersthesis` |
| Submitted to Peer-review | `preprint`, `unpublished` |
| In Preparation | `draft` |
| Other publications | Any other entry type |

Entries use reverse bibliography-file order within each group, matching the supplied publication list. All entries are included, including bachelor/master/doctoral theses represented by the supported types; an unfamiliar type is retained in the fallback group. The template iterates over these groups instead of maintaining a hardcoded selection. The existing CV classification remains unchanged. Optional editorial notes belong in the bibliography's `annotation` field. All authors are printed: the maximum name-list size in the bibliography sets both citation and bibliography limits, so `\fullcite` does not shorten author lists to ‘et al.’.

```sh
python build.py --format publications --date 2026-11-04
```

The output is `gen/All-Publications.tex/pdf`. It uses BibLaTeX and Biber, followed by repeated LaTeX passes to resolve citations and page totals. Both CLIs include this format when using the default `--format all`.


[Template sources](../tmpl/README.md) · [Documentation index](README.md)
