# CV generation package

The package separates data acquisition, processing, and rendering:

- `acquisition.py` loads the shared YAML, activities, and bibliography.
- `processing.py` derives the common presentation data without fetching inputs.
- `rendering.py` renders the selected Jinja/LaTeX template.

[Supporting helpers](helpers/README.md) provide reusable utilities and format-specific presentation logic.
See [build and architecture details](../docs/build.md) for the public commands and pipeline contract.
