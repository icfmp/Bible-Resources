"""No-leak, source-pinned sample prose checks for real AndBible WebViews."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_android_text_witness import (
    _actual_original_authorial_words,
    _actual_android_webview_word_sequences,
    original_prose_in_real_android_webview,
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
