"""No-leak, source-pinned sample prose checks for real AndBible WebViews."""
from __future__ import annotations
from pathlib import Path
import sys
import io
import tempfile
import subprocess
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_android_text_witness import (
    _actual_original_authorial_words,
    _actual_android_webview_word_sequences,
    original_prose_in_real_android_webview,
    read_only_actually_occupied_original_entries,
    full_native_original_prose_in_real_android_webview,
)
from pilot_preflight import PilotError
from probe_andbible_android_emulator import PACKAGE


def original(count=70):
    return ("<p>" + " ".join(
        "authenticatedauthorialword%03d" % n for n in range(count)
    ) + "</p>").encode()


def real_webview(*texts, extra_toolbar=None):
    root = ET.Element("hierarchy")
    if extra_toolbar is not None:
        ET.SubElement(root, "node", {
            "package": PACKAGE, "class": "android.widget.TextView",
            "text": extra_toolbar,
        })
    webview = ET.SubElement(root, "node", {
        "package": PACKAGE,
        "class": "android.webkit.WebView",
        "resource-id": PACKAGE + ":id/mainBibleView",
    })
    for text in texts:
        ET.SubElement(webview, "node", {
            "package": PACKAGE,
            "class": "android.view.View",
            "text": text,
        })
    return ET.tostring(root, encoding="utf-8")


class AndroidOriginalProseWitnessTests(unittest.TestCase):
    def test_exact_original_16_word_prose_with_real_webview_positive(self):
        prose = " ".join(
            "authenticatedauthorialword%03d" % i for i in range(20, 42)
        )
        result = original_prose_in_real_android_webview(
            {"Gen 1:1": original()},
            real_webview(prose, extra_toolbar="MHCC (en)"),
        )
        self.assertTrue(result["actual_original_prose_excerpt_in_Android_WebView_verified"])
        self.assertEqual(result["original_prose_sample_entries_with_16_consecutive_words_visible"], 1)
        self.assertEqual(result["real_AndBible_WebViews_observed"], 1)
        self.assertFalse(result["original_prose_UI_text_XML_screenshots_or_ZIP_exported"])
        self.assertNotIn(prose, str(result))
        self.assertNotIn("authenticatedauthorialword", str(result))

    def test_original_15_word_prose_is_not_enough(self):
        prose = " ".join(
            "authenticatedauthorialword%03d" % i for i in range(20, 35)
        )
        result = original_prose_in_real_android_webview(
            {"Gen 1:1": original()}, real_webview(prose),
        )
        self.assertFalse(result["actual_original_prose_excerpt_in_Android_WebView_verified"])

    def test_source_words_only_outside_webview_are_not_accepted(self):
        prose = " ".join(
            "authenticatedauthorialword%03d" % i for i in range(20, 45)
        )
        result = original_prose_in_real_android_webview(
            {"Gen 1:1": original()},
            real_webview("Actual Bible words differ", extra_toolbar=prose),
        )
        self.assertFalse(result["actual_original_prose_excerpt_in_Android_WebView_verified"])

    def test_source_is_not_approved_when_no_genuine_webview_exists(self):
        prose = " ".join(
            "authenticatedauthorialword%03d" % i for i in range(20, 45)
        )
        root = ET.Element("hierarchy")
        ET.SubElement(root, "node", {
            "package": PACKAGE, "class": "android.widget.TextView", "text": prose
        })
        observed = original_prose_in_real_android_webview(
            {"Gen 1:1": original()}, ET.tostring(root, encoding="utf-8"),
        )
        self.assertFalse(observed["actual_original_prose_excerpt_in_Android_WebView_verified"])
        self.assertEqual(observed["real_AndBible_WebViews_observed"], 0)

    def test_original_strict_markup_not_silently_repaired(self):
        self.assertEqual(_actual_original_authorial_words(
            b"<p>incomplete <b>authorial </p>"
        ), [])
        result = original_prose_in_real_android_webview(
            {"Gen 1:1": b"<p>broken </p><i>not closed"},
            real_webview("Authorial content cannot be inferred"),
        )
        self.assertEqual(result["status"], "inconclusive_no_source_prose_witness_in_accessibility")

    def test_adjacent_real_webview_descendants_can_form_paragraph(self):
        a = " ".join("authenticatedauthorialword%03d" % n for n in range(18, 29))
        b = " ".join("authenticatedauthorialword%03d" % n for n in range(29, 45))
        result = original_prose_in_real_android_webview(
            {"Gen 1:1": original()}, real_webview(a, b),
        )
        self.assertTrue(result["actual_original_prose_excerpt_in_Android_WebView_verified"])

    @patch("commentary_android_text_witness.subprocess.run")
    def test_nonoccupied_original_native_key_is_not_fabricated(self, run):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inspector = root / "native-reader"
            inspector.write_bytes(b"private compiled tool")
            raw = original()
            run.side_effect = [
                subprocess.CompletedProcess([], 0, stdout=raw),
                subprocess.CompletedProcess([], 9, stdout=b""),
                subprocess.CompletedProcess([], 0, stdout=raw),
            ]
            samples, absent = read_only_actually_occupied_original_entries(
                root, "MHCC", ["Gen 1:1", "John 3:16", "Rev 22:21"], inspector,
            )
            self.assertEqual(set(samples), {"Gen 1:1", "Rev 22:21"})
            self.assertEqual(absent, 1)
            self.assertEqual(samples["Gen 1:1"], raw)
            self.assertEqual(run.call_count, 3)

    @patch("commentary_android_text_witness.subprocess.run")
    def test_non_sparse_native_source_failure_never_becomes_absence(self, run):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inspector = root / "native-reader"
            inspector.write_bytes(b"private compiled tool")
            run.return_value = subprocess.CompletedProcess([], 7, stdout=b"")
            with self.assertRaisesRegex(PilotError, "reason other than"):
                read_only_actually_occupied_original_entries(
                    root, "MHCC", ["Gen 1:1", "John 3:16"], inspector,
                )
            run.return_value = subprocess.CompletedProcess([], 9, stdout=b"")
            with self.assertRaisesRegex(PilotError, "No actually occupied"):
                read_only_actually_occupied_original_entries(
                    root, "MHCC", ["Gen 1:1", "John 3:16"], inspector,
                )

    @patch("commentary_android_text_witness.parse_native_raw_corpus")
    @patch("commentary_android_text_witness.subprocess.Popen")
    def test_full_authenticated_native_scan_can_match_unexpected_occupied_key(
        self, popen, parser,
    ):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / "native-corpus-reader"
            executable.write_bytes(b"private compiled C++ scanner")
            proc = Mock()
            proc.stdout = io.BytesIO()
            proc.wait.return_value = 0
            proc.poll.return_value = 0
            popen.return_value = proc
            def stream(scan, *, on_entry):
                on_entry("K", "Gen.1.1", b"<p>Short verse without sustained exposition</p>")
                on_entry("K", "Obad.1.1", original(70))
                on_entry("I", "Gen.1", original(70))
                return ({
                    "all_native_raw_entries_ordered_sha256": "a" * 64,
                    "all_actual_raw_entries_scanned": 3,
                }, [], [], [])
            parser.side_effect = stream
            prose = " ".join(
                "authenticatedauthorialword%03d" % i for i in range(22, 40)
            )
            result = full_native_original_prose_in_real_android_webview(
                root, "MHCC", executable, "a" * 64, real_webview(prose),
            )
        self.assertTrue(result["original_full_native_corpus_sha256_attested"])
        self.assertEqual(result["actual_original_native_occupied_keys_scanned"], 3)
        self.assertEqual(result["source_occupied_entries_with_16_consecutive_words_visible"], 1)
        self.assertTrue(result["actual_original_authorial_prose_in_real_Android_WebView_verified"])
        self.assertFalse(result["source_words_android_UI_XML_screenshots_or_ZIP_exported"])
        self.assertNotIn("Obad", str(result))
        self.assertNotIn("authenticatedauthorialword", str(result))
        self.assertEqual(popen.call_count, 1)

    @patch("commentary_android_text_witness.parse_native_raw_corpus")
    @patch("commentary_android_text_witness.subprocess.Popen")
    def test_full_corpus_digest_mismatch_never_passes_prose(self, popen, parser):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scanner = root / "native-reader"
            scanner.write_bytes(b"private compiled C++ scanner")
            proc = Mock()
            proc.stdout = io.BytesIO()
            proc.wait.return_value = 0
            proc.poll.return_value = 0
            popen.return_value = proc
            parser.return_value = ({
                "all_native_raw_entries_ordered_sha256": "b" * 64,
                "all_actual_raw_entries_scanned": 29975,
            }, [], [], [])
            with self.assertRaisesRegex(PilotError, "digest"):
                full_native_original_prose_in_real_android_webview(
                    root, "MHCC", scanner, "a" * 64,
                    real_webview("genuine Android user interface prose"),
                )

    def test_untrusted_module_and_oversized_ui_fail_closed(self):
        with self.assertRaises(PilotError):
            original_prose_in_real_android_webview(
                {"Gen 1:0": original()}, real_webview("any"),
            )
        with self.assertRaises(PilotError):
            _actual_android_webview_word_sequences(b"x" * 3_000_001)
        with self.assertRaises(PilotError):
            _actual_original_authorial_words(b"x" * 256_001)


if __name__ == "__main__":
    unittest.main()
