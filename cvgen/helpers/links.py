# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/links.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-05
# |
# | Purpose           : Check HTTP links in the four generated PDFs on demand.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261105  Miti/Codex   Add explicit network checks and portable link reports.
# | 20261105  Miti/Codex   Preserve HEAD across supported urllib redirect versions.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Inspect generated PDF annotations and report HTTP link availability.

This optional command performs network requests. Normal CV generation and the
unit tests remain offline. A blocked or inconclusive request is never reported
as a confirmed broken link or as a successfully verified destination.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.parse import urlsplit

from pypdf import PdfReader

from .formats import OUTPUT_STEMS
from .paths import resolve_project_path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT = 10.0
MAX_WORKERS = 8
HEAD_FALLBACK_STATUSES = {400, 403, 404, 405, 406, 410, 501}


@dataclass(frozen=True)
class LinkResult:
    """One deduplicated URL result, before its document/page sources are added."""

    url: str
    status: str
    http_status: int | None = None
    final_url: str | None = None
    method: str | None = None
    detail: str = ""


class ManualReviewRedirect(urllib.error.URLError):
    """Stop before following a redirect that would request an archive capture."""

    def __init__(self, destination: str, detail: str):
        super().__init__(detail)
        self.destination = destination


def manual_review_reason(url: str) -> str | None:
    """Recognize the Wayback capture action, which is not an archived view."""
    parts = urlsplit(url)
    path = parts.path.casefold().rstrip("/")
    if (parts.hostname or "").casefold() == "web.archive.org" and (
        path == "/save" or path.startswith("/save/")
    ):
        return "Wayback /save requests create archive captures; review manually."
    return None


class ReadOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow ordinary HTTP redirects, including the archive-action safeguard."""

    def redirect_request(self, request, response, code, message, headers, new_url):
        reason = manual_review_reason(new_url)
        if reason:
            raise ManualReviewRedirect(new_url, reason)
        if urlsplit(new_url).scheme.casefold() not in {"http", "https"}:
            raise ManualReviewRedirect(
                new_url, "Redirect target is not an HTTP(S) destination."
            )
        redirected = super().redirect_request(
            request, response, code, message, headers, new_url
        )
        # Older supported urllib versions create redirected Requests without
        # an explicit method, which turns HEAD into GET. Retain HEAD so the
        # probe remains body-free; leave the inherited GET behavior unchanged.
        if redirected is not None and request.get_method() == "HEAD":
            redirected.method = "HEAD"
        return redirected


def _request_status(url: str, method: str, timeout: float) -> tuple[int, str]:
    """Read status/redirect metadata and at most one response-body byte."""
    headers = {"User-Agent": "CV-PDF-Link-Checker/1.0"}
    if method == "GET":
        # Some servers reject HEAD. Limit both the requested range and the
        # consumed body even when a server ignores Range and returns a full 200.
        headers["Range"] = "bytes=0-0"
    request = urllib.request.Request(url, headers=headers, method=method)
    opener = urllib.request.build_opener(ReadOnlyRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            if method == "GET":
                response.read(1)
            return int(response.status), response.geturl()
    except urllib.error.HTTPError as error:
        try:
            return error.code, error.geturl()
        finally:
            error.close()


def check_url(url: str, timeout: float = DEFAULT_TIMEOUT) -> LinkResult:
    """Confirm missing links with GET; keep all inconclusive outcomes separate."""
    method = None
    try:
        parts = urlsplit(url)
        if parts.scheme.casefold() not in {"http", "https"} or not parts.hostname:
            return LinkResult(url, "unverified", detail="Invalid HTTP(S) URL.")
        # Accessing port also validates malformed values such as ':not-a-port'.
        parts.port
        reason = manual_review_reason(url)
        if reason:
            return LinkResult(url, "manual-review", detail=reason)
        method = "HEAD"
        status, final_url = _request_status(url, method, timeout)
        if status in HEAD_FALLBACK_STATUSES:
            method = "GET"
            status, final_url = _request_status(url, method, timeout)
        if 200 <= status < 300:
            state, detail = "valid", "HTTP destination responded successfully."
        elif method == "GET" and status in {404, 410}:
            state, detail = "broken", f"HTTP {status} confirmed by a limited GET."
        else:
            state, detail = (
                "unverified",
                f"HTTP {status}; availability is inconclusive.",
            )
        return LinkResult(url, state, status, final_url, method, detail)
    except ManualReviewRedirect as error:
        return LinkResult(
            url,
            "manual-review",
            final_url=error.destination,
            method=method,
            detail=str(error.reason),
        )
    except (
        urllib.error.URLError,
        HTTPException,
        OSError,
        ValueError,
        UnicodeError,
    ) as error:
        return LinkResult(
            url,
            "unverified",
            method=method,
            detail=f"{type(error).__name__}: {error}",
        )


def extract_links(input_dir: Path) -> tuple[dict, list, list, list]:
    """Read only the registered PDFs, retaining each unique document/page source."""
    links, documents, skipped, errors = {}, [], [], []
    for stem in OUTPUT_STEMS.values():
        name = stem + ".pdf"
        path = input_dir / name
        if not path.is_file():
            errors.append({"document": name, "detail": "Expected PDF is missing."})
            continue
        try:
            reader = PdfReader(path, strict=True)
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")
            document_links = []
            document_skipped = []
            for page_number, page in enumerate(reader.pages, 1):
                for reference in page.get("/Annots", []):
                    annotation = reference.get_object()
                    if annotation.get("/Subtype") != "/Link":
                        continue
                    occurrence = {"document": name, "page": page_number}
                    action = annotation.get("/A")
                    action = action.get_object() if action is not None else {}
                    if action.get("/S") != "/URI":
                        document_skipped.append(
                            {
                                **occurrence,
                                "uri": None,
                                "reason": "Internal or non-URI link.",
                            }
                        )
                        continue
                    raw_uri = action.get("/URI")
                    if raw_uri is None:
                        raise ValueError("A PDF URI action has no URI value.")
                    uri = (
                        raw_uri.decode("utf-8")
                        if isinstance(raw_uri, bytes)
                        else str(raw_uri)
                    )
                    if uri.split(":", 1)[0].casefold() not in {"http", "https"}:
                        document_skipped.append(
                            {**occurrence, "uri": uri, "reason": "Non-HTTP(S) URI."}
                        )
                    else:
                        document_links.append((uri, occurrence))
            # Publish a document's links only after all of its annotations parse.
            for uri, occurrence in document_links:
                sources = links.setdefault(uri, [])
                if occurrence not in sources:
                    sources.append(occurrence)
            skipped.extend(document_skipped)
            documents.append({"document": name, "pages": len(reader.pages)})
        except Exception as error:
            errors.append(
                {"document": name, "detail": f"{type(error).__name__}: {error}"}
            )
    return links, documents, skipped, errors


def _report(results: list, documents: list, skipped: list, errors: list) -> dict:
    """Build an explicit coverage summary, including unknown and skipped cases."""
    states = Counter(item["status"] for item in results)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "documents_expected": len(OUTPUT_STEMS),
            "documents_read": len(documents),
            "unique_web_links": len(results),
            "source_page_occurrences": sum(
                len(item["occurrences"]) for item in results
            ),
            "network_attempted": sum(item["method"] is not None for item in results),
            **{
                state: states[state]
                for state in ("valid", "broken", "unverified", "manual-review")
            },
            "skipped_annotations": len(skipped),
            "input_errors": len(errors),
        },
        "documents": documents,
        "results": results,
        "skipped": skipped,
        "errors": errors,
    }


def audit_pdfs(
    input_dir: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = MAX_WORKERS,
    checker: Callable[[str, float], LinkResult] | None = None,
) -> dict:
    """Audit complete PDF input sets with bounded parallel HTTP requests."""
    if not 0 < timeout <= 60:
        raise ValueError("Timeout must be greater than zero and at most 60 seconds.")
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(f"Workers must be between 1 and {MAX_WORKERS}.")
    links, documents, skipped, errors = extract_links(Path(input_dir))
    urls = sorted(links)
    if errors:
        findings = [
            LinkResult(
                url,
                "unverified",
                detail="Not requested because the PDF input set is incomplete or invalid.",
            )
            for url in urls
        ]
    else:
        inspect = checker or check_url
        with ThreadPoolExecutor(max_workers=min(workers, len(urls) or 1)) as executor:
            findings = list(executor.map(lambda url: inspect(url, timeout), urls))
    results = [{**asdict(item), "occurrences": links[item.url]} for item in findings]
    return _report(results, documents, skipped, errors)


def _cell(value: object) -> str:
    """Prevent URL/error text from changing Markdown table or HTML structure."""
    return (
        html.escape(str(value), quote=True)
        .replace("|", "&#124;")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def markdown_report(report: dict) -> str:
    """Render findings as literal URLs, avoiding clickable archive-save actions."""
    lines = [
        "# CV PDF link report",
        "",
        f"Generated: {_cell(report['generated_at'])}",
        "",
        "## Coverage",
        "",
        "| Measure | Count |",
        "| --- | ---: |",
    ]
    for key, value in report["counts"].items():
        lines.append(f"| {_cell(key.replace('_', ' '))} | {value} |")
    for state, title in (
        ("broken", "Broken links"),
        ("unverified", "Unverified links"),
        ("manual-review", "Manual review"),
    ):
        lines.extend(["", f"## {title}", ""])
        selected = [item for item in report["results"] if item["status"] == state]
        if not selected:
            lines.append("None recorded.")
            continue
        lines.extend(["| URL | Source pages | Result |", "| --- | --- | --- |"])
        for item in selected:
            sources = "; ".join(
                f"{source['document']} p. {source['page']}"
                for source in item["occurrences"]
            )
            lines.append(
                f"| <code>{_cell(item['url'])}</code> | {_cell(sources)} | {_cell(item['detail'])} |"
            )
    lines.extend(["", "## Input errors", ""])
    if report["errors"]:
        lines.extend(["| Document | Error |", "| --- | --- |"])
        for error in report["errors"]:
            lines.append(f"| {_cell(error['document'])} | {_cell(error['detail'])} |")
    else:
        lines.append("None recorded.")
    lines.extend(
        [
            "",
            "## Scope and limits",
            "",
            "Only HTTP(S) annotation destinations are requested. Internal links, mailto links, and other URI schemes are skipped. Source pages are physical PDF page numbers.",
            "",
            "HTTP 404/410 responses are classified as broken only after a limited GET. Blocked requests, rate limits, server errors, TLS errors, and timeouts remain unverified. An absence of confirmed broken links does not mean all destinations were verified.",
            "",
            "Wayback /save endpoints are capture actions and require manual review; the checker does not request them or follow redirects to them. URL text is shown literally rather than as clickable capture links.",
            "",
            "A successful HTTP response does not validate page content, fragment anchors, or access beyond a login page. JSON includes all reachable results and skipped annotations.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(report: dict, report_dir: Path) -> None:
    """Write portable machine-readable and human-readable reports."""
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "links.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (report_dir / "links.md").write_text(markdown_report(report), encoding="utf-8")


class ReportArgumentParser(argparse.ArgumentParser):
    """Let the CLI emit a report for invalid arguments as well as PDF errors."""

    def error(self, message):
        raise ValueError(message)


def main(argv: list[str] | None = None) -> int:
    """Return 1 for confirmed broken links, 2 for input/configuration failures."""
    parser = ReportArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default="gen",
        help="Generated PDF directory, relative to the repository root.",
    )
    parser.add_argument(
        "--report-dir",
        default="gen/link-report",
        help="Report directory, relative to the repository root.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Request timeout in seconds, at most 60 (default: 10).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help="Concurrent URL checks, from 1 to 8 (default: 8).",
    )
    report_dir = ROOT / "gen/link-report"
    try:
        # Locate the output first so a malformed checker option still leaves
        # its diagnostic report where the caller explicitly requested it.
        locator = ReportArgumentParser(add_help=False)
        locator.add_argument("--report-dir", default="gen/link-report")
        located, _ = locator.parse_known_args(argv)
        report_dir = resolve_project_path(located.report_dir, root=ROOT)
        args = parser.parse_args(argv)
        report_dir = resolve_project_path(args.report_dir, root=ROOT)
        input_dir = resolve_project_path(args.input_dir, root=ROOT)
        report = audit_pdfs(input_dir, timeout=args.timeout, workers=args.workers)
    except Exception as error:
        report = _report(
            [],
            [],
            [],
            [
                {
                    "document": "configuration",
                    "detail": f"{type(error).__name__}: {error}",
                }
            ],
        )
    try:
        write_reports(report, report_dir)
    except OSError as error:
        print(f"Cannot write link reports: {error}", file=sys.stderr)
        return 2
    counts = report["counts"]
    print(
        f"PDF links: {counts['valid']} valid, {counts['broken']} broken, {counts['unverified']} unverified, {counts['manual-review']} manual review; reports: {report_dir}"
    )
    return 2 if report["errors"] else 1 if counts["broken"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
