"""Reject unsafe Darby 0.1.1 packaging even when someone supplies a green run."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_darby_011_private_release_candidate import (
    ORIGINAL, CORRECTED, RESEARCH_NATIVE, PRIOR_RELEASE_SHA,
    Darby011PreflightError, verify_proofs,
)

CONF = b"""[BRJND2024]
DataPath=./modules/texts/ztext/brjnd2024/
ModDrv=zText
Versification=Luther
Encoding=UTF-8
Version=0.1.1
DistributionLicense=Public Domain
"""
PRIOR = {"release_tag":"darby-jnd-2024-0.1.0",
         "release_zip_sha256":PRIOR_RELEASE_SHA,
         "original_publisher_osis_sha256":ORIGINAL,
         "status":"source_and_native_attested_release_candidate"}
REPORT = {
    "status":"repaired_osis_to_native_sword_full_text_notes_research_passed",
    "publisher_original_sha256":ORIGINAL,
    "private_compiled_osis_sha256":CORRECTED,
    "candidate_binary_sha256_not_public_release":RESEARCH_NATIVE,
    "source_key_count":31166,"source_note_count":6340,
    "official_osis_xsd_conforming":True,
    "original_notes_unchanged_except_approved_navigation_targets":True,
    "research_full_source_native_editorial_division_metadata":{
        "status":"exact_source_and_native_non_display_editorial_markers_equal",
        "source_marker_count":521,"native_marker_count":521,
        "source_and_native_all_marker_types_levels_and_host_verses_equal":True,
        "all_displayable_marker_attributes_absent":True,
        "by_non_display_subtype":{
            "x-original-ascii-star-1":498,
            "x-original-ascii-star-2":10,
            "x-original-ascii-star-3":13,
        }},
    "research_paragraph_whitespace_overlay_receipt":{
        "all_source_nonspace_characters_preserved":True,
        "all_source_note_values_and_positions_preserved":True,
        "counts":{"paragraphs_with_exact_xml_indent":4690,
                  "formatting_spaces_removed":56288}},
    "native_result":{
        "candidate_status":"full_numbered_text_and_note_preflight_equal_not_approved"},
    "attested_private_preview_export":{
        "status":"exact_audited_source_bytes_packaged_for_reader_testing_only",
        "preview_only":True,"release_approved":False,
        "all_module_files_byte_identical_to_audited_candidate":True,
        "module_file_count":7,"zip_sha256":"a"*64,
    },
}


class TestDarbyPrivate011Preflight(unittest.TestCase):
    def test_pinned_synthetic_complete_receipt_is_eligible_for_private_check_only(self):
        preview=verify_proofs(deepcopy(REPORT),deepcopy(PRIOR),CONF)
        self.assertEqual(preview["zip_sha256"],"a"*64)

    def test_source_native_marker_loss_is_not_waived(self):
        audit=deepcopy(REPORT)
        audit["research_full_source_native_editorial_division_metadata"]["native_marker_count"]=520
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(audit,deepcopy(PRIOR),CONF)

    def test_displayable_star_attribute_fails_preflight(self):
        audit=deepcopy(REPORT)
        audit["research_full_source_native_editorial_division_metadata"]["all_displayable_marker_attributes_absent"]=False
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(audit,deepcopy(PRIOR),CONF)

    def test_old_release_cannot_be_relabelled_or_overwritten(self):
        old=deepcopy(PRIOR)
        old["release_tag"]="darby-jnd-2024-0.1.1"
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(deepcopy(REPORT),old,CONF)

    def test_no_approved_status_is_inferred_from_green_native_proof(self):
        audit=deepcopy(REPORT)
        audit["attested_private_preview_export"]["release_approved"]=True
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(audit,deepcopy(PRIOR),CONF)

    def test_wrong_config_version_rejected(self):
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(deepcopy(REPORT),deepcopy(PRIOR),CONF.replace(b"Version=0.1.1",b"Version=0.1.0"))

    def test_wrong_compiled_binary_hash_rejected(self):
        audit=deepcopy(REPORT)
        audit["candidate_binary_sha256_not_public_release"]="0"*64
        with self.assertRaises(Darby011PreflightError):
            verify_proofs(audit,deepcopy(PRIOR),CONF)


if __name__=="__main__":
    unittest.main()
