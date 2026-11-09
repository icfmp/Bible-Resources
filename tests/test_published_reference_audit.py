"""Generic regression checks for previously published source-to-SWORD audit proofs.

No copyrighted Bible text and no special-cased LSG reference is used in the
synthetic fixtures. A real checked-in release is also independently checked.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from published_reference_audit import archived_release_errors


def sha(data):
    return hashlib.sha256(data).hexdigest()


class HistoricalIndexProofTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.module = self.root / "modules/synthetic"
        self.module.mkdir(parents=True)
        self.metadata = {
            "sword_id": "Synthetic",
            "versification": "SyntheticV11n",
            "quality": {"status": "approved"},
        }
        self.source_sha = "a" * 64
        self.pub_sha = "b" * 64
        self.source_ref = "Alpha.2.3"
        self.reader_ref = "Alpha.2.2"
        self.original_ref = "ALP.2.3"
        self.original_dst = "ALP.2.2"
        self.policy = {
            "schema_version": 1,
            "source_document_sha256": self.pub_sha,
            "versification": "SyntheticV11n",
            "policy": "approved_explicit_temporary_adjacent_verse_index_merge",
            "authorization": {"who": "Bible Resources project owner",
                              "date": "2026-11-09", "record": "Synthetic test"},
            "allowed_merges": [{
                "authorial_source_key": self.original_ref,
                "reader_source_key": self.original_dst,
                "osis_source_key": self.source_ref,
                "osis_reader_key": self.reader_ref,
                "source_content_preserved": True,
                "independent_reference_access_lost": True,
                "reversible": True,
                "status": "temporarily_authorized_versification_compromise",
            }],
        }
        self.audit = {
            "versification": "SyntheticV11n",
            "experimental_runtime_needed": False,
            "original_usfm_archive_sha256": "c" * 64,
            "original_usfx_archive_sha256": "d" * 64,
            "original_usfx_sha256": self.pub_sha,
            "stock_sword_compiled_candidate": {"full_source_verse_roundtrip": {
                "total_source_verse_keys": 4,
                "expected_chapters": 2,
                "books": [{"book": "ALP", "chapters": 1, "source_verses": 3},
                          {"book": "BET", "chapters": 1, "source_verses": 1}],
                "totals": {"chapters": 2, "source_verses": 4,
                           "source_keys_missing": 1, "sword_keys_unexpected": 1},
                "unmatched_verse_slot_classification": [
                    {"book": "ALP", "chapter": 2,
                     "source_only_verses": [3], "reader_only_verses": [],
                     "complete_chapter_character_stream_equal_ignoring_whitespace": True,
                     "diagnostic_slot_classes": [{
                         "side": "source_only", "verse": 3,
                         "classification": "readback_preceding_slot_contains_both_verse_character_streams",
                         "preceding_slot_compared": True, "no_reversification_applied": True}]},
                    {"book": "BET", "chapter": 1, "source_only_verses": [],
                     "reader_only_verses": [4],
                     "complete_chapter_character_stream_equal_ignoring_whitespace": True,
                     "diagnostic_slot_classes": [{
                         "side": "reader_only", "verse": 4,
                         "classification": "empty_readback_verse_slot",
                         "no_reversification_applied": True}]}
                ]}},
            "stock_sword_reference_assessment": {
                "source_verse_count": 4, "engine": "stock_released_sword",
                "compiler_versification": "SyntheticV11n",
                "all_reference_differences_explained": True,
                "all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks": True,
                "original_source_modified": False, "unclassified_verse_keys": [],
                "source_only_verse_count": 1, "unoccupied_compiled_verse_count": 1,
                "appended_source_keys": [{
                    "book": "ALP", "chapter": 2, "source_verse": 3,
                    "compiled_verse": 2, "distinct_original_reference_unavailable": True}]},
            "authorized_editorial_index_compromise": {
                "status": "source_bound_owner_authorized_index_compromise",
                "observed_source_to_reader_keys_exactly_match_authorization": True,
                "source_scripture_modified": False, "authorized_merge_count": 1,
                "reviewed_merges": [{
                    "authorial_source_key": self.original_ref,
                    "reader_source_key": self.original_dst,
                    "osis_source_key": self.source_ref,
                    "osis_reader_key": self.reader_ref,
                    "source_verse_content_preserved": True
                }],
            },
            "xiphos_test_preview_package": {
                "status": "private_stock_sword_zip_reinstall_readback_verified",
                "text_payload_files_byte_identical_to_verified_module": True,
                "publisher_original_usfx_sha256": self.pub_sha
            },
        }
        self.write_fixture()

    def write_fixture(self):
        policy_path = self.module / "SOURCE_REFERENCE_MERGES.json"
        policy_path.write_text(json.dumps(self.policy), encoding="utf-8")
        self.audit["authorized_editorial_index_compromise"]["policy_sha256"] = sha(policy_path.read_bytes())
        raw_audit = json.dumps(self.audit, ensure_ascii=False).encode("utf-8")
        (self.module / "SOURCE_AUDIT.json").write_bytes(raw_audit)
        (self.module / "SOURCE_VALIDATION.json").write_text(json.dumps({
            "source_sha256": self.source_sha,
            "provenance_audit_sha256": sha(raw_audit)}))
        payload = self.module / "payload"
        (payload / "mods.d").mkdir(parents=True, exist_ok=True)
        (payload / "modules").mkdir(exist_ok=True)
        (payload / "mods.d/synthetic.conf").write_text("[Synthetic]\n")
        (payload / "modules/data").write_bytes(b"not a real Bible; synthetic fixture")
        manifest = {
            "release_audit_sha256": sha(raw_audit),
            "release_zip_sha256": "f" * 64,
            "module_id": self.metadata["sword_id"],
            "metadata_path": "modules/synthetic/metadata.json",
            "editorial_approval": {"approved_by": "Bible Resources project owner"},
            "provenance": {"final_candidate_osis_sha256": self.source_sha},
            "source_usfm_zip_sha256": "c" * 64,
            "source_usfx_zip_sha256": "d" * 64,
            "files": {
                p.relative_to(payload).as_posix(): sha(p.read_bytes())
                for p in payload.rglob("*") if p.is_file()
            },
        }
        (self.root / "config").mkdir(exist_ok=True)
        (self.root / "config/release.json").write_text(json.dumps(manifest))

    def errors(self):
        return archived_release_errors(
            self.module, self.root, "config/release.json",
            self.metadata, self.source_sha)

    def test_valid_synthetic_approved_adjacent_merge(self):
        self.assertEqual(self.errors(), [])

    def test_corruption_of_published_payload_fails(self):
        (self.module / "payload/modules/data").write_bytes(b"altered")
        self.assertTrue(self.errors())

    def test_corruption_of_source_audit_fails(self):
        self.audit["stock_sword_reference_assessment"]["source_only_verse_count"] = 0
        (self.module / "SOURCE_AUDIT.json").write_text(json.dumps(self.audit))
        self.assertTrue(self.errors())

    def test_tampered_policy_fails_against_original_audit(self):
        self.policy["allowed_merges"][0]["osis_reader_key"] = "Alpha.2.1"
        (self.module / "SOURCE_REFERENCE_MERGES.json").write_text(json.dumps(self.policy))
        self.assertTrue(self.errors())

    def test_missing_note_of_editorial_index_merge_fails(self):
        (self.module / "SOURCE_REFERENCE_MERGES.json").unlink()
        self.assertTrue(self.errors())

    def test_stale_source_sha_fails(self):
        self.assertTrue(archived_release_errors(
            self.module, self.root, "config/release.json",
            self.metadata, "9" * 64))

    def test_parent_path_and_unpinned_manifest_rejected(self):
        self.assertTrue(archived_release_errors(
            self.module, self.root, "../outside.json",
            self.metadata, self.source_sha))

    def test_reclassified_reader_slot_fails_even_if_audit_rehashed(self):
        self.audit["stock_sword_compiled_candidate"]["full_source_verse_roundtrip"][
            "unmatched_verse_slot_classification"][0]["diagnostic_slot_classes"][0][
            "preceding_slot_compared"] = False
        self.write_fixture()
        self.assertTrue(self.errors())

    def test_real_published_module_attestation(self):
        module = ROOT / "modules/lsg-1910"
        if not module.is_dir():
            self.skipTest("Repository has not published an audited module")
        metadata = json.loads((module / "metadata.json").read_text())
        source = json.loads((module / "SOURCE_VALIDATION.json").read_text())
        self.assertEqual(archived_release_errors(
            module, ROOT, metadata["index_audit"]["manifest"],
            metadata, source["source_sha256"]), [])


if __name__ == "__main__":
    unittest.main()
