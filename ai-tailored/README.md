# AI-assisted application documents

This folder contains independently maintained CVs, publication lists, and scientific portfolios adapted with AI assistance for particular applications. The shared-data build does not overwrite these tailored sources.

Use the naming convention defined in [the agent instructions](../AGENTS.md#ai-document-filenames-and-versions):

```text
YYYY-<Type>-Tony-<Target>[-<Role>][-Draft].tex
```

| Type | Example |
| --- | --- |
| CV | `2026-Cv-Tony-Eni-HPC-33545.tex` |
| Publication list | `2026-Publications-Tony-Academic-Draft.tex` |
| Scientific portfolio | `2026-Scientific-Portfolio-Tony-Classiq.tex` |

Use ASCII and hyphens, consistent capitalization, and established acronyms such as `ATS`, `HPC`, `HPQC`, and `BIP`. Keep one canonical file for each variant and let Git track revisions. `-Draft` records a pending review; successful compilation does not imply author approval. Dated snapshots are exceptions requested by the user, using an actual `-YYYYMMDD` suffix rather than invented version numbers or `Final` labels.

PDFs, extracted text, and auxiliary files use the same stem as the source and belong in `build/`. Only this folder guide remains as Markdown here; [review notes and original author answers](../docs/ai-tailored/README.md) are preserved under `docs/ai-tailored/`.

Review factual claims and application-specific selections before reuse. Existing policy/provenance reviews are retained under [`docs/AI-policy-disclosure/reviews/`](../docs/AI-policy-disclosure/reviews/); they describe the reviewed versions and should not be silently rewritten to cover later edits.

For every new tailoring request, [validate the YAML and `getactivities`, regenerate the current CV, and start from the new TeX](../AGENTS.md#tailoring-a-cv-for-a-position). Current author-confirmed corrections are recorded in [the shared-data notes](../docs/confirmed-data.md); archived application reviews retain their original historical context.

For the automatically generated industry CV, use `python build.py --format industry` and edit the shared data or [`tmpl/Cv-Industry_tmpl.tex`](../tmpl/Cv-Industry_tmpl.tex). That output is separate from the tailored sources here.

[Repository guide](../README.md)
