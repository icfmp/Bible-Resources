"""Synthetic source-only note-link triage; no original Scripture or network."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_osis_note_link_triage import (
    triage_source_notes, SourceLinkTriageError,
)

SHA = "a"*64


class SourceNoteLinkTriageTests(unittest.TestCase):
    def setUp(self):
        self.keys = ("Gen.1.1", "Gen.1.2", "Exod.1.1")
        self.notes = {x:[] for x in self.keys}

    def check(self):
        return triage_source_notes(self.notes, set(self.keys),
                                   source_sha256=SHA)

    def test_indexed_verse_chapter_full_range_are_source_only(self):
        self.notes["Gen.1.1"]=[{"targets":(
            "Gen.1.1", "Gen.1", "Gen.1.1-Exod.1.1")}]
        receipt = self.check()
        self.assertEqual(receipt["unresolved_original_target_attributes"],0)
        self.assertEqual(receipt["metadata_counts"][
            "explicit_original_target_attributes"],3)
        self.assertTrue(receipt["source_verse_index_only"])
        self.assertFalse(receipt["actual_compiled_navigation_verified"])
        self.assertFalse(receipt["publication_or_editorial_approval"])

    def test_authorial_unindexed_verse_is_never_filled(self):
        self.notes["Gen.1.1"]=[{"targets":("Gen.1.37",)}]
        report=self.check()
        self.assertEqual(report["unresolved_original_target_attributes"],1)
        self.assertEqual(report["bounded_note_host_findings"][0]["shape_hint"],
                         "source_key_not_present_in_authorial_index")
        self.assertEqual(report["bounded_note_host_findings"][0][
            "authorial_note_host_reference"],"Gen.1.1")
        self.assertEqual(report["bounded_note_host_findings"][0][
            "one_based_note_ordinal"],1)
        self.assertTrue(report["no_missing_verses_invented"])
        self.assertNotIn("Gen.1.37",str(report))

    def test_unsupported_original_osis_syntax_is_review_not_normalized(self):
        self.notes["Gen.1.1"]=[{"targets":(
            "Gen.1.1!SECRET", "private:Gen.1.1",
            "Gen.1.1-2", "Gen.1.1-Gen.1.2-Exod.1.1",
        )}]
        report=self.check()
        self.assertEqual(report["unresolved_original_target_attributes"],4)
        self.assertEqual(report["metadata_counts"][
            "target_with_unsupported_grammar"],4)
        for token in ("SECRET", "private:", "Gen.1.1-2"):
            self.assertNotIn(token, str(report))
        self.assertEqual(
            report["bounded_note_host_findings"][1]["shape_hint"],
            "authorial_work_prefix_or_colon_requires_review")

    def test_unsupported_separator_and_wrapper_are_only_research_hypotheses(self):
        self.notes["Gen.1.1"] = [{"targets": (
            "Gen.1.1; Exod.1.1", "(Gen.1.2)", "Gen.1.1,Exod.1.1"
        )}]
        report = self.check()
        cases = [x["source_navigation_review_detail"]["analysis"]
                 for x in report["bounded_note_host_findings"]]
        self.assertEqual(cases, [
            "punctuation_delimited_indexed_targets_candidate",
            "bracket_wrapped_indexed_target_candidate",
            "punctuation_delimited_indexed_targets_candidate",
        ])
        self.assertEqual(report["unresolved_original_target_attributes"], 3)
        self.assertTrue(all(
            x["source_navigation_review_detail"]["original_grammar_still_unsupported"]
            for x in report["bounded_note_host_findings"]))
        self.assertNotIn("Gen.1.1;", str(report))
        self.assertNotIn("(Gen.1.2)", str(report))

    def test_unindexed_verse_neighbor_diagnostic_does_not_invent_gap(self):
        self.notes["Gen.1.1"] = [{"targets": ("Gen.1.3",)}]
        report = self.check()
        detail = report["bounded_note_host_findings"][0][
            "source_navigation_review_detail"]
        self.assertEqual(detail["analysis"], "simple_missing_publisher_verse_key")
        self.assertTrue(detail["target_same_chapter_as_note"])
        self.assertTrue(detail["preceding_verse_indexed"])
        self.assertFalse(detail["following_verse_indexed"])
        self.assertTrue(detail["chapter_exists_in_source"])
        self.assertFalse(detail["missing_target_created"])
        self.assertNotIn("Gen.1.3", str(report))

    def test_original_nonascii_dash_is_review_only_not_a_rewrite(self):
        self.notes["Gen.1.1"] = [{"targets": ("Gen.1.1–Gen.1.2",)}]
        report = self.check()
        detail = report["bounded_note_host_findings"][0][
            "source_navigation_review_detail"]
        self.assertEqual(detail["analysis"], "unicode_dash_reference_candidate")
        self.assertTrue(detail["original_grammar_still_unsupported"])
        self.assertNotIn("Gen.1.1–Gen.1.2", str(report))

    def test_source_only_reversed_range_does_not_claim_addressability(self):
        self.notes["Gen.1.1"]=[{"targets":("Exod.1.1-Gen.1.1",)}]
        report=self.check()
        self.assertEqual(report["unresolved_original_target_attributes"],1)
        self.assertEqual(report["metadata_counts"][
            "target_with_unreviewed_range_or_other"],1)

    def test_source_and_note_inventory_consistency_fails_closed(self):
        with self.assertRaises(SourceLinkTriageError):
            triage_source_notes({"Gen.1.1":[]},set(self.keys),
                                    source_sha256=SHA)
        self.notes["Gen.1.1"]=[{"targets":["Gen.1.1"]}]
        with self.assertRaises(SourceLinkTriageError):
            self.check()
        self.notes["Gen.1.1"]=[{"targets":("Gen.1.1",)}]
        with self.assertRaises(SourceLinkTriageError):
            triage_source_notes(self.notes,set(self.keys),
                                source_sha256="not-pinned")

    def test_bounded_findings_and_no_raw_source_note_values(self):
        # Source targets remain in private memory even with >40 failures.
        self.notes["Gen.1.1"]=[
            {"targets":tuple("Gen.1."+str(i) for i in range(50,100))}
        ]
        report=self.check()
        self.assertEqual(report["unresolved_original_target_attributes"],50)
        self.assertEqual(len(report["bounded_note_host_findings"]),40)
        self.assertFalse(report["source_note_target_literals_or_bodies_exposed"])

if __name__=="__main__":
    unittest.main()
