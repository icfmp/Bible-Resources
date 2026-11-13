"""Fail-closed candidate GUI receipt and no-release boundary tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_private_candidate_xiphos_gui import (
    PRIVATE_ID, _gate_real_candidate_gui, private_candidate_xiphos_review,
)
from pilot_preflight import PilotError

REFS = ["Gen 1:1", "Ps 23:1", "Matt 5:1", "Gen 1:3", "Exod 2:1"]


def receipt():
    return {
        "selected_private_commentary_module_id": PRIVATE_ID,
        "installed_reviewed_bible": {
            "module_id": "BRLSG1910",
            "all_five_published_bible_files_sha256_attested": True,
        },
        "original_source_corpus_hash_reconfirmed": True,
        "actual_baseline_commentary_samples": REFS[:3],
        "actual_source_link_samples": REFS[3:],
        "actual_substantive_sample_references": REFS,
        "real_main_reader_window_found": True,
        "actual_passage_commands_accepted": True,
        "commentary_clipboard_match_by_passage": dict.fromkeys(REFS, True),
        "independent_gui_commentary_excerpt_match_count": 5,
        "real_markup_rendering_observation_by_passage": {
            ref: {
                "original_internal_reference_elements_found": 1 if ref in REFS[3:] else 0,
                "source_reference_labels_observed_as_real_gui_HTML_anchors":
                    1 if ref in REFS[3:] else 0,
                "exact_native_source_osisref_encoded_in_real_gui_HTML_link_destinations":
                    1 if ref in REFS[3:] else 0,
            } for ref in REFS
        },
        "xiphos_reference_mouse_click_navigation_verified": False,
        "all_authorial_source_edition_differences_resolved": False,
        "published": False,
        "original_words_links_screenshots_or_SWORD_archives_uploaded": False,
    }


class PrivateCandidateRealXiphosTests(unittest.TestCase):
    def test_five_actual_selected_private_commentary_texts_and_two_real_source_hrefs(self):
        _gate_real_candidate_gui(receipt())

    def test_source_and_private_commentary_must_not_be_confused(self):
        bad = receipt()
        bad["selected_private_commentary_module_id"] = "MHCC"
        with self.assertRaisesRegex(PilotError, "expected private module"):
            _gate_real_candidate_gui(bad)

    def test_mere_window_or_unchanged_bible_clipboard_is_never_a_pass(self):
        bad = receipt()
        bad["commentary_clipboard_match_by_passage"]["Gen 1:3"] = False
        with self.assertRaisesRegex(PilotError, "did not match 5"):
            _gate_real_candidate_gui(bad)
        bad = receipt()
        bad["real_main_reader_window_found"] = False
        with self.assertRaisesRegex(PilotError, "did not match 5"):
            _gate_real_candidate_gui(bad)

    def test_generic_webkit_anchor_is_not_an_original_authorial_reference(self):
        bad = receipt()
        bad["real_markup_rendering_observation_by_passage"]["Exod 2:1"][
            "exact_native_source_osisref_encoded_in_real_gui_HTML_link_destinations"
        ] = 0
        with self.assertRaisesRegex(PilotError, "original link label"):
            _gate_real_candidate_gui(bad)

    def test_original_headings_and_mouse_click_are_never_silently_approved(self):
        bad = receipt()
        bad["xiphos_reference_mouse_click_navigation_verified"] = True
        with self.assertRaisesRegex(PilotError, "exceeded its approval scope"):
            _gate_real_candidate_gui(bad)
        bad = receipt()
        bad["published"] = True
        with self.assertRaisesRegex(PilotError, "approval scope"):
            _gate_real_candidate_gui(bad)

    def test_stale_or_unreviewed_candidate_binary_is_refused(self):
        with self.assertRaisesRegex(PilotError, "Unreviewed"):
            private_candidate_xiphos_review(
                "mhcc-crosswire",
                native_full_corpus_binary=Path("/private/nonexistent/full-native"),
                native_single_key_binary=Path("/private/nonexistent/single-key"),
            )

    def test_private_callback_called_after_verified_full_native_corpus(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            full = root / "native-full"
            single = root / "native-key"
            full.write_bytes(b"native test executable")
            single.write_bytes(b"native test executable")
            expected = receipt()
            with patch("commentary_private_candidate_xiphos_gui.make_private_candidate") as candidate, \
                 patch("commentary_private_candidate_xiphos_gui.verify_and_install_reviewed_bible") as bible, \
                 patch("commentary_private_candidate_xiphos_gui._original_stock_reference_bearing_samples") as refs, \
                 patch("commentary_private_candidate_xiphos_gui.pinned_source_intro_witness", return_value={}) as intros, \
                 patch("commentary_private_candidate_xiphos_gui.prepare_original_and_candidate_gui_samples") as samples, \
                 patch("commentary_private_candidate_xiphos_gui._run_real_gui") as gui:
                bible.return_value = expected["installed_reviewed_bible"]
                refs.return_value = {
                    "full_pinned_raw_corpus_sha256_reconfirmed": True,
                    "original_occupied_numbered_keys_with_reference_markup": 5780,
                }
                samples.return_value = (
                    {k: {"commentary": b"private synthetic original content"} for k in REFS},
                    REFS[:3], REFS[3:], []
                )
                gui.return_value = {
                    key: expected[key] for key in (
                        "real_main_reader_window_found",
                        "actual_passage_commands_accepted",
                        "commentary_clipboard_match_by_passage",
                        "independent_gui_commentary_excerpt_match_count",
                        "real_markup_rendering_observation_by_passage",
                    )
                }
                def mock_candidate(resource_id, **kwargs):
                    self.assertEqual(resource_id, "mhcc-crosswire")
                    self.assertEqual(kwargs["candidate_id"], PRIVATE_ID)
                    cb = kwargs["on_verified_private_candidate"]
                    obs = cb(root, root, {
                        "module_id": "MHCC",
                        "native_raw_corpus_sha256": "a"*64,
                    })
                    return {
                        "independent_private_candidate_gui_receipt": obs,
                        "private_candidate_module_id": PRIVATE_ID,
                        "total_native_keys": 29975,
                        "complete_stock_and_candidate_native_raw_corpus_sha256_equal": True,
                        "all_original_SWORD_compressed_files_byte_preserved": True,
                        "private_candidate_archive_destroyed_without_upload": True,
                        "published": False,
                        "editorial_acceptance": False,
                    }
                candidate.side_effect = mock_candidate
                outcome = private_candidate_xiphos_review(
                    "mhcc-crosswire",
                    native_full_corpus_binary=full,
                    native_single_key_binary=single,
                )
                self.assertEqual(outcome["independent_private_candidate_gui_receipt"]["selected_private_commentary_module_id"], PRIVATE_ID)
                self.assertEqual(gui.call_args.kwargs["commentary_module_id"], PRIVATE_ID)
                self.assertTrue(callable(gui.call_args.kwargs["on_gui_ready"]))


if __name__ == "__main__":
    unittest.main()
