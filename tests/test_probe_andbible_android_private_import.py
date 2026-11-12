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
