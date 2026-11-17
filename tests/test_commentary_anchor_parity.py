"""Regression tests for source-neutral CCEL ThML ↔ stock SWORD reference diagnostics."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_anchor_parity import (compare_anchors, summarize_volume_anchor_results,
                                      _original_unoccupied_source_units,
                                      UnoccupiedSourceProseLocator)
from pilot_preflight import PilotError


class CommentaryAnchorParityTests(unittest.TestCase):
    def test_private_original_chapter_ref_witnesses_use_real_source_prose(self):
        from commentary_anchor_parity import compare_original_source_reference_candidates
        from hashlib import sha256
        prose = " ".join("sourceword" + str(i) for i in range(150))
        xml = (b"<ThML><div1><div2>"
               b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'
               b"<div><p>" + prose.encode() + b"</p></div></div2></div1></ThML>")
        plan = {"schema_version": 1,
                "status": "RESEARCH_ONLY_UNAPPROVED_REFERENCE_CANDIDATES",
                "source_xml_sha256": sha256(xml).hexdigest(),
                "candidate_ranges": [{"original_work_qualified_reference":
                                      "Bible:Gen.1.1-Gen.1.3",
                                      "proposed_osis_reference": "Gen.2.1-Gen.2.3"}]}
        native = {"Gen.1": [("Gen.1.1", b"<p>Unrelated book chapter.</p>")],
                  "Gen.2": [("Gen.2.1", b"<p>" + prose.encode() + b"</p>")]}
        r = compare_original_source_reference_candidates(
            xml, plan, native, {"Gen.2.1", "Gen.2.2", "Gen.2.3"})
        self.assertEqual(r["source_sections_checked"], 1)
        self.assertEqual(r["section_evidence"][0]["status"],
                         "CANDIDATE_CHAPTER_STRONGER_WORD_EVIDENCE")
        self.assertFalse(r["published"])
        self.assertFalse(r["rights_and_editorial_approved"])

    def test_private_chapter_candidate_rejects_wrong_original_sha(self):
        from commentary_anchor_parity import compare_original_source_reference_candidates
        with self.assertRaises(PilotError):
            compare_original_source_reference_candidates(
                b"<ThML/>",
                {"schema_version": 1, "status":
                 "RESEARCH_ONLY_UNAPPROVED_REFERENCE_CANDIDATES",
                 "source_xml_sha256": "0" * 64,
                 "candidate_ranges": [{"original_work_qualified_reference":
                                       "Bible:Gen.1.1-Gen.1.3",
                                       "proposed_osis_reference": "Gen.2.1-Gen.2.3"}]},
                {}, {"Gen.2.1", "Gen.2.3"})

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

    def test_valid_unoccupied_source_prose_is_located_in_neighboring_original_native_slot(self):
        original_words = " ".join(f"sourceword{n}" for n in range(55)).encode()
        original = (
            b'<?xml version="1.0"?><ThML><div1><div2>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>' + original_words + b'</p></div>'
            b'</div2></div1></ThML>' + b' ' * 1100
        )
        missing = [{"original_work_qualified_reference": "Bible:Gen.1.1",
                    "start_key": "Gen.1.1"}]
        original_units = _original_unoccupied_source_units(
            original, volume=1, missing=missing,
            canonical_verses={"Gen.1.1", "Gen.1.2"})
        self.assertEqual(len(original_units), 1)
        locator = UnoccupiedSourceProseLocator(original_units)
        locator.observe("K", "Exod.1.1", b"<div>Unrelated</div>")
        locator.observe("K", "Gen.1.2",
                        b"<div><p>Earlier context. " + original_words
                        + b" Follow-on details.</p></div>")
        result = locator.report()
        self.assertEqual(result["original_valid_unoccupied_start_units_checked"], 1)
        self.assertEqual(
            result["units"][0]["bounded_matching_native_candidates"][0]["original_stock_native_key"],
            "Gen.1.2")
        self.assertGreaterEqual(result["units"][0]["bounded_matching_native_candidates"][0][
            "matched_distinct_original_plain_word_windows"], 1)
        self.assertTrue(result["units"][0]["bounded_matching_native_candidates"][0][
            "all_original_plain_words_found_in_stock_order"])
        self.assertTrue(result["units"][0]["bounded_matching_native_candidates"][0][
            "all_original_plain_words_found_as_contiguous_stock_run"])
        self.assertEqual(
            result["units"][0]["provisional_missing_first_verse_alias_preview"],
            {"new_unoccupied_native_key":"Gen.1.1",
             "original_occupied_master_key":"Gen.1.2",
             "original_master_raw_sha256":
                 result["units"][0]["bounded_matching_native_candidates"][0]["stock_raw_sha256"],
             "status":"SOURCE_BOUND_ALIAS_PREVIEW_NOT_AUTHORIZED"})
        self.assertGreaterEqual(
            result["units"][0]["native_candidate_slots_containing_exact_original_visible_unicode"], 1)
        self.assertGreaterEqual(
            result["units"][0][
                "native_candidate_slots_containing_whitespace_folded_original_visible_unicode"], 1)
        incomplete = UnoccupiedSourceProseLocator(original_units)
        incomplete.observe("K", "Gen.1.3",
                           b"<div><p>" + original_words.replace(
                               b"sourceword27", b"alteredword27") + b"</p></div>")
        incomplete_report = incomplete.report()
        self.assertEqual(
            incomplete_report["units"][0]["native_candidate_slots_containing_all_original_words_in_order"], 0)
        self.assertIsNone(
            incomplete_report["units"][0]["provisional_missing_first_verse_alias_preview"])
        self.assertGreater(
            incomplete_report["units"][0]["native_candidate_slots_with_any_exact_plain_word_window"], 0)
        self.assertFalse(result["published"])
        self.assertNotIn("sourceword", json.dumps(result))
        self.assertEqual(_original_unoccupied_source_units(
            original, volume=1, missing=missing, canonical_verses={"Gen.1.2"}), [])

    def test_unoccupied_source_prose_locator_does_not_invent_absent_body(self):
        original = (b'<?xml version="1.0"?><ThML>'
                    b'<scripCom osisRef="Bible:Gen.1.1"/>'
                    b'<p>Not a matching original div.</p></ThML>' + b' ' * 1100)
        with self.assertRaisesRegex(PilotError, "lacks adjacent"):
            _original_unoccupied_source_units(
                original, volume=1, missing=[
                    {"original_work_qualified_reference": "Bible:Gen.1.1",
                     "start_key": "Gen.1.1"}],
                canonical_verses={"Gen.1.1"})

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
