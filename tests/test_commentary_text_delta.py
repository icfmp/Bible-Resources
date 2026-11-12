"""Closed-set, text-private commentary lexical discrepancy classification."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_text_delta import punctuation_relationship, word_relationship, nonword_symbol_excess
from commentary_private_text_compare import _original_source_markers,compare_private_texts


class CommentaryTextDeltaTests(unittest.TestCase):
    def test_punctuation_subtypes_do_not_return_original_symbols_or_words(self):
        items=[
            ("Private, wording.", "Private wording.", "source_nonword_symbols_contain_stock_sequence"),
            ("Private, wording.", "Private; wording.", "nonword_symbol_identity_or_counts_differ"),
            ("Private, wording.", "Private ,wording.", "same_nonword_symbols_but_positions_or_whitespace_differ"),
            ("Private wording", "Private. wording", "nonword_symbols_only_in_stock"),
            ("Private. wording", "Private wording", "nonword_symbols_only_in_source"),
        ]
        for left,right,label in items:
            with self.subTest(label=label):
                self.assertEqual(punctuation_relationship(left,right),label)
                self.assertNotIn("Private",punctuation_relationship(left,right))
        with self.assertRaises(ValueError):
            punctuation_relationship("private old wording","private new wording")

    def test_word_categories_are_independently_exclusive_and_redacted(self):
        items=[
            ("Private Words", "private words", "only_unicode_casefold_differences"),
            ("Ⅳ studies", "IV studies", "only_unicode_compatibility_word_differences"),
            ("ancient commentary words", "words commentary ancient", "same_word_multiset_but_order_differs"),
            ("ancient commentary words", "intro ancient commentary words end", "source_words_contiguous_inside_longer_stock"),
            ("start ancient commentary words end", "ancient commentary words", "stock_words_contiguous_inside_longer_source"),
            ("ancient commentary words", "ancient added commentary extra words", "source_words_in_order_with_extra_stock_words"),
            ("ancient added commentary extra words", "ancient commentary words", "stock_words_in_order_with_extra_source_words"),
            ("ancient commentary words", "different altered chapter", "different_word_order_or_selection_requires_review"),
        ]
        for left,right,label in items:
            with self.subTest(label=label):
                result=word_relationship(left,right)
                self.assertEqual(result["relationship"],label)
                self.assertFalse(result["exact_text_equivalence_established"])
                self.assertFalse(result["word_sequences_or_original_content_returned"])
                self.assertNotIn("ancient",json.dumps(result))
        with self.assertRaises(ValueError):
            word_relationship("same words","same words")

    def test_original_contiguous_in_stock_is_located_without_emitting_extra_words(self):
        original="Private phrase maintained"
        cases=[
            ("Heading Private phrase maintained","extra_stock_words_only_before_original_body",1,0),
            ("Private phrase maintained heading","extra_stock_words_only_after_original_body",0,1),
            ("Title Private phrase maintained ending","extra_stock_words_before_and_after_original_body",1,1),
        ]
        for stock,category,prefix,suffix in cases:
            with self.subTest(category=category):
                report=word_relationship(original,stock)
                self.assertEqual(report["relationship"],"source_words_contiguous_inside_longer_stock")
                self.assertEqual(report["original_words_contiguous_in_stock_location"],category)
                self.assertEqual(report["additional_stock_word_tokens_before_source"],prefix)
                self.assertEqual(report["additional_stock_word_tokens_after_source"],suffix)
                self.assertNotIn("heading",json.dumps(report).lower())
                self.assertNotIn("Private",json.dumps(report))

    def test_original_nonword_glyph_codepoints_are_numeric_ids_not_source_glyphs(self):
        source,stock=nonword_symbol_excess("Private–words.","Private-words.")
        self.assertEqual(source["U+2013"],1)
        self.assertEqual(stock["U+002D"],1)
        self.assertEqual(sum(source.values()),1)
        self.assertEqual(sum(stock.values()),1)
        self.assertNotIn("Private",json.dumps({"source":source,"stock":stock}))

    def test_integration_covers_exactly_every_source_disagreement(self):
        source_xml=(
            b"<?xml version='1.0' encoding='UTF-8'?>"
            b"<ThML><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1'/><div><p>Original, prose.</p></div>"
            b"<scripCom osisRef='Bible:Gen.1.2'/><div><p>Source with serious difference.</p></div>"
            b"</div2></div1></ThML>"+b" " * 1100
        )
        source,proof=_original_source_markers(source_xml)
        result=compare_private_texts(source,{
            "Gen.1.1":b"<p>Original; prose.</p>",
            "Gen.1.2":b"<p>Stock with serious variation.</p>",
        })
        self.assertEqual(result["source_verse_or_range_bodies_compared"],2)
        self.assertEqual(result["lexical_disagreement_classification"]["same_unicode_word_tokens_different_punctuation"],1)
        self.assertEqual(result["lexical_disagreement_classification"]["different_unicode_word_token_sequence_or_selection"],1)
        self.assertEqual(result["same_words_different_punctuation_subtypes"]["nonword_symbol_identity_or_counts_differ"],1)
        self.assertEqual(result["different_word_sequence_relationship_subtypes"]["different_word_order_or_selection_requires_review"],1)
        self.assertEqual(sum(result["different_word_sequence_overlap_buckets"].values()),1)
        self.assertEqual(len(result["bounded_private_prioritized_hash_line_diagnostics"]),1)
        self.assertFalse(result["full_authored_to_stock_parity_verified"])
        self.assertNotIn("serious variation",json.dumps(result))
        self.assertNotIn("Original, prose",json.dumps(result))

if __name__=="__main__":
    unittest.main()
