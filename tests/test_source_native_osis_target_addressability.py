"""Synthetic safe OSIS link-target classification tests."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_osis_target_addressability import (
    audit_explicit_targets,OSISTargetAuditError,_resolve_endpoint,
)


class TargetAddressabilityTests(unittest.TestCase):
    def setUp(self):
        self.keys={"Gen.1.1","Gen.1.2","Gen.2.1","Exod.1.1"}

    def test_exact_verse_chapter_book_resolution(self):
        chapters={"Gen.1","Gen.2","Exod.1"}
        books={"Gen","Exod"}
        self.assertEqual(_resolve_endpoint("Gen.1.1",self.keys,chapters,books),
                         "indexed_verse")
        self.assertEqual(_resolve_endpoint("Gen.2",self.keys,chapters,books),
                         "indexed_chapter")
        self.assertEqual(_resolve_endpoint("Exod",self.keys,chapters,books),
                         "indexed_book")
        self.assertEqual(_resolve_endpoint("Gen.1.37",self.keys,chapters,books),
                         "unindexed_verse")
        self.assertEqual(_resolve_endpoint("Other.1.1",self.keys,chapters,books),
                         "unindexed_verse")

    def test_simple_and_multiple_references_are_index_addressable(self):
        notes={ref:[] for ref in self.keys}
        notes["Gen.1.1"]=[{"targets":("Gen.1.1","Gen.1.2 Exod.1.1","Gen.2")}]
        result=audit_explicit_targets(notes,self.keys,set(self.keys))
        self.assertEqual(result["status"],"all_explicit_targets_index_addressable_simple_syntax")
        self.assertEqual(result["counts"]["explicit_target_attributes_checked"],3)
        self.assertEqual(result["counts"]["addressable_endpoint_components"],4)
        self.assertEqual(result["counts"]["multi_reference_target_attributes"],1)
        self.assertFalse(result["actual_reader_link_click_navigation_verified"])

    def test_invalid_ranges_and_missing_targets_are_flagged_not_fixed(self):
        notes={ref:[] for ref in self.keys}
        notes["Gen.1.1"]=[{"targets":(
            "Gen.1.1-Gen.1.2","Gen.1.37","Bible:Gen.1.1","PRIVATE_PERSON")}]
        result=audit_explicit_targets(notes,self.keys,set(self.keys))
        self.assertEqual(result["status"],"some_explicit_targets_need_grammar_or_editorial_review")
        self.assertEqual(result["counts"]["range_or_compound_reference_requires_review"],1)
        self.assertEqual(result["counts"]["nonindexed_endpoint_requires_review"],2)
        self.assertEqual(result["counts"]["unsupported_endpoint_syntax"],1)
        self.assertEqual(len(result["bounded_note_host_reference_samples"]),4)
        for secret in ("PRIVATE_PERSON","Bible:","Gen.1.37"):
            self.assertNotIn(secret,str(result))
        self.assertFalse(result["publication_approved"])

    def test_fail_closed_on_index_mismatch_and_bad_scope(self):
        notes={ref:[] for ref in self.keys}
        with self.assertRaises(OSISTargetAuditError):
            audit_explicit_targets(notes,self.keys,{"Gen.1.1"})
        with self.assertRaises(OSISTargetAuditError):
            audit_explicit_targets({"Gen.1.1":[]},self.keys,set(self.keys))
        notes["Gen.1.1"]=[{"targets":["Gen.1.1"]}]
        with self.assertRaises(OSISTargetAuditError):
            audit_explicit_targets(notes,self.keys,set(self.keys))


if __name__=="__main__":
    unittest.main()
