"""Bounded Android UI metadata parsing; never accept arbitrary content."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from probe_andbible_android_private_import import (
    safe_controls, tap_allowlisted, relaunch_for_persistence,
    open_documented_reference_probe, probe_observed_note_marker,
    probe_observed_corrected_colossians_link,
    probe_observed_omitted_host_caller,
    probe_observed_omitted_note_printed_link,
    AndroidDarbyImportError,
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

    def test_observed_upgrade_announcement_has_only_explicit_dismissal_controls(self):
        xml=b"""<hierarchy>
            <node text="Application has been upgraded!" bounds="[60,375][775,650]"/>
            <node text="DISMISS" bounds="[90,1280][290,1350]"/>
            <node text="DISMISS UNTIL NEXT UPDATE" bounds="[290,1280][770,1350]"/>
            <node text="Please see the video" bounds="[90,960][720,1060]"/>
        </hierarchy>"""
        controls=safe_controls(xml)
        self.assertEqual([c["label"] for c in controls],
                         ["DISMISS","DISMISS UNTIL NEXT UPDATE"])
        with patch("probe_andbible_android_private_import.adb") as adb, \
             patch("probe_andbible_android_private_import.time.sleep"):
            self.assertEqual(tap_allowlisted(controls,("DISMISS",)), "DISMISS")
            adb.assert_called_once()

    def test_only_known_launcher_anr_exposes_close_app(self):
        xml=b"""<hierarchy>
          <node text="Pixel Launcher isn\'t responding" bounds="[40,500][800,600]"/>
          <node text="Close app" bounds="[70,880][760,970]"/>
          <node text="Wait" bounds="[70,980][760,1070]"/>
          <node text="LOAD DOCUMENTS FROM FILES" bounds="[30,1350][790,1450]"/>
        </hierarchy>"""
        controls=safe_controls(xml)
        self.assertIn("WAIT", [control["label"] for control in controls])
        self.assertIn("CLOSE APP", [control["label"] for control in controls])
        unsafe=safe_controls(xml.replace(b"Pixel Launcher isn\'t responding", b"AndBible isn\'t responding"))
        self.assertNotIn("CLOSE APP", [control["label"] for control in unsafe])
        with patch("probe_andbible_android_private_import.adb") as adb, \
             patch("probe_andbible_android_private_import.time.sleep"):
            self.assertEqual(tap_allowlisted(controls,("CLOSE APP",)), "CLOSE APP")
            adb.assert_called_once()

    def test_relaunch_only_restarts_official_app_without_reimport(self):
        with (patch("probe_andbible_android_private_import.adb") as adb,
              patch("probe_andbible_android_private_import.time.sleep") as sleep):
            relaunch_for_persistence()
        self.assertEqual(adb.call_count, 2)
        self.assertEqual(adb.call_args_list[0].args[:4],
                         ("shell", "am", "force-stop", "net.bible.android.activity"))
        self.assertEqual(adb.call_args_list[1].args[:3],
                         ("shell", "monkey", "-p"))
        self.assertEqual(sleep.call_args.args, (12,))

    def test_official_osis_deep_link_is_module_and_versification_bound(self):
        with (patch("probe_andbible_android_private_import.adb") as adb,
              patch("probe_andbible_android_private_import.time.sleep")):
            open_documented_reference_probe("Rom.16.25")
        args=adb.call_args.args
        self.assertEqual(args[:6],
                         ("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d"))
        self.assertEqual(args[6],
                         "https://read.andbible.org/Rom.16.25?document=JND2024RepairResearch&v11n=Luther")
        self.assertEqual(args[7:9], ("-p", "net.bible.android.activity"))
        with self.assertRaises(AndroidDarbyImportError):
            open_documented_reference_probe("Acts.8.37")

    def test_omitted_verse_host_links_allow_no_phantom_verses(self):
        with (patch("probe_andbible_android_private_import.adb") as adb,
              patch("probe_andbible_android_private_import.time.sleep")):
            for host in ("Matt.23.13", "Acts.8.36", "Acts.15.33"):
                open_documented_reference_probe(host)
        self.assertEqual(adb.call_count, 3)
        for ref in ("Matt.23.14", "Acts.8.37", "Acts.15.34"):
            with self.assertRaises(AndroidDarbyImportError):
                open_documented_reference_probe(ref)

    def test_all_three_authorial_omitted_note_marker_samples_are_bounded(self):
        from tempfile import TemporaryDirectory
        import struct
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"host.png"
            path.write_bytes(bytes.fromhex("89504e470d0a1a0a")
                             +bytes(8)+struct.pack(">II",1080,2280))
            with (patch("probe_andbible_android_private_import.adb") as adb,
                  patch("probe_andbible_android_private_import.time.sleep")):
                for host in ("Matt.23.13", "Acts.8.36", "Acts.15.33"):
                    probe_observed_omitted_host_caller(path,host)
            self.assertEqual([c.args[3:] for c in adb.call_args_list],
                             [("225","1217"),("1017","1080"),("240","1151")])
            with self.assertRaises(AndroidDarbyImportError):
                probe_observed_omitted_host_caller(path,"Acts.8.37")

    def test_research_only_missing_verse_label_taps_are_constrained(self):
        from tempfile import TemporaryDirectory
        import struct
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"note.png"
            path.write_bytes(bytes.fromhex("89504e470d0a1a0a")
                             +bytes(8)+struct.pack(">II",1080,2280))
            with (patch("probe_andbible_android_private_import.adb") as adb,
                  patch("probe_andbible_android_private_import.time.sleep")):
                for host in ("Matt.23.13","Acts.8.36","Acts.15.33"):
                    probe_observed_omitted_note_printed_link(path,host)
            self.assertEqual([c.args[3:] for c in adb.call_args_list],
                             [("685","1185"),("685","1292"),("685","1400")])
            with self.assertRaises(AndroidDarbyImportError):
                probe_observed_omitted_note_printed_link(path,"Acts.8.37")

    def test_note_probe_requires_exact_verified_android_png_geometry(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"screen.png"
            path.write_bytes(b"not-a-png")
            with self.assertRaises(AndroidDarbyImportError):
                probe_observed_note_marker(path)
            import struct
            header=bytes.fromhex("89504e470d0a1a0a")+bytes(8)
            path.write_bytes(header+struct.pack(">II", 832, 1792))
            with self.assertRaises(AndroidDarbyImportError):
                probe_observed_note_marker(path)
            path.write_bytes(header+struct.pack(">II", 1080, 2280))
            with (patch("probe_andbible_android_private_import.adb") as adb,
                  patch("probe_andbible_android_private_import.time.sleep")):
                probe_observed_note_marker(path)
            adb.assert_called_once_with("shell","input","tap","823","1425",timeout=12)

    def test_corrected_note_link_click_checks_same_exact_viewport(self):
        from tempfile import TemporaryDirectory
        import struct
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"popup.png"
            header=bytes.fromhex("89504e470d0a1a0a")+bytes(8)
            path.write_bytes(header+struct.pack(">II", 1080, 2280))
            with (patch("probe_andbible_android_private_import.adb") as adb,
                  patch("probe_andbible_android_private_import.time.sleep")):
                probe_observed_corrected_colossians_link(path)
            adb.assert_called_once_with("shell","input","tap","840","1800",timeout=12)
            path.write_bytes(header+struct.pack(">II", 500, 1000))
            with self.assertRaises(AndroidDarbyImportError):
                probe_observed_corrected_colossians_link(path)

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
        candidates=[item for item in controls
                    if item["label"]=="JND2024REPAIRRESEARCH.ZIP"]
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["x"],229)
        self.assertEqual(candidates[0]["y"],621)
        self.assertTrue(any(c["label"]=="RECENT" for c in controls))

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
