"""Source/native verse-boundary anchoring remains diagnostic, never approval."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_record_scope_triage import (
    ScopeTriageError, compare_body_record_scopes,
)


def a(word, ref, scope="numbered"):
    return {"word_ordinal":word, "inside_word":False,
            "reference":ref, "record_scope":scope}


def original():
    return {"Gen": (["alpha","beta","gamma","delta"], [
        {"kind":"p", "open":a(0,"Gen.1.0","source_between_verses"),
         "close":a(3,"Gen.1.1")},
        {"kind":"q", "open":a(1,"Gen.1.1"),
         "close":a(2,"Gen.1.1")},
        {"kind":"p", "open":a(3,"Gen.1.1"),
         "close":a(4,"Gen.1.2")},
    ])}


def compiled():
    return {"Gen": (["alpha","beta","gamma","delta"], [
        {"kind":"p", "open":a(0,"Gen.1","native_intro"),
         "close":a(3,"Gen.1.2")},
        {"kind":"q", "open":a(1,"Gen.1.1"),
         "close":a(2,"Gen.1.1")},
        {"kind":"p", "open":a(3,"Gen.1.2"),
         "close":a(4,"Gen.1.2")},
    ])}


VERSES = {"Gen.1.1":"alpha beta gamma", "Gen.1.2":"delta"}


class SourceNativeRecordTriageTests(unittest.TestCase):
    def test_adjacent_verse_intro_and_original_before_verse_separately_classified(self):
        report=compare_body_record_scopes(original(),compiled(),VERSES)
        c=report["source_native_scope_counts"]
        self.assertEqual(c["books_checked"],1)
        self.assertEqual(c["events_compared"],3)
        self.assertEqual(c["events_with_different_record_or_scope"],2)
        self.assertEqual(c["open_class_source_native_verse_zero_intro_alias_candidate"],1)
        self.assertEqual(c["close_class_authorial_previous_native_next_numbered_verse_candidate"],1)
        self.assertEqual(c["open_class_authorial_previous_native_next_numbered_verse_candidate"],1)
        self.assertEqual(c["unexplained_or_ambiguous_endpoints_needing_review"],0)
        self.assertEqual(report["status"],
                         "record_scope_candidate_classification_requires_editorial_review")
        self.assertTrue(report["candidate_compiler_record_shifts_are_not_editorial_equivalence"])
        self.assertFalse(report["editorial_or_publication_approved"])
        for secret in ("alpha","beta","gamma","delta","sID","PRIVATE"):
            self.assertNotIn(secret,str(report))

    def test_chapter_intro_next_to_original_first_verse_is_candidate_only(self):
        src=original()
        src["Gen"][1][0]["open"]=a(0,"Gen.1.1")
        cmp=compiled()
        cmp["Gen"][1][0]["open"]=a(0,"Gen.1.0","native_intro")
        report=compare_body_record_scopes(src,cmp,VERSES)
        self.assertEqual(report["source_native_scope_counts"][
            "open_class_chapter_or_book_intro_vs_numbered_boundary_candidate"],1)
        self.assertFalse(report["editorial_or_publication_approved"])

    def test_moved_record_within_original_verse_is_a_real_review_finding(self):
        cmp=compiled()
        cmp["Gen"][1][1]["open"]["reference"]="Gen.1.2"
        r=compare_body_record_scopes(original(),cmp,VERSES)
        self.assertEqual(r["unexplained_or_ambiguous_endpoints"],1)
        self.assertEqual(r["source_native_scope_counts"][
            "open_class_different_record_inside_authored_verse_review"],1)
        self.assertEqual(r["status"],"some_record_scope_shifts_remain_unclassified")

    def test_nonadjacent_previous_or_next_verse_is_never_assumed_safe(self):
        cmp=compiled()
        cmp["Gen"][1][0]["close"]["reference"]="Gen.1.3"
        r=compare_body_record_scopes(original(),cmp,VERSES)
        self.assertEqual(r["source_native_scope_counts"][
            "close_class_record_outside_immediate_source_boundary_review"],1)

    def test_zero_word_verse_at_boundary_blocks_simple_prev_next_inference(self):
        src={"Gen": (["alpha","beta"], [
            {"kind":"p","open":a(1,"Gen.1.1"),
             "close":a(2,"Gen.1.3")},
        ])}
        cmp={"Gen": (["alpha","beta"], [
            {"kind":"p","open":a(1,"Gen.1.3"),
             "close":a(2,"Gen.1.3")},
        ])}
        verses={"Gen.1.1":"alpha", "Gen.1.2":"", "Gen.1.3":"beta"}
        r=compare_body_record_scopes(src,cmp,verses)
        self.assertEqual(r["unexplained_or_ambiguous_endpoints"],1)
        self.assertEqual(r["source_native_scope_counts"][
            "open_class_ambiguous_zero_word_verse_or_multiple_boundary_review"],1)

    def test_exact_same_ref_different_original_between_verse_scope_is_classified(self):
        cmp=compiled()
        cmp["Gen"][1][2]["open"]=a(3,"Gen.1.1")
        src=original()
        src["Gen"][1][2]["open"]=a(3,"Gen.1.1","source_between_verses")
        r=compare_body_record_scopes(src,cmp,VERSES)
        self.assertEqual(r["source_native_scope_counts"][
            "open_class_same_record_different_source_native_scope_tag_candidate"],1)

    def test_identical_opening_closure_ordinal_is_a_required_precondition(self):
        cmp=compiled()
        cmp["Gen"][1][0]["close"]["word_ordinal"]=2
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),cmp,VERSES)
        cmp=compiled()
        cmp["Gen"][1][1]["open"]["inside_word"]=True
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),cmp,VERSES)

    def test_mismatched_source_verse_words_and_bad_order_block_report(self):
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),compiled(),
                                       {"Gen.1.1":"DIFFERENT", "Gen.1.2":"delta"})
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),compiled(),
                                       {"Gen.1.2":"delta", "Gen.1.1":"alpha beta gamma"})

    def test_wrong_book_unsafe_ref_unmapped_book_and_event_kind_fail_closed(self):
        cmp=compiled()
        cmp["Gen"][1][0]["open"]["reference"]="Other.1.1"
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),cmp,VERSES)
        cmp=compiled()
        cmp["Gen"][1][1]["kind"]="p"
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),cmp,VERSES)
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),{},VERSES)
        cmp=compiled()
        cmp["Gen"][1][0]["open"]["reference"]="<PRIVATE XML>"
        with self.assertRaises(ScopeTriageError):
            compare_body_record_scopes(original(),cmp,VERSES)

    def test_original_punctuation_not_in_scope_triage_receipt(self):
        verses={"Gen.1.1":"alpha, beta gamma!", "Gen.1.2":"delta."}
        report=compare_body_record_scopes(original(),compiled(),verses)
        self.assertTrue(report["unchanged_punctuation_linebreak_and_whitespace_positions_unverified"])
        self.assertNotIn("alpha",str(report))
        self.assertNotIn("gamma",str(report))
        self.assertNotIn("delta",str(report))


if __name__ == "__main__":
    unittest.main()
