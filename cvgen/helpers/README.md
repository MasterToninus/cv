# Supporting Python modules

These modules support the generation pipeline without serving as its public build entry points.
`clock.py`, `formats.py`, and `paths.py` define build dates, output names, and path handling.
`dates.py` formats entry dates at month precision without changing the recorded source dates.
`industry.py` and `publications.py` prepare format-specific presentation data; `pagination.py` checks dossier pages.

`links.py` checks HTTP(S) hyperlinks embedded in generated PDFs through `python -m cvgen.helpers.links`.
See [link-checking instructions](../../docs/build.md#link-checking) for its options and CI use.

[Generation package](../README.md)
