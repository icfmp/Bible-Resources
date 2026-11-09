"""Generic, source-bound reviewed-merge publication gate fixtures.

Synthetic data only. These checks verify evidence requirements, not that
any specific Bible's binary has passed external editorial validation.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from stable_sword_refs import (parse_keys,parse_registry,inspect_references,
    proof_errors,module_payload_digest,load_approved_merge_policy)

class ReviewedStockSwordMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.module=Path(self.tmp.name)/"synthetic"
        data=self.module/"payload/mods.d"
        data.mkdir(parents=True)
        (data/"synthetic.conf").write_text("[Synthetic]\nVersification=Segond\n")
        self.source=parse_keys("Mark.1.1\nMark.1.2\nMark.1.3")
        self.reader=parse_keys("Mark.1.1\nMark.1.2")
        self.registry=parse_registry("Segond\tMark\t1\t2\nNRSV\tMark\t1\t3","Segond")
        self.merge=[("Mark.1.3","Mark.1.2")]
        self.publisher_digest="c"*64
        self.policy={
            "schema_version":1,"source_document_sha256":self.publisher_digest,
            "versification":"Segond",
            "policy":"approved_explicit_temporary_adjacent_verse_index_merge",
            "authorization":{"who":"Bible Resources project owner","date":"2026-11-08",
                             "record":"reviewed synthetic fixture"},
            "allowed_merges":[{
                "osis_source_key":"Mark.1.3","osis_reader_key":"Mark.1.2",
                "source_content_preserved":True,"independent_reference_access_lost":True,
                "reversible":True,
                "status":"temporarily_authorized_versification_compromise"
            }]
        }
        self.policy_path=self.module/"SOURCE_REFERENCE_MERGES.json"
        self.save_policy()
    def save_policy(self):
        self.policy_path.write_text(json.dumps(self.policy),encoding="utf-8")
    def report(self, **overrides):
        base=inspect_references(self.source,self.reader,self.registry,self.merge)
        base.update({
            "versification":"Segond",
            "reader_engine":"libsword",
            "reader_version":"1.9.0",
            "engine_release":"stable",
            "registry_source":"installed_sword_versification_mgr",
            "source_osis_sha256":"a"*64,
            "module_payload_sha256":module_payload_digest(self.module),
            "reviewed_by":"independent reviewer",
            "original_publisher_document_sha256":self.publisher_digest,
            "reviewed_merge_policy_sha256":hashlib.sha256(
                self.policy_path.read_bytes()).hexdigest(),
            "full_source_chapter_character_streams_verified":True,
            "full_readback_chapter_count":1,
            "full_readback_evidence_sha256":"f"*64,
        })
        base.update(overrides)
        (self.module/"SWORD_COMPATIBILITY.json").write_text(json.dumps(base))
        return base
    def test_adjacent_trailing_reviewed_merger_preserves_explicit_status(self):
        review=inspect_references(self.source,self.reader,self.registry,self.merge)
        self.assertEqual(review["status"],"stable_reference_index_verified_with_reviewed_merges")
        self.assertFalse(review["exact_reference_key_parity"])
        self.assertTrue(review["reviewed_index_compromise_verified"])
        self.assertEqual(review["reviewed_merge_count"],1)
        self.assertEqual(review["source_references_unreachable_count"],1)
    def test_no_waiver_of_source_body_validation(self):
        self.report()
        self.assertEqual(proof_errors(self.module,"Segond","a"*64),[])
        self.report(full_source_chapter_character_streams_verified=False)
        self.assertTrue(proof_errors(self.module,"Segond","a"*64))
        self.report(full_readback_evidence_sha256="")
        self.assertTrue(proof_errors(self.module,"Segond","a"*64))
    def test_module_policy_bound_to_publisher_source_and_exact_payload(self):
        self.report()
        self.assertTrue(proof_errors(self.module,"Segond","b"*64))
        self.policy["allowed_merges"][0]["osis_source_key"]="Mark.1.9"
        self.save_policy()
        self.assertTrue(proof_errors(self.module,"Segond","a"*64))
        self.save_policy()
        (self.module/"payload/mods.d/synthetic.conf").write_text(
            "[Synthetic]\nVersification=Different\n")
        self.assertTrue(proof_errors(self.module,"Segond","a"*64))
    def test_unapproved_source_only_merger_stays_blocked(self):
        result=inspect_references(self.source,self.reader,self.registry)
        self.assertEqual(result["status"],"blocked")
        for source,dest in [
            ("Mark.1.3","Mark.1.1"),
            ("Mark.1.2","Mark.1.1"),
            ("Mark.1.9","Mark.1.2"),
        ]:
            with self.subTest(source=source,dest=dest),self.assertRaises(ValueError):
                inspect_references(self.source,self.reader,self.registry,
                                   [(source,dest)])
    def test_exact_registry_unchanged_behavior(self):
        result=inspect_references(self.reader,self.reader,self.registry)
        self.assertEqual(result["status"],"stable_reference_index_verified")
        self.assertEqual(result["reviewed_merge_count"],0)
        self.assertFalse(result["reviewed_index_compromise_verified"])
    def test_manifest_must_match_publisher_source(self):
        refs,proof=load_approved_merge_policy(
            self.policy_path,publisher_digest=self.publisher_digest,versification="Segond")
        self.assertEqual(refs,self.merge)
        self.assertEqual(proof,hashlib.sha256(self.policy_path.read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            load_approved_merge_policy(self.policy_path,publisher_digest="d"*64,
                                       versification="Segond")

if __name__=="__main__":
    unittest.main()
