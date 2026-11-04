# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/formats.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Names shared by the renderer, command-line generator, and build.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Names shared by the renderer, command-line generator, and build."""

# Logical selectors remain stable even if output capitalization changes.
# Insertion order also defines the stable build order for --format all.
OUTPUT_STEMS = {
    "current": "Cv-Academic",
    "academic-dossier": "Cv-Academic-Dossier",
    "industry": "Cv-Industry",
    "publications": "All-Publications",
}
FORMAT_CHOICES = (*OUTPUT_STEMS, "all")
# Both command-line entry points build the complete registered set by default.
DEFAULT_FORMAT = "all"


def selected_formats(value: str) -> tuple[str, ...]:
    """Expand the CLI selector while keeping one filename registry for all stages."""
    if value == "all":
        return tuple(OUTPUT_STEMS)
    if value not in OUTPUT_STEMS:
        raise ValueError(f"Unknown CV format: {value}")
    return (value,)
