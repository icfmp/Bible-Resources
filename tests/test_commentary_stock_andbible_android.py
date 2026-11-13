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


    @patch("commentary_stock_andbible_android.adb")
    def test_only_active_or_resumed_original_app_counts_as_foreground(self, adb):
        from commentary_stock_andbible_android import _app_focus_witness
        adb.side_effect = [
            b"mCurrentFocus=Window{11 com.android.documentsui/.Files}\n",
            b"Recent activities include net.bible.android.activity but nothing resumed\n",
        ]
        self.assertEqual(_app_focus_witness(), [])
        adb.side_effect = [
            b"mCurrentFocus=Window{42 net.bible.android.activity/MainActivity}\n",
            b"",
        ]
        self.assertEqual(_app_focus_witness(), ["focused_window"])
        adb.side_effect = [
            b"",
            b"topResumedActivity=ActivityRecord{12 net.bible.android.activity/.MainActivity}\n",
        ]
        self.assertEqual(_app_focus_witness(), ["top_resumed_activity"])

    @patch("commentary_stock_andbible_android.adb")
    def test_reference_intent_must_have_actual_activity_manager_acceptance(self, adb):
        from commentary_stock_andbible_android import _dispatch_documented_reference
        manifest = {"module_id": "MHCC", "sample_references": ["Gen 1:1"]}
        adb.return_value = b""
        self.assertFalse(_dispatch_documented_reference(manifest))
        adb.return_value = b"Error: Activity not found"
        self.assertFalse(_dispatch_documented_reference(manifest))
        adb.return_value = b"Starting: Intent { act=android.intent.action.VIEW }"
        self.assertTrue(_dispatch_documented_reference(manifest))
        self.assertIn("read.andbible.org/Gen.1.1", adb.call_args.args[6])


    def test_only_confirmed_system_launcher_anr_can_expose_close_app(self):
        xml = b'''<hierarchy>
          <node text="Pixel Launcher isn't responding" bounds="[40,400][760,600]"/>
          <node text="Close app" bounds="[80,850][600,970]"/>
          <node text="Wait" bounds="[80,970][600,1080]"/>
        </hierarchy>'''
        result = safe_controls(xml, "MHCC", TITLE)
        self.assertIn("CLOSE APP", [r["action"] for r in result["controls"]])
        unsafe = safe_controls(
            xml.replace(b"Pixel Launcher isn't responding",
                        b"AndBible isn't responding"),
            "MHCC", TITLE,
        )
        self.assertNotIn("CLOSE APP", [r["action"] for r in unsafe["controls"]])

    @patch("commentary_stock_andbible_android.time.sleep")
    @patch("commentary_stock_andbible_android.adb")
    @patch("commentary_stock_andbible_android._screen")
    def test_bounded_startup_recovers_transient_wait_overlay(self, screen, adb, _sleep):
        from commentary_stock_andbible_android import _start_bounded_android_import
        screen.side_effect = [
            {"controls":[{"action":"WAIT","x":200,"y":300}]},
            {"controls":[{"action":"LOAD DOCUMENTS FROM FILES","x":400,"y":600}]},
        ]
        out = _start_bounded_android_import("MHCC", TITLE)
        self.assertEqual(out["recovery_actions"], ["WAIT"])
        self.assertEqual(out["startup_snapshots_checked"], 2)
        self.assertEqual(out["import_button"], "LOAD DOCUMENTS FROM FILES")
        self.assertEqual(adb.call_count, 2)

    @patch("commentary_stock_andbible_android.time.sleep")
    @patch("commentary_stock_andbible_android._screen")
    def test_bounded_startup_still_fails_if_real_import_never_appears(self, screen, _sleep):
        from commentary_stock_andbible_android import _start_bounded_android_import
        screen.return_value = {"controls": []}
        with self.assertRaisesRegex(PilotError, "after bounded recovery"):
            _start_bounded_android_import("MHCC", TITLE)
        self.assertEqual(screen.call_count, 6)


if __name__ == "__main__":
    unittest.main()
