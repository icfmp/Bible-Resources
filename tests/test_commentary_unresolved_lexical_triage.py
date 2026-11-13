"""Synthetic lexical/markup audit. Never return authorial words or stock XML."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_unresolved_lexical_triage import (
    source_stock_unresolved_words, stock_raw_element_counts,
    marked_word_token_indices, UnresolvedLexicalSelectionCensus,
)
from commentary_private_text_compare import _original_source_markers, compare_private_texts
from pilot_preflight import PilotError


class UnresolvedLexicalSourceMarkupTests(unittest.TestCase):
    def test_one_word_substitution_counts_metadata_only(self):
        result=source_stock_unresolved_words(
            "Opening ancient sacred written ending.",
            "Opening ancient different written ending."
        )
        self.assertEqual(result["lexical_middle_shape"],"one_to_one_middle_word_substitution")
        self.assertEqual(result["one_word_difference_subtype"],
                         "different_case_sensitive_unicode_word")
        self.assertEqual(result["source_changed_middle_words"],1)
        self.assertEqual(result["stock_changed_middle_words"],1)
        self.assertEqual(result["common_start_word_tokens"],2)
        self.assertEqual(result["common_end_word_tokens"],2)
        self.assertEqual(result["middle_alignment_class"],"single_edit_block")
        self.assertEqual(result["alignment_opcode_type_counts"],{"replace":1})
        self.assertNotIn("sacred",json.dumps(result))
        self.assertNotIn("ancient different written",json.dumps(result))

    def test_distinct_replacements_inside_middle_not_hidden_as_one_edit(self):
        out=source_stock_unresolved_words(
            "start older retained verse kept ending",
            "start newer retained text kept ending"
        )
        self.assertEqual(out["lexical_middle_shape"],"middle_partial_shared_word_occurrences")
        self.assertEqual(out["middle_alignment_class"],"multiple_distinct_edit_blocks")
        self.assertEqual(out["alignment_edit_opcode_count"],2)
        self.assertEqual(out["exact_middle_matching_words_in_alignment"],1)

    def test_insertion_and_deletion_are_distinguished_from_edits(self):
        inserted=source_stock_unresolved_words("start end","start extra end")
        self.assertEqual(inserted["lexical_middle_shape"],"only_stock_middle_words_added")
        removed=source_stock_unresolved_words("start extra end","start end")
        self.assertEqual(removed["lexical_middle_shape"],"only_source_middle_words_removed")

    def test_disjoint_reordered_word_sets_are_only_diagnostic(self):
        result=source_stock_unresolved_words(
            "begin old words swapped keep",
            "begin swapped words old keep"
        )
        self.assertEqual(result["lexical_middle_shape"],"middle_same_word_multiset_different_order")
        self.assertTrue(result["unresolved_selection_does_not_prove_content_loss_or_edition_equivalence"])

    def test_oversized_alignment_skips_without_approving_parity(self):
        a=" ".join(["original"]*1100)
        b=" ".join(["changed"]*1100)
        result=source_stock_unresolved_words("begin "+a+" end","begin "+b+" end")
        self.assertEqual(result["middle_alignment_class"],
                         "alignment_skipped_under_explicit_safe_cell_limit")
        self.assertEqual(result["source_changed_middle_words"],1100)
        self.assertFalse(result["original_words_or_replacements_exposed"])

    def test_stock_markup_strict_parse_only_and_no_original_content(self):
        result=stock_raw_element_counts(
            b'<p>Made up words <reference osisRef="Gen.1">Chapter</reference></p>'
            b'<title>Title</title><table><tr><td>Data</td></tr></table>')
        self.assertEqual(result["reference"],1)
        self.assertEqual(result["title"],1)
        self.assertEqual(result["table"],1)
        self.assertNotIn("Chapter",json.dumps(result))
        with self.assertRaises(PilotError):
            stock_raw_element_counts(b"<p>invalid</title>")

    def test_inline_source_link_marked_word_indices_do_not_include_tails(self):
        from lxml import etree
        root=etree.fromstring(
            b'<p>A <scripRef osisRef="Bible:Gen.1.1">scripture'
            b'<hi> citation</hi></scripRef> then end</p>'
        )
        text="".join(root.itertext())
        self.assertEqual(
            marked_word_token_indices(root,"scripRef",text),[1,2])
        with self.assertRaises(PilotError):
            marked_word_token_indices(root,"scripRef","unrelated text")

    def test_integrated_verse_marker_count_and_markup_census(self):
        original_xml=(
            b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>Leading reference <scripRef osisRef="Bible:Gen.2.1">'
            b'next chapter</scripRef> and final word.</p></div>'
            b'<scripCom osisRef="Bible:Gen.1.2"/>'
            b'<div><p>Opening old word closes.</p></div>'
            b'</div2></div1></ThML.body></ThML>' + b" "*1100
        )
        source,_ = _original_source_markers(original_xml)
        report=compare_private_texts(source,{
            "Gen.1.1": b'<p>Leading reference <reference osisRef="Gen.2.1">'
                        b'changed chapter</reference> and final word.</p>',
            "Gen.1.2": b'<p>Opening new word closes.</p>',
        })
        triage=report["unresolved_source_stock_lexical_selection_triage"]
        self.assertEqual(triage["source_vs_stock_unresolved_word_selection_cases"],2)
        self.assertEqual(triage["source_scripRef_presence"],
                         {"source_has_scripRef":1,"source_no_scripRef":1})
        self.assertEqual(triage["stock_reference_presence"],
                         {"stock_has_reference":1,"stock_no_reference":1})
        self.assertEqual(triage["one_to_one_middle_word_changes_inside_source_and_stock_references"],{
            "source_outside_scripRef_stock_outside_reference":1,
            "source_within_scripRef_stock_within_reference":1,
        })
        self.assertEqual(triage["source_scripRef_and_stock_reference_changed_word_overlap"],{
            "source_link_overlap_stock_ref_overlap":1,
            "source_no_link_overlap_stock_no_ref_overlap":1,
        })
        self.assertEqual(
            sum(triage["differing_middle_shape_classes"].values()),2)
        self.assertEqual(len(triage["bounded_highest_changed_word_count_line_hash_only_cases"]),2)
        self.assertNotIn("next chapter",json.dumps(triage))
        self.assertNotIn("changed chapter",json.dumps(triage))
        self.assertFalse(triage["full_original_commentary_authorial_text_parity_approved"])


if __name__=="__main__":
    unittest.main()
