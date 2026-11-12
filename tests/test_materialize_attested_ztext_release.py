"""Synthetic fail-closed stable SWORD owner-approval and attestation tests."""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from materialize_attested_ztext_release import verified_approval


def fixtures(blob: bytes):
    approved = json.loads((ROOT / "config/darby-release-authorization.json").read_text())
    audit = {
        "schema_version": 1,
        "status": "repaired_osis_to_native_sword_full_text_notes_research_passed",
        "publisher_original_sha256": approved["original_publisher_osis_sha256"],
        "private_plain_omitted_reference_osis_sha256":
            approved["final_private_corrected_osis_sha256"],
        "candidate_binary_sha256_not_public_release":
            approved["tested_native_compiled_payload_sha256"],
        "source_key_count": 31166, "source_note_count": 6340,
        "machine_note_targets_replaced": 8,
        "plain_nonhyperlink_omission_label_count": 3,
        "invalid_inline_osis_elements_replaced": 2,
        "original_unedited_osis_bytes_preserved": True,
        "original_notes_unchanged_except_approved_navigation_targets": True,
        "original_verse_words_and_punctuation_equal": True,
        "official_osis_xsd_conforming": True,
        "native_result": {
            "candidate_status": "full_numbered_text_and_note_preflight_equal_not_approved",
            "candidate_versification": "Luther",
            "candidate_module_id": "JND2024RepairResearch",
        },
        "omitted_verse_notes_source_and_native": {
            "no_omitted_verses_fabricated": True,
        },
        "attested_private_preview_export": {
            "status": "exact_audited_source_bytes_packaged_for_reader_testing_only",
            "module_id": "JND2024RepairResearch",
            "versification": "Luther",
            "module_file_count": 7,
            "zip_sha256": sha256(blob).hexdigest(),
            "all_module_files_byte_identical_to_audited_candidate": True,
        },
    }
    return approved, audit


class OwnerApprovedStableZtextTest(unittest.TestCase):
    def test_complete_exact_owner_attestation_accepted(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.zip"
            path.write_bytes(b"synthetic-nonbible-placeholder")
            approval, audit = fixtures(path.read_bytes())
            verified_approval(approval, audit, path)

    def test_unapproved_or_nonidentical_input_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.zip"
            path.write_bytes(b"synthetic-placeholder")
            approval, audit = fixtures(path.read_bytes())
            cases = [
                ("status", "research_only"),
                ("publisher_public_domain_evidence", "https://invalid.example/"),
                ("original_publisher_osis_sha256", "0" * 64),
                ("final_private_corrected_osis_sha256", "0" * 64),
                ("tested_native_compiled_payload_sha256", "0" * 64),
                ("reviewed_contextual_destination_corrections", 7),
                ("reviewed_omitted_verse_plain_labels", 2),
            ]
            for field, bad in cases:
                with self.subTest(field=field):
                    altered = copy.deepcopy(approval)
                    altered[field] = bad
                    with self.assertRaises(ValueError):
                        verified_approval(altered, audit, path)
            path.write_bytes(b"altered")
            with self.assertRaises(ValueError):
                verified_approval(approval, audit, path)

    def test_any_full_corpus_or_private_export_regression_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.zip"
            path.write_bytes(b"synthetic-placeholder")
            approval, audit = fixtures(path.read_bytes())
            for field, bad in (
                ("source_key_count", 31165),
                ("source_note_count", 6339),
                ("official_osis_xsd_conforming", False),
                ("original_verse_words_and_punctuation_equal", False),
                ("machine_note_targets_replaced", 7),
            ):
                with self.subTest(field=field):
                    altered = copy.deepcopy(audit)
                    altered[field] = bad
                    with self.assertRaises(ValueError):
                        verified_approval(approval, altered, path)
            altered = copy.deepcopy(audit)
            altered["omitted_verse_notes_source_and_native"]["no_omitted_verses_fabricated"] = False
            with self.assertRaises(ValueError):
                verified_approval(approval, altered, path)
            altered = copy.deepcopy(audit)
            altered["attested_private_preview_export"]["module_file_count"] = 6
            with self.assertRaises(ValueError):
                verified_approval(approval, altered, path)


if __name__ == "__main__":
    unittest.main()
