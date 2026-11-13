"""Private source paragraph run-boundary audit; synthetic examples only."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_chapter_neighbors import original_chapter_neighbors
from commentary_chapter_p_boundaries import ChapterParagraphBoundaryProbe, anchor_window
from commentary_private_text_compare import raw_as_strict_xml_text
from pilot_preflight import PilotError


def sample_xml():
    return (
        b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
        b'<scripCom osisRef="Bible:Gen.1"/>'
        b'<p>Alpha beta gamma <hi>delta</hi> epsilon zeta.</p>'
        b'<scripCom osisRef="Bible:Gen.1.1"/>'
        b'<div><p>Unrelated reference text.</p></div>'
        b'</div2></div1></ThML.body></ThML>'
    )


class OriginalParagraphWordBoundariesTests(unittest.TestCase):
    def setup_probe(self, prior_max=3):
        original, _ = original_chapter_neighbors(sample_xml())
        obj = original["Gen.1"][0]
        probe = ChapterParagraphBoundaryProbe(original)
        case = {
            "alternative_stock_location_class": "not_found_in_other_same_book_stock_slots",
            "original_neighbor_tag": "p",
            "source_line": obj["source_line"],
            "original_reference_sha256": obj["source_reference_sha256"],
            "original_neighbor_text_sha256": obj["source_sibling_sha256"],
        }
        alternative = {"bounded_originally_unlocated_line_hash_only_cases": [case]}
        partial = {
            "unlocated_original_p_line_hash_only_best_contiguous_word_spans": [{
                "original_reference_sha256": case["original_reference_sha256"],
                "original_neighbor_text_sha256": case["original_neighbor_text_sha256"],
                "largest_identical_case_word_span_by_slot_scope": {
                    "same_chapter_numbered": prior_max
                },
            }]
        }
        return probe, alternative, partial

    def test_run_location_uses_real_contiguous_tokens_not_multiset(self):
        self.assertEqual(
            anchor_window(["a","b","c","d"], ["x","a","b","y","c","d"],2),
            (0,1,2))
        self.assertEqual(anchor_window(["a","b","a"], ["a","b","a"],3),(0,0,1))
        with self.assertRaises(PilotError):
            anchor_window(["a","b"], ["a","x"],2)

    def test_original_source_and_stock_remainders_are_structural_metadata_only(self):
        probe, alternative, partial = self.setup_probe()
        # Original is 6 tokens; 3-word head matches, one token differs,
        # two original tail tokens appear in the compiled witness.
        raw = b"<p>prefix Alpha beta gamma changed epsilon zeta suffix</p>"
        probe.observe("K","Gen.1.1",raw,raw_as_strict_xml_text)
        receipt = probe.report(alternative,partial)
        self.assertEqual(receipt["previously_unlocated_p_examined"],1)
        case = receipt["source_paragraph_word_run_boundary_cases"][0]
        self.assertEqual(case["best_same_chapter_contiguous_word_run"],3)
        self.assertEqual(case["original_tokens_before_shared_run"],0)
        self.assertEqual(case["original_tokens_after_shared_run"],3)
        self.assertEqual(case["selected_stock_run_start_token_offset"],1)
        self.assertEqual(case["stock_key_slots_tied_for_best_word_run"],1)
        self.assertEqual(case["original_word_token_multiset_occurrences_in_selected_stock_key"],5)
        self.assertEqual(case["source_paragraph_direct_child_element_counts"],{"hi":1})
        self.assertEqual(case["original_next_sibling_tag"],"scripCom")
        self.assertEqual(case["original_parent_element_tag"],"div2")
        rendered = json.dumps(receipt)
        self.assertNotIn("Alpha",rendered)
        self.assertNotIn("zeta",rendered)
        self.assertFalse(receipt["full_original_to_stock_authorial_paragraph_parity_proven"])

    def test_repeated_native_keys_are_recorded_not_confused_with_distinct_comments(self):
        probe, alternative, partial = self.setup_probe()
        raw = b"<p>Alpha beta gamma changed epsilon zeta</p>"
        probe.observe("K","Gen.1.1",raw,raw_as_strict_xml_text)
        probe.observe("K","Gen.1.2",raw,raw_as_strict_xml_text)
        case = probe.report(alternative,partial)["source_paragraph_word_run_boundary_cases"][0]
        self.assertEqual(case["stock_key_slots_tied_for_best_word_run"],2)

    def test_strict_mismatch_and_non_matching_chapter_are_blocking_or_ignored(self):
        probe, alternative, partial = self.setup_probe(prior_max=3)
        probe.observe("K","Gen.2.1",b"<p>Alpha beta gamma</p>",raw_as_strict_xml_text)
        probe.observe("K","Gen.1.1",b"<p>Alpha beta gamma changed</p>",
                      raw_as_strict_xml_text)
        partial["unlocated_original_p_line_hash_only_best_contiguous_word_spans"][0][
            "largest_identical_case_word_span_by_slot_scope"]["same_chapter_numbered"]=4
        with self.assertRaises(PilotError):
            probe.report(alternative,partial)

    def test_bad_stock_xml_cannot_be_used_as_proof(self):
        probe, alternative, partial = self.setup_probe()
        probe.observe("K","Gen.1.1",b"<p>bad</h3>",raw_as_strict_xml_text)
        self.assertEqual(probe.stock_xml_parse_errors,1)
        with self.assertRaises(PilotError):
            probe.report(alternative,partial)


if __name__ == "__main__":
    unittest.main()
