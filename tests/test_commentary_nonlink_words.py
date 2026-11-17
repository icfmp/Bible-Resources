"""Synthetic original/compiled prose word integrity outside genuine scripture links."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_nonlink_words import compare_words_outside_links, _private_unique_original_gap_spans
from commentary_private_text_compare import _original_source_markers, compare_private_texts
from pilot_preflight import PilotError


class CommentaryOriginalOutsideLinkWordsTests(unittest.TestCase):
    def test_markup_label_changes_do_not_create_unmarked_prose_discrepancy(self):
        out=compare_words_outside_links(
            ["Begin","Gen","1","end"],["Begin","Genesis","one","end"],
            [1,2],[1,2])
        self.assertEqual(out["outside_link_word_relation"],
                         "same_ordered_case_sensitive_unicode_plain_words")
        self.assertEqual(out["original_plain_word_tokens"],2)
        self.assertEqual(out["stock_plain_word_tokens"],2)
        self.assertFalse(out["actual_original_words_or_compiled_content_exposed"])
        self.assertNotIn("Genesis",json.dumps(out))

    def test_unmarked_stock_citation_label_can_be_extra_plain_text(self):
        out=compare_words_outside_links(
            ["Start","Gen","1","End"],["Start","Gen","1","End"],
            [1,2],[])
        self.assertEqual(out["outside_link_word_relation"],
                         "original_plain_words_in_order_with_extra_unmarked_stock_words")
        self.assertEqual(out["shared_plain_word_multiset_occurrences"],2)

    def test_stock_metadata_before_original_prose_does_not_establish_authorial_parity(self):
        out=compare_words_outside_links(
            ["Original","prose"],["Title","Original","prose"],
            [],[])
        self.assertEqual(out["outside_link_word_relation"],
                         "original_plain_words_contiguous_inside_longer_stock_plain_text")
        self.assertTrue(out[
            "plain_word_containment_or_sequence_match_is_not_edition_or_markup_parity"])

    def test_actual_differing_plain_prose_stays_unresolved(self):
        out=compare_words_outside_links(
            ["Beginning","original","ending"],["Beginning","altered","ending"],
            [],[])
        self.assertEqual(out["outside_link_word_relation"],
                         "plain_word_order_or_selection_requires_editorial_review")
        self.assertEqual(out["shared_plain_word_multiset_occurrences"],2)

    def test_unicode_case_changes_are_not_exact_original_prose(self):
        out=compare_words_outside_links(["Original"],["original"],[],[])
        self.assertEqual(out["outside_link_word_relation"],
                         "same_ordered_plain_words_only_casefold_differs")

    def test_unique_source_extra_word_gaps_are_only_topology_not_edition_proof(self):
        cases = (
            (["onlyprefixsecret", "alpha", "beta"], ["alpha", "beta"],
             "unique_alignment_prefix_extra_words_only", (1, 0, 0, 1)),
            (["alpha", "beta", "onlysuffixsecret"], ["alpha", "beta"],
             "unique_alignment_suffix_extra_words_only", (0, 0, 1, 1)),
            (["alpha", "onlymiddlesecret", "beta"], ["alpha", "beta"],
             "unique_alignment_interior_extra_words_only", (0, 1, 0, 1)),
            (["onlyprefixsecret", "alpha", "onlybetweensecret", "beta", "onlysuffixsecret"], ["alpha", "beta"],
             "unique_alignment_interior_and_edge_extra_words", (1, 1, 1, 3)),
        )
        for source, stock, category, expected in cases:
            with self.subTest(category=category):
                result=compare_words_outside_links(source,stock,[],[])
                layout=result["source_extra_unlinked_word_gap_layout"]
                self.assertEqual(layout["alignment_topology"],category)
                self.assertEqual((
                    layout["fixed_prefix_extra_words"],
                    layout["fixed_interior_extra_words"],
                    layout["fixed_suffix_extra_words"],
                    layout["source_extra_nonlink_word_count"],
                ),expected)
                self.assertFalse(layout[
                    "textual_section_or_editional_ownership_established"])
                self.assertNotIn("onlyprefixsecret",json.dumps(result))
                self.assertNotIn("onlymiddlesecret",json.dumps(result))

    def test_repeated_original_tokens_must_not_be_assigned_to_one_gap(self):
        result=compare_words_outside_links(
            ["alpha","alpha","beta"],["alpha","beta"],[],[])
        layout=result["source_extra_unlinked_word_gap_layout"]
        self.assertEqual(layout["alignment_topology"],
                         "multiple_exact_subsequence_alignments_no_fixed_gap_ownership")
        self.assertEqual(layout["source_extra_nonlink_word_count"],1)
        self.assertIsNone(layout["fixed_extra_word_spans"])
        self.assertIsNone(layout["fixed_prefix_extra_words"])
        self.assertIsNone(layout["fixed_interior_extra_words"])
        self.assertIsNone(layout["fixed_suffix_extra_words"])

    def test_real_link_label_exclusion_precedes_extra_word_location(self):
        result=compare_words_outside_links(
            ["alpha","sourcecitationsecret","label","nonlinkedsecret","beta"],
            ["alpha","stockcitationsecret","reference","beta"],[1,2],[1,2])
        layout=result["source_extra_unlinked_word_gap_layout"]
        self.assertEqual(layout["alignment_topology"],
                         "unique_alignment_interior_extra_words_only")
        self.assertEqual(layout["source_extra_nonlink_word_count"],1)
        self.assertEqual(result["original_scripture_link_word_tokens_removed"],2)
        self.assertEqual(result["stock_reference_word_tokens_removed"],2)
        self.assertNotIn("nonlinkedsecret",json.dumps(result))
        self.assertNotIn("stockcitationsecret",json.dumps(result))

    def test_private_exact_unmatched_original_spans_are_never_automatically_public(self):
        original=["alpha","secretchapter","secretpassage","beta","secretending","gamma"]
        stock=["alpha","beta","gamma"]
        self.assertEqual(_private_unique_original_gap_spans(original,stock),
                         [["secretchapter","secretpassage"],["secretending"]])
        self.assertIsNone(_private_unique_original_gap_spans(
            ["alpha","alpha","beta"],["alpha","beta"]))
        public=compare_words_outside_links(original,stock,[],[])
        self.assertNotIn("secretchapter",json.dumps(public))
        self.assertNotIn("secretending",json.dumps(public))
        self.assertEqual(public["source_extra_unlinked_word_gap_layout"][
            "fixed_extra_word_spans"],2)

    def test_word_index_must_be_real_bound_and_unique(self):
        for ids in ([1,1],[-1],[2]):
            with self.subTest(ids=ids):
                with self.assertRaises(PilotError):
                    compare_words_outside_links(["One","Two"],["One","Two"],ids,[])

    def test_integrated_lexical_source_markup_versus_plain_prose(self):
        original_xml=(
            b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>Leading <scripRef osisRef="Bible:Gen.2.1">'
            b'first label</scripRef> closing words.</p></div>'
            b'<scripCom osisRef="Bible:Gen.1.2"/>'
            b'<div><p>Original ordinary words.</p></div>'
            b'</div2></div1></ThML.body></ThML>'+b" "*1100
        )
        source,_=_original_source_markers(original_xml)
        out=compare_private_texts(source,{
            "Gen.1.1":b'<p>Leading <reference osisRef="Gen.2.1">'
                        b'changed label</reference> closing words.</p>',
            "Gen.1.2":b"<p>Original different words.</p>",
        })
        d=out["unresolved_source_stock_lexical_selection_triage"]
        self.assertEqual(d["source_vs_stock_unresolved_word_selection_cases"],2)
        self.assertEqual(d["original_prose_outside_link_word_relation_counts"],{
            "same_ordered_case_sensitive_unicode_plain_words":1,
            "plain_word_order_or_selection_requires_editorial_review":1,
        })
        self.assertEqual(len(d["bounded_plain_word_nontrivial_differences_line_and_hash_cases"]),1)
        self.assertEqual(d["original_prose_outside_link_relations_by_compiled_reference_markup"],{
            "stock_has_reference":{"same_ordered_case_sensitive_unicode_plain_words":1},
            "stock_no_reference":{"plain_word_order_or_selection_requires_editorial_review":1},
        })
        self.assertNotIn("changed label",json.dumps(d))
        self.assertNotIn("Original different",json.dumps(d))


if __name__=="__main__":
    unittest.main()
