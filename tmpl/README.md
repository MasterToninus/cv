# CV templates

Main Jinja templates render the shared data into four LaTeX documents:

| Format | Template |
| --- | --- |
| Academic | [Cv-Academic_tmpl.tex](Cv-Academic_tmpl.tex) |
| Academic dossier | [Cv-Academic-Dossier_tmpl.tex](Cv-Academic-Dossier_tmpl.tex) |
| Industry | [Cv-Industry_tmpl.tex](Cv-Industry_tmpl.tex) |
| Publications | [All-Publications_tmpl.tex](All-Publications_tmpl.tex) |

Shared macros live in [`helpers/`](helpers/README.md). Templates control presentation; they do not fetch or edit data.

See the [template reference](../docs/templates.md) for delimiters, fields, fallback rules, and citation behavior, and the [build guide](../docs/build.md) for compilation.
