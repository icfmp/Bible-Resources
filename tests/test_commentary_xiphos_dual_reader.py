"""Synthetic controls for an attested Bible + exact original Xiphos commentary."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_xiphos_dual_reader import (
    _long_commentary_excerpt_is_on_gui_clipboard,
    _normalized_words,
    _main_xiphos_window,
    attempt_real_xiphos_passage_copy,
    verify_and_install_reviewed_bible,
)
from pilot_preflight import PilotError


class ExactDualModuleXiphosReaderTests(unittest.TestCase):
    def test_long_distinct_original_commentary_in_real_clipboard(self):
        text = ("Original commentary source. " +
                " ".join("exegeticalword%03d" % n for n in range(100)))
        self.assertTrue(
            _long_commentary_excerpt_is_on_gui_clipboard(
                text.encode(), b"Some other original Bible verse.",
                ("Copy from Bible reader\n" + text[10:]).encode(),
            )
        )

    def test_bible_verse_or_short_module_label_is_not_commentary_proof(self):
        text = " ".join("word%03d" % n for n in range(130))
        scripture = text.encode()
        self.assertFalse(_long_commentary_excerpt_is_on_gui_clipboard(
            scripture, scripture, scripture
        ))
        self.assertFalse(_long_commentary_excerpt_is_on_gui_clipboard(
            scripture, b"Unrelated source", b"MHCC Genesis 1:1"
        ))
        self.assertFalse(_long_commentary_excerpt_is_on_gui_clipboard(
            scripture, b"Unrelated source", b""
        ))

    def test_readback_word_normalization_is_comparison_only(self):
        self.assertEqual(
            _normalized_words("Ésaïe 1:1 — coöpération".encode()),
            ["esaie", "1", "1", "cooperation"],
        )

    @patch("commentary_xiphos_dual_reader.install_checked_out_rawtext_comparison")
    def test_attested_exact_five_bible_files_are_not_rewritten(self, install):
        names = [
            "mods.d/brlsg1910.conf",
            "modules/texts/rawtext/brlsg1910/ot",
            "modules/texts/rawtext/brlsg1910/ot.vss",
            "modules/texts/rawtext/brlsg1910/nt",
            "modules/texts/rawtext/brlsg1910/nt.vss",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "baseline"
            dest = root / "installed"
            source.mkdir()
            dest.mkdir()
            expected = {}
            for n in names:
                file = source / n
                file.parent.mkdir(parents=True, exist_ok=True)
                original = (b"authorially checked data " + n.encode()) * 2
                file.write_bytes(original)
                expected[n] = sha256(original).hexdigest()
            receipt = root / "attestation.json"
            receipt.write_text(
                json.dumps({"module_id": "BRLSG1910",
                            "release_tag": "lsg-0.1.0",
                            "files": expected})
            )
            install.return_value = {
                "file_count": 5,
                "module_id": "BRLSG1910",
            }
            out = verify_and_install_reviewed_bible(
                dest, source=source, attestation=receipt
            )
            self.assertTrue(out["all_five_published_bible_files_sha256_attested"])
            self.assertEqual(out["module_id"], "BRLSG1910")
            install.assert_called_once()
            # An accidental source Bible mutation fails closed.
            (source / "modules/texts/rawtext/brlsg1910/nt").write_bytes(b"changed")
            with self.assertRaisesRegex(PilotError, "changed"):
                verify_and_install_reviewed_bible(
                    dest, source=source, attestation=receipt
                )

    @patch("commentary_xiphos_dual_reader._x11")
    def test_visible_full_xiphos_window_required_not_tiny_notice(self, command):
        command.side_effect = [
            b"101\n102\n",
            b"WIDTH=300\nHEIGHT=120\n",
            b"WIDTH=1100\nHEIGHT=760\n",
        ]
        self.assertEqual(_main_xiphos_window({"DISPLAY": ":91"}), "102")

    @patch("commentary_xiphos_dual_reader._main_xiphos_window", return_value=None)
    def test_missing_real_main_window_does_not_claim_visual_content(self, _window):
        samples = {"Gen 1:1": {"commentary": b"real", "bible": b"real"}}
        receipt = attempt_real_xiphos_passage_copy(
            {"DISPLAY": ":91", "GDK_BACKEND": "x11"}, samples
        )
        self.assertFalse(receipt["real_main_reader_window_found"])
        self.assertFalse(receipt["actual_passage_commands_accepted"])
        self.assertEqual(receipt["independent_gui_commentary_excerpt_match_count"], 0)

    def test_sparse_original_source_slots_are_not_filled_with_invented_verses(self):
        from commentary_xiphos_dual_reader import _candidate_passages
        manifest={"sample_references":["Gen 1:1","John 3:16","Ps 23:1"]}
        self.assertEqual(
            _candidate_passages(manifest),
            ("Gen 1:1","John 3:16","John 3:1","Ps 23:1"),
        )
        with self.assertRaisesRegex(PilotError,"Malformed"):
            _candidate_passages({"sample_references":["Gen 0:0"]})

    @patch("commentary_xiphos_dual_reader.subprocess.run")
    def test_private_clipboard_seed_uses_nonempty_sentinel_without_captured_stdout(self, run):
        import subprocess
        from commentary_xiphos_dual_reader import _seed_x11_clipboard
        run.return_value.returncode=0
        _seed_x11_clipboard({"DISPLAY":":91"})
        self.assertEqual(run.call_args.args[0], [
            "xclip","-selection","clipboard","-i"
        ])
        self.assertIn(b"PRIVATE_CLIPBOARD_SENTINEL",run.call_args.kwargs["input"])
        self.assertEqual(run.call_args.kwargs["stdout"],subprocess.DEVNULL)
        run.return_value.returncode=1
        with self.assertRaisesRegex(PilotError,"stale"):
            _seed_x11_clipboard({"DISPLAY":":91"})

    @patch("commentary_xiphos_dual_reader._x11")
    def test_commentary_focus_targets_bound_to_real_private_main_window(self, command):
        from commentary_xiphos_dual_reader import _commentary_pane_focus_points
        command.return_value = b"X=40\nY=20\nWIDTH=1200\nHEIGHT=740\n"
        points = _commentary_pane_focus_points({"DISPLAY": ":91"}, "101")
        self.assertEqual(len(points), 2)
        for x, y in points:
            self.assertGreater(x, 700)
            self.assertLess(x, 1280)
            self.assertGreater(y, 200)
            self.assertLess(y, 800)
        command.return_value = b"X=0\nY=0\nWIDTH=200\nHEIGHT=100\n"
        with self.assertRaisesRegex(PilotError, "outside reviewed"):
            _commentary_pane_focus_points({"DISPLAY": ":91"}, "101")

    def test_repeated_verse_focus_does_not_wait_for_pointer_motion_at_same_point(self):
        from commentary_xiphos_dual_reader import attempt_real_xiphos_passage_copy
        probes = {
            "Gen 1:1": {"commentary": b"source", "bible": b"bible"},
            "Ps 23:1": {"commentary": b"source", "bible": b"bible"},
        }
        with patch("commentary_xiphos_dual_reader._main_xiphos_window", return_value="101"), \
             patch("commentary_xiphos_dual_reader._commentary_pane_focus_points",
                   return_value=((1000, 390),)), \
             patch("commentary_xiphos_dual_reader._seed_x11_clipboard"), \
             patch("commentary_xiphos_dual_reader._long_commentary_excerpt_is_on_gui_clipboard",
                   return_value=True), \
             patch("commentary_xiphos_dual_reader.time.sleep"), \
             patch("commentary_xiphos_dual_reader._x11", return_value=b"copied") as x11:
            result = attempt_real_xiphos_passage_copy(
                {"DISPLAY": ":91", "GDK_BACKEND": "x11"}, probes,
            )
        self.assertTrue(result["actual_passage_commands_accepted"])
        self.assertEqual(result["independent_gui_commentary_excerpt_match_count"], 2)
        pointer = [c.args[0] for c in x11.call_args_list
                   if c.args[0][:2] == ["xdotool", "mousemove"]]
        self.assertEqual(len(pointer), 2)
        self.assertTrue(all("--sync" not in command for command in pointer))

    def test_actual_source_heading_and_rich_html_are_measured_without_leaking_text(self):
        from commentary_xiphos_dual_reader import _markup_display_witness
        original = (
            b'MHCC:Gen.1.1: <title type="chapter">The first creation</title>'
            b'<p>Original author commentary <reference osisRef="Gen.2.1">'
            b'see another scripture</reference>.</p>'
        )
        copied = b"The first creation\nOriginal author commentary see another scripture."
        rich = b'<div><h2>The first creation</h2><p>Original author commentary <a href="sword://Bible/Gen.2.1">see another scripture</a></p></div>'
        report = _markup_display_witness(original, copied, rich)
        self.assertEqual(report["original_internal_title_elements_found"], 1)
        self.assertEqual(report["exact_original_titles_in_copied_gui_text"], 1)
        self.assertEqual(report["original_internal_reference_elements_found"], 1)
        self.assertEqual(report["original_stock_nontrivial_reference_labels_found"], 1)
        self.assertEqual(report["source_reference_labels_observed_as_real_gui_HTML_anchors"], 1)
        self.assertEqual(report["exact_original_titles_in_copied_gui_rich_html"], 1)
        self.assertEqual(report["real_gui_rich_html_anchor_elements_found"], 1)
        self.assertFalse(report["xiphos_link_click_target_and_navigation_verified"])
        self.assertNotIn("The first creation", str(report))
        self.assertNotIn("Gen.2.1", str(report))

    def test_no_rich_clipboard_or_wrong_heading_never_counts_as_gui_markup(self):
        from commentary_xiphos_dual_reader import _markup_display_witness
        original = b"<title>A real section heading</title><reference osisRef='John.3.16'>ref</reference>"
        report = _markup_display_witness(original, b"Unrelated Bible passage", None)
        self.assertEqual(report["original_internal_title_elements_found"], 1)
        self.assertEqual(report["exact_original_titles_in_copied_gui_text"], 0)
        self.assertEqual(report["original_internal_reference_elements_found"], 1)
        self.assertFalse(report["real_gui_rich_html_selection_available"])
        self.assertEqual(report["real_gui_rich_html_anchor_elements_found"], 0)
        self.assertEqual(report["source_reference_labels_observed_as_real_gui_HTML_anchors"], 0)

    def test_unrelated_webkit_anchor_does_not_certify_original_sword_reference(self):
        from commentary_xiphos_dual_reader import _markup_display_witness
        original=b'<reference osisRef="Gen.2.1">a real original reference label</reference>'
        clipboard=b'<a href="about:blank">unrelated menu link</a>'
        result=_markup_display_witness(original,b"unrelated menu link",clipboard)
        self.assertEqual(result["original_stock_nontrivial_reference_labels_found"],1)
        self.assertEqual(result["real_gui_rich_html_anchor_elements_found"],1)
        self.assertEqual(result["source_reference_labels_observed_as_real_gui_HTML_anchors"],0)
        self.assertFalse(result["xiphos_link_click_target_and_navigation_verified"])

    def test_bounded_private_gui_markup_input_and_source_limits(self):
        from commentary_xiphos_dual_reader import _markup_display_witness
        for source, copied, html in (
            (b"x" * 256001, b"", None),
            (b"", b"x" * 256001, None),
            (b"", b"", b"x" * 256001),
        ):
            with self.assertRaisesRegex(PilotError, "Unbounded"):
                _markup_display_witness(source, copied, html)

    @patch("commentary_xiphos_dual_reader._x11")
    def test_rich_selection_absence_is_not_invented(self, x11):
        from commentary_xiphos_dual_reader import _optional_real_rich_xiphos_selection
        x11.return_value = b"UTF8_STRING\nSTRING\n"
        self.assertIsNone(_optional_real_rich_xiphos_selection({"DISPLAY": ":91"}))
        self.assertEqual(x11.call_count, 1)
        x11.side_effect = [b"UTF8_STRING\ntext/html\n", b"<a href='x'>link</a>"]
        self.assertEqual(
            _optional_real_rich_xiphos_selection({"DISPLAY": ":91"}),
            b"<a href='x'>link</a>",
        )

    @patch("commentary_xiphos_dual_reader.subprocess.run")
    def test_native_sword_inspection_uses_exact_key_and_never_logs_source(self, run):
        from commentary_xiphos_dual_reader import _exact_native_commentary_raw
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "installed"
            installed.mkdir()
            tool = root / "native-key"
            tool.write_bytes(b"placeholder native binary")
            source = b"<title>Faithful original chapter heading</title>"
            run.return_value.returncode = 0
            run.return_value.stdout = source
            self.assertEqual(_exact_native_commentary_raw(
                installed, "MHCC", "Gen 1:1", tool,
            ), source)
            self.assertEqual(run.call_args.args[0], [
                str(tool), "MHCC", "Gen 1:1"
            ])
            self.assertEqual(run.call_args.kwargs["env"]["SWORD_PATH"], str(installed))
            import subprocess
            self.assertEqual(run.call_args.kwargs["stderr"], subprocess.DEVNULL)
            run.return_value.returncode = 9
            with self.assertRaisesRegex(PilotError, "missing"):
                _exact_native_commentary_raw(installed, "MHCC", "Gen 1:1", tool)
            with self.assertRaisesRegex(PilotError, "Unsafe"):
                _exact_native_commentary_raw(installed, "MHCC", "Gen 0:0", tool)

    @patch("commentary_xiphos_dual_reader.parse_native_raw_corpus")
    @patch("commentary_xiphos_dual_reader.subprocess.Popen")
    def test_private_full_stock_reference_discovery_preserves_corpus_identity(
        self, popen, scan,
    ):
        from commentary_xiphos_dual_reader import _original_stock_reference_bearing_samples
        from unittest.mock import MagicMock
        from io import BytesIO
        expected = "a" * 64
        stream = MagicMock()
        stream.stdout = BytesIO()
        stream.wait.return_value = 0
        stream.poll.return_value = 0
        popen.return_value = stream

        def scan_source(_stdout, *, on_entry):
            on_entry(
                "K", "Gen.1.1",
                b'<title>Some original heading</title><reference osisRef="Gen.2.1">true source</reference>'
            )
            on_entry("K", "Ps.23.1",
                     b'<reference osisRef="Ps.23.1">another true reference</reference>')
            on_entry("K", "Matt.5.1", b"<title>No original link</title>")
            return ({
                "all_native_raw_entries_ordered_sha256": expected,
                "all_actual_raw_entries_scanned": 29975,
            }, [], [], [])

        scan.side_effect = scan_source
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            binary = folder / "sword-inspector"
            binary.write_bytes(b"binary")
            result = _original_stock_reference_bearing_samples(
                folder, "MHCC", binary, expected_corpus_sha256=expected
            )
        self.assertEqual(result["real_reference_bearing_original_native_samples"],
                         ["Gen 1:1", "Ps 23:1"])
        self.assertEqual(result["original_occupied_numbered_keys_with_reference_markup"], 2)
        self.assertEqual(result["complete_native_original_stock_entries_checked"], 29975)
        self.assertTrue(result["full_pinned_raw_corpus_sha256_reconfirmed"])
        self.assertFalse(result["actual_link_click_and_target_verified_in_xiphos"])
        self.assertFalse(result["original_authorial_reference_targets_exported"])

    @patch("commentary_xiphos_dual_reader.parse_native_raw_corpus")
    @patch("commentary_xiphos_dual_reader.subprocess.Popen")
    def test_full_stock_digest_drift_fails_before_authorizing_source_link_samples(
        self, popen, scan,
    ):
        from commentary_xiphos_dual_reader import _original_stock_reference_bearing_samples
        from unittest.mock import MagicMock
        from io import BytesIO
        proc = MagicMock()
        proc.stdout = BytesIO()
        proc.wait.return_value = 0
        proc.poll.return_value = 0
        popen.return_value = proc
        scan.return_value = ({
            "all_native_raw_entries_ordered_sha256": "b"*64,
            "all_actual_raw_entries_scanned": 29975,
        }, [], [], [])
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            binary = folder / "real-inspector"
            binary.write_bytes(b"placeholder")
            with self.assertRaisesRegex(PilotError, "diverged"):
                _original_stock_reference_bearing_samples(
                    folder, "MHCC", binary, expected_corpus_sha256="a"*64
                )

    def test_no_user_display_or_wayland_gui_capture(self):
        with self.assertRaisesRegex(PilotError, "Unsafe virtual"):
            attempt_real_xiphos_passage_copy(
                {"DISPLAY": ":0", "GDK_BACKEND": "x11"}, {}
            )


if __name__ == "__main__":
    unittest.main()
