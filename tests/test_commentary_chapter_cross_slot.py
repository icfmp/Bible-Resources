"""Pure synthetic tests of alternate same-book SWORD slot location, no edition approval."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_chapter_cross_slot import ChapterNeighborSameBookAlternativeProbe
from commentary_chapter_neighbors import original_chapter_neighbors, ChapterNeighborNumberedProbe
from commentary_private_text_compare import raw_as_strict_xml_text


def original():
    return (b"<?xml version='1.0'?><ThML><ThML.body><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1'/>"
            b"<h2>First chapter title.</h2>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.2'/>"
            b"<div><p>Separate verse commentary.</p></div>"
            b"</div2></div1></ThML.body></ThML>")


class ChapterOtherSlotWitnessTests(unittest.TestCase):
    def start(self):
        source, _ = original_chapter_neighbors(original())
        return ChapterNeighborNumberedProbe(source), ChapterNeighborSameBookAlternativeProbe(source)

    def test_same_chapter_numbered_exact_takes_precedence(self):
        same, extra = self.start()
        raw = b"<p>First chapter title.</p>"
        same.observe("K", "Gen.1.1", raw, raw_as_strict_xml_text)
        extra.observe("K", "Gen.1.1", raw, raw_as_strict_xml_text)
        extra.observe("K", "Gen.2.1", raw, raw_as_strict_xml_text)
        found = extra.report(same)
        self.assertEqual(found["previously_not_found_in_same_chapter_numbered_slots"], 0)
        self.assertEqual(
            found["source_sibling_locations_in_alternative_same_book_slots"],
            {"previously_found_exact_in_same_chapter_numbered_slot": 1})

    def test_other_chapter_numbered_text_can_be_located_without_key_reassignment(self):
        same, extra = self.start()
        same.observe("K", "Gen.1.1", b"<p>Different wording.</p>", raw_as_strict_xml_text)
        extra.observe("K", "Gen.2.1",
                      b"<p>After the first chapter, First chapter title.</p>",
                      raw_as_strict_xml_text)
        result = extra.report(same)
        self.assertEqual(result["previously_not_found_in_same_chapter_numbered_slots"], 1)
        self.assertEqual(
            result["source_sibling_locations_in_alternative_same_book_slots"],
            {"other_chapter_numbered_exact_unicode_containment": 1})
        sample = result["bounded_originally_unlocated_line_hash_only_cases"][0]
        self.assertEqual(sample["original_neighbor_tag"], "h2")
        self.assertEqual(len(sample["original_reference_sha256"]), 64)
        self.assertEqual(len(sample["matching_native_key_sha256"]), 64)
        self.assertNotIn("First chapter title", json.dumps(result))
        self.assertFalse(result["authorial_edition_and_exact_text_structure_parity_proven"])

    def test_same_chapter_intro_word_match_is_not_unicode_equality(self):
        same, extra = self.start()
        same.observe("K", "Gen.1.1", b"<p>Different words.</p>", raw_as_strict_xml_text)
        extra.observe("I", "Gen.1.0", b"<p>First chapter title!</p>", raw_as_strict_xml_text)
        result = extra.report(same)
        self.assertEqual(
            result["source_sibling_locations_in_alternative_same_book_slots"],
            {"same_chapter_intro_contiguous_unicode_word_tokens_only": 1})

    def test_other_book_text_cannot_create_spurious_same_book_witness(self):
        same, extra = self.start()
        same.observe("K", "Gen.1.1", b"<p>Unrelated material.</p>", raw_as_strict_xml_text)
        extra.observe("K", "Exod.2.1", b"<p>First chapter title.</p>",
                      raw_as_strict_xml_text)
        result = extra.report(same)
        self.assertEqual(result["source_sibling_locations_in_alternative_same_book_slots"],
                         {"not_found_in_other_same_book_stock_slots": 1})

    def test_malformed_stock_entry_does_not_appear_as_faithful(self):
        same, extra = self.start()
        same.observe("K", "Gen.1.1", b"<p>Different material.</p>", raw_as_strict_xml_text)
        extra.observe("K", "Gen.2.1", b"<p>unclosed</bad>", raw_as_strict_xml_text)
        result = extra.report(same)
        self.assertEqual(result["stock_xml_strict_parse_failures_by_kind"], {"K": 1})
        self.assertEqual(result["source_sibling_locations_in_alternative_same_book_slots"],
                         {"not_found_in_other_same_book_stock_slots": 1})


if __name__ == "__main__":
    unittest.main()
