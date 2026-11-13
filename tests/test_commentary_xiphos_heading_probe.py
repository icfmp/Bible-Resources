"""Original pinned SWORD intro vs actual private Xiphos context menu evidence."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_xiphos_heading_probe import (
    _intro_in_gui_clipboard, probe_real_xiphos_commentary_heading_menu,
)
from pilot_preflight import PilotError


class SourceNativeIntroContextMenuTests(unittest.TestCase):
    def test_actual_original_intro_prose_can_be_proven_without_copying_source_verse(self):
        intro = b"<p>" + b" ".join(("introductionword%02d" % x).encode() for x in range(20)) + b"</p>"
        gui = b"GUI header" + intro[3:-4] + b" trailing text"
        self.assertTrue(_intro_in_gui_clipboard(intro, gui, b"Unrelated commentary verse text"))
        self.assertFalse(_intro_in_gui_clipboard(intro, b"Unrelated GUI text", b"unrelated verse"))
        self.assertFalse(_intro_in_gui_clipboard(intro, gui, gui))

    def test_short_original_heading_can_be_verified_without_guessing_words(self):
        original=b"<title>Remarkable title of Genesis commentary</title>"
        self.assertTrue(_intro_in_gui_clipboard(
            original,b"GUI Remarkable title of Genesis commentary",
            b"Unrelated first verse exposition",
        ))
        self.assertFalse(_intro_in_gui_clipboard(
            original,b"GUI Remarkable title of Genesis commentary",
            b"Remarkable title of Genesis commentary",
        ))

    def test_invalid_private_reader_context_fails_closed(self):
        with self.assertRaisesRegex(PilotError,"Unreviewed"):
            probe_real_xiphos_commentary_heading_menu(
                {"DISPLAY": ":0", "GDK_BACKEND": "x11"}, {}, ordinary_first_verse=b"")

    def test_real_source_intro_not_available_is_not_missing_text(self):
        with patch("commentary_xiphos_heading_probe._main_xiphos_window",return_value="101"),\
             patch("commentary_xiphos_heading_probe._commentary_pane_focus_points",return_value=((1000,390),)):
            r=probe_real_xiphos_commentary_heading_menu(
                {"DISPLAY":":91","GDK_BACKEND":"x11"}, {}, ordinary_first_verse=b"commentary")
        self.assertFalse(r["heading_GUI_presentation_verified"])
        self.assertTrue(r["no_heading_missing_from_source_inferred"])
        self.assertEqual(set(r["book_and_chapter_menu_observations"]),{"book","chapter"})

    def test_no_real_window_is_not_a_heading_pass(self):
        with patch("commentary_xiphos_heading_probe._main_xiphos_window",return_value=None):
            r=probe_real_xiphos_commentary_heading_menu(
                {"DISPLAY":":91","GDK_BACKEND":"x11"}, {"book":b"original"},
                ordinary_first_verse=b"commentary")
        self.assertFalse(r["heading_context_real_main_reader_window_found"])
        self.assertFalse(r["heading_GUI_presentation_verified"])

    @patch("commentary_xiphos_heading_probe._intro_in_gui_clipboard",return_value=True)
    @patch("commentary_xiphos_heading_probe.time.sleep")
    @patch("commentary_xiphos_heading_probe._seed_x11_clipboard")
    @patch("commentary_xiphos_heading_probe._x11",return_value=b"unique original introduction")
    @patch("commentary_xiphos_heading_probe._commentary_pane_focus_points",return_value=((1000,390),))
    @patch("commentary_xiphos_heading_probe._main_xiphos_window",return_value="101")
    def test_both_real_menu_actions_are_required_before_positive_GUI_evidence(
        self,*_mocks
    ):
        intro={"book":b"<p>book intro</p>","chapter":b"<p>chapter intro</p>"}
        out=probe_real_xiphos_commentary_heading_menu(
            {"DISPLAY":":91","GDK_BACKEND":"x11"},intro,ordinary_first_verse=b"verse")
        self.assertTrue(out["heading_GUI_presentation_verified"])
        self.assertFalse(out["intro_data_or_clipboard_exported"])


if __name__=="__main__":
    unittest.main()
