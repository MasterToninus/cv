# CV data

The generator reads these local, versioned inputs:

| File | Contents |
| --- | --- |
| `cv.yaml` | Personal information, section data, and section order/layout |
| `cv.schema.json` | Local editor schema for this repository's YAML configuration |
| `activities.csv` | Snapshot of website activities, with semicolon-separated columns |
| `publications.bib` | Publication references and their existing BibTeX categories |

`cv.yaml` explicitly selects the adjacent `cv.schema.json` with a `yaml-language-server` modeline. This prevents editors from applying an unrelated schema based on the generic `cv.yaml` filename. Validation stays enabled for known fields, while custom sections and LaTeX display text remain supported. The directive is a comment and does not change the generated CV data.

The three CV formats use the shared inputs. The standalone `publications` format reads only `publications.bib` and does not require `cv.yaml` or `activities.csv`:

```sh
python build.py --format publications
```

Its citation groups and entry lists are derived automatically from the BibTeX entries; no citation keys need to be copied into the template. See [the publication-template contract](../tmpl/README.md#publications) for classification and output details.

Normal generation does not fetch the website. From the repository root, update the activities snapshot explicitly with:

```sh
python build.py --refresh-activities
```

The refresh validates the downloaded CSV before replacing the snapshot; network or validation errors leave the previous file intact. Review its diff and rebuild the CV before committing an update. A fixed snapshot and build date make the activity lists and counters reproducible.

CSV column names must be unique. Duplicate headers are rejected before reading records, because otherwise a later column could silently overwrite a required value.

The processing layer preserves the existing activity selection, list order, and publication classification. Data corrections and classification changes should be reviewed separately from the pipeline refactoring.

See [author-confirmed CV data](../docs/confirmed-data.md) for the corrections approved on 4 November 2026. It also distinguishes the doctoral-scholarship competition won in November 2016 from the contract beginning in January 2017; the existing YAML scholarship period remains unchanged.

The complete publication list is generated directly from `publications.bib`. Use `python build.py --format publications` to produce `gen/All-Publications.tex/pdf`.

[BibTeX Tidy](https://flamingtempura.github.io/bibtex-tidy/) can help clean bibliographic files, but review its changes before replacing `publications.bib`.

Before tailoring a CV, follow the [bibliography metadata checks](../AGENTS.md#bibliography-metadata-checks). Local parsing verifies syntax; publisher, Crossref, arXiv, and thesis records establish bibliographic accuracy and current status.
