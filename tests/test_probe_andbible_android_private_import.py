"""Bounded Android UI metadata parsing; never accept arbitrary content."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from probe_andbible_android_private_import import (
    safe_controls, tap_allowlisted, AndroidDarbyImportError,
)


class AndBiblePrivateImportUiTest(unittest.TestCase):
    def test_documented_real_stable_startup_control_is_readable(self):
        xml=b"""<?xml version='1.0' encoding='utf-8'?>
<hierarchy rotation="0">
  <node text="AndBible: Bible Study" bounds="[0,0][1080,2000]"/>
  <node text="LOAD DOCUMENTS FROM FILES"
        content-desc="" bounds="[64,1310][978,1475]"/>
  <node text="EASY START" bounds="[64,1030][978,1175]"/>
</hierarchy>"""
        values=safe_controls(xml)
        self.assertEqual(values[0]["label"],"LOAD DOCUMENTS FROM FILES")
        self.assertEqual(values[0]["x"],521)
        self.assertEqual(values[0]["y"],1392)
        self.assertTrue(any(c["label"]=="EASY START" for c in values))
        self.assertFalse(any("Bible Study" in c["label"] for c in values))

    def test_actual_andbible_file_import_confirmation_is_restricted(self):
        dialog=b"""<hierarchy>
          <node text="PROCEED" bounds="[625,1140][785,1240]"/>
          <node text="CANCEL" bounds="[80,1140][280,1240]"/>
          <node text="Load Documents From Files" bounds="[100,500][700,570]"/>
        </hierarchy>"""
        controls=safe_controls(dialog)
        self.assertIn("PROCEED",[c["label"] for c in controls])
        with patch("probe_andbible_android_private_import.adb") as adb, \
             patch("probe_andbible_android_private_import.time.sleep"):
            self.assertEqual(tap_allowlisted(controls,("PROCEED",)),"PROCEED")
            adb.assert_called_once()

    def test_file_picker_identifies_only_explicit_private_candidate(self):
        xml=b"""<hierarchy>
          <node text="JND2024RepairResearch.zip" bounds="[80,620][1000,740]"/>
          <node text="public-sword-other.zip" bounds="[80,740][1000,850]"/>
          <node text="Downloads" bounds="[65,140][1000,220]"/>
        </hierarchy>"""
        labels=[x["label"] for x in safe_controls(xml)]
        self.assertEqual(labels,["JND2024REPAIRRESEARCH.ZIP","DOWNLOADS"])

    def test_actual_android_recent_file_card_shortened_title_is_candidate(self):
        # Recorded Pixel 4 DocumentsUI screenshot after pressing PROCEED:
        # JND2024Repai... at 1.96 MB is the sole private uploaded ZIP.
        xml="""<hierarchy>
          <node text="Recent" bounds="[200,40][600,150]"/>
          <node text="JND2024Repai…" bounds="[58,390][400,852]"/>
          <node text="an unrelated.zip" bounds="[58,855][400,1250]"/>
        </hierarchy>""".encode("utf-8")
        controls=safe_controls(xml)
        self.assertEqual(len(controls),1)
        self.assertEqual(controls[0]["label"],"JND2024REPAIRRESEARCH.ZIP")
        self.assertEqual(controls[0]["x"],229)
        self.assertEqual(controls[0]["y"],621)

    def test_out_of_screen_or_invalid_xml_is_rejected_or_ignored(self):
        self.assertEqual(safe_controls(b"<notxml"),[])
        self.assertEqual(safe_controls(b"""<hierarchy>
         <node text="INSTALL" bounds="[9999,0][9999,220]"/>
         <node text="INSTALL" bounds="[900,200][500,300]"/>
        </hierarchy>"""),[])
        with self.assertRaises(AndroidDarbyImportError):
            safe_controls(b"x" * 3_000_001)

    def test_pointer_only_clicks_allowlisted_real_controls(self):
        candidates=[{"label":"DOWNLOADS","x":500,"y":190}]
        with self.assertRaises(AndroidDarbyImportError):
            tap_allowlisted(candidates,("PURCHASE PREMIUM",))
        with patch("probe_andbible_android_private_import.adb") as adb, \
             patch("probe_andbible_android_private_import.time.sleep"):
            self.assertEqual(tap_allowlisted(candidates,("DOWNLOADS",)),"DOWNLOADS")
            adb.assert_called_once_with(
                "shell","input","tap","500","190",timeout=12)


if __name__=="__main__":
    unittest.main()
