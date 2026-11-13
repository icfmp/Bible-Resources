"""Synthetic, source-neutral tests for private exact Unicode prose alignment."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_private_text_compare import _original_source_markers, compare_private_texts
from pilot_preflight import PilotError


class OriginalPlainWordsAlignmentTests(unittest.TestCase):
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
        self.assertNotIn("original",json.dumps(result))

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
