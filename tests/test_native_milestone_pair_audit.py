"""Safety and ordering tests for original stock SWORD structural milestones."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from native_milestone_pair_audit import NativeMilestonePairAudit, NativeMilestoneAuditError


class NativeMilestonePairTests(unittest.TestCase):
    def test_actual_numerical_closure_across_book_intro_and_numbered_refs(self):
        check = NativeMilestonePairAudit()
        check.observe("I", "Gen", b'<div type="book" sID="book-PRIVATE-ID"/>')
        check.observe("I", "Gen.1", b'<div type="x-p" sID="p-PRIVATE-ID"/>'
                                   b'<lg sID="lg-PRIVATE-ID"/>'
                                   b'<l sID="line-PRIVATE-ID"/>')
        check.observe("K", "Gen.1.1", b'<l eID="line-PRIVATE-ID"/>'
                                     b'<lg eID="lg-PRIVATE-ID"/>'
                                     b'<div type="x-p" eID="p-PRIVATE-ID"/>'
                                     b'<note sID="ignored-PRIVATE-ID">PRIVATE NOTE</note>')
        check.observe("K", "Gen.1.2", b'<div type="book" eID="book-PRIVATE-ID"/>')
        receipt = check.finish()
        self.assertEqual(receipt["status"], "compiled_milestone_pairs_verified_only")
        self.assertEqual(receipt["native_milestone_tag_counts"]["div:paired"], 2)
        self.assertEqual(receipt["native_milestone_tag_counts"]["l:paired"], 1)
        self.assertEqual(receipt["native_milestone_tag_counts"]["lg:paired"], 1)
        self.assertEqual(receipt["native_milestone_pair_categories"]["intro_to_numbered_verse_pairs"], 4)
        self.assertEqual(receipt["native_milestone_pairing_findings"], {})
        self.assertEqual(receipt["remaining_unclosed_milestones_by_tag"], {})
        self.assertFalse(receipt["source_to_compiled_same_type_event_order_verified"])
        self.assertNotIn("PRIVATE", str(receipt))

    def test_duplicate_active_identifier_and_unpaired_are_explicit(self):
        check = NativeMilestonePairAudit()
        check.observe("I", "Gen", b'<div sID="private-same"/>')
        check.observe("K", "Gen.1.1", b'<div sID="private-same"/>')
        receipt = check.finish()
        self.assertEqual(receipt["native_milestone_pairing_findings"]["duplicate_active_sID"], 1)
        self.assertEqual(receipt["native_milestone_pairing_findings"]["unclosed_sID_at_end_of_native_corpus"], 1)
        self.assertNotIn("private-same", str(receipt))

    def test_orphan_closing_detected_even_if_total_counts_match(self):
        check = NativeMilestonePairAudit()
        check.observe("I", "Gen", b'<div sID="private-wrong"/>')
        check.observe("K", "Gen.1.1", b'<div eID="private-else"/>')
        result = check.finish()
        self.assertEqual(result["native_milestone_pairing_findings"][
            "orphan_eID_without_matching_active_sID"], 1)
        self.assertEqual(result["native_milestone_pairing_findings"][
            "unclosed_sID_at_end_of_native_corpus"], 1)
        self.assertEqual(result["native_milestone_tag_counts"]["div:open"],1)
        self.assertEqual(result["native_milestone_tag_counts"]["div:close"],1)

    def test_out_of_order_nesting_detected(self):
        check = NativeMilestonePairAudit()
        check.observe("I","Gen.1",b'<div sID="parent"/><lg sID="child"/>')
        check.observe("K","Gen.1.1",b'<div eID="parent"/><lg eID="child"/>')
        result = check.finish()
        self.assertEqual(result["native_milestone_pair_categories"][
            "different_tag_interleaving_diagnostic"],1)
        self.assertNotIn("same_tag_overlapping_milestone_ranges",
                         result["native_milestone_pairing_findings"])
        self.assertTrue(result["different_tag_interleavings_are_diagnostic_not_nesting_defects"])
        self.assertEqual(result["native_milestone_tag_counts"]["div:paired"],1)
        self.assertEqual(result["native_milestone_tag_counts"]["lg:paired"],1)

    def test_cross_book_and_different_types_flagged(self):
        check=NativeMilestonePairAudit()
        check.observe("I","Gen",b'<div type="paragraph" sID="p"/>')
        check.observe("K","Exod.1.1",b'<div type="poetry" eID="p"/>')
        result=check.finish()
        self.assertEqual(result["native_milestone_pair_categories"][
            "pair_spans_multiple_books_review_scope"],1)
        self.assertEqual(result["cross_book_pair_reference_samples_no_ids"],[
            {"start_ref":"Gen","end_ref":"Exod.1.1","structural_tag":"div",
             "opening_type_allowlisted":"paragraph"}])
        self.assertEqual(result["native_milestone_pairing_findings"][
            "matched_id_has_conflicting_types"],1)

    def test_malformed_xml_declaration_and_unaddressable_top_not_passed(self):
        check=NativeMilestonePairAudit()
        check.observe("U","TOP:1",b'<div sID="private-anonymous"/>')
        check.observe("I","Gen",b'<!DOCTYPE a><div sID="private-missing"/>')
        result=check.finish()
        self.assertEqual(result["native_numbered_intro_scan_counts"][
            "unaddressable_TOP_entries_unverified"],1)
        self.assertEqual(result["native_milestone_pairing_findings"][
            "unparseable_native_fragment"],1)
        self.assertEqual(result["native_numbered_intro_scan_counts"][
            "unaddressable_TOP_milestone_events_unverified"],1)
        self.assertNotEqual(result["status"],"compiled_milestone_pairs_verified_only")

    def test_source_words_and_note_values_never_escape(self):
        check=NativeMilestonePairAudit()
        check.observe("K","Gen.1.1",b'<div sID="PRIVATE_IDENTIFIER"/>'
                      b'PRIVATE SCRIPTURE'
                      b'<note><div sID="PRIVATE_NOTE_STRUCTURE"/>PRIVATE NOTE</note>'
                      b'<div eID="PRIVATE_IDENTIFIER"/>')
        receipt=check.finish()
        self.assertEqual(receipt["native_milestone_tag_counts"]["div:paired"],1)
        for forbidden in ("PRIVATE","SCRIPTURE","NOTE","IDENTIFIER"):
            self.assertNotIn(forbidden,str(receipt))

    def test_invalid_ref_and_repeated_entry_fail_without_partial_receipt(self):
        check=NativeMilestonePairAudit()
        with self.assertRaises(NativeMilestoneAuditError):
            check.observe("K","Gen.0.1",b'<div sID="x"/>')
        check.observe("K","Gen.1.1",b'<div sID="x"/>')
        with self.assertRaises(NativeMilestoneAuditError):
            check.observe("K","Gen.1.1",b'<div eID="x"/>')

    def test_same_tag_crossing_is_not_excused_by_other_tag_interleaving(self):
        check=NativeMilestonePairAudit()
        check.observe("I","Gen",b'<div sID="a"/><div sID="b"/>')
        check.observe("K","Gen.1.1",b'<div eID="a"/><div eID="b"/>')
        report=check.finish()
        self.assertEqual(report["native_milestone_pairing_findings"][
            "same_tag_same_type_overlapping_milestones"],1)
        self.assertNotEqual(report["status"],"compiled_milestone_pairs_verified_only")

    def test_two_div_semantic_types_may_interleave_but_need_review(self):
        check=NativeMilestonePairAudit()
        check.observe("I","Gen.1",b'<div type="x-p" sID="paragraph"/>'
                                   b'<div type="x-milestone" sID="tech"/>')
        check.observe("K","Gen.1.1",b'<div type="x-p" eID="paragraph"/>'
                                     b'<div type="x-milestone" eID="tech"/>')
        r=check.finish()
        self.assertEqual(r["native_milestone_pair_categories"][
            "same_tag_different_type_interleaving_review"],1)
        self.assertNotIn("same_tag_same_type_overlapping_milestones",
                         r["native_milestone_pairing_findings"])
        self.assertEqual(r["paired_div_types_allowlisted"]["x-p"],1)
        self.assertEqual(r["paired_div_types_allowlisted"]["x-milestone"],1)
        self.assertEqual(check.native_x_p_pairs_by_book(),{"Gen":1})
        self.assertFalse(r["source_to_compiled_same_type_event_order_verified"])

    def test_osis2mod_paragraph_vs_preverse_div_types_not_conflated(self):
        check=NativeMilestonePairAudit()
        check.observe("I","Gen.1",
                      b'<div type="x-p" sID="paragraph-one"/>'
                      b'<div type="x-milestone" subType="x-preverse" sID="technical"/>')
        check.observe("K","Gen.1.1",
                      b'<div type="x-milestone" subType="x-preverse" eID="technical"/>'
                      b'<div type="x-p" eID="paragraph-one"/>')
        r=check.finish()
        self.assertEqual(r["paired_div_types_allowlisted"]["x-p"],1)
        self.assertEqual(r["paired_div_types_allowlisted"]["x-milestone"],1)
        self.assertEqual(r["native_milestone_tag_counts"]["div:paired"],2)
        self.assertNotIn("technical",str(r))
        self.assertNotIn("paragraph-one",str(r))

    def test_untrusted_div_type_remains_categorized_and_not_disclosed(self):
        check=NativeMilestonePairAudit()
        check.observe("K","Gen.1.1",
                      b'<div type="private-super-sensitive-type" sID="x"/>'
                      b'<div type="private-super-sensitive-type" eID="x"/>')
        r=check.finish()
        self.assertEqual(r["paired_div_types_allowlisted"]["other_unreviewed_type"],1)
        self.assertNotIn("private-super-sensitive-type",str(r))

    def test_reused_identifier_after_prior_close_is_allowed(self):
        check=NativeMilestonePairAudit()
        check.observe("K","Gen.1.1",b'<l sID="x"/><l eID="x"/>')
        check.observe("K","Gen.1.2",b'<l sID="x"/><l eID="x"/>')
        result=check.finish()
        self.assertEqual(result["native_milestone_tag_counts"]["l:paired"],2)
        self.assertEqual(result["native_milestone_pairing_findings"],{})


if __name__=="__main__":
    unittest.main()
