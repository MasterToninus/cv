# Shared CV data

| File | Purpose |
| --- | --- |
| [cv.yaml](cv.yaml) | Personal information, section entries, and layout order |
| [cv.schema.json](cv.schema.json) | Local editor schema selected by the YAML modeline |
| [activities.csv](activities.csv) | Versioned, semicolon-separated activity snapshot |
| [publications.bib](publications.bib) | Complete bibliography and stable citation keys |

Normal builds read these files offline. The publication-list format reads only the bibliography.

See the [data contract](../docs/data.md), [author-confirmed corrections](../docs/confirmed-data.md), and [build guide](../docs/build.md) for validation, deliberate snapshot refreshes, and generation.
