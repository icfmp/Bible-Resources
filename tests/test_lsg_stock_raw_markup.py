"""Synthetic stock-SWORD raw markup comparison fixtures (no Bible data)."""
from collections import Counter
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_raw_markup import compare_raw_rows
from pilot_preflight import PilotError

class RawStockReaderTests(unittest.TestCase):
    def setUp(self):
        self.keys=[("Mark.1.1","Mark 1:1"),("Mark.1.2","Mark 1:2")]
        self.expected={
            "Mark.1.1":Counter({"w":3,"note":2,"l":1,"verses":2}),
            "Mark.1.2":Counter({"w":2,"note":0,"l":1,"verses":1}),
        }
        self.poetry={"Mark":2}
        self.rows=[
            "Mark 1:1\t3\t2\t0\t1\t0",
            "Mark 1:2\t2\t0\t3\t1\t0",
        ]
    def run_audit(self):
        return compare_raw_rows(self.rows,self.keys,self.expected,self.poetry)
    def test_verified_merge_raw_markup_has_no_extra_words_or_notes(self):
        result=self.run_audit()
        self.assertEqual(result["status"],"raw_stock_sword_word_note_poetry_counts_verified")
        self.assertEqual(result["checked_reader_entries"],2)
        self.assertEqual(result["expected_source_word_tags"],5)
        self.assertEqual(result["compiled_note_tags"],2)
        self.assertEqual(result["compiled_cross_reference_tag_count"],3)
        self.assertTrue(result["source_to_compiled_word_tag_counts_verified"])
        self.assertTrue(result["source_to_compiled_note_tag_counts_verified"])
        self.assertTrue(result["source_to_compiled_poetry_line_counts_verified"])
        self.assertFalse(result["compiled_note_text_targets_verified"])
    def test_missing_word_or_note_blocks_raw_markup(self):
        for row in ("Mark 1:1\t2\t2\t0\t1\t0",
                    "Mark 1:1\t3\t1\t0\t1\t0"):
            with self.subTest(row=row):
                self.rows[0]=row
                self.assertEqual(self.run_audit()["status"],"blocked_compiled_raw_markup_mismatch")
    def test_changed_poetry_count_blocks_raw_markup(self):
        self.rows[0]="Mark 1:1\t3\t2\t0\t0\t0"
        result=self.run_audit()
        self.assertFalse(result["source_to_compiled_poetry_line_counts_verified"])
        self.assertEqual(result["status"],"blocked_compiled_raw_markup_mismatch")
    def test_misaligned_or_missing_raw_entries_are_fatal(self):
        for rows in ([],self.rows[:1],
                     ["Mark 1:2\t3\t2\t0\t1\t0",self.rows[1]],
                     ["Mark 1:1\tbroken\t2\t0\t1\t0",self.rows[1]]):
            with self.subTest(rows=rows), self.assertRaises(PilotError):
                compare_raw_rows(rows,self.keys,self.expected,self.poetry)

if __name__=="__main__":
    unittest.main()
