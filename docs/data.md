# Data contract

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

Its citation groups and entry lists are derived automatically from the BibTeX entries; no citation keys need to be copied into the template. See [the publication-template contract](templates.md#publications) for classification and output details.

Normal generation does not fetch the website. From the repository root, update the activities snapshot explicitly with:

```sh
python build.py --refresh-activities
```

The refresh validates the downloaded CSV before replacing the snapshot; network or validation errors leave the previous file intact. Review its diff and rebuild the CV before committing an update. A fixed snapshot and build date make the activity lists and counters reproducible.

CSV column names must be unique. Duplicate headers are rejected before reading records, because otherwise a later column could silently overwrite a required value.

The processing layer preserves the existing activity selection, list order, and publication classification. Data corrections and classification changes should be reviewed separately from the pipeline refactoring.

The **Conferences and Schools Attended** counter includes `Workshop`, `Conference`, and `School` records whose `Start_Date` is on or before the build's reference date. Other training-course types are excluded. Future activities remain visible within the 200-day display horizon and are marked scheduled, but do not increase the attendance counter. Talk counters retain their existing all-source-record behavior. These totals are derived from `activities.csv`, not configured in YAML.

See [author-confirmed CV data](confirmed-data.md) for the corrections approved on 4 November 2026. It also distinguishes the doctoral-scholarship competition won in November 2016 from the contract beginning in January 2017; the existing YAML scholarship period remains unchanged.

The complete publication list is generated directly from `publications.bib`. Use `python build.py --format publications` to produce `gen/All-Publications.tex/pdf`.

[BibTeX Tidy](https://flamingtempura.github.io/bibtex-tidy/) can help clean bibliographic files, but review its changes before replacing `publications.bib`.

## Optional additional information

`additional_information` is an optional YAML list of LaTeX strings shared by the two academic formats. The Academic Dossier displays it after Honors & Awards; the generic Academic CV displays it as its final block. Both use mathematical dot markers and matching compact list spacing, preceded by flexible vertical space. An absent or empty list omits both the block and its spacer. Industry and All-Publications do not display this field.

```yaml
additional_information:
  - >-
    Author-supplied context with \textbf{emphasis}.
```

Keep this content author-approved, like the other personal statements. The local schema checks that every item is a string.

Before tailoring a CV, follow the [bibliography metadata checks](../AGENTS.md#bibliography-metadata-checks). Local parsing verifies syntax; publisher, Crossref, arXiv, and thesis records establish bibliographic accuracy and current status.


[Data sources](../data/README.md) · [Documentation index](README.md)
