"""Synthetic stock-SWORD raw markup comparison fixtures (no Bible data)."""
from collections import Counter
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_raw_markup import (compare_raw_rows, summarize_intro_rows,
                                 reconcile_full_stock_markup)
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

    def test_chapter_zero_poetry_marker_probe_is_separate_and_text_free(self):
        queries=[("Mark 1:0","Mark"),("Mark 0:0","Mark")]
        rows=["\t".join(("Mark 1:0","0","0","0","2","0","0")),
              "\t".join(("Mark 0:0","0","0","0","1","0","0"))]
        report=summarize_intro_rows(rows,queries)
        self.assertEqual(report["total_marker_counts"]["poetry_start"],3)
        self.assertEqual(report["total_marker_counts"]["poetry_end"],0)
        self.assertEqual(report["inspected_verse_zero_entries"],2)
        self.assertFalse(report["intro_rendering_verified"])

    def test_invalid_intro_reference_row_fails_closed(self):
        with self.assertRaises(PilotError):
            summarize_intro_rows(
                ["\t".join(("Mark 1:1","0","0","0","1","0","0"))],
                [("Mark 1:0","Mark")])

    def test_full_scope_reconciles_poetry_opener_in_real_intro_slot(self):
        # An opener outside a standard verse must not be declared lost.
        self.rows[0]=chr(9).join(("Mark 1:1","3","2","0","0","1","0"))
        main=self.run_audit()
        intro=summarize_intro_rows(
            [chr(9).join(("Mark 1:0","0","0","0","1","0","0"))],
            [("Mark 1:0","Mark")])
        source={"Mark":Counter({"w":5,"note":2,"l":2,"reference":3})}
        review=reconcile_full_stock_markup(main,intro,source)
        self.assertEqual(review["status"],
                         "full_stock_sword_word_note_poetry_reference_counts_match")
        self.assertEqual(review["source_marker_totals"],
                         review["compiled_with_intros_marker_totals"])
        self.assertFalse(review["source_content_verified"])

    def test_full_scope_blocks_missing_poetry_or_changed_reference_target_count(self):
        main=self.run_audit()
        empty_intro=summarize_intro_rows(
            [chr(9).join(("Mark 1:0","0","0","0","0","0","0"))],
            [("Mark 1:0","Mark")])
        source={"Mark":Counter({"w":5,"note":2,"l":2,"reference":3})}
        self.rows[0]=chr(9).join(("Mark 1:1","3","2","0","0","1","0"))
        missing=reconcile_full_stock_markup(self.run_audit(),empty_intro,source)
        self.assertEqual(missing["status"],"blocked_full_scope_marker_mismatch")
        self.assertEqual(missing["mismatching_books"][0]["book"],"Mark")
        changed={"Mark":Counter({"w":5,"note":2,"l":2,"reference":2})}
        mismatch=reconcile_full_stock_markup(main,empty_intro,changed)
        self.assertEqual(mismatch["status"],"blocked_full_scope_marker_mismatch")

    def test_full_scope_rejects_incomplete_intro_inventory(self):
        with self.assertRaises(PilotError):
            reconcile_full_stock_markup(self.run_audit(),
                {"status":"verse_zero_markup_counted_not_release_approved",
                 "book_marker_counts":{}},
                {"Mark":Counter({"w":5,"note":2,"l":2,"reference":3})})
        blocked=reconcile_full_stock_markup(self.run_audit(),
            {"status":"intro_probe_failed"},
            {"Mark":Counter({"w":5,"note":2,"l":2,"reference":3})})
        self.assertEqual(blocked["status"],"blocked_incomplete_verse_zero_inspection")

    def test_misaligned_or_missing_raw_entries_are_fatal(self):
        for rows in ([],self.rows[:1],
                     ["Mark 1:2\t3\t2\t0\t1\t1\t0",self.rows[1]],
                     ["Mark 1:1\tbroken\t2\t0\t1\t1\t0",self.rows[1]]):
            with self.subTest(rows=rows), self.assertRaises(PilotError):
                compare_raw_rows(rows,self.keys,self.expected,self.poetry)

if __name__=="__main__":
    unittest.main()
