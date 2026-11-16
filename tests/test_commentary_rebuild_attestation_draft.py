"""Invented-only tests of private, text-free native rebuild attestation."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_rebuild_attestation_draft import private_rebuild_attestation_draft
from compiled_stock_commentary_proof import SUFFIXES
from reviewed_compiled_commentary_rebuild import reviewed_rebuilt_commentary_errors


def sha(raw):
    return sha256(raw).hexdigest()


def receipt(data, digest):
    return {
        "status": "actual_full_native_raw_corpus_hashed_not_source_parity_approved",
        "actual_occupied_numbered_entry_count": len(data["K"]),
        "actual_occupied_intro_entry_count": len(data["I"]),
        "actual_occupied_anonymous_top_entry_count": len(data["U"]),
        "all_native_raw_entries_ordered_sha256": digest,
    }


class PrivateNativeRebuildDraftTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.original_name = "config/commentary-intake/invented.json"
        self.original_path = self.root / self.original_name
        self.original_path.parent.mkdir(parents=True)
        self.original_path.write_text(json.dumps({
            "category": "commentary", "archive_sha256": "a"*64,
            "native_raw_corpus_sha256": "b"*64,
            "stock_conf_sha256": "c"*64,
            "module_id": "Invented", "version": "2.0",
            "provider": "synthetic",
            "source_page_url": "https://example.org/source",
        }))
        self.old = b"<p>Invented source name Dn</p>"
        self.new = b"<p>Invented source name Dan</p>"
        self.control = b"<p>Entirely independent invented section</p>"
        self.source = {
            "Gen.1": [("Gen.1.1", self.old), ("Gen.1.2", self.old),
                      ("Gen.1.3", self.control)]
        }
        self.intros = {"Gen": b"<title>Book</title>", "Gen.1": b""}
        self.opaque = [b"<head>top</head>"]
        self.index = {
            "K": {"Gen.1.1": self.old, "Gen.1.2": self.old,
                  "Gen.1.3": self.control, "Gen.1.4": self.old},
            "I": self.intros.copy(), "U": self.opaque.copy()
        }
        self.revised = {
            "K": {"Gen.1.1": self.new, "Gen.1.2": self.new,
                  "Gen.1.3": self.control, "Gen.1.4": self.new},
            "I": self.intros.copy(), "U": self.opaque.copy()
        }
        self.payload = self.root / "installed"
        self.payload_data = {
            "mods.d/brdemo.conf": b"[BRDemo]\nVersion=0.1.1\n",
            **{
                "modules/comments/zcom/brdemo/"+name: b"Test member "+name.encode()
                for name in SUFFIXES
            },
        }
        for rel, content in self.payload_data.items():
            path = self.payload / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.args = {
            "repo_root": self.root,
            "original_manifest": self.original_name,
            "module_id": "BRDemo", "version": "0.1.1",
            "versification": "KJV",
            "original_native_corpus_sha256": "b"*64,
            "original_source_numbered": self.source,
            "original_source_intros": self.intros,
            "original_source_top": self.opaque,
            "original_index_compiled": self.index,
            "revised_compiled": self.revised,
            "installed_compiled": self.revised,
            "index_receipt": receipt(self.index, "d"*64),
            "revised_receipt": receipt(self.revised, "e"*64),
            "installed_receipt": receipt(self.revised, "e"*64),
            "source_edit_receipts": [{
                "original_native_entry": "Gen.1.1",
                "original_raw_sha256": sha(self.old),
                "proposed_raw_sha256": sha(self.new),
                "reverse_restores_exact_original_raw_bytes": True,
            }],
            "source_edit_affected_keys": [["Gen.1.1", "Gen.1.2"]],
            "corrected_source_by_original_key": {
                "Gen.1.1": self.new, "Gen.1.2": self.new
            },
            "aliases": {"Gen.1.4": {
                "link_to": "Gen.1.1",
                "source_raw_sha256": sha(self.old),
            }},
            "installed_candidate_root": self.payload,
            "existing_links_preserved": True,
            "full_source_semantic_and_structure_parity_verified": True,
            "all_new_native_aliases_linked": True,
            "real_reader_passage_matches": 3,
        }

    def build(self, **changes):
        return private_rebuild_attestation_draft(**{**self.args, **changes})

    def test_evidence_from_exact_private_native_maps_is_draft_only(self):
        got = self.build()
        self.assertEqual(got["status"], "PRIVATE_REAL_NATIVE_ATTESTATION_DRAFT_NOT_RELEASE")
        self.assertFalse(got["release_authorized"])
        self.assertFalse(got["data_text_exported"])
        self.assertEqual(got["original_native_K_count"], 3)
        self.assertEqual(got["original_K_keys_edited"], 2)
        self.assertEqual(got["added_native_K_count"], 1)
        a = got["source_audit"]
        self.assertEqual(a["index_only_rebuild_native_corpus_sha256"], "d"*64)
        self.assertEqual(a["candidate_native_corpus_sha256"], "e"*64)
        self.assertEqual(a["source_edits"][0]["affected_original_keys"],
                         ["Gen.1.1", "Gen.1.2"])
        self.assertEqual(got["review_manifest"]["status"],
                         "private_draft_not_owner_authorized_for_release")
        self.assertEqual(got["source_validation"]["status"],
                         "private_draft_not_release_validated")
        self.assertEqual(got["source_audit_sha256"],
                         sha((json.dumps(a, sort_keys=True, indent=2)+"\n").encode()))
        self.assertNotIn("Invented source name", str(got))
        self.assertNotIn("<p>", str(got))

    def test_private_draft_cannot_pass_production_owner_release_gate(self):
        got = self.build()
        mod = self.root / "modules/invented"
        mod.mkdir(parents=True)
        (mod/"SOURCE_AUDIT.json").write_text(
            json.dumps(got["source_audit"], sort_keys=True, indent=2)+"\n"
        )
        (mod/"SOURCE_VALIDATION.json").write_text(
            json.dumps(got["source_validation"]))
        review = self.root / "config/commentary-rebuilds/invented.json"
        review.parent.mkdir(parents=True)
        review.write_text(json.dumps(got["review_manifest"]))
        meta = {
            "id": "invented", "sword_id": "BRDemo", "category": "commentary",
            "version": "0.1.1", "versification": "KJV",
            "origin": {"url": "https://example.org/source"},
            "rights": {"license": "Public Domain", "redistribution_allowed": True,
                       "derivatives_allowed": True},
            "quality": {"status": "approved"},
            "upstreams": [{"module_id": "Invented", "provider": "synthetic",
                           "last_integrated_version": "2.0",
                           "last_integrated_conf_sha256": "c"*64}],
            "index_audit": {"mode": "reviewed_compiled_commentary_rebuild",
                            "manifest": "config/commentary-rebuilds/invented.json"},
        }
        conf = {
            "ModDrv": "zCom", "SourceType": "OSIS", "Versification": "KJV",
            "Version": "0.1.1", "DistributionLicense": "Public Domain",
            "BlockType": "CHAPTER",
        }
        errors = reviewed_rebuilt_commentary_errors(mod, self.root, meta, conf)
        self.assertTrue(errors)
        self.assertIn("Original, version or source-audit identity differs", str(errors))
        got["review_manifest"]["status"] = "owner_authorized_for_release"
        review.write_text(json.dumps(got["review_manifest"]))
        errors = reviewed_rebuilt_commentary_errors(mod, self.root, meta, conf)
        self.assertIn("owner review unavailable", str(errors))

    def test_wrong_original_source_or_pinned_bytes_fails_closed(self):
        for change in (
            {"original_native_corpus_sha256": "f"*64},
            {"original_manifest": "../invented.json"},
            {"original_source_numbered": {"Gen.1": [("Gen.1.1", self.old)]}},
        ):
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError):
                    self.build(**change)

    def test_any_unreviewed_native_content_or_missing_intro_fails(self):
        extras = {
            "K": {**self.revised["K"], "Gen.1.3": b"unreviewed words"},
            "I": self.revised["I"], "U": self.revised["U"]
        }
        with self.assertRaises(ValueError):
            self.build(revised_compiled=extras, installed_compiled=extras)
        no_intro = {**self.revised, "I": {"Gen": b"changed"}}
        with self.assertRaises(ValueError):
            self.build(revised_compiled=no_intro, installed_compiled=no_intro)
        with self.assertRaises(ValueError):
            self.build(existing_links_preserved=False)

    def test_wrong_source_fingerprint_or_alias_claim_rejected(self):
        edited = {"Gen.1.1": self.new, "Gen.1.2": self.old}
        with self.assertRaises(ValueError):
            self.build(corrected_source_by_original_key=edited)
        with self.assertRaises(ValueError):
            self.build(aliases={"Gen.1.4": {
                "link_to": "Gen.1.3",
                "source_raw_sha256": sha(self.old),
            }})
        with self.assertRaises(ValueError):
            self.build(source_edit_affected_keys=[["Gen.1.1"]])

    def test_native_streams_and_exact_installed_files_must_match(self):
        with self.assertRaises(ValueError):
            self.build(installed_receipt=receipt(self.revised, "f"*64))
        with self.assertRaises(ValueError):
            self.build(revised_receipt=receipt(self.index, "e"*64))
        path = self.payload / "modules/comments/zcom/brdemo/nt.bzz"
        path.unlink()
        with self.assertRaises(ValueError):
            self.build()

    def test_reader_or_semantic_proof_cannot_be_skipped(self):
        for change in (
            {"real_reader_passage_matches": 0},
            {"full_source_semantic_and_structure_parity_verified": False},
            {"all_new_native_aliases_linked": False},
        ):
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError):
                    self.build(**change)


if __name__ == "__main__":
    unittest.main()
