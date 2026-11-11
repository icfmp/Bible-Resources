"""Synthetic non-leaking source/native OSIS endpoint and range audits."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_osis_target_addressability import (
    audit_explicit_targets, OSISTargetAuditError, _resolve_endpoint,
)


class OSISAddressabilityTests(unittest.TestCase):
    def setUp(self):
        self.ordered=("Gen.1.1","Gen.1.2","Gen.2.1","Exod.1.1")
        self.keys=set(self.ordered)
        self.notes={x:[] for x in self.ordered}

    def check(self):
        return audit_explicit_targets(self.notes,self.keys,set(self.keys))

    def test_single_book_chapter_verse_and_full_range_syntax(self):
        self.notes["Gen.1.1"]=[{"targets":(
            "Gen","Gen.1","Gen.1.1",
            "Gen.1.1-Gen.2.1","Gen.1-Gen.2",
            "Gen-Exod","Gen.1.1 Exod.1.1",
        )}]
        proof=self.check()
        self.assertTrue(proof["all_original_explicit_targets_index_addressable"])
        self.assertEqual(proof["counts"]["explicit_target_attributes_checked"],7)
        self.assertEqual(proof["counts"]["target_component_indexed_ordered_full_range"],3)
        self.assertEqual(proof["counts"]["addressable_endpoint_components"],10)
        self.assertEqual(proof["counts"]["multi_reference_target_attributes"],1)
        self.assertFalse(proof["actual_reader_link_click_navigation_verified"])

    def test_missing_authored_verse_not_silently_filled(self):
        self.notes["Gen.1.1"]=[{"targets":(
            "Gen.1.37","Other.1.1","Gen.9",
            "Gen.1.1-Gen.1.37",
        )}]
        proof=self.check()
        self.assertFalse(proof["all_original_explicit_targets_index_addressable"])
        self.assertEqual(proof["counts"]["target_with_unindexed_endpoint"],4)
        self.assertEqual(proof["counts"]["target_component_unindexed_verse_existing_book"],1)
        self.assertEqual(proof["counts"]["target_component_unindexed_verse_unknown_book"],1)
        self.assertEqual(proof["counts"]["target_component_unindexed_chapter_existing_book"],1)
        self.assertEqual(proof["counts"]["target_component_unindexed_range_endpoint"],1)
        self.assertNotIn("Gen.1.37",str(proof))

    def test_unsupported_shorthand_and_work_prefix_are_unreviewed(self):
        self.notes["Gen.1.1"]=[{"targets":(
            "Gen.1.1-2","Bible:Gen.1.1","Gen.1.1!test",
            "PRIVATE_SECRET","Gen.1.1-Gen.1.2-Gen.2.1",
        )}]
        proof=self.check()
        self.assertEqual(proof["counts"]["target_with_unsupported_grammar"],5)
        for secret in ("PRIVATE_SECRET","Bible:","Gen.1.1!test"):
            self.assertNotIn(secret,str(proof))
        self.assertFalse(proof["publication_approved"])

    def test_reversed_source_range_detected(self):
        self.notes["Gen.1.1"]=[{"targets":("Exod.1.1-Gen.1.1",)}]
        proof=self.check()
        self.assertFalse(proof["all_original_explicit_targets_index_addressable"])
        self.assertEqual(proof["counts"]["target_component_reversed_or_invalid_range"],1)
        self.assertEqual(proof["counts"]["target_with_reversed_range_or_other"],1)

    def test_invalid_source_native_scope_and_bad_targets_fail_closed(self):
        self.notes["Gen.1.1"]=[{"targets":("Gen.1.1",)}]
        with self.assertRaises(OSISTargetAuditError):
            audit_explicit_targets(self.notes,self.keys,{"Gen.1.1"})
        with self.assertRaises(OSISTargetAuditError):
            audit_explicit_targets({"Gen.1.1":[]},self.keys,set(self.keys))
        self.notes["Gen.1.1"]=[{"targets":["Gen.1.1"]}]
        with self.assertRaises(OSISTargetAuditError):
            self.check()

    def test_compatibility_simple_endpoint_classifier(self):
        chapters={"Gen.1","Gen.2","Exod.1"}
        books={"Gen","Exod"}
        self.assertEqual(_resolve_endpoint("Gen.1.1",self.keys,chapters,books),
                         "indexed_verse")
        self.assertEqual(_resolve_endpoint("Gen.1",self.keys,chapters,books),
                         "indexed_chapter")
        self.assertEqual(_resolve_endpoint("Gen.1.88",self.keys,chapters,books),
                         "unindexed_verse")


if __name__=="__main__":
    unittest.main()
