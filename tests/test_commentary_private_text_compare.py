"""Synthetic, source-neutral CCEL↔stock SWORD private lexical comparison checks."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_private_text_compare import (
    _original_source_markers,compare_private_texts,raw_as_strict_xml_text)
from pilot_preflight import PilotError


class CommentaryOriginalStockTextTests(unittest.TestCase):
    def test_real_compiled_reference_markup_exclusion_is_independent_of_text(self):
        from commentary_private_text_compare import private_actual_native_reference_word_positions
        from commentary_nonlink_words import compare_words_outside_links
        raw=b"<p>Alpha <reference osisRef='Gen.2.1'>quoted citation</reference> omega.</p>"
        visible=raw_as_strict_xml_text(raw)
        self.assertEqual(visible,"Alpha quoted citation omega.")
        positions=private_actual_native_reference_word_positions(raw,visible)
        self.assertEqual(positions,[1,2])
        checked=compare_words_outside_links(
            ["Alpha","quoted","citation","omega"],
            ["Alpha","quoted","citation","omega"],
            [1,2],positions)
        self.assertEqual(checked["outside_link_word_relation"],
                         "same_ordered_case_sensitive_unicode_plain_words")
        self.assertEqual(checked["stock_reference_word_tokens_removed"],2)
        self.assertFalse(checked["actual_original_words_or_compiled_content_exposed"])
        self.assertNotIn('"quoted"',json.dumps(checked))

    def test_compiled_reference_word_positions_block_malformed_markup_or_text_mismatch(self):
        from commentary_private_text_compare import private_actual_native_reference_word_positions
        with self.assertRaises(PilotError):
            private_actual_native_reference_word_positions(
                b"<p>Unclosed</invalid>","Unclosed")
        with self.assertRaises(PilotError):
            private_actual_native_reference_word_positions(
                b"<p>Original native</p>","Other")

    def test_large_ordered_source_witness_never_claims_exact_content_parity(self):
        from commentary_private_text_compare import select_authorial_word_loss_attention
        def case(value):
            return {"exact_plain_word_alignment": {
                "original_plain_words_not_matched_in_exact_order": None,
                "linear_exact_source_subsequence_in_stock": value}}
        selected,receipt=select_authorial_word_loss_attention(
            [case(True),case(False),case(None)])
        self.assertEqual(selected,[])
        self.assertEqual(receipt["classes"],{
            "original_alignment_budget_not_resolved":1,
            "over_budget_all_source_words_in_stock_order":1,
            "over_budget_source_order_not_proven":1})
        self.assertTrue(receipt["source_punctuation_and_markup_parity_not_proven"])
        with self.assertRaises(PilotError):
            select_authorial_word_loss_attention([case("unsafe")])

    def test_stock_extra_words_around_source_do_not_invoke_suffix_only_prefix_probe(self):
        original, proof = _original_source_markers(self.source())
        observed = compare_private_texts(original, {
            "Gen.1.1": b"<p>Extra opening words. Exact private text; punctuation? "
                       b"Extra closing words.</p>",
            "Gen.1.4": b"<p>Original next paragraph.</p>",
        })
        locations = observed["stock_containment_additional_word_position_counts"]
        self.assertEqual(
            locations.get("extra_stock_words_before_and_after_original_body"), 1)
        self.assertEqual(observed["source_book_word_relationship_subtypes"],
                         {"Gen":{"source_words_contiguous_inside_longer_stock":1}})
        self.assertEqual(
            observed["original_body_mid_stock_or_at_start_not_assumed_covered_by_prefix_probe"], 1)
        self.assertEqual(
            observed["strict_original_body_at_stock_suffix_prefix_topology_cases"], 0)
        self.assertEqual(
            observed["source_neighbor_compared_to_stock_prefix_entry_count"], 0)
        self.assertFalse(observed["all_selected_verse_range_body_text_exact_matches"])

    def test_empty_authorial_div_remains_in_original_marker_census(self):
        xml = self.source().replace(
            b"<div><p>Original next paragraph.</p></div>",
            b"<div><p>  </p></div>")
        with self.assertRaisesRegex(PilotError, "Empty original source"):
            _original_source_markers(xml)
        source, proof = _original_source_markers(xml, on_no_visible_text="record")
        self.assertEqual(proof["original_verse_or_range_body_count"], 2)
        self.assertEqual(proof["original_verse_or_range_body_with_visible_text_count"], 1)
        self.assertEqual(proof["original_sections_without_visible_text_count"], 1)
        self.assertEqual(sum(map(len, source.values())), 1)
        self.assertFalse(proof["original_sections_without_visible_text_examples_truncated"])
        self.assertTrue(proof["original_reference_and_adjacent_divisions_not_modified"])
        self.assertEqual(
            proof["bounded_original_sections_without_visible_text_line_sha_structure"][0]
            ["original_adjacent_div_child_tag_counts"], {"p": 1})
        self.assertNotIn("Original next paragraph.", json.dumps(proof))

    def test_only_source_words_not_found_are_routed_to_loss_identity_gate(self):
        from commentary_private_text_compare import select_authorial_word_loss_attention
        candidate = lambda missing: {
            "exact_plain_word_alignment": {
                "original_plain_words_not_matched_in_exact_order": missing}}
        selected, proof = select_authorial_word_loss_attention(
            [candidate(0), candidate(3), candidate(None)])
        self.assertEqual(len(selected), 1)
        self.assertEqual(
            selected[0]["exact_plain_word_alignment"][
                "original_plain_words_not_matched_in_exact_order"], 3)
        self.assertEqual(proof["bounded_original_lexical_attention_cases_checked"], 3)
        self.assertEqual(sum(proof["classes"].values()), 3)
        self.assertTrue(proof["all_original_lexical_cases_remain_in_main_text_diagnostic"])
        self.assertFalse(proof["source_punctuation_and_markup_parity_not_proven"] is False)
        with self.assertRaises(PilotError):
            select_authorial_word_loss_attention([candidate(-1)])

    def test_all_unreviewed_chapter_siblings_produce_explicit_not_tested_receipts(self):
        from commentary_private_text_compare import unreviewed_original_chapter_sibling_receipts
        proof = {"explicit_chapter_source_marker_count": 2,
                 "original_chapter_siblings_reviewed_count": 0,
                 "original_chapter_siblings_not_reviewed_count": 2}
        receipts = unreviewed_original_chapter_sibling_receipts(proof)
        self.assertEqual(len(receipts), 4)
        self.assertEqual(receipts[0]["original_chapter_source_siblings_compared"], 0)
        for row in receipts:
            self.assertFalse(row["authorial_chapter_structure_or_native_introduction_parity"])
            self.assertTrue(row[
                "unreviewed_source_sibling_must_not_be_called_missing_content"])
        with self.assertRaises(PilotError):
            unreviewed_original_chapter_sibling_receipts({
                **proof, "original_chapter_siblings_reviewed_count": 1})

    def test_select_six_volume_source_requires_explicit_original_volume(self):
        from commentary_private_text_compare import select_pinned_source_volume
        source = {"commentary_source": {"xml_witness_volumes": [
            {"number": 1, "url": "https://www.ccel.org/ccel/h/henry/mhc1.xml",
             "sha256": "a"*64},
            {"number": 2, "url": "https://www.ccel.org/ccel/h/henry/mhc2.xml",
             "sha256": "b"*64},
        ]}}
        with self.assertRaises(PilotError):
            select_pinned_source_volume(source)
        self.assertEqual(
            select_pinned_source_volume(source, 2),
            (2, "https://www.ccel.org/ccel/h/henry/mhc2.xml", "b"*64, True, 2))
        with self.assertRaises(PilotError):
            select_pinned_source_volume(source, 3)
        with self.assertRaises(PilotError):
            select_pinned_source_volume(source, 0)

    def test_select_single_source_keeps_existing_legacy_call(self):
        from commentary_private_text_compare import select_pinned_source_volume
        source = {"commentary_source": {
            "xml_witness_url": "https://www.ccel.org/ccel/h/henry/mhcc.xml",
            "xml_witness_sha256": "d"*64,
        }}
        self.assertEqual(
            select_pinned_source_volume(source),
            (1, "https://www.ccel.org/ccel/h/henry/mhcc.xml", "d"*64, False, 1))
        with self.assertRaises(PilotError):
            select_pinned_source_volume(source, 2)

    def source(self):
        return (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b"<ThML><ThML.body><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.3'/>"
            b"<div><p>Exact private text, punctuation!</p></div>"
            b"<scripCom osisRef='Bible:Gen.1.4'/>"
            b"<div><p>Original next paragraph.</p></div>"
            b"<scripCom osisRef='Bible:Gen.1'/>"
            b"<h2>Chapter heading not a verse unit.</h2>"
            b"</div2></div1></ThML.body></ThML>" + b" " * 1100)

    def test_exact_and_changed_punctuation_are_distinct_and_private(self):
        units,proof=_original_source_markers(self.source())
        self.assertEqual(proof["original_verse_or_range_body_count"],2)
        self.assertEqual(proof["chapter_source_markers_not_compared"],1)
        out=compare_private_texts(units,{
            "Gen.1.1":b"<p>Exact private text, punctuation!</p>",
            "Gen.1.4":b"<p>Original next paragraph?</p>",
        })
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["exact_unicode_text_match"],1)
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["lexical_text_or_punctuation_difference"],1)
        self.assertFalse(out["all_selected_verse_range_body_text_exact_matches"])
        self.assertFalse(out["full_authored_to_stock_parity_verified"])
        self.assertFalse(out["original_paragraphs_notes_and_quotations_verified"])
        self.assertNotIn("Exact private text",json.dumps(out))
        self.assertNotIn("Original next paragraph",json.dumps(out))

    def test_diagnostic_word_sequence_and_added_stock_markup_are_not_false_parity(self):
        original,_=_original_source_markers(self.source())
        punctuation=compare_private_texts(original,{
            "Gen.1.1":b"<p>Exact private text punctuation!</p>",
            "Gen.1.4":b"<p>Original next paragraph.</p>",
        })
        self.assertEqual(
            punctuation["lexical_disagreement_classification"][
                "same_unicode_word_tokens_different_punctuation"],1)
        self.assertFalse(punctuation["full_authored_to_stock_parity_verified"])
        with_heading=compare_private_texts(original,{
            "Gen.1.1":b"<h3>Added heading. </h3><p>Exact private text, punctuation!</p>",
            "Gen.1.4":b"<p>Original next paragraph.</p>",
        })
        self.assertEqual(
            with_heading["lexical_disagreement_classification"][
                "full_original_whitespace_collapsed_body_inside_stock"],1)
        self.assertTrue(with_heading["disagreement_categories_are_only_exploratory_not_text_parity"])
        self.assertFalse(with_heading["full_authored_to_stock_parity_verified"])

    def test_whitespace_only_differences_are_not_exact_fidelity(self):
        units,_=_original_source_markers(self.source())
        out=compare_private_texts(units,{
            "Gen.1.1":b"<p> Exact private text, punctuation! </p>",
            "Gen.1.4":b"<p>Original  next paragraph.</p>",
        })
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["edge_whitespace_difference_only"],1)
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["interior_whitespace_difference_only"],1)
        self.assertFalse(out["all_selected_verse_range_body_text_exact_matches"])

    def test_raw_xml_must_parse_without_guesswork(self):
        self.assertIsNone(raw_as_strict_xml_text(b"<p>bad</span>"))
        self.assertIsNone(raw_as_strict_xml_text(b"<!DOCTYPE x><p>unsupported</p>"))
        self.assertEqual(raw_as_strict_xml_text(b"<p>Fine punctuation.</p>"),"Fine punctuation.")

    def test_missing_native_start_is_not_claimed_as_missing_source_text(self):
        units,_=_original_source_markers(self.source())
        out=compare_private_texts(units,{"Gen.1.1":b"<p>Exact private text, punctuation!</p>"})
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["missing_original_start_in_native_raw"],1)
        self.assertFalse(out["full_authored_to_stock_parity_verified"])

    def test_intervening_nonwhitespace_original_text_blocks(self):
        source=self.source().replace(
            b"<scripCom osisRef='Bible:Gen.1.4'/>",
            b"<scripCom osisRef='Bible:Gen.1.4'/>Original words before div"
        )
        with self.assertRaisesRegex(PilotError,"Nonwhitespace"):
            _original_source_markers(source)


if __name__=="__main__":
    unittest.main()
