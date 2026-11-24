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
from reviewed_compiled_commentary_rebuild import (
    zcom_member_suffixes, zcom_payload_paths, checked_zcom_payload_files,
    commentary_payload_paths, checked_commentary_payload_files,
)
from jsonschema import Draft202012Validator


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


class NativeZcomPayloadPathTests(unittest.TestCase):
    def test_native_compression_modes_use_exact_seven_safe_paths(self):
        for mode, infix in (("BOOK", "bz"), ("CHAPTER", "cz"), ("VERSE", "vz")):
            with self.subTest(mode=mode):
                paths = zcom_payload_paths("Review2026", mode)
                self.assertEqual(len(paths), 7)
                self.assertIn("mods.d/review2026.conf", paths)
                self.assertEqual(
                    paths - {"mods.d/review2026.conf"},
                    {"modules/comments/zcom/review2026/" + part + "." + infix + suffix
                     for part in ("nt", "ot") for suffix in ("s", "v", "z")},
                )

    def test_exact_inventory_rejects_extra_missing_and_symlinked_files(self):
        with TemporaryDirectory() as tmp:
            payload = Path(tmp) / "payload"
            names = zcom_payload_paths("Fixture", "CHAPTER")
            for name in names:
                p = payload / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"non-Scripture test data")
            actual = checked_zcom_payload_files(payload, "Fixture", "CHAPTER")
            self.assertEqual(set(actual), names)
            extra = payload / "extra.txt"
            extra.write_bytes(b"unreviewed")
            with self.assertRaisesRegex(ValueError, "inventory"):
                checked_zcom_payload_files(payload, "Fixture", "CHAPTER")
            extra.unlink()
            missing = payload / "modules/comments/zcom/fixture/ot.czz"
            missing.unlink()
            with self.assertRaisesRegex(ValueError, "Added or omitted"):
                checked_zcom_payload_files(payload, "Fixture", "CHAPTER")
            missing.write_bytes(b"restored synthetic data")
            alias = payload / "alias"
            alias.symlink_to(payload / "mods.d/fixture.conf")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                checked_zcom_payload_files(payload, "Fixture", "CHAPTER")
            alias.unlink()
            other = Path(tmp) / "alias-dir"
            other.symlink_to(payload, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "unsafe"):
                checked_zcom_payload_files(other, "Fixture", "CHAPTER")

    def test_native_zcom4_layout_and_exact_inventory_are_fail_closed(self):
        for mode, ext in (("BOOK", "bz"), ("CHAPTER", "cz"), ("VERSE", "vz")):
            with self.subTest(mode=mode), TemporaryDirectory() as tmp:
                payload = Path(tmp) / "payload"
                names = commentary_payload_paths("Attested", mode, "zCom4")
                self.assertEqual(len(names), 7)
                self.assertIn("mods.d/attested.conf", names)
                self.assertEqual(
                    names - {"mods.d/attested.conf"},
                    {"modules/comments/zcom4/attested/" + part + "." + ext + suffix
                     for part in ("nt", "ot") for suffix in ("s", "v", "z")},
                )
                for name in names:
                    file = payload / name
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_bytes(b"synthetic native member")
                self.assertEqual(
                    set(checked_commentary_payload_files(
                        payload, "Attested", mode, "zCom4")), names)
                unexpected = payload / "extra.bin"
                unexpected.write_bytes(b"unapproved")
                with self.assertRaisesRegex(ValueError, "inventory"):
                    checked_commentary_payload_files(payload, "Attested", mode, "zCom4")
                unexpected.unlink()
                alias = payload / "unexpected-symlink"
                alias.symlink_to(payload / "mods.d/attested.conf")
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    checked_commentary_payload_files(payload, "Attested", mode, "zCom4")

    def test_unsafe_native_driver_is_not_inferred_from_an_unknown_name(self):
        for driver in ("", "zcom", "zCom5", "../zCom", None):
            with self.subTest(driver=driver), self.assertRaises(ValueError):
                commentary_payload_paths("Attested", "CHAPTER", driver)

    def test_module_path_or_unknown_block_mode_is_rejected(self):
        for bad in ("../outside", "/absolute", "", "with-hyphen", "ab/../../x"):
            with self.subTest(module=bad), self.assertRaises(ValueError):
                zcom_payload_paths(bad, "CHAPTER")
        for bad in ("", "chapter", "OTHER", None):
            with self.subTest(mode=bad), self.assertRaises(ValueError):
                zcom_payload_paths("Review2026", bad)


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
            "index_only_rebuild_native_corpus_sha256": "9" * 64,
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
            "index_only_rebuild_native_corpus_sha256":
                self.review["index_only_rebuild_native_corpus_sha256"],
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

    def test_reviewed_index_only_digest_is_bound_to_real_audit(self):
        self.review["index_only_rebuild_native_corpus_sha256"] = "0" * 64
        self.write()
        self.assertIn("Native comparison", str(self.errors()))
        self.audit["index_only_rebuild_native_corpus_sha256"] = "0" * 64
        self.write()
        self.assertEqual(self.errors(), [])
        self.review["index_only_rebuild_native_corpus_sha256"] = (
            self.review["candidate_native_corpus_sha256"]
        )
        self.audit["index_only_rebuild_native_corpus_sha256"] = (
            self.review["candidate_native_corpus_sha256"]
        )
        self.write()
        self.assertTrue(self.errors())

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

    def incremental_fixture(self):
        """Use two distinct invented source revisions, never real-module exceptions."""
        self.meta["language"] = "en"
        edition = self.root / "sources/cleaned/commentaries/en/synthetic"
        old = edition / "editorial/evidence/release-0.1.1"
        old.mkdir(parents=True)
        (old / "review-manifest.json").write_bytes(self.review_path.read_bytes())
        (old / "SOURCE_AUDIT.json").write_bytes((self.module / "SOURCE_AUDIT.json").read_bytes())
        old_source = b"<osis>original synthetic text</osis>"
        new_source = b"<osis>corrected synthetic text</osis>"
        (old / "CLEANUP_MANIFEST.json").write_text(json.dumps({
            "reconstructed_source_sha256": digest(old_source),
            "source_native_corpus_sha256": self.review["candidate_native_corpus_sha256"],
        }))
        (edition / "synthetic.osis.xml").write_bytes(new_source)
        evdir = edition / "editorial/evidence/release-0.1.2"
        evdir.mkdir()
        evidence = {
            "schema_version": 1, "previous_source_sha256": digest(old_source),
            "candidate_source_sha256": digest(new_source),
            "previous_native_corpus_sha256": self.review["candidate_native_corpus_sha256"],
            "candidate_native_corpus_sha256": "2" * 64,
            "candidate_native_counts": self.review["candidate_native_counts"],
            "payload_sha256": self.review["payload_sha256"],
            "semantic_changed_keys": ["Gen.1.1"], "reference_changed_keys": [],
            "missing_keys": [], "extra_keys": [], "changed_alias_links": [],
            "parse_failures": 0, "brnp_findings": 0,
            "official_osis_schema_validated": True, "native_link_topology_equal": True,
            "opaque_top_bytes_equal": True, "source_reversible": True,
            "source_idempotent_normalization": True, "remaining_source_text_and_markup_equal": True,
            "all_native_entries_compared": True, "reader_checks_passed": True,
        }
        evfile = evdir / "incremental-native-reader.json"
        evfile.write_text(json.dumps(evidence))
        revision = {
            "previous_version": "0.1.1", "previous_review_sha256": digest((old/"review-manifest.json").read_bytes()),
            "previous_cleanup_sha256": digest((old/"CLEANUP_MANIFEST.json").read_bytes()),
            "previous_native_corpus_sha256": evidence["previous_native_corpus_sha256"],
            "previous_source_sha256": digest(old_source), "source_name": "synthetic.osis.xml",
            "candidate_source_sha256": digest(new_source), "evidence_sha256": digest(evfile.read_bytes()),
            "semantic_changed_keys": ["Gen.1.1"], "reference_changed_keys": [],
        }
        self.meta["version"] = self.conf["Version"] = "0.1.2"
        self.review.update(schema_version=2, version="0.1.2",
                           candidate_native_corpus_sha256="2"*64, incremental_revision=revision)
        self.audit.update(schema_version=2, status="complete_native_semantic_rebuild_comparison",
                          candidate_native_corpus_sha256="2"*64, incremental_revision=revision)
        self.audit.pop("all_other_original_K_bytes_identical")
        self.audit.pop("all_original_I_bytes_identical")
        self.proof.update(schema_version=2, curated_version="0.1.2",
                          candidate_native_corpus_sha256="2"*64,
                          candidate_source_sha256=digest(new_source), incremental_evidence_sha256=digest(evfile.read_bytes()))
        self.write()
        return edition, evfile, evidence

    def test_incremental_source_and_native_review_passes(self):
        self.incremental_fixture()
        self.assertEqual(self.errors(), [])

    def test_incremental_source_and_previous_review_are_bound(self):
        edition, _, _ = self.incremental_fixture()
        (edition/"synthetic.osis.xml").write_bytes(b"tampered")
        self.assertIn("Canonical OSIS source checksum mismatch", str(self.errors()))
        (edition/"synthetic.osis.xml").write_bytes(b"<osis>corrected synthetic text</osis>")
        old = edition/"editorial/evidence/release-0.1.1/review-manifest.json"
        old.write_bytes(old.read_bytes()+b" ")
        self.assertIn("Prior immutable review", str(self.errors()))

    def test_incremental_semantic_proof_rejects_false_byte_identity_and_failed_checks(self):
        _, evfile, evidence = self.incremental_fixture()
        self.audit["all_original_I_bytes_identical"] = True
        self.write()
        self.assertIn("must not claim", str(self.errors()))
        self.audit.pop("all_original_I_bytes_identical")
        self.write()
        evidence["reader_checks_passed"] = False
        evfile.write_text(json.dumps(evidence))
        fingerprint = digest(evfile.read_bytes())
        self.review["incremental_revision"]["evidence_sha256"] = fingerprint
        self.audit["incremental_revision"]["evidence_sha256"] = fingerprint
        self.proof["incremental_evidence_sha256"] = fingerprint
        self.write()
        self.assertIn("Incremental native/source/reader proof differs", str(self.errors()))
