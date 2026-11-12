"""Offline exact source-body stock-suffix diagnostic tests; no original words exported."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_stock_prefix_topology import (
    stock_prefixed_source_body_concordance, unexplained_word_boundary_census,
)
from commentary_private_text_compare import (
    _original_source_markers, compare_private_texts,
)


class CommentaryStockSuffixTests(unittest.TestCase):
    def test_prefixed_exact_unicode_suffix_keeps_unapproved_extra_original_stock(self):
        result=stock_prefixed_source_body_concordance(
            "Original words, punctuation.",
            b"<title>Additional heading.</title><hi>Original words, punctuation.</hi>",
        )
        self.assertEqual(result["stock_extra_prefix_word_tokens"],2)
        self.assertEqual(result["original_source_body_to_stock_suffix_class"],
                         "exact_source_body_unicode_equals_stock_text_suffix")
        self.assertEqual(result["aligned_suffix_changed_nonword_gaps"],0)
        self.assertFalse(result["stock_prefix_proven_authorial_or_legal"])
        self.assertTrue(result["stock_raw_full_prefix_retained"])
        self.assertNotIn("Additional heading",json.dumps(result))

    def test_prefixed_suffix_punctuation_changes_not_accepted_as_exact(self):
        result=stock_prefixed_source_body_concordance(
            "Original – commentary.",
            b"<title>Unverified title.</title><hi>Original - commentary.</hi>",
        )
        self.assertEqual(result["original_source_body_to_stock_suffix_class"],
                         "same_original_word_sequence_with_other_punctuation_or_markup_text_difference")
        self.assertEqual(result["aligned_suffix_one_to_one_numeric_glyph_substitutions"],
                         {"U+2013>U+002D":1})
        self.assertFalse(result["complete_authorial_text_and_structure_parity_proven"])

    def test_only_source_leading_whitespace_is_distinguished_from_exact(self):
        result=stock_prefixed_source_body_concordance(
            "\n  Original words.",
            b"<title>Heading</title><hi>Original words.</hi>",
        )
        self.assertEqual(result["original_source_body_to_stock_suffix_class"],
                         "only_source_leading_whitespace_before_first_word")

    def test_reject_noncontiguous_or_suffix_stock_extra_material(self):
        with self.assertRaises(ValueError):
            stock_prefixed_source_body_concordance("Original words.",
                                                   b"<title>Added</title><hi>Original changed words.</hi>")
        with self.assertRaises(ValueError):
            stock_prefixed_source_body_concordance("Original words.",
                                                   b"<title>Added</title><hi>Original words. Ending</hi>")
        with self.assertRaises(ValueError):
            stock_prefixed_source_body_concordance("Original words.",
                                                   b"<title>Added</title><hi>Original &external; words.</hi>")

    def test_unresolved_boundaries_identify_localized_vs_disjoint_differences(self):
        one=unexplained_word_boundary_census(
            "We should carry this exact source forward",
            "We should not carry this exact source forward",
        )
        self.assertEqual(one["common_start_word_tokens"],2)
        self.assertEqual(one["source_middle_different_word_tokens"],0)
        self.assertEqual(one["stock_middle_different_word_tokens"],1)
        self.assertTrue(one["changed_in_middle_with_both_matching_boundaries"])
        self.assertFalse(one["source_loss_or_editorial_equivalence_proven"])
        disjoint=unexplained_word_boundary_census("Original wholly different words",
                                                  "Unrelated compiled material")
        self.assertEqual(disjoint["common_start_word_tokens"],0)
        self.assertEqual(disjoint["common_end_word_tokens"],0)
        self.assertEqual(disjoint["common_suffix_fraction_bucket"],
                         "no_exact_common_word_suffix")
        self.assertNotIn("Unrelated",json.dumps(disjoint))

    def test_integrated_existing_original_source_to_stock_diagnostic_all_counts(self):
        original=(
            b"<?xml version='1.0' encoding='UTF-8'?>"
            b"<ThML><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1'/><div><p>Original, words.</p></div>"
            b"<scripCom osisRef='Bible:Gen.1.2'/><div><p>Source words differ here.</p></div>"
            b"</div2></div1></ThML>"+b" "*1100
        )
        source,_=_original_source_markers(original)
        result=compare_private_texts(source,{
            "Gen.1.1":b"<title>Separate label</title><hi>Original, words.</hi>",
            "Gen.1.2":b"<hi>Source words vary here.</hi>",
        })
        self.assertEqual(result["stock_original_body_suffix_exact_unicode_and_difference_classes"],
                         {"exact_source_body_unicode_equals_stock_text_suffix":1})
        self.assertEqual(result["unexplained_original_to_stock_word_boundary_count"],1)
        self.assertEqual(result["unexplained_original_to_stock_changed_segment_positions"],
                         {"middle_with_shared_edges":1})
        self.assertFalse(result["stock_body_suffix_comparison_does_not_approve_omitted_prefix_or_layout"] is False)
        self.assertFalse(result["full_authored_to_stock_parity_verified"])
        self.assertNotIn("Source words",json.dumps(result))
        self.assertNotIn("Separate label",json.dumps(result))


if __name__=="__main__":
    unittest.main()
