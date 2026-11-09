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
        self.poetry={"Mark":Counter({"w":5,"note":2,"l":2})}
        self.rows=[
            "Mark 1:1\t3\t2\t0\t1\t1\t0",
            "Mark 1:2\t2\t0\t3\t1\t1\t0",
        ]
    def run_audit(self):
        return compare_raw_rows(self.rows,self.keys,self.expected,self.poetry)
    def test_verified_merge_raw_markup_has_no_extra_words_or_notes(self):
        result=self.run_audit()
        self.assertEqual(result["status"],"raw_stock_sword_global_markers_verified_with_interverse_diagnostics")
        self.assertEqual(result["checked_reader_entries"],2)
        self.assertEqual(result["source_global_word_tags"],5)
        self.assertEqual(result["compiled_raw_note_tags"],2)
        self.assertEqual(result["compiled_cross_reference_tag_count"],3)
        self.assertTrue(result["source_global_raw_markup_counts_match_compiled"])
        self.assertTrue(result["source_global_raw_markup_counts_match_compiled"])
        self.assertTrue(result["source_global_raw_markup_counts_match_compiled"])
        self.assertFalse(result["compiled_note_text_targets_verified"])
    def test_missing_word_or_note_blocks_raw_markup(self):
        for row in ("Mark 1:1\t2\t2\t0\t1\t1\t0",
                    "Mark 1:1\t3\t1\t0\t1\t1\t0"):
            with self.subTest(row=row):
                self.rows[0]=row
                self.assertEqual(self.run_audit()["status"],"blocked_compiled_raw_markup_mismatch")
    def test_changed_poetry_count_blocks_raw_markup(self):
        self.rows[0]="Mark 1:1\t3\t2\t0\t0\t1\t0"
        result=self.run_audit()
        self.assertFalse(result["source_global_raw_markup_counts_match_compiled"])
        self.assertEqual(result["status"],"blocked_compiled_raw_markup_mismatch")
    def test_poetry_start_end_asymmetry_is_reported_without_forgiving_loss(self):
        self.rows[0]="Mark 1:1\t3\t2\t0\t0\t1\t0"
        report=self.run_audit()
        self.assertEqual(report["status"],"blocked_compiled_raw_markup_mismatch")
        self.assertEqual(report["poetry_asymmetric_reader_entry_count"],1)
        self.assertEqual(report["poetry_reader_entries_with_fewer_start_markers_than_source_inside"],1)
        self.assertFalse(report["poetry_start_end_milestones_balanced"])
        self.assertTrue(report["poetry_end_milestones_match_source_line_count"])
        self.assertEqual(report["first_poetry_marker_location_diagnostics"][0]["osis_ref"],"Mark.1.1")
        self.assertEqual(report["book_level_diagnostics"][0]["compiled_poetry_end_minus_start"],1)

    def test_balanced_source_poetry_has_no_location_diagnostics(self):
        report=self.run_audit()
        self.assertTrue(report["poetry_start_end_milestones_balanced"])
        self.assertTrue(report["poetry_end_milestones_match_source_line_count"])
        self.assertEqual(report["first_poetry_marker_location_diagnostics"],[])

    def test_misaligned_or_missing_raw_entries_are_fatal(self):
        for rows in ([],self.rows[:1],
                     ["Mark 1:2\t3\t2\t0\t1\t1\t0",self.rows[1]],
                     ["Mark 1:1\tbroken\t2\t0\t1\t1\t0",self.rows[1]]):
            with self.subTest(rows=rows), self.assertRaises(PilotError):
                compare_raw_rows(rows,self.keys,self.expected,self.poetry)

if __name__=="__main__":
    unittest.main()
