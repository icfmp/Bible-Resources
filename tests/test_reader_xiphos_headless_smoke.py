"""Synthetic Xiphos headless smoke ZIP safety; never launch GUI in unit tests."""
import sys
from pathlib import Path
from hashlib import sha256
import tempfile
import unittest
from zipfile import ZipFile
import subprocess
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from reader_xiphos_headless_smoke import (
    extract_pinned_preview,XiphosSmokeError,_notice_click_from_geometry,
    _sample_reader_passages, _capture_parallel_toggle_sample,
    _capture_note_hover_sample, GENESIS_1_2_NOTE_HOVER, READER_SAMPLES,
    install_checked_out_rawtext_comparison, _capture_module_tree_probe,
)


class XiphosSmokeUnitTests(unittest.TestCase):
    def make_zip(self,folder):
        root=Path(folder)
        path=root/"candidate.zip"
        module="GenericPreview"
        slug=module.lower()
        with ZipFile(path,"w") as z:
            z.writestr(f"mods.d/{slug}.conf",
                       f"[{module}]\nDataPath=./modules/texts/ztext/{slug}/\n"
                       "ModDrv=zText\nVersification=Luther\n"
                       "Version=0.0.0-research\n")
            for section in ("ot","nt"):
                for ext in ("bzs","bzv","bzz"):
                    z.writestr(f"modules/texts/ztext/{slug}/{section}.{ext}",
                               b"private-synthetic-bytes")
        return path,sha256(path.read_bytes()).hexdigest()

    def test_strict_exact_zip_allows_isolated_test_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            root=Path(folder)/"payload"
            root.mkdir()
            actual=extract_pinned_preview(source,root,"GenericPreview",
                                           digest,"Luther")
            self.assertEqual(actual,root)
            self.assertEqual(len([item for item in root.rglob("*") if item.is_file()]),7)
            self.assertNotIn("private-synthetic-bytes",str(actual))

    def test_only_small_notice_window_gets_click_coordinates(self):
        self.assertEqual(
            _notice_click_from_geometry({"X":0,"Y":0,"WIDTH":564,"HEIGHT":135}),
            (282,117))
        self.assertIsNone(
            _notice_click_from_geometry({"X":40,"Y":40,"WIDTH":800,"HEIGHT":600}))
        self.assertIsNone(
            _notice_click_from_geometry({"X":5,"Y":5,"WIDTH":300,"HEIGHT":65}))
        self.assertIsNone(_notice_click_from_geometry({"X":3}))

    def test_real_reader_sample_commands_remain_nonpublication_evidence(self):
        with tempfile.TemporaryDirectory() as base:
            folder=Path(base)/"samples"
            commands=[]
            def fake_run(args, **kwargs):
                commands.append(args)
                if args[:2] == ["xdotool", "search"]:
                    return subprocess.CompletedProcess(args, 0, stdout=b"12345")
                if args[0] == "import":
                    Path(args[-1]).write_bytes(b"synthetic screenshot only")
                return subprocess.CompletedProcess(args, 0)
            with (patch("reader_xiphos_headless_smoke.subprocess.run",
                        side_effect=fake_run),
                  patch("reader_xiphos_headless_smoke.time.sleep")):
                result=_sample_reader_passages({"DISPLAY":":91"},folder)
            self.assertEqual(len(result),len(READER_SAMPLES))
            self.assertEqual([entry["sample"] for entry in result],
                             [entry[0] for entry in READER_SAMPLES])
            self.assertEqual([entry["requested_reference"] for entry in result],
                             [entry[1] for entry in READER_SAMPLES])
            self.assertTrue(all(entry["gui_navigation_outcome_requires_visual_inspection"]
                                for entry in result))
            # One additional Gen 1:2 note-hover frame is independent
            # reader evidence; a screenshot is not an assertion of popup success.
            self.assertEqual(len(list(folder.glob("*.png"))),
                             len(READER_SAMPLES)+1)
            note=result[0]["note_hover_sample"]
            self.assertEqual(note["host_reference"],"Gen.1.2")
            self.assertFalse(note["previewed_note_body_verified"])
            self.assertFalse(note["actual_link_navigation_verified"])
            x,y=GENESIS_1_2_NOTE_HOVER
            self.assertIn(["xdotool","mousemove","--sync",str(x),str(y)],
                          commands)
            self.assertIn(
                ["xdotool","windowfocus","--sync","12345"],commands)
            self.assertIn(
                ["xdotool","windowsize","12345","1216","736"],commands)
            self.assertIn(
                ["xdotool","windowmove","12345","16","16"],commands)
            self.assertFalse(any("windowactivate" in command
                                 for command in commands))
            self.assertEqual(sum(command[:2] == ["xdotool","key"]
                                 for command in commands),2*len(READER_SAMPLES))
            # The *filename* of the test screenshot may mention 'note'.
            # No authored note BODY, source prose or link target enters
            # command arguments or public logs.
            self.assertFalse(any("private-synthetic-bytes" in " ".join(command)
                                 or "note body" in " ".join(command).lower()
                                 for command in commands))

    def test_real_reader_samples_do_not_overwrite_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as base:
            folder=Path(base)/"samples"
            folder.mkdir()
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=AssertionError("No X11 action allowed")):
                with self.assertRaises(XiphosSmokeError):
                    _sample_reader_passages({"DISPLAY":":91"},folder)

    def test_note_hover_requires_isolated_xvfb_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as base:
            directory=Path(base)/"samples"
            directory.mkdir()
            note=directory/"genesis-note-hover.png"
            note.write_bytes(b"previous source-linked evidence")
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=AssertionError("Must not touch X11")):
                with self.assertRaises(XiphosSmokeError):
                    _capture_note_hover_sample({"DISPLAY":":91"}, directory)
                self.assertEqual(note.read_bytes(),b"previous source-linked evidence")
                note.unlink()
                with self.assertRaises(XiphosSmokeError):
                    _capture_note_hover_sample({"DISPLAY":":0"}, directory)

    def test_parallel_view_toggle_is_only_unreviewed_gui_evidence(self):
        with tempfile.TemporaryDirectory() as base:
            folder=Path(base)/"samples"
            folder.mkdir()
            calls=[]
            def fake_run(args, **kwargs):
                calls.append(args)
                if args[0]=="import":
                    Path(args[-1]).write_bytes(b"synthetic X11 screenshot")
                return subprocess.CompletedProcess(args,0)
            with (patch("reader_xiphos_headless_smoke.subprocess.run",
                        side_effect=fake_run),
                  patch("reader_xiphos_headless_smoke.time.sleep")):
                result=_capture_parallel_toggle_sample({"DISPLAY":":91"},folder)
            self.assertEqual(result["shortcut_invoked"],"Alt+P")
            self.assertFalse(result["actual_parallel_second_translation_visible_verified"])
            self.assertTrue(result["gui_outcome_requires_visual_inspection"])
            self.assertEqual(calls[0][:4],
                             ["xdotool","key","--clearmodifiers","alt+p"])
            self.assertEqual(calls[1][:4],
                             ["import","-display",":91","-window"])
            self.assertTrue((folder/"parallel-toggle.png").is_file())

    def test_parallel_probe_rejects_overwrite_or_untrusted_display_before_x11(self):
        with tempfile.TemporaryDirectory() as base:
            folder=Path(base)/"samples"
            folder.mkdir()
            (folder/"parallel-toggle.png").write_bytes(b"earlier verified proof")
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=AssertionError("No X11 allowed")):
                with self.assertRaises(XiphosSmokeError):
                    _capture_parallel_toggle_sample({"DISPLAY":":91"},folder)
            self.assertEqual((folder/"parallel-toggle.png").read_bytes(),
                             b"earlier verified proof")
            (folder/"parallel-toggle.png").unlink()
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=AssertionError("No other display allowed")):
                with self.assertRaises(XiphosSmokeError):
                    _capture_parallel_toggle_sample({"DISPLAY":":0"},folder)


    def make_comparison_module(self, folder):
        root = Path(folder) / "reviewed-comparison"
        raw = root / "modules/texts/rawtext/genericsecond"
        raw.mkdir(parents=True)
        conf = root / "mods.d/genericsecond.conf"
        conf.parent.mkdir(parents=True)
        conf.write_text(
            "[GenericSecond]\n"
            "DataPath=./modules/texts/rawtext/genericsecond/\n"
            "ModDrv=RawText\nVersification=Segond\n",
            encoding="utf-8")
        for part in ("ot", "nt"):
            for ext in ("", ".vss"):
                (raw / (part + ext)).write_bytes(b"synthetic distinct comparison")
        return root

    def test_checked_out_second_module_isolated_byte_preserving_copy(self):
        with tempfile.TemporaryDirectory() as base:
            source = self.make_comparison_module(base)
            isolated = Path(base) / "isolated"
            isolated.mkdir()
            receipt = install_checked_out_rawtext_comparison(
                source, isolated, "GenericSecond", "Segond")
            self.assertEqual(receipt["file_count"], 5)
            self.assertFalse(receipt["gui_two_module_parallel_content_verified"])
            for original in source.rglob("*"):
                if original.is_file():
                    target = isolated / original.relative_to(source)
                    self.assertEqual(target.read_bytes(), original.read_bytes())
            self.assertFalse((source / "mods.d/genericsecond.conf").is_symlink())

    def test_second_module_rejects_wrong_v11n_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as base:
            source = self.make_comparison_module(base)
            isolated = Path(base) / "isolated"
            isolated.mkdir()
            with self.assertRaises(XiphosSmokeError):
                install_checked_out_rawtext_comparison(
                    source, isolated, "GenericSecond", "Luther")
            self.assertEqual(list(isolated.rglob("*")), [])
            extra = source / "modules/texts/rawtext/genericsecond/unreviewed"
            extra.write_bytes(b"not a standard SWORD member")
            with self.assertRaises(XiphosSmokeError):
                install_checked_out_rawtext_comparison(
                    source, isolated, "GenericSecond", "Segond")
            self.assertEqual(list(isolated.rglob("*")), [])


    def test_module_tree_probe_records_only_unapproved_gui_screenshots(self):
        with tempfile.TemporaryDirectory() as base:
            study = Path(base) / "study"
            study.mkdir()
            commands = []
            def fake_run(args, **kwargs):
                commands.append(args)
                if args[0] == "import":
                    Path(args[-1]).write_bytes(b"synthetic tree screenshot")
                return subprocess.CompletedProcess(args, 0)
            with (patch("reader_xiphos_headless_smoke.subprocess.run",
                        side_effect=fake_run),
                  patch("reader_xiphos_headless_smoke.time.sleep")):
                report = _capture_module_tree_probe({"DISPLAY": ":91"}, study)
            self.assertEqual(len(report["snapshots"]), 2)
            self.assertFalse(report["module_selection_verified"])
            self.assertEqual(commands[0],
                             ["xdotool", "mousemove", "--sync", "100", "134",
                              "click", "1"])
            self.assertEqual([x for x in commands if x[0] == "import"].__len__(), 2)
            self.assertEqual(len(list(study.glob("module-tree-stage-*.png"))), 2)

    def test_module_tree_probe_rejects_existing_or_untrusted_fixture(self):
        with tempfile.TemporaryDirectory() as base:
            study = Path(base) / "study"
            study.mkdir()
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=AssertionError("X11 should be rejected")):
                with self.assertRaises(XiphosSmokeError):
                    _capture_module_tree_probe({"DISPLAY": ":0"}, study)
            (study / "module-tree-stage-1.png").write_bytes(b"prior evidence")
            with patch("reader_xiphos_headless_smoke.subprocess.run",
                       side_effect=lambda args, **kw: subprocess.CompletedProcess(args, 0)):
                with self.assertRaises(XiphosSmokeError):
                    _capture_module_tree_probe({"DISPLAY": ":91"}, study)

    def test_hash_and_scheme_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            out=Path(folder)/"out"
            out.mkdir()
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview","0"*64,"Luther")
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview",digest,"KJV")

    def test_traversal_member_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            with ZipFile(source,"a") as archive:
                archive.writestr("../PRIVATE-OUTSIDE",b"untrusted")
            digest=sha256(source.read_bytes()).hexdigest()
            out=Path(folder)/"out"
            out.mkdir()
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview",digest,"Luther")
            self.assertFalse((Path(folder)/"PRIVATE-OUTSIDE").exists())


if __name__=="__main__":
    unittest.main()
