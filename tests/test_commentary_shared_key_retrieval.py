#!/usr/bin/env python3
"""Private, language-neutral authored commentary overlap navigation tests."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_osis import (source_commentary_shared_key_retrieval_map,
                        source_commentary_reviewed_shared_key_plan)


class SharedCommentaryScopeTests(unittest.TestCase):
    def setUp(self):
        self.groups=[
            {"sID":"Rom.4.9-17", "keys":tuple(
                f"Rom.4.{v}" for v in range(9,18)),
             "line":12, "text":"L'interprétation en français — avec fidélité."},
            {"sID":"Rom.4.17-22", "keys":tuple(
                f"Rom.4.{v}" for v in range(17,23)),
             "line":21, "text":"English original commentary: distinct text."},
            {"sID":"2Chr.1.1", "keys":("2Chr.1.1",),
             "line":54, "text":"Ελληνικά, ancien commentaire introductif."},
            {"sID":"2Chr.1.1-12", "keys":tuple(
                f"2Chr.1.{v}" for v in range(1,13)),
             "line":58, "text":"Deuxième section distincte — même premier verset."},
        ]
        self.native={"Rom.4.9","Rom.4.17","2Chr.1.1"}

    def test_one_original_source_group_can_have_multiple_authorial_owners(self):
        untouched=deepcopy(self.groups)
        result=source_commentary_shared_key_retrieval_map(
            self.groups, self.native
        )
        self.assertEqual(result["original_authored_groups"],4)
        self.assertEqual(result["original_shared_verse_keys"],2)
        self.assertEqual(result["shared_verse_source_sections"],4)
        self.assertFalse(result["original_prose_in_report"])
        self.assertFalse(result["source_groups_rewritten"])
        self.assertEqual(self.groups,untouched)
        by_key={item["bible_verse_key"]:item
                for item in result["shared_verses"]}
        self.assertEqual(set(by_key),{"Rom.4.17","2Chr.1.1"})
        romans=by_key["Rom.4.17"]
        self.assertEqual(
            romans["native_retrieval_keys_in_authorial_order"],
            ["Rom.4.9","Rom.4.17"])
        self.assertEqual(romans["distinct_native_first_key_count"],2)
        self.assertEqual(
            romans["presentation_class"],
            "DISTINCT_FIRST_KEYS_REQUIRE_MULTISECTION_READER")
        self.assertEqual(
            [m["original_source_scope"] for m in
             romans["original_sections_in_source_order"]],
            ["Rom.4.9-17","Rom.4.17-22"])
        chronicles=by_key["2Chr.1.1"]
        self.assertEqual(
            chronicles["native_retrieval_keys_in_authorial_order"],
            ["2Chr.1.1"])
        self.assertEqual(
            chronicles["presentation_class"],
            "SAME_FIRST_KEY_REQUIRES_INNER_SECTION_MARKUP_CHECK")
        encoded=json.dumps(result,ensure_ascii=False)
        for phrase in ("L'interprétation", "Ελληνικά",
                       "English original commentary", "Deuxième section"):
            self.assertNotIn(phrase,encoded)
        self.assertEqual(
            source_commentary_shared_key_retrieval_map(self.groups,self.native),
            result)

    def test_missing_real_native_source_entry_blocks_navigation_proof(self):
        with self.assertRaisesRegex(ValueError,"no real native first key"):
            source_commentary_shared_key_retrieval_map(
                self.groups,self.native-{"Rom.4.9"})

    def test_duplicate_or_invalid_origins_are_rejected(self):
        for invalid in (
            self.groups+[deepcopy(self.groups[0])],
            [dict(self.groups[0],text="")],
            [dict(self.groups[0],line=0)],
            [dict(self.groups[0],keys=("Rom.4.0",))],
            [dict(self.groups[0],keys=("Rom.4.17-extra",))],
        ):
            with self.subTest(invalid=invalid[-1]),self.assertRaises(ValueError):
                source_commentary_shared_key_retrieval_map(invalid,self.native)

    def test_reviewed_index_keeps_only_real_authored_multiowners(self):
        original=source_commentary_shared_key_retrieval_map(
            self.groups,self.native)
        revised=deepcopy(self.groups)
        revised[0]["keys"]=tuple(f"Rom.4.{v}" for v in range(9,17))
        revised[0]["sID"]="Rom.4.9-16"
        candidate=source_commentary_shared_key_retrieval_map(revised,self.native)
        self.assertEqual(candidate["original_shared_verse_keys"],1)
        pin="a"*64
        plan={
            "schema_version":1,
            "status":"RESEARCH_ONLY_PRIVATE_SCOPE_REVIEW",
            "original_authoring_osis_sha256":pin,
            "retain_original_overlaps":[{
                "bible_verse_key":"Rom.4.17",
                "evidence_url":"https://example.org/independent-half-verse-index",
            }],
        }
        result=source_commentary_reviewed_shared_key_plan(
            original,candidate,plan,pinned_original_sha256=pin)
        self.assertEqual(result["original_syntactic_shared_verses"],2)
        self.assertEqual(result["compiled_source_shared_verses"],1)
        self.assertEqual(result["retained_original_intra_verse_boundaries"],1)
        self.assertEqual(result["reader_multiowner_verse_count"],2)
        self.assertEqual(result["non_reader_shared_source_index_ranges"],0)
        members={v["bible_verse_key"]:v for v in
                 result["reader_multiowner_verses"]}
        self.assertEqual(members["Rom.4.17"]["native_retrieval_keys_in_authorial_order"],
                         ["Rom.4.9","Rom.4.17"])
        self.assertEqual(members["2Chr.1.1"]["native_retrieval_keys_in_authorial_order"],
                         ["2Chr.1.1"])
        self.assertEqual(members["2Chr.1.1"]["ownership_basis"],
                         "PRESENT_IN_COMPILED_SOURCE_MULTIOWNER")
        for invalid in (
            dict(plan,retain_original_overlaps=[
                {"bible_verse_key":"Rom.4.18","evidence_url":"https://a.org"}]),
            dict(plan,retain_original_overlaps=[
                {"bible_verse_key":"2Chr.1.1","evidence_url":"https://a.org"}]),
            dict(plan,original_authoring_osis_sha256="b"*64),
            dict(plan,retain_original_overlaps=[
                plan["retain_original_overlaps"][0],
                plan["retain_original_overlaps"][0]]),
        ):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                source_commentary_reviewed_shared_key_plan(
                    original,candidate,invalid,pinned_original_sha256=pin)
        self.assertNotIn("L'interprétation",json.dumps(result))

    def test_nonoverlapping_source_has_no_synthetic_shared_verse(self):
        a=[self.groups[0],dict(self.groups[1],keys=("Rom.4.18",),
                                sID="Rom.4.18",line=25)]
        result=source_commentary_shared_key_retrieval_map(
            a,self.native|{"Rom.4.18"})
        self.assertEqual(result["original_shared_verse_keys"],0)
        self.assertEqual(result["shared_verses"],[])


if __name__=="__main__":
    unittest.main()
