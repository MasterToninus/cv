# Agent instructions

<!-- BEGIN USER COMMIT PROVENANCE POLICY -->
## Commit provenance policy — 17 October 2026

Apply this convention whenever you create or propose a new commit message for this user's repositories:

- Start the subject with `[AI] ` for predominantly AI-generated content (approximately 90% AI).
- Start the subject with `[AI-Human] ` for content developed interactively by the human and an AI.
- Use no provenance tag only for content classified as human-authored. Never omit the tag to present AI-generated or AI-assisted changes as human-only.

Use exactly these capitalizations and put the tag before any existing conventional-commit prefix, for example `[AI-Human] docs: revise the AI policy`. Classify the origin of the committed changes, not the account running Git. A prompt or approval alone does not turn predominantly AI-generated content into human-authored content. State uncertainty rather than inventing an exact percentage or silently claiming human provenance.

Check the subject before committing and retain the appropriate tag in any newly authored squash or merge message. Pass this convention to delegated agents and commit-message generators. When initializing a new repository for this user, carry this policy into its agent instructions.

This prospective rule supersedes older tag spellings; preserve historical commit messages and records. Continue to respect the current task's scope and existing commit/push permissions. This labeling policy does not itself require a commit or push.
<!-- END USER COMMIT PROVENANCE POLICY -->

## Tailoring a CV for a position

Whenever the user asks to adapt a CV to a job, call, or academic position, start
from a freshly generated CV using the current repository data. Apply this
workflow on every request, even when a previous tailored version exists.

1. Work from the repository root. Read `data/cv.yaml`, the local activities
   snapshot, and `data/publications.bib`. Check the YAML directly; do not rely
   only on an earlier PDF, an old tailored CV, or remembered facts.
   Report discrepancies in `data/cv.yaml` and propose the exact corrections
   before editing it. Apply YAML corrections only after explicit user approval.
2. Verify that the legacy `getactivities` helpers actually run and that the YAML
   can be loaded. Run the following command and inspect its result:

   ```sh
   python -c "from pathlib import Path; from cvgen.acquisition import load_config; import getactivities as g; config = load_config(Path('data/cv.yaml')); activities = g.readmywebsite(); g.readmybibfile(); g.readmyconfigurations(); assert config.get('name'); assert all(key in activities for key in ('talks', 'conferences', 'schools')); print('YAML and getactivities: OK')"
   ```

3. Check the entire `data/publications.bib` against current primary sources,
   following the bibliography checks below. Complete this before generating
   the CV; parsing successfully is not evidence that its metadata is current.
4. Run `python build.py` to regenerate and compile all four documents. Use the
   current date, or the reference date explicitly requested by the user. Use
   `--date YYYY-MM-DD` when fixing that date. Normal generation reads local
   data; refreshing the website snapshot is a separate, deliberate operation.
   If validation or generation fails, fix or report the failure before adapting
   the CV; do not silently fall back to an older generated file.
5. Choose the newly generated TeX matching the requested position: normally
   `gen/Cv-Industry.tex` for industry, and `gen/Cv-Academic.tex` or
   `gen/Cv-Academic-Dossier.tex` for academic applications. Honor any format
   explicitly requested by the user. Use `gen/All-Publications.tex` when a
   publication list is needed.
6. Copy that generated TeX into `ai-tailored/`, following the naming convention
   below, for example `2026-Cv-Tony-Organization-Role-Draft.tex`. Adapt this
   copy of the generated source. `gen/` remains reproducible build output; an
   existing tailored CV may supply context, but is not the default source of
   current personal facts or publication status.
7. Check the result against the shared YAML, activities, bibliography, and job
   requirements. Compile the tailored TeX, using Biber if it contains BibLaTeX,
   and inspect the PDF and extracted text. Check publication author lists,
   links, dates, page numbering, and missing or duplicated sections.
8. In the handoff, state which generated TeX was used, the reference date, that
   YAML loading and `getactivities` validation succeeded, and the build checks
   performed, including bibliography sources, verification date, corrections,
   and unresolved metadata. Do not treat tailoring as authorization to commit, push, submit,
   or send the application.

## Bibliography metadata checks

For every CV-tailoring request, review all entries in `data/publications.bib`,
not only those selected for that particular document:

- Verify complete author names and their order, the title (preserving valid
  LaTeX/math and proper names such as Peierls), year/month/day, publication
  venue, volume, issue, pages/article number, DOI, arXiv identifier/version,
  and journal ISSN when present.
- Use primary sources: the publisher's DOI/landing page and issue record,
  Crossref's DOI metadata, arXiv's abstract/version/journal-reference record,
  or the institutional thesis repository. Use the author's confirmation for
  unpublished work whose details are not publicly verifiable.
- Distinguish first-online dates from issue dates and degree-award dates from
  thesis-deposit dates. Report conflicts rather than silently choosing a year.
- Check whether each record is published, accepted/in press, submitted/preprint,
  or in preparation. Flag contradictions such as `@draft` together with
  `pubstate = {forthcoming}` or `pages = {to appear}`. Never infer acceptance or
  publication from a manuscript title, filename, or earlier tailored CV.
- Resolve DOI/arXiv targets and check for duplicate works or identifiers.
  Preserve meaningful links between a preprint and a proceedings version.
  Do not truncate author lists or invent missing metadata.
- Record sources and the verification date in concise document notes. Correct
  unambiguous typos within the authorized scope; propose conflicting or
  uncertain factual/status changes to the author before applying them.
- Preserve citation keys by default, since templates and standalone documents
  refer to them. Validate the bibliography with Pybtex and Biber, regenerate
  the output, and inspect the resulting citations and full author lists.
- If a primary source is unavailable, record exactly what remains unverified.
  Do not report a complete metadata check when only local parsing succeeded.

## AI document filenames and versions

Keep AI-assisted CVs and other application-document sources in `ai-tailored/`.
Use this canonical filename convention:

```text
YYYY-<Type>-Tony-<Target>[-<Role>][-Draft].tex
```

- `YYYY` is the document's preparation year. A call year or identifier belongs
  in the target/role when needed; do not invent a preparation date.
- Use the exact types `Cv`, `Publications`, and `Scientific-Portfolio` for the
  existing document families. Other families use an equally descriptive type,
  such as `Cover-Letter`, `Research-Statement`, or `Teaching-Statement`.
- Use ASCII letters, digits, and hyphens, without spaces or underscores.
  Capitalize target/role words consistently and preserve brand spellings and
  established acronyms, such as `DeepBlue`, `UniBo`, `ATS`, `HPC`, `HPQC`, and
  `BIP`. Retain meaningful call identifiers such as `33545` or `R0034582`.
- Examples: `2026-Cv-Tony-Eni-HPC-33545.tex`,
  `2026-Publications-Tony-Academic-Draft.tex`, and
  `2026-Scientific-Portfolio-Tony-Classiq.tex`.
- A new document awaiting author review uses `-Draft`. Remove that suffix only
  after explicit author approval. Preserve the documented status of existing
  sources; a filename alone is not evidence that an application was approved
  or submitted. Never label a source `Final` merely because it compiled.
- Keep one canonical file per tailored variant; Git records its revisions.
  Do not invent `v01`, `v2`, `final`, or `definitivo` suffixes. If the user needs
  dated snapshots side by side, append the actual snapshot date as `-YYYYMMDD`,
  for example `2026-Cv-Tony-Organization-Role-Draft-20261104.tex`.
- Compiled PDFs, extracted text, logs, and auxiliary files use the same stem
  as their TeX source and belong under `ai-tailored/build/`.
- Keep `ai-tailored/README.md` as the folder guide. Store substantive review
  notes, author answers, and evidence under `docs/ai-tailored/`, normally as
  `<document-stem>-Notes.md`. Shared `-Review.md` and `-FollowUp.md` records may
  serve multiple artifacts. Do not delete useful author confirmations or
  rewrite historical assessments to make them describe newer revisions.
- When renaming a source or moving its notes, update local links and known
  cross-repository references. Preserve historical content hashes and unrelated
  external export paths: a rename does not authorize a new provenance claim.

## Python source style

Use four-space indentation and keep functions, classes, and logical blocks
visually separated. Keep the boxed source headers current. Explain non-obvious
behavior, compatibility choices, data-selection rules, and failure handling in
concise comments or docstrings; avoid narrating obvious statements.

Apply the Black and isort settings in `pyproject.toml` to every Python source,
including tests. Install the optional tools with
`python -m pip install -r requirements-dev.txt`, then run `make format` and
`make format-check`, or the equivalent Python commands documented in the README.
Keep formatting changes separate from behavior changes and run the test suite.

## Historical document filename years

For existing documents in `hand-tailored/` and `old-tailored/`, use the first Git
introduction year of that specific variant as the filename prefix. Follow actual
renames, but stop at an addition or copy; a copied variant does not inherit its
ancestor's creation year. Record the introducing commit and timestamp in
`docs/document-origins.md`. Do not derive a Git year from a document's content,
call year, modification time, or the current date when no history exists.
