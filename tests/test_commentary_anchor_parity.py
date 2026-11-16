"""Regression tests for source-neutral CCEL ThML ↔ stock SWORD reference diagnostics."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_anchor_parity import compare_anchors, summarize_volume_anchor_results
from pilot_preflight import PilotError


class CommentaryAnchorParityTests(unittest.TestCase):
    def xml(self, markers):
        return (
            b'<?xml version="1.0"?><ThML><ThML.body><div1 title="Book">'
            b'<div2 title="Chapter">' + markers +
            b'<p>' + (b"Unchanged original source text must never be output. " * 40) +
            b'</p></div2></div1></ThML.body></ThML>'
        )

    def native(self, rows, *, numbered, intros=0):
        return (b"M\tTestCom\tKJV\t1.9.0\tzCom\n" + rows +
                f"S\t32000\t{numbered}\t{intros}\t0\n".encode())

    def test_native_kjv_registry_differentiates_invalid_source_endpoint_from_unoccupied_slot(self):
        xml = self.xml(
            b'<scripCom osisRef="Bible:Gen.1"/>'
            b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'
            b'<scripCom osisRef="Bible:Gen.1.2"/>'
        )
        stock = self.native(
            b"I\tGen.1\nK\tGen.1.1\nK\tGen.1.2\n",
            numbered=2, intros=1,
        )
        registry = {
            "module_id": "TestCom", "versification": "KJV",
            "verse_keys": {"Gen.1.1", "Gen.1.2"},
            "chapter_maximums": {"Gen.1": 2},
        }
        report = compare_anchors(xml, stock, "TestCom", native_registry=registry)
        self.assertTrue(report["original_native_versification_registry_checked"])
        self.assertEqual(report["original_reference_registry_classes"], {
            "EXACT_CHAPTER_IN_REGISTRY": 1,
            "EXACT_SINGLE_VERSE_IN_REGISTRY": 1,
            "SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY": 1,
        })
        self.assertEqual(len(report["bounded_original_out_of_registry_reference_examples"]), 1)
        self.assertTrue(report["canonical_validity_does_not_prove_semantic_passage_correctness"])
        self.assertFalse(report["authored_source_to_compiled_text_parity"])
        self.assertNotIn("Unchanged original source text", json.dumps(report))
        wrong_registry = dict(registry, versification="Vulg")
        with self.assertRaisesRegex(PilotError, "disagree"):
            compare_anchors(xml, stock, "TestCom", native_registry=wrong_registry)

    def test_exact_chapter_verse_range_and_single_anchors_are_diagnostics_only(self):
        xml = self.xml(
            b'<scripCom osisRef="Bible:Gen.1" />'
            b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.3" />'
            b'<scripCom osisRef="Bible:Gen.1.1" />'
            b'<scripCom osisRef="Bible:John.3.14-John.3.21" />'
        )
        native = self.native(b"I\tGen.1\nK\tGen.1.1\nK\tGen.1.3\nK\tJohn.3.14\n",
                             numbered=3, intros=1)
        r = compare_anchors(xml, native, "TestCom", ("John.3.16",))
        self.assertEqual(r["source_marker_count"], 4)
        self.assertEqual(r["matched_exact_start_by_class"]["work_qualified_chapter"], 1)
        self.assertEqual(r["matched_exact_start_by_class"]["work_qualified_same_book_verse_range"], 2)
        self.assertEqual(r["matched_exact_start_by_class"]["work_qualified_verse"], 1)
        self.assertFalse(r["explicit_verse_probes"]["John.3.16"]["native_occupied_exact_key"])
        self.assertEqual(r["explicit_verse_probes"]["John.3.16"]["source_explicit_verse_range_containing_probe"], 1)
        self.assertFalse(r["authored_source_to_compiled_text_parity"])
        self.assertNotIn("Unchanged original source text", json.dumps(r))

    def test_missing_source_start_must_not_be_described_as_lost_authorial_text(self):
        xml = self.xml(b'<scripCom osisRef="Bible:Gen.1.1"/>')
        native = self.native(b"K\tGen.1.2\n", numbered=1)
        r = compare_anchors(xml, native, "TestCom")
        self.assertEqual(r["unoccupied_source_start_by_class"]["work_qualified_verse"], 1)
        self.assertEqual(r["bounded_unoccupied_start_references"][0]["start_key"], "Gen.1.1")
        self.assertIn("not_automatic_content_loss", r["bounded_unoccupied_start_references"][0]["diagnostic"])
        self.assertFalse(r["section_range_boundaries_verified"])

    def test_duplicate_source_commentary_anchors_must_remain_distinct(self):
        xml = self.xml(
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
        )
        r = compare_anchors(xml, self.native(b"K\tGen.1.1\n", numbered=1), "TestCom")
        self.assertEqual(r["source_marker_count"], 2)
        self.assertEqual(r["duplicate_exact_ref_appearances"], 1)
        self.assertEqual(r["matched_exact_start_by_class"]["work_qualified_verse"], 2)

    def test_stock_book_without_explicit_source_marker_is_an_advisory_finding(self):
        original = self.xml(b'<scripCom osisRef="Bible:Gen.1.1"/>')
        stock = self.native(b"K\tGen.1.1\nK\tJude.1.1\n", numbered=2)
        result = compare_anchors(original, stock, "TestCom")
        self.assertEqual(result["stock_books_without_explicit_source_scripCom_markers"], ["Jude"])
        self.assertTrue(result["lack_of_source_marker_is_not_proof_of_missing_book_text"])
        self.assertFalse(result["authored_source_to_compiled_text_parity"])

    def test_unknown_original_reference_is_not_guessed(self):
        xml = self.xml(b'<scripCom osisRef="Unclear 1:2"/>')
        r = compare_anchors(xml, self.native(b"K\tGen.1.1\n", numbered=1), "TestCom")
        self.assertEqual(r["unoccupied_source_start_by_class"]["unreviewed_reference_syntax"], 1)
        self.assertFalse(r["authored_source_to_compiled_text_parity"])

    def test_corrupted_stock_index_cannot_be_interpreted_as_source_loss(self):
        xml = self.xml(b'<scripCom osisRef="Bible:Gen.1.1"/>')
        with self.assertRaises(PilotError):
            compare_anchors(xml, self.native(b"K\tGen.1.1\n", numbered=2), "TestCom")


    def test_two_volumes_share_one_stock_index_without_inventing_sections(self):
        native = self.native(
            b"K\tGen.1.1\nK\tJohn.3.16\n", numbered=2)
        first = compare_anchors(
            self.xml(b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'),
            native, "TestCom")
        second = compare_anchors(
            self.xml(b'<scripCom osisRef="Bible:John.3.16"/>'
                     b'<scripCom osisRef="Bible:John.3.16"/>'),
            native, "TestCom")
        merged = summarize_volume_anchor_results([
            {"volume": 1, "anchor_diagnostic": first},
            {"volume": 2, "anchor_diagnostic": second},
        ])
        self.assertEqual(merged["original_xml_volume_count"], 2)
        self.assertEqual(merged["source_annotation_markers_across_volumes"], 3)
        self.assertEqual(merged["stock_native_occupied_numbered_count"], 2)
        self.assertEqual(merged["duplicate_exact_references_within_each_source_volume"], 1)
        self.assertEqual(merged["source_books_with_explicit_markers_across_volumes"],
                         ["Gen", "John"])
        self.assertTrue(merged["cross_volume_identical_reference_identity_not_established"])
        self.assertFalse(merged["authored_source_to_compiled_text_parity"])
        self.assertFalse(merged["published"])
        self.assertEqual(
            merged["bounded_source_range_end_mismatch_examples"][0]["end_key"],
            "Gen.1.3")
        self.assertEqual(
            merged["bounded_source_range_end_mismatch_examples"][0]["volume"], 1)
        self.assertNotIn("Unchanged original source text", json.dumps(merged))

        with self.assertRaisesRegex(PilotError, "original declared order"):
            summarize_volume_anchor_results([
                {"volume": 2, "anchor_diagnostic": second},
                {"volume": 1, "anchor_diagnostic": first},
            ])
        with self.assertRaisesRegex(PilotError, "stock native keys"):
            wrong_index = self.native(b"K\tGen.1.1\n", numbered=1)
            wrong = compare_anchors(self.xml(b'<scripCom osisRef="Bible:Gen.1.1"/>'),
                                    wrong_index, "TestCom")
            summarize_volume_anchor_results([
                {"volume": 1, "anchor_diagnostic": first},
                {"volume": 2, "anchor_diagnostic": wrong},
            ])


if __name__ == "__main__":
    unittest.main()
