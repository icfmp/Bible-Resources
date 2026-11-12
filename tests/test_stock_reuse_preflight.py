"""Synthetic note-caller and other stock-SWORD material loss fixtures."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stock_reuse_preflight import preflight_stock_reuse


def check(*, attrs=None, note_classes=None, source=2, native=2,
          prose=True, scanned=True, anchors=True, scope=None):
    return preflight_stock_reuse(
        native_scan_complete=scanned, main_text_preserved=prose,
        notes={
            "status":"numbered_source_to_native_note_body_diagnostic_not_editorial_approval",
            "source_numbered_note_count":source,
            "native_parseable_numbered_note_count":native,
            "classifications":note_classes or {},
            "note_annotation_structure_diagnostic":{
                "classifications":attrs if attrs is not None else
                  {"native_note_n_present":source,"literal_caller_string_equal":source},
            }},
        note_positions={"all_numbered_note_nonspace_anchor_positions_match":anchors},
        original_note_scope=scope or {},
    )


class StockReuseTests(unittest.TestCase):
    def test_clean_machine_screen_still_requires_review(self):
        receipt=check()
        self.assertEqual(receipt["status"],"REVIEW_REQUIRED")
        self.assertFalse(receipt["stock_reuse_approved"])
        self.assertFalse(receipt["proven_material_stock_loss"])

    def test_literal_source_callers_lost_blocks_unmodified_stock(self):
        receipt=check(attrs={"native_note_n_absent":2,
                             "literal_source_caller_no_native_n":2})
        self.assertEqual(receipt["status"],"BLOCKED")
        self.assertEqual(receipt["material_loss_categories"][
            "literal_source_caller_no_native_n"],2)

    def test_missing_source_note_verse_is_material_loss(self):
        receipt=check(note_classes={
            "source_note_bearing_verses_without_native_slot": 1,
        })
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["material_loss_categories"][
            "source_note_bearing_verses_without_native_slot"], 1)

    def test_changed_caller_and_machine_targets_block_stock(self):
        receipt=check(attrs={"native_note_n_present":2,
                             "literal_caller_string_differs":1,
                             "authored_explicit_target_absent_in_native":1})
        self.assertEqual(receipt["status"],"BLOCKED")
        self.assertEqual(len(receipt["material_loss_categories"]),2)

    def test_verse_or_numbered_note_loss_blocks_stock(self):
        receipt=check(note_classes={"note_count_differs":1},native=1,prose=False)
        self.assertEqual(receipt["status"],"BLOCKED")
        self.assertIn("numbered_main_text_not_preserved",receipt["material_loss_categories"])
        self.assertIn("source_native_note_total_difference",receipt["material_loss_categories"])

    def test_formatting_and_automatic_callers_only_need_review(self):
        receipt=check(attrs={"native_note_n_absent":2,
                             "source_caller_automatic_absent_or_unverifiable":2},
                      note_classes={"ordered_note_bodies_equal_after_whitespace_folding":1},
                      anchors=False,scope={"notes_outside_numbered_verses":1})
        self.assertEqual(receipt["status"],"REVIEW_REQUIRED")
        self.assertIn("note_body_whitespace_requires_editorial_review",
                      receipt["other_unverified_categories"])

    def test_missing_evidence_cannot_look_approved(self):
        receipt=check(attrs={},scanned=False)
        self.assertEqual(receipt["status"],"REVIEW_REQUIRED")
        self.assertIn("note_annotation_attribute_coverage_unverified",
                      receipt["other_unverified_categories"])
        self.assertFalse(receipt["stock_reuse_approved"])

    def test_reject_invalid_and_private_metadata(self):
        with self.assertRaises(ValueError):
            check(attrs={"literal_source_caller_no_native_n":"PRIVATE"})
        with self.assertRaises(ValueError):
            check(source=-1)
        with self.assertRaises(ValueError):
            check(attrs={"native_note_n_present":500_000})


if __name__=="__main__":
    unittest.main()
