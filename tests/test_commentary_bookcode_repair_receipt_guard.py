"""Regression: the generic private source-repair receipt does not assume MHCC's five cases."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_bookcode_repair_receipt_guard import validate_private_bookcode_repair_receipt
from pilot_preflight import PilotError


def h(value):
    return sha256(value.encode("utf-8")).hexdigest()


KIND = "all_source_prose_words_found_in_order_at_correct_book_stock_key"


def fixture(count):
    original, stock = h("original source"), h("exact stock")
    receipt = {
        "schema_version": 1,
        "status": "private_exact_scripCom_book_token_repair_proposal_not_approved",
        "original_source_sha256": original,
        "private_corrected_source_sha256": h("candidate") if count else original,
        "reviewed_private_original_bookcode_replacements": count,
        "all_original_scripCom_elements_preserved": count + 10,
        "corrected_book_source_marker_count_compared": count,
        "actual_original_stock_full_native_corpus_sha256": stock,
        "original_scripCom_replacement_operations_without_authorial_text": [
            {
                "source_line": i+1,
                "original_source_osisRef_sha256": h("old"+str(i)),
                "proposed_private_osisRef_sha256": h("new"+str(i)),
                "only_inferred_book_code_changed_in_scripCom": True,
            } for i in range(count)
        ],
        "original_repaired_book_line_SHA_only_stock_comparison_cases": [
            {
                "original_source_line": i+1,
                "original_authorial_body_sha256": h("body"+str(i)),
                "original_wrong_book_start_sha256": h("oldkey"+str(i)),
                "proposed_book_start_sha256": h("newkey"+str(i)),
                "source_plain_words_not_aligned_at_proposed_book_key": 0,
                "private_original_repaired_book_text_witness_class": KIND,
                "not_authorized_to_reassign_crosswire_original_reference": True,
            } for i in range(count)
        ],
        "original_repaired_book_source_text_match_classes": {KIND: count} if count else {},
        "only_unique_original_exact_english_div1_title_conflicts_proposed": True,
        "original_source_byte_for_byte_restorable": True,
        "every_original_other_XML_text_title_note_reference_and_structure_unmodified": True,
        "original_crosswire_sword_data_or_versification_changed": False,
        "source_book_repair_is_not_crosswire_text_or_verse_repair": True,
        "original_XML_or_stock_SWORD_mutated": False,
        "independent_authorial_edition_identity_established": False,
        "source_owner_or_editor_approved": False,
        "public_release_authorized": False,
    }
    return {
        "source_original_sha256": original,
        "stock_full_raw_content_sha256": stock,
        "original_source_book_marker_private_repair_proposal_stock_review": receipt,
    }


class GenericOriginalBookcodeReceiptTests(unittest.TestCase):
    def test_zero_repair_is_valid_and_cannot_invent_an_error(self):
        report = fixture(0)
        result = validate_private_bookcode_repair_receipt(report)
        self.assertTrue(result["zero_change_original_source_candidate_allowed"])
        self.assertEqual(result["original_book_marker_repairs_proposed_privately"], 0)
        self.assertFalse(result["editorial_and_publication_approved"])

    def test_multiple_source_bound_counts_have_no_mhcc_special_case(self):
        for count in (1, 2, 5, 9):
            with self.subTest(count=count):
                result = validate_private_bookcode_repair_receipt(fixture(count))
                self.assertEqual(result["repaired_markers_compared_to_pinned_original_stock"], count)

    def test_no_ops_with_changed_xml_fails_closed(self):
        report = fixture(0)
        report["original_source_book_marker_private_repair_proposal_stock_review"][
            "private_corrected_source_sha256"] = h("unsolicited change")
        with self.assertRaisesRegex(PilotError, "candidate hash"):
            validate_private_bookcode_repair_receipt(report)

    def test_disconnected_stock_comparison_fails_closed(self):
        report = fixture(2)
        report["original_source_book_marker_private_repair_proposal_stock_review"][
            "original_repaired_book_line_SHA_only_stock_comparison_cases"][0][
            "original_source_line"] = 100
        with self.assertRaisesRegex(PilotError, "do not match"):
            validate_private_bookcode_repair_receipt(report)

    def test_inconsistent_count_fails_closed(self):
        report = fixture(2)
        report["original_source_book_marker_private_repair_proposal_stock_review"][
            "corrected_book_source_marker_count_compared"] = 1
        with self.assertRaisesRegex(PilotError, "counts disagree"):
            validate_private_bookcode_repair_receipt(report)

    def test_unapproved_and_immutable_guards_are_mandatory(self):
        for key, value in (
            ("public_release_authorized", True),
            ("original_XML_or_stock_SWORD_mutated", True),
            ("independent_authorial_edition_identity_established", True),
        ):
            with self.subTest(key=key):
                report = fixture(1)
                report["original_source_book_marker_private_repair_proposal_stock_review"][key] = value
                with self.assertRaisesRegex(PilotError, "unchanged-source/release guard"):
                    validate_private_bookcode_repair_receipt(report)

    def test_true_is_not_integer_one_and_stock_pin_is_immutable(self):
        report = fixture(1)
        report["original_source_book_marker_private_repair_proposal_stock_review"][
            "reviewed_private_original_bookcode_replacements"] = True
        with self.assertRaisesRegex(PilotError, "counts disagree"):
            validate_private_bookcode_repair_receipt(report)
        report = fixture(2)
        report["stock_full_raw_content_sha256"] = h("different stock")
        with self.assertRaisesRegex(PilotError, "not authenticated"):
            validate_private_bookcode_repair_receipt(report)


if __name__ == "__main__":
    unittest.main()
