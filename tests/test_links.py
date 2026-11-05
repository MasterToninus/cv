# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : tests/test_links.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-05
# |
# | Purpose           : Verify PDF link extraction and conservative HTTP reporting offline.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261105  Miti/Codex   Cover annotation sources, HTTP fallbacks, and error reports.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Check link auditing with synthetic PDFs and mocked HTTP; never use the network."""

import json
import os
import tempfile
import unittest
import urllib.error
import urllib.request
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from cvgen.helpers import links
from cvgen.helpers.formats import OUTPUT_STEMS

URL = "https://example.test/publication"


def make_pdf(path, pages):
    """Create page links directly so fixtures do not depend on TeX or HTTP."""
    writer = PdfWriter()
    for uris in pages:
        page = writer.add_blank_page(width=595, height=842)
        annotations = []
        for uri in uris:
            annotation = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Link"),
                    NameObject("/Rect"): ArrayObject(
                        [NumberObject(n) for n in (0, 0, 10, 10)]
                    ),
                }
            )
            if uri is None:
                annotation[NameObject("/Dest")] = TextStringObject("section")
            else:
                annotation[NameObject("/A")] = DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/URI"),
                        NameObject("/URI"): TextStringObject(uri),
                    }
                )
            annotations.append(writer._add_object(annotation))
        page[NameObject("/Annots")] = ArrayObject(annotations)
    writer.write(path)


def make_input_set(directory):
    for stem in OUTPUT_STEMS.values():
        make_pdf(directory / (stem + ".pdf"), [[URL]])


class Response:
    def __init__(self, status=200, url=URL):
        self.status = status
        self.url = url
        self.read_sizes = []
        self.closed = False

    def geturl(self):
        return self.url

    def read(self, size):
        self.read_sizes.append(size)
        return b"x"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


def http_error(status):
    return urllib.error.HTTPError(URL, status, "Test status", {}, BytesIO())


class PdfLinkExtractionTests(unittest.TestCase):
    def test_deduplicates_urls_and_pages_across_all_four_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            make_input_set(directory)
            first = next(iter(OUTPUT_STEMS.values())) + ".pdf"
            make_pdf(
                directory / first,
                [[URL, URL, "mailto:person@example.test", None], [URL]],
            )
            urls, documents, skipped, errors = links.extract_links(directory)
            self.assertFalse(errors)
            self.assertEqual(len(documents), 4)
            self.assertEqual(list(urls), [URL])
            self.assertEqual(len(urls[URL]), 5)
            self.assertEqual(
                urls[URL][:2],
                [{"document": first, "page": 1}, {"document": first, "page": 2}],
            )
            self.assertEqual(len(skipped), 2)
            self.assertEqual(skipped[0]["uri"], "mailto:person@example.test")
            self.assertIsNone(skipped[1]["uri"])

    def test_missing_and_invalid_pdfs_prevent_network_checks(self):
        for failure in ("missing", "invalid"):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                make_input_set(directory)
                first = directory / (next(iter(OUTPUT_STEMS.values())) + ".pdf")
                if failure == "missing":
                    first.unlink()
                else:
                    first.write_bytes(b"this is not a PDF")
                inspect = Mock()
                report = links.audit_pdfs(directory, checker=inspect)
                inspect.assert_not_called()
                self.assertEqual(report["counts"]["input_errors"], 1)
                self.assertEqual(report["counts"]["documents_read"], 3)
                self.assertEqual(report["counts"]["network_attempted"], 0)

    def test_encrypted_pdf_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            make_input_set(directory)
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            writer.encrypt("secret")
            writer.write(directory / "Cv-Industry.pdf")
            report = links.audit_pdfs(directory, checker=Mock())
            self.assertIn("Encrypted PDFs", report["errors"][0]["detail"])

    def test_checker_runs_once_for_a_shared_url_and_retains_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            make_input_set(directory)
            inspect = Mock(
                return_value=links.LinkResult(URL, "valid", 200, URL, "HEAD")
            )
            report = links.audit_pdfs(directory, timeout=3.5, checker=inspect)
            inspect.assert_called_once_with(URL, 3.5)
            self.assertEqual(report["counts"]["valid"], 1)
            self.assertEqual(report["counts"]["source_page_occurrences"], 4)


class HttpLinkTests(unittest.TestCase):
    def inspect(self, outcomes):
        opener = Mock()
        opener.open.side_effect = outcomes
        with patch.object(links.urllib.request, "build_opener", return_value=opener):
            result = links.check_url(URL, timeout=4)
        return result, opener

    def test_head_success_preserves_the_resolved_url_and_does_not_read_a_body(self):
        response = Response(url="https://destination.test/paper")
        result, opener = self.inspect([response])
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.final_url, response.url)
        self.assertEqual(result.method, "HEAD")
        self.assertEqual(response.read_sizes, [])
        self.assertTrue(response.closed)
        self.assertEqual(opener.open.call_args.args[0].get_method(), "HEAD")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 4)

    def test_rejected_head_falls_back_to_a_limited_get(self):
        for status in (400, 403, 405, 406, 501):
            with self.subTest(status=status):
                response = Response(status=206)
                result, opener = self.inspect([http_error(status), response])
                self.assertEqual(result.status, "valid")
                request = opener.open.call_args.args[0]
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(request.get_header("Range"), "bytes=0-0")
                self.assertEqual(response.read_sizes, [1])

    def test_404_and_410_need_get_confirmation(self):
        for status in (404, 410):
            with self.subTest(status=status):
                result, opener = self.inspect([http_error(status), http_error(status)])
                self.assertEqual(result.status, "broken")
                self.assertEqual(result.http_status, status)
                self.assertEqual(result.method, "GET")
                self.assertEqual(opener.open.call_count, 2)

    def test_head_404_with_successful_get_is_reachable(self):
        result, _ = self.inspect([http_error(404), Response()])
        self.assertEqual(result.status, "valid")

    def test_head_404_followed_by_a_blocked_get_remains_unverified(self):
        result, _ = self.inspect([http_error(404), http_error(403)])
        self.assertEqual(result.status, "unverified")
        self.assertEqual(result.http_status, 403)

    def test_rate_limits_server_errors_and_network_failures_are_not_broken(self):
        for outcome in (
            http_error(429),
            http_error(500),
            http_error(503),
            TimeoutError("timed out"),
            urllib.error.URLError("TLS failure"),
        ):
            with self.subTest(outcome=type(outcome).__name__):
                result, opener = self.inspect([outcome])
                self.assertEqual(result.status, "unverified")
                self.assertEqual(opener.open.call_count, 1)

    def test_archive_capture_endpoints_are_not_requested(self):
        with patch.object(links.urllib.request, "build_opener") as create:
            for url in (
                "https://web.archive.org/save",
                "http://web.archive.org/save/https://example.test",
                "https://web.archive.org/save?url=https://example.test",
            ):
                self.assertEqual(links.check_url(url).status, "manual-review")
            create.assert_not_called()

    def test_redirect_handler_follows_http_but_blocks_capture_and_nonweb_targets(self):
        handler = links.ReadOnlyRedirectHandler()
        request = urllib.request.Request(URL, method="HEAD")
        redirected = handler.redirect_request(
            request, None, 302, "Found", {}, "https://destination.test"
        )
        self.assertEqual(redirected.full_url, "https://destination.test")
        self.assertEqual(redirected.get_method(), "HEAD")
        for url in (
            "https://web.archive.org/save/https://example.test",
            "ftp://example.test/file",
        ):
            with self.subTest(url=url), self.assertRaises(links.ManualReviewRedirect):
                handler.redirect_request(request, None, 302, "Found", {}, url)

    def test_a_redirect_to_capture_is_reported_as_manual_review(self):
        result, opener = self.inspect(
            [
                links.ManualReviewRedirect(
                    "https://web.archive.org/save/https://example.test",
                    "Capture action",
                )
            ]
        )
        self.assertEqual(result.status, "manual-review")
        self.assertEqual(opener.open.call_count, 1)

    def test_malformed_http_url_is_unverified_without_a_request(self):
        with patch.object(links.urllib.request, "build_opener") as create:
            for url in ("https://", "http://[", "https://example.test:invalid"):
                self.assertEqual(links.check_url(url).status, "unverified")
            create.assert_not_called()


class LinkReportCliTests(unittest.TestCase):
    def test_report_escapes_url_and_error_text_and_explains_unknown_coverage(self):
        url = 'https://example.test/a|b?x=<script>&quote="yes"'
        report = links._report(
            [
                {
                    **links.asdict(
                        links.LinkResult(
                            url, "unverified", detail="Blocked | <tag>\nsecond line"
                        )
                    ),
                    "occurrences": [{"document": "Cv-Academic.pdf", "page": 2}],
                }
            ],
            [],
            [],
            [],
        )
        rendered = links.markdown_report(report)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<tag>", rendered)
        self.assertIn("&#124;", rendered)
        self.assertIn("&quot;yes&quot;", rendered)
        self.assertIn("Cv-Academic.pdf p. 2", rendered)
        self.assertIn("does not mean all destinations were verified", rendered)

    def test_cli_returns_one_for_confirmed_broken_links_and_keeps_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            make_input_set(directory)
            report_dir = directory / "reports"
            result = links.LinkResult(URL, "broken", 404, URL, "GET", "Confirmed 404")
            with (
                patch.object(links, "check_url", return_value=result),
                patch("sys.stdout", new_callable=StringIO),
            ):
                status = links.main(
                    ["--input-dir", str(directory), "--report-dir", str(report_dir)]
                )
            self.assertEqual(status, 1)
            self.assertEqual(
                json.loads((report_dir / "links.json").read_text())["counts"]["broken"],
                1,
            )
            self.assertTrue((report_dir / "links.md").is_file())

    def test_unknown_urls_do_not_fail_the_cli_or_claim_successful_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            make_input_set(directory)
            report_dir = directory / "reports"
            with (
                patch.object(
                    links,
                    "check_url",
                    return_value=links.LinkResult(URL, "unverified", detail="429"),
                ),
                patch("sys.stdout", new_callable=StringIO),
            ):
                status = links.main(
                    ["--input-dir", str(directory), "--report-dir", str(report_dir)]
                )
            report = json.loads((report_dir / "links.json").read_text())
            self.assertEqual(status, 0)
            self.assertEqual(report["counts"]["valid"], 0)
            self.assertEqual(report["counts"]["unverified"], 1)

    def test_missing_pdfs_emit_both_reports_and_exit_two(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            report_dir = directory / "reports"
            with (
                patch.object(links.urllib.request, "build_opener") as create,
                patch("sys.stdout", new_callable=StringIO),
            ):
                status = links.main(
                    ["--input-dir", str(directory), "--report-dir", str(report_dir)]
                )
            create.assert_not_called()
            self.assertEqual(status, 2)
            self.assertEqual(
                json.loads((report_dir / "links.json").read_text())["counts"][
                    "input_errors"
                ],
                4,
            )
            self.assertTrue((report_dir / "links.md").is_file())

    def test_invalid_arguments_keep_the_explicit_report_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            report_dir = Path(temporary) / "custom-reports"
            with (
                patch.object(links.urllib.request, "build_opener") as create,
                patch("sys.stdout", new_callable=StringIO),
            ):
                status = links.main(
                    ["--workers", "invalid", "--report-dir", str(report_dir)]
                )
            create.assert_not_called()
            self.assertEqual(status, 2)
            self.assertTrue((report_dir / "links.json").is_file())
            self.assertTrue((report_dir / "links.md").is_file())

    def test_relative_paths_use_the_repository_root_instead_of_the_callers_cwd(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            tempfile.TemporaryDirectory() as elsewhere,
        ):
            root = Path(temporary)
            (root / "pdfs").mkdir()
            make_input_set(root / "pdfs")
            original = Path.cwd()
            try:
                os.chdir(elsewhere)
                with (
                    patch.object(links, "ROOT", root),
                    patch.object(
                        links,
                        "check_url",
                        return_value=links.LinkResult(URL, "valid", 200),
                    ),
                    patch("sys.stdout", new_callable=StringIO),
                ):
                    status = links.main(
                        ["--input-dir", "pdfs", "--report-dir", "reports"]
                    )
            finally:
                os.chdir(original)
            self.assertEqual(status, 0)
            self.assertTrue((root / "reports/links.json").is_file())

    def test_invalid_configuration_and_arguments_emit_an_error_report(self):
        for arguments in (
            ["--workers", "9"],
            ["--timeout", "0"],
            ["--workers", "invalid"],
        ):
            with (
                self.subTest(arguments=arguments),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                with (
                    patch.object(links, "ROOT", directory),
                    patch("sys.stdout", new_callable=StringIO),
                ):
                    status = links.main(arguments)
                report_dir = directory / "gen/link-report"
                self.assertEqual(status, 2)
                report = json.loads((report_dir / "links.json").read_text())
                self.assertEqual(report["errors"][0]["document"], "configuration")
                self.assertTrue((report_dir / "links.md").is_file())


if __name__ == "__main__":
    unittest.main()
