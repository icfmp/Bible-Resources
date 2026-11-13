"""Read-only, source-joined Unicode testimony for commentary lexical differences."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_near_prose_unicode_review import classify_same_book_unicode_variants
from pilot_preflight import PilotError
from commentary_private_text_compare import raw_as_strict_xml_text

REVIEW = "meaningful_separate_editions_lexical_review_still_required"


def digest(value):
    return sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def fixture(original: str, stock: str, *, line=12, unmatched=1):
    original_sha = digest(original)
    stock_xml = ("<p>" + stock + "</p>").encode("utf-8")
    unit = {
        "original_source_line": line,
        "original_full_reference_sha256": digest("source reference " + str(line)),
        "original_text_sha256": original_sha,
        "original_text": original,
        "private_original_scripRef_word_indices": [],
    }
    report = {
        "source_identity_gated_original_line_hash_cases": [{
            "original_source_line": line,
            "original_full_reference_sha256": unit["original_full_reference_sha256"],
            "original_body_sha256": original_sha,
            "stock_raw_sha256": digest(stock_xml),
            "source_div1_vs_stock_book_comparison_gate": REVIEW,
            "source_nonlink_word_tokens_not_found_in_stock_order": unmatched,
        }]
    }
    return {"Gen.1.1": [unit]}, {"Gen.1.1": stock_xml}, report


class NearCommentaryUnicodeProseTests(unittest.TestCase):
    def check(self, original, stock, expected, *, unmatched=1):
        source, stocked, identity = fixture(
            original, stock, unmatched=unmatched
        )
        result = classify_same_book_unicode_variants(
            source, stocked, identity,
            stock_text_parser=raw_as_strict_xml_text,
        )
        self.assertEqual(
            result["authentic_same_book_original_digital_edition_cases_evaluated"], 1
        )
        self.assertEqual(result["source_nonlink_unicode_witness_classes"], {
            expected: 1
        })
        self.assertNotIn(original, str(result))
        self.assertNotIn(stock, str(result))
        self.assertFalse(result["editorial_approved"])
        self.assertFalse(result["published"])
        return result

    def test_changed_case_can_be_explained_by_unicode_casefold_only(self):
        r = self.check(
            "In the beginning", "in the beginning",
            "original_plain_word_order_compatible_after_unicode_casefold",
        )
        line = r["bounded_source_line_hash_only_unicode_review_cases"][0]
        self.assertEqual(line["after_unicode_casefold_unmatched_original_nonlink_words"], 0)
        self.assertTrue(line["casefold_compatible_order_does_not_certify_exact_wording_or_markup"])

    def test_genuinely_different_words_remain_unresolved(self):
        r = self.check(
            "Faith comes through hearing", "Hope comes through hearing",
            "original_plain_word_order_still_differs_after_casefold_and_nfkc",
        )
        line = r["bounded_source_line_hash_only_unicode_review_cases"][0]
        self.assertEqual(line["after_nfkc_casefold_unmatched_original_nonlink_words"], 1)

    def test_unicode_nfkc_can_explain_roman_numeral_form_not_printing_fidelity(self):
        self.check(
            "Ⅰ begins the chapter", "I begins the chapter",
            "original_plain_word_order_compatible_after_nfkc_casefold",
        )

    def test_large_source_word_difference_is_not_downgraded_to_case_only(self):
        source, stocked, identity = fixture(
            "Many original prose words omitted",
            "A separate abbreviated edition",
            unmatched=4,
        )
        r = classify_same_book_unicode_variants(
            source, stocked, identity,
            stock_text_parser=raw_as_strict_xml_text,
        )
        self.assertEqual(r["source_nonlink_unicode_witness_classes"], {
            "more_than_two_original_nonlink_word_order_gaps_review_manually": 1
        })
        self.assertIsNone(
            r["bounded_source_line_hash_only_unicode_review_cases"][0]
             ["after_unicode_casefold_unmatched_original_nonlink_words"]
        )

    def test_wrong_original_source_identity_or_stock_hash_fails_closed(self):
        source, stocked, identity = fixture("In the beginning", "in the beginning")
        identity["source_identity_gated_original_line_hash_cases"][0][
            "original_body_sha256"
        ] = digest("another original source")
        with self.assertRaisesRegex(PilotError, "authentic near-match"):
            classify_same_book_unicode_variants(
                source, stocked, identity,
                stock_text_parser=raw_as_strict_xml_text,
            )
        source, stocked, identity = fixture("In the beginning", "in the beginning")
        stocked["Gen.1.1"] = b"<p>corrupted stock contents</p>"
        with self.assertRaisesRegex(PilotError, "authenticated"):
            classify_same_book_unicode_variants(
                source, stocked, identity,
                stock_text_parser=raw_as_strict_xml_text,
            )

    def test_incorrect_assumed_nonlink_alignment_is_not_approved(self):
        source, stocked, identity = fixture("In the beginning", "in the beginning", unmatched=2)
        with self.assertRaisesRegex(PilotError, "no longer reproducible"):
            classify_same_book_unicode_variants(
                source, stocked, identity,
                stock_text_parser=raw_as_strict_xml_text,
            )

    def test_quarantined_cross_book_source_record_is_never_tried(self):
        source, stocked, identity = fixture("In the beginning", "in the beginning")
        identity["source_identity_gated_original_line_hash_cases"][0][
            "source_div1_vs_stock_book_comparison_gate"
        ] = "quarantine_original_book_title_vs_osis_marker_conflict"
        result = classify_same_book_unicode_variants(
            source, stocked, identity,
            stock_text_parser=raw_as_strict_xml_text,
        )
        self.assertEqual(result["authentic_same_book_original_digital_edition_cases_evaluated"], 0)
        self.assertEqual(result["source_nonlink_unicode_witness_classes"], {})


if __name__ == "__main__":
    unittest.main()
