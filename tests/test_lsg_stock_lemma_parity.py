"""Synthetic, text-free stable SWORD lexical metadata regression tests."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lsg_stock_lemma_parity import (
    compare_compiled_lemma_rows, ordered_lemma_reader_plan)
from pilot_preflight import PilotError


class StableLemmaParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "authoritative.osis.xml"
        self.source.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText>
    <div type="book" osisID="Gen">
      <chapter sID="Gen.1"/>
      <verse sID="Gen.1.1"/>
      <w lemma="strong:H123">a</w>
      <w lemma="lemma:ancient strong:H124">b</w>
      <verse eID="Gen.1.1"/>
      <verse sID="Gen.1.2"/>
      <w>c</w>
      <verse eID="Gen.1.2"/>
      <chapter eID="Gen.1"/>
      <chapter sID="Gen.2"/>
      <verse sID="Gen.2.1"/>
      <w lemma="strong:H125">d</w>
      <verse eID="Gen.2.1"/>
    </div>
    <div type="book" osisID="Exod">
      <chapter sID="Exod.1"/>
      <verse sID="Exod.1.1"/>
      <w lemma="strong:H126">e</w>
      <verse eID="Exod.1.1"/>
    </div>
  </osisText>
</osis>''', encoding="utf-8")
        self.rows = [
            "Gen\tstrong:H123",
            "Gen\tlemma:ancient strong:H124",
            "Gen\t",
            "Gen\tstrong:H125",
            "Exod\tstrong:H126",
        ]
        self.aliases = [
            ("Exod.1.1", "Exodus 1:1"),
            ("Gen.2.1", "Genesis 2:1"),
            ("Gen.1.2", "Genesis 1:2"),
            ("Gen.1.1", "Genesis 1:1"),
        ]

    def test_all_lexical_values_and_empty_slots_match_in_order(self):
        report = compare_compiled_lemma_rows(self.source, self.rows)
        self.assertEqual(report["status"], "compiled_ordered_lemma_attributes_verified")
        self.assertEqual(report["books_with_exact_ordered_lemma_values"], 2)
        self.assertEqual(report["source_word_slots"], 5)
        self.assertEqual(report["compiled_word_slots"], 5)
        self.assertEqual(report["mismatching_books"], [])
        self.assertFalse(report["compiled_note_bodies_verified"])

    def test_value_change_is_blocked_without_exporting_word_or_lemma_text(self):
        altered = list(self.rows)
        altered[1] = "Gen\tlemma:ancient strong:H222"
        report = compare_compiled_lemma_rows(self.source, altered)
        self.assertEqual(report["status"], "blocked_compiled_lemma_attributes_mismatch")
        self.assertFalse(report["mismatching_books"][0]["book_lemma_multisets_equal"])
        self.assertEqual(report["mismatching_books"][0]["first_mismatch_word_position"], 2)
        self.assertNotIn("H222", str(report))
        self.assertNotIn("ancient", str(report))

    def test_reordering_identical_lemma_values_is_detected(self):
        altered = list(self.rows)
        altered[0], altered[1] = altered[1], altered[0]
        report = compare_compiled_lemma_rows(self.source, altered)
        self.assertEqual(report["status"], "blocked_compiled_lemma_attributes_mismatch")
        self.assertTrue(report["mismatching_books"][0]["book_lemma_multisets_equal"])

    def test_missing_word_marker_is_detected(self):
        report = compare_compiled_lemma_rows(self.source, self.rows[:2] + self.rows[3:])
        self.assertEqual(report["status"], "blocked_compiled_lemma_attributes_mismatch")
        self.assertEqual(report["source_word_slots"], 5)
        self.assertEqual(report["compiled_word_slots"], 4)

    def test_unknown_strong_notation_blocks(self):
        altered = list(self.rows)
        altered[0] = "Gen\tstrong:unsupported"
        report = compare_compiled_lemma_rows(self.source, altered)
        self.assertEqual(report["status"], "blocked_compiled_lemma_attributes_mismatch")
        self.assertEqual(report["unparseable_compiled_lemma_slots"], 1)

    def test_unexpected_book_and_bad_row_fail_closed(self):
        for row in ("Lev\tstrong:H123", "Gen", "Gen\tstrong:H123\textra"):
            with self.subTest(row=row), self.assertRaises(PilotError):
                compare_compiled_lemma_rows(self.source, [row])

    def test_reader_keys_include_standard_intro_slots_in_canonical_order(self):
        plan, books = ordered_lemma_reader_plan(self.source, self.aliases)
        self.assertEqual([b.get("osisID") for b in books], ["Gen", "Exod"])
        self.assertEqual(plan, [
            ("Genesis 0:0", "Gen", "1"),
            ("Genesis 1:0", "Gen", "1"),
            ("Genesis 1:1", "Gen", "0"),
            ("Genesis 1:2", "Gen", "0"),
            ("Genesis 2:0", "Gen", "1"),
            ("Genesis 2:1", "Gen", "0"),
            ("Exodus 0:0", "Exod", "1"),
            ("Exodus 1:0", "Exod", "1"),
            ("Exodus 1:1", "Exod", "0"),
        ])

    def test_duplicate_reader_key_and_chapter_gap_are_rejected(self):
        for altered in (
            self.aliases + [("Gen.1.1", "Genesis 1:1")],
            [x for x in self.aliases if x[0] != "Gen.2.1"]
            + [("Gen.3.1", "Genesis 3:1")],
        ):
            with self.subTest(altered=altered), self.assertRaises(PilotError):
                ordered_lemma_reader_plan(self.source, altered)


if __name__ == "__main__":
    unittest.main()
