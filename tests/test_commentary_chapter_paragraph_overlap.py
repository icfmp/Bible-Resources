"""Synthetic source-neutral test for longest shared chapter-adjacent paragraph word spans."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_chapter_neighbors import original_chapter_neighbors
from commentary_chapter_paragraph_overlap import (
    OriginalChapterParagraphSpanProbe, longest_common_contiguous_word_run,
)
from commentary_private_text_compare import raw_as_strict_xml_text
from pilot_preflight import PilotError


def source():
    return (b"<?xml version='1.0'?><ThML><ThML.body><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1'/>"
            b"<p>Original private words here.</p>"
            b"<scripCom osisRef='Bible:Gen.1.1'/>"
            b"<div><p>Other verse material.</p></div>"
            b"</div2></div1></ThML.body></ThML>")


class OriginalParagraphOverlapTests(unittest.TestCase):
    def prepare(self):
        original,_ = original_chapter_neighbors(source())
        unit = original["Gen.1"][0]
        return OriginalChapterParagraphSpanProbe(original),{
            "previously_not_found_in_same_chapter_numbered_slots":1,
            "bounded_originally_unlocated_line_hash_only_cases":[{
                "original_reference_sha256":unit["source_reference_sha256"],
                "original_neighbor_text_sha256":unit["source_sibling_sha256"],
                "source_line":unit["source_line"],
                "original_neighbor_tag":"p",
                "alternative_stock_location_class":"not_found_in_other_same_book_stock_slots",
            }],
        }

    def test_largest_span_uses_exact_order_not_word_multiset(self):
        self.assertEqual(longest_common_contiguous_word_run(
            ["First","second","third"],["second","first","third"]),1)
        self.assertEqual(longest_common_contiguous_word_run(
            ["one","two","three","four"],["x","one","two","three","y"]),3)
        self.assertEqual(longest_common_contiguous_word_run(["x","y"],["a","b"]),0)
        self.assertEqual(longest_common_contiguous_word_run(["x","x"],["x","x"]),2)

    def test_one_changed_word_does_not_count_as_complete_text(self):
        probe,prior=self.prepare()
        probe.observe("K","Gen.1.1",b"<p>Original private changed here.</p>",
                      raw_as_strict_xml_text)
        receipt=probe.report(prior)
        self.assertEqual(receipt["original_explicit_chapter_marker_adjacent_p_count"],1)
        sample=receipt["unlocated_original_p_line_hash_only_best_contiguous_word_spans"][0]
        self.assertEqual(sample["original_word_token_count"],4)
        self.assertEqual(sample["largest_identical_case_word_span_by_slot_scope"][
            "same_chapter_numbered"],2)
        self.assertFalse(receipt["no_source_to_stock_full_chapter_or_edition_parity_proven"] is False)
        self.assertNotIn("Original private words here",json.dumps(receipt))

    def test_casefold_is_distinct_from_exact_original_word_case(self):
        probe,prior=self.prepare()
        probe.observe("I","Gen.1.0",b"<p>ORIGINAL PRIVATE WORDS HERE.</p>",
                      raw_as_strict_xml_text)
        item=probe.report(prior)["unlocated_original_p_line_hash_only_best_contiguous_word_spans"][0]
        self.assertEqual(item["largest_identical_case_word_span_by_slot_scope"][
            "same_chapter_intro"],0)
        self.assertEqual(item["largest_casefolded_word_span_by_slot_scope"][
            "same_chapter_intro"],4)

    def test_other_book_entries_do_not_supply_false_positive(self):
        probe,prior=self.prepare()
        probe.observe("K","Exod.1.1",b"<p>Original private words here.</p>",
                      raw_as_strict_xml_text)
        item=probe.report(prior)["unlocated_original_p_line_hash_only_best_contiguous_word_spans"][0]
        self.assertEqual(max(item["largest_identical_case_word_span_by_slot_scope"].values()),0)

    def test_unreviewed_source_word_bound_is_explicit_failure(self):
        with self.assertRaises(PilotError):
            longest_common_contiguous_word_run(["token"]*513,["token"]*514)


if __name__ == "__main__":
    unittest.main()
