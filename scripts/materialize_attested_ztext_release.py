#!/usr/bin/env python3
"""Materialize an already source-audited, owner-approved zText release.

Generic SWORD zText promotion and independent stock-reader index proof.
The source compiler and full-corpus structural/text/note review run upstream;
this script consumes their *actual* receipt and exact temporary preview ZIP.
Never modify official original OSIS, infer approval from passing tests or
overwrite an approved release. Do not call this from research-only workflows.
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
from stable_sword_refs import (
    inspect_references, module_payload_digest, parse_keys, parse_registry,
)
from sword_native_inventory import collect_native_inventory

HEX = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_STATUS = "owner_authorized_for_stable_release_after_all_final_gates"
RESEARCH_STATUS = "repaired_osis_to_native_sword_full_text_notes_research_passed"


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def encode(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def verified_approval(approval: dict, audit: dict, research_zip: Path) -> None:
    """Block stale/nonapproved preview, unresolved compiler audit or wrong edition."""
    required = (
        approval.get("schema_version") == 1,
        approval.get("status") == EXPECTED_STATUS,
        approval.get("published") is False,
        approval.get("owner_decision")
            == "https://github.com/icfmp/Bible-Resources/issues/133#issuecomment-6826689084",
        approval.get("publisher_public_domain_evidence")
            == "https://editeurbpc.com/telechargements",
        approval.get("release_tag") == "darby-jnd-2024-0.1.0",
        approval.get("version") == "0.1.0",
        approval.get("resource_id") == "frajnd-2024",
        approval.get("module_id") == "BRJND2024",
        approval.get("module_directory") == "modules/darby-jnd-2024",
        approval.get("expected_versification") == "Luther",
        approval.get("expected_verse_count") == 31166,
        approval.get("expected_note_count") == 6340,
        approval.get("reviewed_contextual_destination_corrections") == 8,
        approval.get("reviewed_omitted_verse_plain_labels") == 3,
        approval.get("reviewed_inline_technical_markup_count") == 2,
        audit.get("schema_version") == 1,
        audit.get("status") == RESEARCH_STATUS,
        audit.get("publisher_original_sha256")
            == approval.get("original_publisher_osis_sha256"),
        audit.get("private_plain_omitted_reference_osis_sha256")
            == approval.get("final_private_corrected_osis_sha256"),
        audit.get("candidate_binary_sha256_not_public_release")
            == approval.get("tested_native_compiled_payload_sha256"),
        audit.get("source_key_count") == approval.get("expected_verse_count"),
        audit.get("source_note_count") == approval.get("expected_note_count"),
        audit.get("machine_note_targets_replaced")
            == approval.get("reviewed_contextual_destination_corrections"),
        audit.get("plain_nonhyperlink_omission_label_count")
            == approval.get("reviewed_omitted_verse_plain_labels"),
        audit.get("invalid_inline_osis_elements_replaced")
            == approval.get("reviewed_inline_technical_markup_count"),
        audit.get("original_unedited_osis_bytes_preserved") is True,
        audit.get("original_notes_unchanged_except_approved_navigation_targets") is True,
        audit.get("original_verse_words_and_punctuation_equal") is True,
        audit.get("official_osis_xsd_conforming") is True,
        audit.get("native_result", {}).get("candidate_status")
            == "full_numbered_text_and_note_preflight_equal_not_approved",
        audit.get("native_result", {}).get("candidate_versification") == "Luther",
        audit.get("native_result", {}).get("candidate_module_id")
            == "JND2024RepairResearch",
        audit.get("omitted_verse_notes_source_and_native", {}).get(
            "no_omitted_verses_fabricated") is True,
    )
    if not all(required):
        raise ValueError("No exact owner-approved, original-pinned complete SWORD candidate")
    for key in ("original_publisher_osis_sha256",
                "final_private_corrected_osis_sha256",
                "tested_native_compiled_payload_sha256"):
        if not isinstance(approval.get(key), str) or not HEX.fullmatch(approval[key]):
            raise ValueError("Invalid approved publisher/candidate digest")
    preview = audit.get("attested_private_preview_export")
    if (not isinstance(preview, dict)
            or preview.get("status")
                != "exact_audited_source_bytes_packaged_for_reader_testing_only"
            or preview.get("all_module_files_byte_identical_to_audited_candidate")
                is not True
            or preview.get("module_id") != "JND2024RepairResearch"
            or preview.get("versification") != "Luther"
            or preview.get("module_file_count") != 7
            or not research_zip.is_file() or research_zip.is_symlink()
            or not HEX.fullmatch(preview.get("zip_sha256", ""))
            or digest(research_zip.read_bytes()) != preview["zip_sha256"]):
        raise ValueError("Exact exported private ZIP did not match audited compiler output")


def materialize(
    repo: Path, research_zip: Path, source_report: Path,
    approval_file: Path, stable_conf: Path, native_inspector: Path,
    release_dir: Path,
) -> dict:
    approval_raw = approval_file.read_bytes()
    approval = json.loads(approval_raw)
    audit_raw = source_report.read_bytes()
    audit = json.loads(audit_raw)
    verified_approval(approval, audit, research_zip)
    folder = repo / approval["module_directory"]
    metadata_path = folder / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (metadata["quality"]["status"] != "in_review"
            or metadata["quality"]["edition"] != "reader_optimized"
            or metadata["sword_id"] != approval["module_id"]
            or metadata["version"] != approval["version"]
            or metadata["versification"] != approval["expected_versification"]
            or metadata["rights"]["license"] != "Public Domain"
            or metadata["rights"]["derivatives_allowed"] is not True
            or metadata["rights"]["redistribution_allowed"] is not True
            or metadata["index_audit"]["mode"] != "stock_reader_keys"
            or (folder / "payload").exists()
            or (folder / "SOURCE_AUDIT.json").exists()
            or not (folder / "EDITORIAL.md").is_file()):
        raise ValueError("Existing or unapproved release module, forbidden overwrite")
    release_dir.mkdir(exist_ok=False)
    release_zip = release_dir / (approval["module_id"] + "-" + approval["version"] + ".zip")
    result = promote(
        research_zip, release_zip,
        expected_source_sha256=audit["attested_private_preview_export"]["zip_sha256"],
        source_id="JND2024RepairResearch", destination_id=approval["module_id"],
        config=stable_conf, driver="zText", versification="Luther",
    )
    if (result["status"] != "exact_sword_payload_promoted_with_reviewed_metadata"
            or result["published"] is not False or result["data_byte_equal"] is not True
            or len(result["per_file_sha256"]) != 6):
        raise ValueError("Publisher-audited SWORD zText data bytes not preserved")
    payload = folder / "payload"
    payload.mkdir(exist_ok=False)
    with ZipFile(release_zip) as z:
        names = z.namelist()
        expected = {"mods.d/brjnd2024.conf"} | {
            "modules/texts/ztext/brjnd2024/" + part + "." + ext
            for part in ("ot", "nt") for ext in ("bzs", "bzv", "bzz")
        }
        if len(names) != 7 or set(names) != expected or z.testzip() is not None:
            raise ValueError("Unsafe or unexpected promoted SWORD ZIP")
        for name in sorted(names):
            path = payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(z.read(name))
    # Independently examine the FINAL stable identity through actual libsword.
    native_keys, registry, native = collect_native_inventory(
        native_inspector, folder, approval["module_id"])
    original = read_pinned_publisher_osis(approval["resource_id"])
    if digest(original) != approval["original_publisher_osis_sha256"]:
        raise ValueError("Authoritative publisher bytes changed since owner approval")
    authorial_keys, _meta = source_inventory(original)
    index = inspect_references(
        parse_keys(authorial_keys), parse_keys(native_keys),
        parse_registry(registry, "Luther"))
    if (index["status"] != "stable_reference_index_verified"
            or index["source_reference_count"] != 31166
            or index["resolved_reader_reference_count"] != 31166
            or index["unexpected_populated_reader_references_count"] != 0
            or native["module_driver"] != "zText"
            or native["native_versification"] != "Luther"):
        raise ValueError("Final stable module has wrong actual occupied keys or index")
    index.update({
        "versification": "Luther",
        "reader_engine": "libsword",
        "reader_version": audit["native_result"]["compiled_engine_version"],
        "engine_release": "stable",
        "registry_source": "installed_sword_versification_mgr",
        "source_osis_sha256": approval["final_private_corrected_osis_sha256"],
        "module_payload_sha256": module_payload_digest(folder),
        "reviewed_by": "Bible Resources project owner, 2026-11-12",
    })
    # This is only the validated *technical overlay* source, not the
    # pristine publisher original. Each retains its own immutable identity.
    policy = json.loads((repo / "config/osis-policy.json").read_text())
    if policy.get("schema_status") != "reviewed":
        raise ValueError("Official OSIS schema policy not reviewed")
    policy_sha = digest(json.dumps(policy, sort_keys=True, ensure_ascii=False).encode())
    audit_sha = digest(audit_raw)
    source_receipt = {
        "status": "validated", "source_kind": "bible",
        "no_transformation_performed": True,
        "source_sha256": approval["final_private_corrected_osis_sha256"],
        "schema_sha256": policy["schema_sha256"],
        "policy_sha256": policy_sha,
        "provenance_audit_sha256": audit_sha,
        "note": "Pinned XSD validation of separately reviewed corrected OSIS; original BPC source unchanged.",
    }
    diff = {
        "publisher_original_osis_sha256": approval["original_publisher_osis_sha256"],
        "final_corrected_osis_sha256": approval["final_private_corrected_osis_sha256"],
        "reviewed_reference_destinations": 8,
        "textcritical_plain_reference_wrappers": 3,
        "invalid_inline_measurement_tags": 2,
        "original_all_authorial_characters_unchanged": True,
        "original_missing_numbered_verses_uninvented": True,
        "source_attested_audit_sha256": audit_sha,
    }
    link = (repo / "config/publisher-osis/frajnd-2024-note-link-research.json").read_bytes()
    inline = (repo / "config/publisher-osis/frajnd-2024-inline-markup-research.json").read_bytes()
    normalization = {
        "status": "structural_edit_verified_not_published",
        "edition": "reader_optimized", "kind": "bible",
        "full_text_exactly_preserved": True,
        "inline_semantic_tags_preserved": True,
        "original_source_unchanged": True,
        "schema_sha256": policy["schema_sha256"],
        "source_sha256": approval["original_publisher_osis_sha256"],
        "output_sha256": approval["final_private_corrected_osis_sha256"],
        "plan_sha256": digest(link + inline + approval_raw),
        "diff_sha256": digest(encode(diff)),
        "operations": [
            {"kind": "correct_reviewed_note_machine_destination", "count": 8},
            {"kind": "retype_unlinked_omitted_verse_label_as_plain_segment", "count": 3},
            {"kind": "replace_invalid_measurement_inline_tag", "count": 2},
        ],
        "review_asserted_by_plan": "Bible Resources project owner 2026-11-12 (issue #133)",
        "provenance_audit_sha256": audit_sha,
        "diff_format": "text-free source-attested semantic operation inventory",
    }
    folder.joinpath("SOURCE_VALIDATION.json").write_bytes(encode(source_receipt))
    folder.joinpath("NORMALIZATION_REPORT.json").write_bytes(encode(normalization))
    folder.joinpath("NORMALIZATION_DIFF_MANIFEST.json").write_bytes(encode(diff))
    folder.joinpath("SWORD_COMPATIBILITY.json").write_bytes(encode(index))
    folder.joinpath("SOURCE_AUDIT.json").write_bytes(audit_raw)
    files = {}
    for file in sorted(payload.rglob("*")):
        if file.is_file():
            files[file.relative_to(payload).as_posix()] = digest(file.read_bytes())
    provenance = {
        "status": "source_and_native_attested_release_candidate",
        "release_tag": approval["release_tag"],
        "release_zip_sha256": result["release_zip_sha256"],
        "release_zip_bytes": result["release_zip_bytes"],
        "original_publisher_osis_sha256": approval["original_publisher_osis_sha256"],
        "corrected_candidate_osis_sha256": approval["final_private_corrected_osis_sha256"],
        "full_native_audit_sha256": audit_sha,
        "review_approval_sha256": digest(approval_raw),
        "source_research_preview_sha256": result["source_zip_sha256"],
        "six_ztext_payload_files_byte_identical_to_full_native_audit": True,
        "complete_release_member_sha256": files,
        "published": False,
    }
    folder.joinpath("RELEASE_PROVENANCE.json").write_bytes(encode(provenance))
    metadata["quality"]["status"] = "approved"
    metadata_path.write_bytes(encode(metadata))
    release_dir.joinpath("SHA256SUMS.txt").write_text(
        result["release_zip_sha256"] + "  " + release_zip.name + "\n",
        encoding="utf-8")
    release_dir.joinpath("SOURCE_AUDIT.json").write_bytes(audit_raw)
    release_dir.joinpath("RELEASE_PROVENANCE.json").write_bytes(encode(provenance))
    return provenance


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--preview-zip", required=True, type=Path)
    p.add_argument("--source-audit", required=True, type=Path)
    p.add_argument("--approval", required=True, type=Path)
    p.add_argument("--stable-conf", required=True, type=Path)
    p.add_argument("--native-index", required=True, type=Path)
    p.add_argument("--release-dir", required=True, type=Path)
    args = p.parse_args()
    if args.release_dir.exists() or args.release_dir.is_symlink():
        p.error("Release staging folder must not already exist")
    manifest = materialize(
        args.root, args.preview_zip, args.source_audit,
        args.approval, args.stable_conf, args.native_index,
        args.release_dir)
    print(json.dumps({
        "status": manifest["status"],
        "release_tag": manifest["release_tag"],
        "package_sha256": manifest["release_zip_sha256"],
        "source_index_verified": True,
        "source_note_count_preserved": True,
        "published": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
