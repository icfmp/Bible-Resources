"""Invented-only, offline regression guards for rebuilt SWORD commentary proofs.

The fixture is not a real content/rights approval and never resembles an
actual CrossWire resource or a production authorization.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reviewed_compiled_commentary_rebuild import reviewed_rebuilt_commentary_errors
from reviewed_compiled_commentary_rebuild import zcom_member_suffixes
from jsonschema import Draft202012Validator


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


class RebuiltCommentaryContractTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.module = self.root / "modules/synthetic"
        self.payload = self.module / "payload"
        self.module.mkdir(parents=True)
        self.original_name = "config/commentary-intake/synthetic.json"
        self.review_name = "config/commentary-rebuilds/synthetic.json"
        self.original_path = self.root / self.original_name
        self.review_path = self.root / self.review_name
        self.original_path.parent.mkdir(parents=True)
        self.review_path.parent.mkdir(parents=True)
        self.original = {
            "module_id": "Original", "version": "2.0",
            "provider": "synthetic", "category": "commentary",
            "archive_sha256": "a" * 64,
            "native_raw_corpus_sha256": "b" * 64,
            "stock_conf_sha256": "c" * 64,
            "source_page_url": "https://example.org/source",
        }
        self.original_path.write_text(json.dumps(self.original))
        self.meta = {
            "id": "synthetic", "sword_id": "Synth", "category": "commentary",
            "version": "0.1.1", "versification": "KJV",
            "origin": {"url": "https://example.org/source"},
            "upstreams": [{"module_id": "Original", "provider": "synthetic",
                           "last_integrated_version": "2.0",
                           "last_integrated_conf_sha256": "c" * 64}],
            "rights": {"license": "Public Domain", "redistribution_allowed": True,
                       "derivatives_allowed": True},
            "quality": {"status": "approved"},
            "index_audit": {"mode": "reviewed_compiled_commentary_rebuild",
                            "manifest": self.review_name},
        }
        self.conf = {
            "ModDrv": "zCom", "BlockType": "CHAPTER",
            "SourceType": "OSIS", "Versification": "KJV",
            "Version": "0.1.1", "DistributionLicense": "Public Domain",
        }
        file_data = {
            "mods.d/synth.conf": b"[Synth]\nVersion=0.1.1\n",
            **{
                "modules/comments/zcom/synth/" + name:
                    b"Invented compiled test member: " + name.encode("ascii")
                for name in zcom_member_suffixes("CHAPTER")
            },
        }
        for path, raw in file_data.items():
            target = self.payload / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        self.review = {
            "schema_version": 1, "status": "owner_authorized_for_release",
            "module_id": "synthetic", "sword_id": "Synth",
            "version": "0.1.1", "versification": "KJV",
            "original_manifest": self.original_name,
            "original_manifest_sha256": digest(self.original_path.read_bytes()),
            "original_archive_sha256": "a" * 64,
            "original_native_corpus_sha256": "b" * 64,
            "original_module_id": "Original",
            "candidate_native_corpus_sha256": "d" * 64,
            "original_native_counts": {"K": 3, "I": 2, "TOP": 1},
            "candidate_native_counts": {"K": 4, "I": 2, "TOP": 1},
            "source_edits": [{
                "master_key": "Gen.1.1", "original_sha256": "e" * 64,
                "revised_sha256": "f" * 64,
                "affected_original_keys": ["Gen.1.1", "Gen.1.2"],
            }],
            "added_links": [{"new_key": "Gen.1.4", "master_key": "Gen.1.1"}],
            "block_type": "CHAPTER",
            "payload_sha256": {path: digest(raw) for path, raw in file_data.items()},
            "authorization": {
                "approved_by": "Bible Resources project owner",
                "scope": "Synthetic fixture for strict release contract only",
                "evidence_url": "https://github.com/example/example/issues/123",
            },
        }
        self.audit = {
            "schema_version": 1,
            "status": "complete_native_rebuild_comparison",
            "source_kind": "reviewed_compiled_commentary_rebuild",
            "original_archive_sha256": self.review["original_archive_sha256"],
            "original_native_corpus_sha256":
                self.review["original_native_corpus_sha256"],
            "candidate_native_corpus_sha256":
                self.review["candidate_native_corpus_sha256"],
            "original_native_counts": self.review["original_native_counts"],
            "candidate_native_counts": self.review["candidate_native_counts"],
            "source_edits": self.review["source_edits"],
            "added_links": self.review["added_links"],
            "versification": "KJV", "compiler": "osis2mod", "reader": "libSWORD",
            "full_original_and_rebuilt_native_inventory_compared": True,
            "all_other_original_K_bytes_identical": True,
            "all_original_I_bytes_identical": True,
            "all_original_TOP_bytes_identical": True,
            "all_original_linked_section_boundaries_preserved": True,
            "all_added_K_keys_link_to_reviewed_original_master": True,
            "all_edited_source_structure_and_unedited_content_preserved": True,
            "no_unreviewed_original_native_keys_changed": True,
            "no_source_prose_exported": True,
        }
        self.proof = {
            "schema_version": 1, "status": "validated",
            "source_kind": "reviewed_compiled_commentary_rebuild",
            "review_manifest": self.review_name,
            "original_archive_sha256": "a" * 64,
            "candidate_native_corpus_sha256": "d" * 64,
            "curated_module_id": "Synth", "curated_version": "0.1.1",
        }
        self.write()

    def write(self):
        audit_data = json.dumps(self.audit).encode()
        audit_digest = digest(audit_data)
        (self.module / "SOURCE_AUDIT.json").write_bytes(audit_data)
        self.review["source_audit_sha256"] = audit_digest
        self.review_path.write_text(json.dumps(self.review))
        self.proof["source_audit_sha256"] = audit_digest
        (self.module / "SOURCE_VALIDATION.json").write_text(json.dumps(self.proof))

    def errors(self):
        return reviewed_rebuilt_commentary_errors(
            self.module, self.root, self.meta, self.conf)

    def test_members_follow_real_sword_block_granularity(self):
        self.assertEqual(zcom_member_suffixes("BOOK"),
                         ("nt.bzs", "nt.bzv", "nt.bzz", "ot.bzs", "ot.bzv", "ot.bzz"))
        self.assertEqual(zcom_member_suffixes("CHAPTER"),
                         ("nt.czs", "nt.czv", "nt.czz", "ot.czs", "ot.czv", "ot.czz"))
        self.assertEqual(zcom_member_suffixes("VERSE"),
                         ("nt.vzs", "nt.vzv", "nt.vzz", "ot.vzs", "ot.vzv", "ot.vzz"))
        with self.assertRaises(ValueError):
            zcom_member_suffixes("WRONG")
        self.assertEqual(self.errors(), [])
        self.conf["BlockType"] = "BOOK"
        self.assertTrue(self.errors())
    def test_exact_attestation_and_payload_pass_synthetic_fixture(self):
        self.assertEqual(self.errors(), [])

    def test_tampered_member_or_extra_member_is_rejected(self):
        p = self.payload / "modules/comments/zcom/synth/nt.czz"
        p.write_bytes(b"tampered")
        self.assertIn("checksum mismatch", str(self.errors()))
        p.write_bytes(b"Invented compiled test member: nt.czz")
        (p.parent / "secret").write_bytes(b"hidden")
        self.assertIn("Added or omitted", str(self.errors()))

    def test_missing_or_changed_original_witness_is_rejected(self):
        self.original["archive_sha256"] = "d" * 64
        self.original_path.write_text(json.dumps(self.original))
        self.assertTrue(self.errors())
        self.original_path.unlink()
        self.assertTrue(self.errors())

    def test_stale_proof_or_audit_is_rejected(self):
        self.audit["all_original_I_bytes_identical"] = False
        self.write()
        self.assertIn("Native comparison", str(self.errors()))
        self.audit["all_original_I_bytes_identical"] = True
        self.write()
        self.proof["source_audit_sha256"] = "0" * 64
        (self.module / "SOURCE_VALIDATION.json").write_text(json.dumps(self.proof))
        self.assertTrue(self.errors())

    def test_source_edits_and_alias_counts_must_reconcile(self):
        self.review["candidate_native_counts"]["K"] = 5
        self.audit["candidate_native_counts"]["K"] = 5
        self.write()
        self.assertIn("do not reconcile", str(self.errors()))
        self.review["candidate_native_counts"]["K"] = 4
        self.audit["candidate_native_counts"]["K"] = 4
        self.review["added_links"][0]["master_key"] = "Gen.1.4"
        self.write()
        self.assertTrue(self.errors())

    def test_unrefereed_new_source_or_original_entry_overlap_fails(self):
        self.review["source_edits"][0]["affected_original_keys"] += ["Gen.1.4"]
        self.write()
        self.assertTrue(self.errors())
        self.review["source_edits"][0]["affected_original_keys"] = [
            "Gen.1.1", "Gen.1.1"
        ]
        self.write()
        self.assertTrue(self.errors())

    def test_owner_approval_and_rebuild_proof_cannot_be_stock_flags(self):
        self.review["authorization"]["approved_by"] = "PENDING"
        self.write()
        self.assertIn("owner review", str(self.errors()))
        self.review["authorization"]["approved_by"] = "Bible Resources project owner"
        self.proof["all_original_compressed_files_byte_identical"] = True
        self.write()
        self.assertIn("impersonate", str(self.errors()))

    def test_wrong_edition_rights_and_source_index_route_rejected(self):
        self.meta["rights"]["derivatives_allowed"] = False
        self.assertIn("rights", str(self.errors()))
        self.meta["rights"]["derivatives_allowed"] = True
        self.meta["index_audit"]["mode"] = "stock_reader_keys"
        self.assertIn("manifest", str(self.errors()))

    def test_unsafe_review_manifest_paths_cannot_switch_source_class(self):
        for name in ("config/../comments.json", "../review.json",
                     "config/commentary-rebuilds/../synthetic.json",
                     "config/commentary-intake/synthetic.json"):
            with self.subTest(name=name):
                self.meta["index_audit"]["manifest"] = name
                self.assertTrue(self.errors())
        self.meta["index_audit"]["manifest"] = self.review_name

    def test_schema_allows_only_reviewed_mode_with_manifest(self):
        schema = json.loads((ROOT / "schemas/module.schema.json").read_text())
        validator = Draft202012Validator(schema)
        full = {
            "schema_version": 1, "id": "synthetic", "sword_id": "Synth",
            "title": {"en": "Synthetic test"}, "category": "commentary",
            "language": "en", "version": "0.1.1",
            "versification": "KJV",
            "origin": {"publisher": "Independent", "url": "https://example.org/source",
                       "source_revision": "Synthetic"},
            "rights": {"license": "Public Domain",
                       "evidence_url": "https://example.org/rights",
                       "redistribution_allowed": True,
                       "derivatives_allowed": True, "reviewed_by": "Editor"},
            "quality": {"status": "approved", "edition": "faithful",
                        "reviewed_by": "Editor", "smoke_key": "Gen 1:1"},
            "canonical_edition_id": "synthetic-collection",
            "index_audit": {"mode": "reviewed_compiled_commentary_rebuild",
                            "manifest": self.review_name},
        }
        self.assertFalse(list(validator.iter_errors(full)))
        del full["index_audit"]["manifest"]
        self.assertTrue(list(validator.iter_errors(full)))
