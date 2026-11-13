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


    def test_real_toolbar_resource_id_and_exact_original_commentary_popup_only(self):
        # AndBible main_bible_view.xml -> commentaryButton; menuForDocs uses
        # "<abbreviation> (language)". Full MHC is NOT concise MHCC.
        xml = b'''<hierarchy>
          <node class="android.widget.ImageButton"
                resource-id="net.bible.android.activity:id/commentaryButton"
                content-desc="Commentary" bounds="[850,180][955,295]"/>
          <node class="android.widget.TextView"
                text="MHC (en)" bounds="[520,430][980,550]"/>
          <node class="android.widget.TextView"
                text="MHCC (en)" bounds="[520,560][980,680]"/>
        </hierarchy>'''
        out = safe_controls(xml, "MHCC", TITLE)
        self.assertEqual(
            [item["action"] for item in out["controls"]],
            ["OPEN_COMMENTARY_MENU", "EXACT_COMMENTARY_MENU_MODULE"],
        )
        self.assertFalse(out["reader_module_metadata_detected"])
        no_concise = safe_controls(xml.replace(b"MHCC (en)", b"MHC (en)"), "MHCC", TITLE)
        self.assertEqual(
            [item["action"] for item in no_concise["controls"]],
            ["OPEN_COMMENTARY_MENU"],
        )

    def test_spoofed_commentary_text_without_exact_toolbar_id_is_not_tappable(self):
        wrong_id = b'''<hierarchy>
          <node text="Commentary" content-desc="Commentary"
                resource-id="net.bible.android.activity:id/workspaceButton"
                bounds="[850,180][955,295]"/>
        </hierarchy>'''
        out = safe_controls(wrong_id, "MHCC", TITLE)
        self.assertNotIn("OPEN_COMMENTARY_MENU",
                         [item["action"] for item in out["controls"]])

    @patch("commentary_stock_andbible_android._screenshot_sha256", side_effect=["a"*64, "b"*64])
    @patch("commentary_stock_andbible_android._tap")
    @patch("commentary_stock_andbible_android._screen")
    def test_exact_concise_menu_selection_and_identity_are_separate(self, screen, tap, _sha):
        from commentary_stock_andbible_android import _attempt_commentary_toolbar_selection
        screen.side_effect = [
            {"controls":[{"action":"OPEN_COMMENTARY_MENU","x":900,"y":240}],
             "reader_module_metadata_detected":False},
            {"controls":[{"action":"EXACT_COMMENTARY_MENU_MODULE","x":820,"y":580}],
             "reader_module_metadata_detected":False},
            {"controls":[],"reader_module_metadata_detected":True},
        ]
        tap.side_effect = ["OPEN_COMMENTARY_MENU", "EXACT_COMMENTARY_MENU_MODULE"]
        out = _attempt_commentary_toolbar_selection("MHCC", TITLE)
        self.assertTrue(out["actual_commentary_toolbar_resource_found"])
        self.assertTrue(out["exact_original_commentary_popup_item_found"])
        self.assertTrue(out["exact_original_commentary_menu_item_tapped"])
        self.assertTrue(out["reader_source_identity_witness_after_selection"])
        self.assertTrue(out["reader_screen_changed_after_selection"])
        self.assertFalse(out["possible_auto_switch_without_menu"])

    @patch("commentary_stock_andbible_android._screenshot_sha256", side_effect=["a"*64, "a"*64])
    @patch("commentary_stock_andbible_android._tap")
    @patch("commentary_stock_andbible_android._screen")
    def test_only_full_MHC_popup_never_counts_as_MHCC_selection(self, screen, tap, _sha):
        from commentary_stock_andbible_android import _attempt_commentary_toolbar_selection
        screen.side_effect = [
            {"controls":[{"action":"OPEN_COMMENTARY_MENU","x":900,"y":240}],
             "reader_module_metadata_detected":False},
            {"controls":[],"reader_module_metadata_detected":False},
            {"controls":[],"reader_module_metadata_detected":False},
        ]
        tap.return_value = "OPEN_COMMENTARY_MENU"
        out = _attempt_commentary_toolbar_selection("MHCC", TITLE)
        self.assertTrue(out["actual_commentary_toolbar_resource_found"])
        self.assertFalse(out["exact_original_commentary_popup_item_found"])
        self.assertFalse(out["exact_original_commentary_menu_item_tapped"])
        self.assertFalse(out["reader_source_identity_witness_after_selection"])
        self.assertFalse(out["reader_screen_changed_after_selection"])
        self.assertEqual(tap.call_count, 1)

    @patch("commentary_stock_andbible_android._tap")
    @patch("commentary_stock_andbible_android._screen")
    def test_missing_toolbar_never_claims_source_selection(self, screen, tap):
        from commentary_stock_andbible_android import _attempt_commentary_toolbar_selection
        screen.return_value = {"controls":[],"reader_module_metadata_detected":False}
        tap.return_value = None
        out = _attempt_commentary_toolbar_selection("MHCC", TITLE)
        self.assertFalse(out["actual_commentary_toolbar_resource_found"])
        self.assertFalse(out["exact_original_commentary_menu_item_tapped"])
        self.assertFalse(out["reader_source_identity_witness_after_selection"])


    def test_main_reader_resource_ids_are_checked_without_exporting_unknown_ui_text(self):
        from commentary_stock_andbible_android import _classify_main_reader_context
        xml = b'''<hierarchy>
            <node resource-id="net.bible.android.activity:id/bibleButton"
                  text="Private Bible passage" bounds="[10,200][90,300]"/>
            <node resource-id="net.bible.android.activity:id/optionsMenu"
                  content-desc="More options" bounds="[950,200][1040,300]"/>
            <node resource-id="net.bible.android.activity:id/otherUnknown"
                  text="Private user note" bounds="[10,300][900,390]"/>
        </hierarchy>'''
        output = _classify_main_reader_context(
            xml,
            b"topResumedActivity=ActivityRecord{12 net.bible.android.activity/net.bible.android.view.activity.page.MainBibleActivity}\n",
        )
        self.assertEqual(output["known_reader_toolbar_resource_ids_visible"],
                         ["bibleButton", "optionsMenu"])
        self.assertTrue(output["main_bible_reader_activity_resumed"])
        self.assertFalse(output["another_andbible_activity_resumed"])
        self.assertNotIn("Private user note", str(output))
        self.assertFalse(output["actual_commentary_rendering_verified"])

    def test_missing_reader_window_is_not_a_mhcc_data_failure(self):
        from commentary_stock_andbible_android import _classify_main_reader_context
        state = _classify_main_reader_context(
            b"<hierarchy/>",
            b"topResumedActivity=ActivityRecord{42 net.bible.android.activity/net.bible.android.view.activity.download.DocumentDownloadActivity}\n",
        )
        self.assertFalse(state["main_bible_reader_activity_resumed"])
        self.assertTrue(state["another_andbible_activity_resumed"])
        self.assertEqual(state["known_reader_toolbar_resource_ids_visible"], [])

    def test_context_diagnostics_reject_unbounded_inputs(self):
        from commentary_stock_andbible_android import _classify_main_reader_context
        with self.assertRaisesRegex(PilotError, "Unbounded"):
            _classify_main_reader_context(b"x"*3_000_001, b"")
        with self.assertRaisesRegex(PilotError, "Unbounded"):
            _classify_main_reader_context(b"", b"x"*4_000_001)


if __name__ == "__main__":
    unittest.main()
