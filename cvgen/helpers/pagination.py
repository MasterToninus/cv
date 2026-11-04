# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/pagination.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Find pages containing only the dossier's header and footer, without editing PDFs.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Document pipeline and standardize source headers.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Find pages containing only the dossier's header and footer, without editing PDFs."""

from math import isfinite
from pathlib import Path

# Matches the dossier's 1.5 cm top/bottom bands, where its running furniture sits.
BODY_MARGIN_PT = 72 * 1.5 / 2.54


def _numbers(values):
    """Reject invalid coordinates instead of treating unreadable marks as empty."""
    numbers = tuple(float(value) for value in values)
    if not all(isfinite(value) for value in numbers):
        raise ValueError("PDF contains non-finite coordinates")
    return numbers


def _has_body_content(page, margin):
    """Inspect text, painted paths and annotations for any body-area overlap."""
    if int(page.get("/Rotate", 0)) % 360:
        raise ValueError(
            "Rotated PDF pages are not supported by the dossier pagination check"
        )
    bottom, top = _numbers((page.mediabox.bottom, page.mediabox.top))
    low, high = bottom + margin, top - margin
    if low >= high:
        raise ValueError("The body margin leaves no PDF page area")
    has_content = False
    path_points = []
    line_width = 1.0
    width_stack = []

    def intersects(lower, upper):
        """Keep marks that touch either body boundary, not just its interior."""
        return upper >= low and lower <= high

    def point(x, y, matrix):
        """Apply the PDF six-number affine transform to a point."""
        # PDF coordinates must be transformed before comparison with page bands.
        x, y = _numbers((x, y))
        a, b, c, d, e, f = _numbers(matrix)
        return x * a + y * c + e, x * b + y * d + f

    def text(value, cm, tm, font, size):
        nonlocal has_content
        if not value.strip():
            return
        if font is None:
            raise ValueError("Cannot determine the font of PDF text")
        _, y = point(tm[4], tm[5], cm)
        a, b, c, d, _, _ = _numbers(tm)
        _, cb, _, cd, _, _ = _numbers(cm)
        # A rotated or slanted baseline can carry a long run from a margin
        # into the body. Text extraction supplies no reliable run width, so
        # retain the page instead of bounding the whole run by a single em.
        if a * cb + b * cd != 0:
            has_content = True
            return
        # Enclose a transformed em square, including descenders. Overestimating
        # the bounds preserves content rather than deleting a marginal glyph.
        extent = abs(float(size)) * (abs(a * cb + b * cd) + abs(c * cb + d * cd))
        if not isfinite(extent):
            raise ValueError("PDF contains a non-finite font size")
        if intersects(y - extent, y + extent):
            has_content = True

    def operand(operator, arguments, cm, tm):
        """Track painted graphics so non-text content also retains a page."""
        nonlocal has_content, line_width
        if operator == b"q":
            width_stack.append(line_width)
        elif operator == b"Q":
            if not width_stack:
                raise ValueError("PDF has an unbalanced graphics-state restore")
            line_width = width_stack.pop()
        elif operator in (b"Do", b"INLINE IMAGE", b"sh"):
            # Forms, images and shadings can contain content not exposed by
            # text extraction. Retain their pages conservatively.
            has_content = True
        elif operator == b"w":
            line_width = abs(_numbers(arguments)[0])
        elif operator in (b"m", b"l"):
            path_points.append(point(arguments[0], arguments[1], cm))
        elif operator == b"re":
            x, y, width, height = _numbers(arguments)
            path_points.extend(
                point(px, py, cm)
                for px, py in (
                    (x, y),
                    (x + width, y),
                    (x, y + height),
                    (x + width, y + height),
                )
            )
        elif operator in (b"c", b"v", b"y"):
            path_points.extend(
                point(arguments[index], arguments[index + 1], cm)
                for index in range(0, len(arguments), 2)
            )
        elif operator in (b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"):
            if path_points:
                ys = [coordinate[1] for coordinate in path_points]
                # Control points bound Bezier curves conservatively; account
                # for stroke width as well as the path's centerline.
                scale = sum(abs(value) for value in _numbers(cm[:4]))
                padding = line_width * scale / 2
                if intersects(min(ys) - padding, max(ys) + padding):
                    has_content = True
            path_points.clear()
        elif operator == b"n":
            path_points.clear()  # An unpainted or clipping-only path.

    page.extract_text(visitor_text=text, visitor_operand_before=operand)
    # Links and other interactive regions may be meaningful even without text.
    for reference in page.get("/Annots", []):
        annotation = reference.get_object()
        rectangle = annotation.get("/Rect")
        if rectangle is None or len(rectangle) != 4:
            raise ValueError("Cannot determine the position of a PDF annotation")
        _, y0, _, y1 = _numbers(rectangle)
        if intersects(min(y0, y1), max(y0, y1)):
            has_content = True
    return has_content


def find_empty_body_pages(
    pdf_path: Path, margin_pt: float = BODY_MARGIN_PT
) -> tuple[int, ...]:
    """Return physical 1-based pages with no content between the margin bands.

    Any reading failure aborts the check; sparse pages and pages containing
    graphical or interactive content are retained. No files are modified.
    """
    margin = float(margin_pt)
    if not isfinite(margin) or margin < 0:
        raise ValueError("The PDF body margin must be finite and non-negative")
    # Keep PDF inspection optional for TeX-only and non-dossier generation.
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError(
            "Install requirements.txt to enable the PDF pagination check (pypdf)"
        ) from error
    try:
        reader = PdfReader(str(pdf_path), strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs cannot be checked for empty dossier pages")
        return tuple(
            index
            for index, page in enumerate(reader.pages, 1)
            if not _has_body_content(page, margin)
        )
    except Exception as error:
        raise RuntimeError(
            f"Cannot safely inspect PDF pagination in {pdf_path}: {error}"
        ) from error
