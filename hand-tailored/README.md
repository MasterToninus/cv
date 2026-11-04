# Standalone tailored documents

This folder contains independently maintained sources:

- [Personal CV variant](2025-Cv-Giusy.tex), concerning a different person from the shared Antonio Miti data.
- [Selected publications](2025-Selected-Publications.tex).
- [Selected publications with a motivation](2026-Selected-Publications-Commented.tex).

They are separate from the four generated outputs: `python build.py` does not compile or overwrite them. Compile each source with its required packages and bibliography, keeping auxiliary files under `build/`.

The earlier full publication list, analytical MCF CV and other historical references are archived in [`old-tailored/`](../old-tailored/README.md). AI-assisted application sources live in [`ai-tailored/`](../ai-tailored/README.md), with their notes under [`docs/ai-tailored/`](../docs/ai-tailored/README.md).

Document filename prefixes record the [first Git introduction year](../docs/document-origins.md). They do not indicate the last revision or approval date.

For the current complete publication list, use `python build.py --format publications`, which produces `gen/All-Publications.tex/pdf` directly from the shared BibTeX file.

[Repository guide](../README.md)
