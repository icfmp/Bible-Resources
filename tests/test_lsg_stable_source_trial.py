"""Stock SWORD Segond candidate: synthetic index and text-preservation gates."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lsg_stable_source_trial import assess_stock_readback

def example():
    return {
        "expected_chapters": 2,
        "total_source_verse_keys": 6,
        "totals": {"chapters": 2, "source_verses": 6,
                   "source_keys_missing": 1, "sword_keys_unexpected": 1},
        "chapters_where_every_residual_difference_is_added_asterisk_only": 2,
        "first_unexplained_chapter_character_streams": [],
        "unmatched_verse_slot_classification": [
            {"book": "Example", "chapter": 1,
             "source_only_verses": [4], "reader_only_verses": [],
             "diagnostic_slot_classes": [{
                 "verse": 4, "side": "source_only",
                 "classification": "readback_preceding_slot_contains_both_verse_character_streams",
                 "preceding_slot_compared": True, "no_reversification_applied": True}]},
            {"book": "Other", "chapter": 2,
             "source_only_verses": [], "reader_only_verses": [3],
             "diagnostic_slot_classes": [{
                 "verse": 3, "side": "reader_only",
                 "classification": "empty_readback_verse_slot",
                 "no_reversification_applied": True}]},
        ],
    }

class StockSwordCandidateTests(unittest.TestCase):
    def test_official_append_is_documented_not_approved(self):
        r = assess_stock_readback(example())
        self.assertEqual(r["status"], "stock_segond_limitations_classified_not_approved")
        self.assertTrue(r["all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks"])
        self.assertTrue(r["all_reference_differences_explained"])
        self.assertTrue(r["source_verse_accessibility_lost"])
        self.assertFalse(r["exact_source_index_preserved"])
        self.assertFalse(r["approved_for_publication"])
        self.assertEqual(r["appended_source_keys"], [{
            "book": "Example", "chapter": 1, "source_verse": 4,
            "compiled_verse": 3, "distinct_original_reference_unavailable": True
        }])
    def test_missing_source_characters_are_blocked(self):
        r = example()
        r["chapters_where_every_residual_difference_is_added_asterisk_only"] = 1
        self.assertEqual(assess_stock_readback(r)["status"],
                         "blocked_unexplained_scripture_or_reference_change")
    def test_an_extra_reader_character_is_blocked(self):
        r = example()
        r["first_unexplained_chapter_character_streams"] = [{"book": "Other", "chapter": 2}]
        self.assertEqual(assess_stock_readback(r)["status"],
                         "blocked_unexplained_scripture_or_reference_change")
    def test_unexplained_source_verse_loss_is_blocked(self):
        r = example()
        r["unmatched_verse_slot_classification"][0]["diagnostic_slot_classes"][0][
            "classification"] = "unresolved_missing_verse_index"
        self.assertEqual(assess_stock_readback(r)["status"],
                         "blocked_unexplained_scripture_or_reference_change")
    def test_populated_extra_reader_verse_is_blocked(self):
        r = example()
        r["unmatched_verse_slot_classification"][1]["diagnostic_slot_classes"][0][
            "classification"] = "unexpected_populated_reader_slot"
        self.assertEqual(assess_stock_readback(r)["status"],
                         "blocked_unexplained_scripture_or_reference_change")
    def test_wrong_or_incomplete_classification_is_blocked(self):
        for variant in ("wrong-count", "no-prev", "wrong-side", "unreported-slot"):
            with self.subTest(variant=variant):
                r = example()
                if variant == "wrong-count":
                    r["totals"]["source_keys_missing"] = 2
                elif variant == "no-prev":
                    r["unmatched_verse_slot_classification"][0][
                        "diagnostic_slot_classes"][0]["preceding_slot_compared"] = False
                elif variant == "wrong-side":
                    r["unmatched_verse_slot_classification"][0][
                        "diagnostic_slot_classes"][0]["side"] = "reader_only"
                else:
                    r["unmatched_verse_slot_classification"][0][
                        "diagnostic_slot_classes"].append({
                            "verse": 2, "side": "reader_only",
                            "classification": "empty_readback_verse_slot",
                            "no_reversification_applied": True})
                self.assertEqual(assess_stock_readback(r)["status"],
                                 "blocked_unexplained_scripture_or_reference_change")
    def test_exact_index_requires_no_difference(self):
        r = example()
        r["totals"]["source_keys_missing"] = 0
        r["totals"]["sword_keys_unexpected"] = 0
        r["unmatched_verse_slot_classification"] = []
        result = assess_stock_readback(r)
        self.assertEqual(result["status"], "stock_segond_limitations_classified_not_approved")
        self.assertTrue(result["exact_source_index_preserved"])
        self.assertFalse(result["source_verse_accessibility_lost"])
        self.assertFalse(result["approved_for_publication"])

if __name__ == "__main__":
    unittest.main()
