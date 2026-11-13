"""Synthetic Android UI interaction safety checks for pinned original zCom stock."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_stock_andbible_android import (
    safe_controls, _tap, _reference_uri, _screenshot_sha256, _app_foreground,
)
from pilot_preflight import PilotError

TITLE = "Matthew Henry's Concise Commentary on the Whole Bible"


class CommentaryAndroidStockTests(unittest.TestCase):
    def test_actual_module_zip_filename_but_not_arbitrary_source_text_is_selectable(self):
        xml = b"""<hierarchy>
            <node text="MHCC.zip" bounds="[100,250][600,350]"/>
            <node text="DOWNLOADS" bounds="[100,550][650,670]"/>
            <node text="Commentary authorial prose should never be exported"
                  bounds="[100,800][750,900]"/>
            <node text="Delete everything" bounds="[200,950][750,1030]"/>
        </hierarchy>"""
        result = safe_controls(xml, "MHCC", TITLE)
        self.assertEqual([x["action"] for x in result["controls"]],
                         ["EXACT_MODULE_ZIP", "DOWNLOADS"])
        self.assertFalse(result["reader_module_metadata_detected"])

    def test_metadata_identity_not_file_picker_filename_is_reader_witness(self):
        xml = (b'<hierarchy><node text="MHCC" bounds="[50,100][600,200]"/>'
               b'<node text="MHCC.zip" bounds="[50,200][600,300]"/></hierarchy>')
        self.assertTrue(
            safe_controls(xml, "MHCC", TITLE)["reader_module_metadata_detected"]
        )
        self.assertFalse(
            safe_controls(xml.replace(b'text="MHCC"', b'text="Other"'), "MHCC", TITLE)
            ["reader_module_metadata_detected"]
        )

    def test_malformed_or_oversized_ui_does_not_forge_success(self):
        self.assertFalse(safe_controls(b"<broken", "MHCC", TITLE)["controls"])
        with self.assertRaisesRegex(PilotError, "Unsafe"):
            safe_controls(b"x" * 3_000_001, "MHCC", TITLE)
        with self.assertRaises(PilotError):
            safe_controls(b"<hierarchy/>", "../evil", TITLE)

    def test_rejects_coordinates_beyond_real_Android_screen(self):
        xml = b'<hierarchy><node text="MHCC.zip" bounds="[2,100][9999,250]"/></hierarchy>'
        self.assertFalse(safe_controls(xml, "MHCC", TITLE)["controls"])

    def test_tap_must_be_exact_safe_allowlisted_ui_control(self):
        buttons = [{"action":"EXACT_MODULE_ZIP","x":520,"y":900}]
        with patch("commentary_stock_andbible_android.adb") as adb, \
             patch("commentary_stock_andbible_android.time.sleep"):
            self.assertEqual(_tap(buttons, ("EXACT_MODULE_ZIP",)), "EXACT_MODULE_ZIP")
        self.assertEqual(adb.call_args.args[:3], ("shell", "input", "tap"))
        with self.assertRaisesRegex(PilotError, "Unreviewed"):
            _tap(buttons, ("DELETE FILES",))

    def test_deep_link_is_derived_from_reviewed_manifest_sample(self):
        url = _reference_uri({"module_id":"MHCC","sample_references":["Gen 1:1"]})
        self.assertEqual(
            url,
            "https://read.andbible.org/Gen.1.1?document=MHCC&v11n=KJV"
        )
        with self.assertRaisesRegex(PilotError, "Unreviewed"):
            _reference_uri({"module_id":"MHCC","sample_references":["Gen 1:1;evil"]})

    @patch("commentary_stock_andbible_android.adb")
    def test_screen_image_is_hashed_but_not_saved(self, adb):
        adb.return_value = b"\x89PNG\r\n\x1a\n" + b"some bytes" * 500
        self.assertEqual(len(_screenshot_sha256()), 64)
        self.assertEqual(adb.call_args.args[:3], ("exec-out", "screencap", "-p"))

    @patch("commentary_stock_andbible_android.adb")
    def test_only_actual_foreground_android_app_counts(self, adb):
        adb.return_value = b"mCurrentFocus=Window{42 net.bible.android.activity/MainActivity}\n"
        self.assertTrue(_app_foreground())
        adb.return_value = b"mCurrentFocus=Window{42 com.android.documentsui/MainActivity}\n"
        self.assertFalse(_app_foreground())


if __name__ == "__main__":
    unittest.main()
