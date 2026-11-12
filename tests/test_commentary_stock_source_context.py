"""Actual CCEL neighboring title/heading provenance vs stock prefix XML — private tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_private_text_compare import _original_source_markers, compare_private_texts
from commentary_stock_prefix_topology import stock_prefix_context_correspondence


class CommentaryStockSourceContextTests(unittest.TestCase):
    def original(self):
        return (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<ThML><div1 title="Source book."><div2 title="Original chapter.">'
            b'<h2>Nearby source heading.</h2>'
            b'<scripCom osisRef="Bible:Gen.1.1" passage="First passage."/>'
            b'<div><p>Original commentary words.</p></div>'
            b'</div2></div1></ThML>'+b' '*1100
        )

    def test_exact_original_adjacent_heading_matches_stock_title_not_approved(self):
        source,_=_original_source_markers(self.original())
        original=source["Gen.1.1"][0]
        self.assertEqual(len(original["private_original_neighbor_candidates"]),4)
        stock=b"<title>Nearby source heading.</title><hi>Original commentary words?</hi>"
        match=stock_prefix_context_correspondence(
            original["original_text"],stock,original["private_original_neighbor_candidates"])
        self.assertEqual(
            match["source_neighbor_to_stock_element_correspondence_classes"],
            {"exact_unicode:title:source_immediate_previous_heading_element":1})
        self.assertTrue(match["any_exact_source_neighbor_text_in_stock_metadata"])
        self.assertFalse(match["actual_source_candidate_is_not_approved_compiled_heading"] is False)
        self.assertNotIn("Nearby source heading",json.dumps(match))

    def test_source_chapter_attribute_not_assumed_owned_but_can_match(self):
        source,_=_original_source_markers(self.original())
        item=source["Gen.1.1"][0]
        stock=(b"<title>Original chapter.</title>"
               b"<title>Unverified extra context.</title>"
               b"<hi>Original commentary words?</hi>")
        result=stock_prefix_context_correspondence(
            item["original_text"],stock,item["private_original_neighbor_candidates"])
        self.assertEqual(
            result["source_neighbor_to_stock_element_correspondence_classes"],
            {"exact_unicode:title:source_div2_title_attribute":1})
        self.assertEqual(result["preceding_stock_metadata_element_count_by_tag"],{"title":2})
        self.assertFalse(result["source_or_stock_text_or_attribute_values_disclosed"])
        self.assertNotIn("Original chapter",json.dumps(result))

    def test_stock_title_with_no_original_neighbor_witness_remains_unattributed(self):
        source,_=_original_source_markers(self.original())
        item=source["Gen.1.1"][0]
        stock=b"<title>Novel publisher material.</title><hi>Original commentary words?</hi>"
        result=stock_prefix_context_correspondence(
            item["original_text"],stock,item["private_original_neighbor_candidates"])
        self.assertEqual(result["source_neighbor_to_stock_element_correspondence_classes"],{})
        self.assertFalse(result["any_exact_source_neighbor_text_in_stock_metadata"])
        self.assertEqual(result["preceding_stock_metadata_element_count_by_tag"],{"title":1})

    def test_exact_source_candidate_is_not_invented_from_previous_commentary_div(self):
        source=(b"<?xml version='1.0' encoding='UTF-8'?>"
                b"<ThML><div1><div2>"
                b"<scripCom osisRef='Bible:Gen.1.1'/>"
                b"<div><p>Prior commentary with heading-like words.</p></div>"
                b"<scripCom osisRef='Bible:Gen.1.2'/>"
                b"<div><p>Original new body.</p></div>"
                b"</div2></div1></ThML>"+b" "*1100)
        items,_=_original_source_markers(source)
        self.assertEqual(items["Gen.1.2"][0]["private_original_neighbor_candidates"],[])

    def test_full_private_cross_source_stock_audit_uses_observed_heading_only(self):
        source,_=_original_source_markers(self.original())
        stock={"Gen.1.1":b"<title>Nearby source heading.</title><hi>Original commentary words?</hi>"}
        result=compare_private_texts(source,stock)
        self.assertEqual(result["source_neighbor_compared_to_stock_prefix_entry_count"],1)
        self.assertEqual(result["source_neighbor_exact_context_match_stock_entry_count"],1)
        self.assertEqual(result["source_neighbor_same_word_tokens_not_exact_context_match_stock_entry_count"],0)
        self.assertEqual(result["stock_prefix_matched_authentic_source_neighbor_context_classes"],
                         {"exact_unicode:title:source_immediate_previous_heading_element":1})
        self.assertFalse(result["full_authored_to_stock_parity_verified"])
        self.assertNotIn("Original commentary words",json.dumps(result))
        self.assertNotIn("Nearby source heading",json.dumps(result))


if __name__=="__main__":
    unittest.main()
