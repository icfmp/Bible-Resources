"""Source-neutral OSIS/native paragraph and poetry opening-order regression."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from research.bible.source_native_ordered_body import (
    OrderedStructureError, compare_ordered_body_openings,
)
from research.bible.native_milestone_pair_audit import NativeMilestonePairAudit

# Events have already been verified by the strict original OSIS inventory.
# The generic comparator must not reconstruct original USFX or source prose.
SOURCE = {"Gen": [("p", "Gen.1.1"), ("q", "Gen.1.2"), ("p", "Gen.1.3")]}
COUNTS = {"source_body_p_openings": 2, "source_body_q_openings": 1}


def native_openings(kinds):
    pairs = NativeMilestonePairAudit()
    for index, kind in enumerate(kinds, start=1):
        if kind == "p":
            xml = (f'<div type="x-p" sID="p{index}"/>'
                   f'<div type="x-p" eID="p{index}"/>').encode()
        else:
            xml = (f'<l sID="q{index}"/><l eID="q{index}"/>').encode()
        pairs.observe("K", f"Gen.1.{index}", xml)
    result = pairs.finish()
    assert result["native_milestone_pairing_findings"] == {}, result
    return pairs.private_ordered_body_openings()


class SourceNativeOpeningOrderTests(unittest.TestCase):
    def test_same_order_and_kind_does_not_claim_editorial_fidelity(self):
        receipt = compare_ordered_body_openings(
            SOURCE, native_openings(["p", "q", "p"]), COUNTS)
        self.assertTrue(receipt["same_order_and_kind_in_every_mapped_book"])
        counts = receipt["source_native_body_opening_kind_counts"]
        self.assertEqual(counts["books_with_exact_body_opening_kind_order"], 1)
        self.assertEqual(counts["native_paragraph_starts"], 2)
        self.assertEqual(counts["native_poetry_line_starts"], 1)
        self.assertFalse(receipt["source_native_exact_word_positions_or_boundary_spans_verified"])
        self.assertFalse(receipt["source_native_whitespace_or_full_editorial_layout_verified"])
        self.assertFalse(receipt["explicit_prechapter_book_title_styles_separately_accounted_for"])
        self.assertNotIn("PRIVATE", str(receipt))

    def test_reordered_kinds_are_detected_even_with_equal_count(self):
        receipt = compare_ordered_body_openings(
            SOURCE, native_openings(["q", "p", "p"]), COUNTS)
        c = receipt["source_native_body_opening_kind_counts"]
        self.assertFalse(receipt["same_order_and_kind_in_every_mapped_book"])
        self.assertEqual(c["books_with_equal_count_but_reordered_kinds"], 1)
        mismatch = receipt["first_mismatch_book_references_no_scripture"][0]
        self.assertEqual(mismatch["first_different_one_based_event_index"], 1)
        self.assertEqual(mismatch["original_previous_reference_id"], "Gen.1.1")
        self.assertEqual(mismatch["compiled_marker_reference_id"], "Gen.1.1")

    def test_missing_and_extra_openings_are_explicit_differences(self):
        for kinds in (["p", "q"], ["p", "q", "p", "q"]):
            with self.subTest(kinds=kinds):
                result = compare_ordered_body_openings(
                    SOURCE, native_openings(kinds), COUNTS)
                self.assertFalse(result["same_order_and_kind_in_every_mapped_book"])
                self.assertEqual(
                    result["source_native_body_opening_kind_counts"][
                        "books_with_body_opening_count_difference"], 1)

    def test_missing_or_unmapped_native_book_never_claims_parity(self):
        no_native = compare_ordered_body_openings(SOURCE, {}, COUNTS)
        self.assertFalse(no_native["same_order_and_kind_in_every_mapped_book"])
        with self.assertRaises(OrderedStructureError):
            compare_ordered_body_openings(
                SOURCE,
                {"Gen": [("p", "Gen.1.1")], "Other": [("p", "Other.1.1")]},
                COUNTS)


if __name__ == "__main__":
    unittest.main()
