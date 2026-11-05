# GitHub Actions workflows

These workflows validate the repository and make generated outputs available on GitHub.

- [Build CV PDFs](build-cv.yml) runs the tests, compiles all four PDFs, and uploads them directly plus a ZIP bundle.
- [Check CV PDF links](check-links.yml) reuses successful build artifacts and publishes a report of broken and unverified URLs.

Detailed configuration and local verification commands are documented in the [build guide](../../docs/build.md#github-actions) and [link-checking guide](../../docs/build.md#link-checking).
