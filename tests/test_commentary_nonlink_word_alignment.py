"""Synthetic, source-neutral tests for private exact Unicode prose alignment."""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_chapter_paragraph_overlap import longest_common_contiguous_word_run
from commentary_text_delta import longest_contiguous_token_run
from commentary_private_text_compare import _original_source_markers, compare_private_texts
from pilot_preflight import PilotError


class OriginalPlainWordsAlignmentTests(unittest.TestCase):
    def test_source_longer_full_difference_explained_by_actual_scripture_ref_label(self):
        from commentary_nonlink_word_alignment import (
            classify_original_link_label_effect_on_source_longer_words as inspect)
        a=inspect(["Start","cited","verse","End"],["Start","End"],[1,2])
        self.assertEqual(a["source_original_link_label_exclusion_class"],
                         "only_original_scripRef_label_words_account_for_full_source_extra")
        self.assertEqual(a["original_marked_scripRef_label_words"],2)
        self.assertEqual(a["source_nonlink_word_surplus_vs_native"],0)
        self.assertFalse(a["full_original_source_or_native_text_modified"])

    def test_original_extra_nonlink_words_remain_unexplained_by_link_labels(self):
        from commentary_nonlink_word_alignment import (
            classify_original_link_label_effect_on_source_longer_words as inspect)
        a=inspect(["Start","extra","End"],["Start","End"],[])
        self.assertEqual(a["source_original_link_label_exclusion_class"],
                         "native_words_in_order_with_extra_original_nonlink_words")
        self.assertEqual(a["source_nonlink_word_surplus_vs_native"],1)
        b=inspect(["Start","linked","extra","End"],["Start","End"],[1])
        self.assertEqual(b["source_original_link_label_exclusion_class"],
                         "native_words_in_order_with_extra_original_nonlink_words")
        self.assertEqual(b["source_nonlink_word_surplus_vs_native"],1)
        self.assertNotIn("extra",json.dumps(b))

    def test_source_link_label_classification_never_guesses_order_or_indexes(self):
        from commentary_nonlink_word_alignment import (
            classify_original_link_label_effect_on_source_longer_words as inspect)
        with self.assertRaises(PilotError):
            inspect(["source","middle","end"],["end","source"],[])
        with self.assertRaises(PilotError):
            inspect(["source","middle","end"],["source","end"],[3])
        with self.assertRaises(PilotError):
            inspect(["source","middle","end"],["source","end"],[1,1])
        with self.assertRaises(PilotError):
            inspect(["source","middle","end"],["source","end"],[True])
    def test_bounded_linear_fallback_for_large_exact_source_word_order(self):
        source=[f"βWord{i}" for i in range(4001)]
        compiled=["prefix"]+source[:1500]+["interposed"]+source[1500:]+["suffix"]
        result=plain_word_alignment(source,compiled)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "alignment_skipped_exceeds_reviewed_word_or_cell_bound")
        self.assertTrue(result["linear_exact_source_subsequence_in_stock"])
        self.assertIsNone(result["original_plain_words_not_matched_in_exact_order"])
        self.assertTrue(result[
            "linear_source_subsequence_does_not_certify_original_text_or_markup_parity"])
        missing=plain_word_alignment(source,source[:2000]+source[2001:])
        self.assertFalse(missing["linear_exact_source_subsequence_in_stock"])
        repeated=plain_word_alignment(["repeat"]*4001,["repeat"]*4000)
        self.assertFalse(repeated["linear_exact_source_subsequence_in_stock"])

    def test_linear_subsequence_limit_remains_explicit(self):
        result=plain_word_alignment(["word"]*100001,["word"])
        self.assertIsNone(result["linear_exact_source_subsequence_in_stock"])
        self.assertIsNone(result["original_plain_words_not_matched_in_exact_order"])

    def test_shared_exact_span_equals_independent_bruteforce_across_short_unicode_cases(self):
        """Characterize both old consumers, including repeats, case and order."""
        alphabet = ("a", "A", "β")
        cases = [[]] + [
            list(words) for size in range(1, 4)
            for words in product(alphabet, repeat=size)
        ]

        def independent_span(left, right):
            best = 0
            for i in range(len(left)):
                for j in range(len(right)):
                    run = 0
                    while (i + run < len(left) and j + run < len(right)
                           and left[i + run] == right[j + run]):
                        run += 1
                    best = max(best, run)
            return best

        for source in cases:
            for stock in cases:
                expected = independent_span(source, stock)
                self.assertEqual(longest_contiguous_token_run(source, stock),
                                 expected)
                self.assertEqual(longest_common_contiguous_word_run(source, stock),
                                 expected)
                result = plain_word_alignment(source, stock)
                self.assertEqual(
                    result["exact_unicode_longest_contiguous_shared_word_run_count"],
                    expected,
                )
                self.assertTrue(result[
                    "longest_common_subsequence_is_not_textual_or_edition_parity"
                ])
                self.assertTrue(result["original_words_never_exposed"])

    def test_original_words_exact_in_order_with_extra_stock_words(self):
        result=plain_word_alignment(["before","original","after"],
                                    ["before","extra","original","after"])
        self.assertEqual(result["exact_unicode_longest_common_subsequence_word_count"],3)
        self.assertEqual(result["exact_unicode_longest_contiguous_shared_word_run_count"],2)
        self.assertEqual(result["original_plain_words_not_matched_in_exact_order"],0)
        self.assertEqual(result["stock_plain_words_not_matched_in_exact_order"],1)
        self.assertEqual(result["common_start_word_tokens"],1)
        self.assertEqual(result["common_end_word_tokens"],2)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "all_source_plain_words_in_stock_order_with_extra_stock_words")
        self.assertNotIn("\"before\"",json.dumps(result))

    def test_word_reordering_is_not_an_exact_source_preserving_subsequence(self):
        result=plain_word_alignment(["one","two","three"],["one","three","two"])
        self.assertEqual(result["exact_unicode_longest_common_subsequence_word_count"],2)
        self.assertEqual(result["original_plain_words_not_matched_in_exact_order"],1)
        self.assertEqual(result["stock_plain_words_not_matched_in_exact_order"],1)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "one_or_two_original_plain_words_not_found_in_exact_order")

    def test_large_mismatch_classifies_without_guessing_missing_content(self):
        source=["heading"]+[f"original{i}" for i in range(12)]
        compiled=["heading"]+["compiled"]*3
        result=plain_word_alignment(source,compiled)
        self.assertEqual(result["exact_unicode_longest_common_subsequence_word_count"],1)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "more_than_ten_original_plain_words_not_found_in_exact_order")
        self.assertTrue(result["longest_common_subsequence_is_not_textual_or_edition_parity"])

    def test_repeated_words_do_not_falsely_consume_compiled_occurrences(self):
        result=plain_word_alignment(["repeat","repeat","word"],["repeat","word"])
        self.assertEqual(result["exact_unicode_longest_common_subsequence_word_count"],2)
        self.assertEqual(result["original_plain_words_not_matched_in_exact_order"],1)
        self.assertEqual(result["stock_plain_words_not_matched_in_exact_order"],0)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "all_stock_plain_words_in_source_order_with_extra_source_words")

    def test_alignment_bound_is_explicit_and_never_approves_parity(self):
        result=plain_word_alignment(["different"]*1500,["source"]*1500)
        self.assertEqual(result["exact_unicode_ordered_alignment_class"],
                         "alignment_skipped_exceeds_reviewed_word_or_cell_bound")
        self.assertIsNone(result["exact_unicode_longest_common_subsequence_word_count"])
        self.assertTrue(result["longest_common_subsequence_is_not_textual_or_edition_parity"])

    def test_invalid_stream_elements_are_blocking(self):
        with self.assertRaises(PilotError):
            plain_word_alignment(["word",None],["word"])
        with self.assertRaises(PilotError):
            plain_word_alignment(["word"],[""])

    def test_integrates_only_nonlink_cases_and_keeps_source_lines_and_hashes(self):
        xml=(
            b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>Opening <scripRef osisRef="Bible:Gen.2.1">'
            b'first label</scripRef> closing words.</p></div>'
            b'<scripCom osisRef="Bible:Gen.1.2"/>'
            b'<div><p>Original ordinary words.</p></div>'
            b'</div2></div1></ThML.body></ThML>'+b" "*1100
        )
        source,_=_original_source_markers(xml)
        comparison=compare_private_texts(source,{
            "Gen.1.1":b'<p>Opening <reference osisRef="Gen.2.1">'
                        b'changed label</reference> closing words.</p>',
            "Gen.1.2":b"<p>Original different words.</p>",
        })
        d=comparison["unresolved_source_stock_lexical_selection_triage"]
        cases=d["bounded_plain_word_nontrivial_differences_line_and_hash_cases"]
        self.assertEqual(len(cases),1)
        self.assertEqual(cases[0]["original_source_p_element_count"],1)
        self.assertEqual(cases[0]["stock_p_element_count"],1)
        self.assertEqual(cases[0]["original_source_scripRef_element_count"],0)
        self.assertEqual(cases[0]["stock_reference_element_count"],0)
        self.assertEqual(
            cases[0]["exact_plain_word_alignment"]["original_plain_words_not_matched_in_exact_order"],1)
        self.assertEqual(d["bounded_plain_word_alignment_classes"],{
            "one_or_two_original_plain_words_not_found_in_exact_order":1
        })
        self.assertNotIn("Original ordinary",json.dumps(cases))
        self.assertNotIn("Original different",json.dumps(cases))


if __name__ == "__main__":
    unittest.main()
