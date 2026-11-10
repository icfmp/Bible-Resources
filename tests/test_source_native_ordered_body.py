"""Order-only source-to-stock paragraph/poetry event proof, without Scripture."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_ordered_body import (
    OrderedStructureError, original_body_opening_sequences,
    compare_ordered_body_openings,
)
from native_milestone_pair_audit import NativeMilestonePairAudit

MAPPING = [("GEN", "Gen")]
SOURCE = (
    b'<usfx><book id="GEN">'
    b'<p sfm="mt">PRIVATE AUTHORIAL TITLE</p>'
    b'<c id="1"/>'
    b'<p><v id="1"/>PRIVATE SCRIPTURE ONE</p>'
    b'<q><v id="2"/>PRIVATE SCRIPTURE TWO</q>'
    b'<p><v id="3"/>PRIVATE SCRIPTURE THREE</p>'
    b'</book></usfx>'
)


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
    def test_original_title_excluded_only_from_body_not_from_original_census(self):
        source, stats = original_body_opening_sequences(SOURCE, MAPPING)
        self.assertEqual([kind for kind,_ref in source["Gen"]],["p","q","p"])
        self.assertEqual(stats["authored_pre_chapter_book_titles_separately_verified"],1)
        self.assertEqual(stats["source_body_p_openings"],2)
        self.assertEqual(stats["source_body_q_openings"],1)
        receipt=compare_ordered_body_openings(
            source, native_openings(["p","q","p"]), stats)
        self.assertTrue(receipt["same_order_and_kind_in_every_mapped_book"])
        counts=receipt["source_native_body_opening_kind_counts"]
        self.assertEqual(counts["books_with_exact_body_opening_kind_order"],1)
        self.assertEqual(counts["books_with_body_opening_kind_difference"],0)
        self.assertEqual(counts["native_paragraph_starts"],2)
        self.assertEqual(counts["native_poetry_line_starts"],1)
        self.assertFalse(receipt["source_native_exact_word_positions_or_boundary_spans_verified"])
        self.assertFalse(receipt["source_native_whitespace_or_full_editorial_layout_verified"])
        self.assertNotIn("PRIVATE",str(receipt))

    def test_reordered_opening_kinds_are_detected_with_matching_total(self):
        source,stats=original_body_opening_sequences(SOURCE,MAPPING)
        report=compare_ordered_body_openings(
            source,native_openings(["q","p","p"]),stats)
        counts=report["source_native_body_opening_kind_counts"]
        self.assertFalse(report["same_order_and_kind_in_every_mapped_book"])
        self.assertEqual(counts["books_with_equal_count_but_reordered_kinds"],1)
        self.assertEqual(report["first_mismatch_book_references_no_scripture"][0][
            "first_different_one_based_event_index"],1)
        self.assertNotIn("PRIVATE",str(report))

    def test_missing_or_duplicate_openings_are_detected_not_auto_repaired(self):
        source,stats=original_body_opening_sequences(SOURCE,MAPPING)
        for kinds in (["p","q"],["p","q","p","q"]):
            with self.subTest(kinds=kinds):
                receipt=compare_ordered_body_openings(
                    source,native_openings(kinds),stats)
                self.assertEqual(receipt["source_native_body_opening_kind_counts"][
                    "books_with_body_opening_count_difference"],1)
                self.assertFalse(receipt["same_order_and_kind_in_every_mapped_book"])

    def test_maintext_p_inside_source_note_not_silently_counted_as_body(self):
        raw=(b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>VERSE'
             b'<f><p>PRIVATE NOTE TEXT</p></f></p></book></usfx>')
        source,counts=original_body_opening_sequences(raw,MAPPING)
        self.assertEqual(len(source["Gen"]),1)
        self.assertEqual(counts["source_p_or_q_nested_in_notes_excluded"],1)
        self.assertNotIn("PRIVATE",str(counts))

    def test_non_title_p_before_first_chapter_must_remain_in_body_scope(self):
        raw=(b'<usfx><book id="GEN"><p>PRIVATE PARAGRAPH</p><c id="1"/>'
             b'<p><v id="1"/>VERSE</p></book></usfx>')
        source,stats=original_body_opening_sequences(raw,MAPPING)
        self.assertEqual([x for x,_ in source["Gen"]],["p","p"])
        self.assertEqual(stats["non_title_p_before_first_chapter_requires_review"],1)

    def test_extra_compiled_book_and_malformed_mapping_fail_closed(self):
        source,stats=original_body_opening_sequences(SOURCE,MAPPING)
        with self.assertRaises(OrderedStructureError):
            compare_ordered_body_openings(source,{"Gen":[("p","Gen.1.1")],
                                                 "Other":[("p","Other.1.1")]},stats)
        with self.assertRaises(OrderedStructureError):
            original_body_opening_sequences(SOURCE,[("GEN","Gen"),("GEN","Gen")])
        with self.assertRaises(OrderedStructureError):
            original_body_opening_sequences(SOURCE,[("OTHER","Gen")])


if __name__ == "__main__":
    unittest.main()
