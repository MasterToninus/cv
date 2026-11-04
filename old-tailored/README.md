# Historical and reference CVs

This folder keeps earlier standalone CVs, supporting documents, and source material retained for reference. They are independent snapshots: `build.py` does not compile them or merge their text into the generated CVs.

The sources include compact and alternative CV layouts, the French CV, teaching/titles documents, and the original academic-dossier and industry references. Their generated successors are maintained in [`tmpl/`](../tmpl/README.md) and use the shared data under [`data/`](../data/README.md).

[`2027-Cv-Tony-ERC.tex`](2027-Cv-Tony-ERC.tex) extracts the complete CV and track record from the HiDRA ERC Starting Grant 2027 proposal, with the original 2026 data snapshot. It is a standalone document and does not add an ERC output format to the generator.

The ERC CV body is preserved verbatim from source lines 1633–2257 (SHA-256 `97b8f36d15fcea40729503055ecf2d1bb6ba2905dc4da47edb785e51f1a13683`). Its standalone wrapper retains the original provenance notes and inlines the required ERC styling with attribution. Compile it with pdfLaTeX; no project-local ERC classes or Biber run are needed.

Historical sources can require their own document classes, packages, or bibliographies. Build them separately and keep auxiliary files in a `build/` directory. Preserve source credits and provenance when adapting an archived document.

The [earlier full publication list](2020-All-Publications.tex) is the layout reference for the generated `All-Publications` format. For an updated list, use the shared build rather than editing this archived snapshot.

For the [analytical MCF CV](mcf-temp/2026-Cv-Analytical-MCF.tex), run the following from the repository root. Both the shared bibliography and the local [historical bibliography](mcf-temp/2026-Bibliography-Old.bib) are resolved from the source directory:

```sh
cd old-tailored/mcf-temp
python -c "from pathlib import Path; Path('build').mkdir(exist_ok=True)"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build 2026-Cv-Analytical-MCF.tex
biber --input-directory build --output-directory build 2026-Cv-Analytical-MCF
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build 2026-Cv-Analytical-MCF.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build 2026-Cv-Analytical-MCF.tex
```

[Repository guide](../README.md)

Document filename prefixes use the [first Git introduction year](../docs/document-origins.md), preserving the history of each distinct variant.
