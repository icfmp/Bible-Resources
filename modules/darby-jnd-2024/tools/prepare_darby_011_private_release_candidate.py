#!/usr/bin/env python3
"""Privately materialize and independently audit a Darby 0.1.1 ZIP candidate.

Research / publication preflight only. This script never writes to modules/,
catalog/, Pages or a GitHub Release. Source text and ZIP bytes stay local to CI.
Only bounded metadata is exported. Actual publication requires a new explicit
owner authorization and a separate protected-PR release workflow.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import ZipFile

from promote_sword_preview import promote
from publisher_osis_observation import read_pinned_publisher_osis
from source_osis_inventory import source_inventory
from stable_sword_refs import inspect_references, parse_keys, parse_registry
from sword_native_inventory import collect_native_inventory

SOURCE_ID = "JND2024RepairResearch"
TARGET = "BRJND2024"
VERSION = "0.1.1"
ORIGINAL = "2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3"
CORRECTED = "35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d"
RESEARCH_NATIVE = "1d9eac592c6ef99a92493d73dd4718e3a353b1fb478f961c6c09605be6e2524c"
PRIOR_RELEASE_SHA = "5910669e5eeb85d2ba06a4602918ce71d6773f36d64502bbdf7f96fff0585f15"
HEX = re.compile(r"[a-f0-9]{64}\Z")


class Darby011PreflightError(ValueError):
    pass


def digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def _require(condition: bool, reason: str):
    if not condition:
        raise Darby011PreflightError(reason)


def verify_proofs(audit: dict, prior: dict, stable_conf: bytes) -> dict:
    _require(audit.get("status") == "repaired_osis_to_native_sword_full_text_notes_research_passed",
             "Source/native verification status not complete")
    _require(audit.get("publisher_original_sha256") == ORIGINAL,
             "Original BPC 2024 source identity drifted")
    _require(audit.get("private_compiled_osis_sha256") == CORRECTED,
             "Original-to-candidate corrective overlay differs")
    _require(audit.get("candidate_binary_sha256_not_public_release") == RESEARCH_NATIVE,
             "Not the complete independently reviewed native binary")
    _require(audit.get("source_key_count") == 31166 and audit.get("source_note_count") == 6340,
             "Numbered verse or source note inventory changed")
    _require(audit.get("official_osis_xsd_conforming") is True,
             "Corrected source has no valid OSIS XSD proof")
    _require(audit.get("original_notes_unchanged_except_approved_navigation_targets") is True,
             "Original note preservation is unverified")
    marks = audit.get("research_full_source_native_editorial_division_metadata") or {}
    _require(marks.get("status") == "exact_source_and_native_non_display_editorial_markers_equal"
             and marks.get("source_marker_count") == 521
             and marks.get("native_marker_count") == 521
             and marks.get("source_and_native_all_marker_types_levels_and_host_verses_equal") is True
             and marks.get("all_displayable_marker_attributes_absent") is True,
             "All 521 authorial division levels and native positions are not verified")
    _require(marks.get("by_non_display_subtype") == {
        "x-original-ascii-star-1": 498,
        "x-original-ascii-star-2": 10,
        "x-original-ascii-star-3": 13,
    }, "Source section level census drifted")
    indent = audit.get("research_paragraph_whitespace_overlay_receipt") or {}
    counts = indent.get("counts") or {}
    _require(indent.get("all_source_nonspace_characters_preserved") is True
             and indent.get("all_source_note_values_and_positions_preserved") is True
             and counts.get("paragraphs_with_exact_xml_indent") == 4690
             and counts.get("formatting_spaces_removed") == 56288,
             "XML-only indentation correction evidence is incomplete")
    _require(audit.get("native_result", {}).get("candidate_status")
             == "full_numbered_text_and_note_preflight_equal_not_approved",
             "Full independent SWORD source/main/notes/structure preflight failed")
    preview = audit.get("attested_private_preview_export") or {}
    _require(preview.get("status") == "exact_audited_source_bytes_packaged_for_reader_testing_only"
             and preview.get("preview_only") is True
             and preview.get("release_approved") is False
             and preview.get("all_module_files_byte_identical_to_audited_candidate") is True
             and preview.get("module_file_count") == 7
             and isinstance(preview.get("zip_sha256"), str)
             and HEX.fullmatch(preview["zip_sha256"]) is not None,
             "Source/native audited exact SWORD preview was not exported privately")
    _require(prior.get("release_tag") == "darby-jnd-2024-0.1.0"
             and prior.get("release_zip_sha256") == PRIOR_RELEASE_SHA
             and prior.get("original_publisher_osis_sha256") == ORIGINAL
             and prior.get("status") == "source_and_native_attested_release_candidate",
             "Existing immutable 0.1.0 release baseline is not verified")
    c = stable_conf.decode("utf-8")
    _require(c.startswith("["+TARGET+"]\n")
             and "\nVersion=0.1.1\n" in ("\n"+c+"\n")
             and "\nModDrv=zText\n" in ("\n"+c+"\n")
             and "\nVersification=Luther\n" in ("\n"+c+"\n")
             and "\nDistributionLicense=Public Domain\n" in ("\n"+c+"\n"),
             "The target 0.1.1 conf does not describe the reviewed edition")
    return preview


def preflight(*, audit_path: Path, preview_zip: Path, old_provenance: Path,
              final_conf: Path, native_index: Path, private_directory: Path) -> dict:
    _require(not private_directory.exists() and not private_directory.is_symlink()
             and private_directory.parent.is_dir(),
             "Preflight requires an entirely new isolated private output directory")
    _require(preview_zip.is_file() and not preview_zip.is_symlink()
             and native_index.is_file() and not native_index.is_symlink(),
             "Private original trial ZIP or actual native reader unavailable")
    audit_bytes = audit_path.read_bytes()
    audit = json.loads(audit_bytes)
    prior = json.loads(old_provenance.read_bytes())
    preview = verify_proofs(audit, prior, final_conf.read_bytes())
    _require(digest(preview_zip.read_bytes()) == preview["zip_sha256"],
             "Private SWORD ZIP differs from full native audit")
    private_directory.mkdir()
    final_zip = private_directory / f"{TARGET}-{VERSION}.zip"
    result = promote(
        preview_zip, final_zip, expected_source_sha256=preview["zip_sha256"],
        source_id=SOURCE_ID, destination_id=TARGET, config=final_conf,
        driver="zText", versification="Luther",
    )
    _require(result["data_byte_equal"] is True
             and result["published"] is False
             and len(result["per_file_sha256"]) == 6,
             "Final SWORD bytes differ from exact research candidate")
    payload = private_directory / "final-module" / "payload"
    with ZipFile(final_zip) as z:
        names = z.namelist()
        expected = {"mods.d/brjnd2024.conf"} | {
            "modules/texts/ztext/brjnd2024/" + side + "." + ext
            for side in ("ot", "nt") for ext in ("bzs", "bzv", "bzz")
        }
        _require(len(names) == 7 and set(names) == expected and z.testzip() is None,
                 "Promoted SWORD contains unexpected files")
        for name in sorted(expected):
            f = payload / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(z.read(name))
    native_keys, registry, native = collect_native_inventory(
        native_index, private_directory / "final-module", TARGET)
    original = read_pinned_publisher_osis("frajnd-2024")
    _require(digest(original) == ORIGINAL, "Original BPC publisher source changed")
    source_keys, original_meta = source_inventory(original)
    index = inspect_references(
        parse_keys(source_keys), parse_keys(native_keys),
        parse_registry(registry, "Luther"))
    _require(index["status"] == "stable_reference_index_verified"
             and index["source_reference_count"] == 31166
             and index["resolved_reader_reference_count"] == 31166
             and index["unexpected_populated_reader_references_count"] == 0
             and native["module_driver"] == "zText"
             and native["native_versification"] == "Luther",
             "Final 0.1.1 identity did not preserve native source indexing")
    _require(final_conf.read_bytes() == (payload/"mods.d"/"brjnd2024.conf").read_bytes(),
             "Final ZIP and checked SWORD 0.1.1 conf are not identical")
    _require(digest(preview_zip.read_bytes()) == preview["zip_sha256"],
             "Private original research ZIP was modified")
    report = {
        "schema_version": 1,
        "status": "reproducible_private_final_module_id_0_1_1_preflight_verified",
        "new_release_tag_proposal": "darby-jnd-2024-0.1.1",
        "old_immutable_release_zip_sha256": PRIOR_RELEASE_SHA,
        "old_publisher_source_sha256": ORIGINAL,
        "new_compiler_source_osis_sha256": CORRECTED,
        "private_final_candidate_sword_zip_sha256": result["release_zip_sha256"],
        "private_final_candidate_sword_zip_bytes": result["release_zip_bytes"],
        "independently_inspected_final_module_id": TARGET,
        "final_conf_version": VERSION,
        "source_verse_keys": 31166,
        "source_note_count": 6340,
        "native_verse_index_verified": True,
        "native_reader_engine": "libsword",
        "all_521_division_metadata_source_native_pairs_verified": True,
        "full_source_native_audit_sha256": digest(audit_bytes),
        "six_ztext_member_hashes": result["per_file_sha256"],
        "binary_data_unchanged_during_identity_promotion": True,
        "original_publisher_source_unchanged": True,
        "old_0_1_0_release_untouched": True,
        "last_0_1_1_reader_gui_on_final_module_id_verified": False,
        "owner_release_approval": False,
        "published": False,
        "public_catalogue_modified": False,
    }
    (private_directory/"metadata-only-report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
        encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit", type=Path, required=True)
    p.add_argument("--private-research-zip", type=Path, required=True)
    p.add_argument("--old-release-provenance", type=Path, required=True)
    p.add_argument("--final-conf", type=Path, required=True)
    p.add_argument("--native-index", type=Path, required=True)
    p.add_argument("--private-output-dir", type=Path, required=True)
    args = p.parse_args()
    report = preflight(
        audit_path=args.audit, preview_zip=args.private_research_zip,
        old_provenance=args.old_release_provenance, final_conf=args.final_conf,
        native_index=args.native_index, private_directory=args.private_output_dir)
    print("Validated private 0.1.1 final identity, 31,166 keys, 6,340 notes, "
          "all 521 non-display source/native divisions, full file SHA-256.")
    print("Final test-only ZIP SHA-256:", report["private_final_candidate_sword_zip_sha256"])
    print("No publication, external source change or final-reader GUI signoff.")


if __name__ == "__main__":
    main()
