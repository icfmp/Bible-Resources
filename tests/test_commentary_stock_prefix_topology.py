"""Offline evidence: original stock XML prefix location and aligned glyph deltas."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_stock_prefix_topology import (
    aligned_punctuation_gap_diagnostics, source_word_prefix_topology,
)
from commentary_private_text_compare import (
    _original_source_markers, compare_private_texts,
)


class CommentaryStockPrefixTopologyTests(unittest.TestCase):
    def test_stock_prefix_separate_top_level_heading_before_source_paragraph(self):
        raw=b"<h3>Unverified stock heading </h3><p>Original body with <i>markup</i>.</p>"
        result=source_word_prefix_topology("Original body with markup!",raw)
        self.assertEqual(result["unapproved_stock_extra_word_prefix_count"],4)
        self.assertEqual(result["source_word_boundary_stock_top_level_owner"],"p")
        self.assertEqual(result["top_level_element_types_wholly_before_original_source_words"],
                         {"h3":1})
        self.assertEqual(result["prefix_text_top_level_owner_types"],["h3"])
        self.assertFalse(result["additional_stock_words_approved_as_heading"])
        self.assertNotIn("Unverified stock heading",json.dumps(result))

    def test_stock_prefix_inside_same_paragraph_and_in_root_text(self):
        paragraph=source_word_prefix_topology(
            "Original content",b"<p><hi>Extra title </hi>Original content.</p>")
        self.assertEqual(paragraph["source_word_boundary_stock_top_level_owner"],"p")
        self.assertEqual(paragraph["top_level_element_types_wholly_before_original_source_words"],{})
        self.assertEqual(paragraph["prefix_text_top_level_owner_types"],["p"])
        root=source_word_prefix_topology("Original content",b"Unverified prefix Original content.")
        self.assertEqual(root["source_word_boundary_stock_top_level_owner"],"_ROOT_TEXT")
        self.assertEqual(root["prefix_text_top_level_owner_types"],["_ROOT_TEXT"])

    def test_reject_missing_or_unreviewed_pure_prefix_and_invalid_markup(self):
        with self.assertRaises(ValueError):
            source_word_prefix_topology("Original content",b"<p>Different wording</p>")
        with self.assertRaises(ValueError):
            source_word_prefix_topology("Original content",b"<p>Original content plus suffix</p>")
        with self.assertRaises(ValueError):
            source_word_prefix_topology("Original content",b"<p>Bad <i>markup</p>")
        with self.assertRaises(ValueError):
            source_word_prefix_topology("Original content",b"<p>Bad &hidden; Original content</p>")

    def test_aligned_glyph_substitutions_without_replacing_original(self):
        report=aligned_punctuation_gap_diagnostics(
            'Original – prose with “quotes”!', 'Original - prose with "quotes"!')
        self.assertEqual(report["punctuation_gap_classes"]["one_to_one_glyph_substitution"],3)
        self.assertEqual(report["one_to_one_unicode_numeric_glyph_replacements"]["U+2013>U+002D"],1)
        self.assertEqual(report["one_to_one_unicode_numeric_glyph_replacements"]["U+201C>U+0022"],1)
        self.assertEqual(report["one_to_one_unicode_numeric_glyph_replacements"]["U+201D>U+0022"],1)
        self.assertTrue(report["all_nonword_glyph_differences_consistently_mapped"])
        self.assertFalse(report["editorial_punctuation_approval"])
        self.assertNotIn("Original",json.dumps(report))
        with self.assertRaises(ValueError):
            aligned_punctuation_gap_diagnostics("Original words","Different words")

    def test_integration_counts_all_source_prefix_and_punctuation_entries(self):
        source=(
            b"<?xml version='1.0' encoding='UTF-8'?>"
            b"<ThML><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1'/><div><p>Original body!</p></div>"
            b"<scripCom osisRef='Bible:Gen.1.2'/><div><p>Next – sentence.</p></div>"
            b"</div2></div1></ThML>"+b" " * 1100
        )
        units,_=_original_source_markers(source)
        stock={
            "Gen.1.1":b"<h3>Unapproved heading </h3><p>Original body?</p>",
            "Gen.1.2":b"<p>Next - sentence.</p>",
        }
        report=compare_private_texts(units,stock)
        self.assertEqual(report["stock_prefixed_body_first_source_word_top_level_tag_counts"],{"p":1})
        self.assertEqual(report["stock_prefix_complete_top_level_elements_preceding_source_word_by_tag"],{"h3":1})
        self.assertEqual(report["stock_prefix_cases_with_at_least_one_complete_prior_top_level_element"],1)
        self.assertEqual(report["punctuation_aligned_one_to_one_numeric_unicode_replacements"],
                         {"U+2013>U+002D":1})
        self.assertEqual(report["punctuation_entries_with_exclusively_one_to_one_glyph_changes"],1)
        self.assertFalse(report["full_authored_to_stock_parity_verified"])
        self.assertNotIn("Unapproved heading",json.dumps(report))


if __name__=="__main__":
    unittest.main()
