#!/usr/bin/env python3
"""Materialize the first hash-locked, owner-approved LSG release for the SWORD repo.

The exact release ZIP and full source-fidelity report are immutable upstream
GitHub Release assets. The vetted binary is extracted byte for byte, never
recompiled. This edition-specific adapter exists because the generic
source-to-SWORD importer is still under development (issue #28).
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZipFile

MAX_PACKAGE_BYTES = 64 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def verified_members(zip_path: Path, manifest: dict) -> dict[str, bytes]:
    if zip_path.is_symlink() or zip_path.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError("Unsafe release archive")
    if sha(zip_path.read_bytes()) != manifest["release_zip_sha256"]:
        raise ValueError("Release ZIP does not match published SHA-256")
    expected = manifest["files"]
    with ZipFile(zip_path) as archive:
        entries = archive.infolist()
        if len(entries) != len(expected) or set(i.filename for i in entries) != set(expected):
            raise ValueError("Unexpected SWORD archive member")
        if archive.testzip() is not None:
            raise ValueError("Release ZIP CRC failed")
        if sum(i.file_size for i in entries) > MAX_PACKAGE_BYTES:
            raise ValueError("Release package decompressed size too large")
        if any(i.is_dir() or stat.S_IFMT(i.external_attr >> 16) == stat.S_IFLNK
               or i.filename.startswith("/") or ".." in Path(i.filename).parts
               for i in entries):
            raise ValueError("Unsafe release member type/path")
        data = {name: archive.read(name) for name in expected}
    for name, digest in expected.items():
        if sha(data[name]) != digest:
            raise ValueError("SWORD payload byte mismatch: " + name)
    return data


def verify_audit(audit: dict, manifest: dict, policy: dict) -> None:
    if audit["original_usfm_archive_sha256"] != manifest["source_usfm_zip_sha256"]:
        raise ValueError("Mismatch in source USFM identity")
    if audit["original_usfx_archive_sha256"] != manifest["source_usfx_zip_sha256"]:
        raise ValueError("Mismatch in source USFX identity")
    if audit["versification"] != "Segond" or audit["experimental_runtime_needed"] is not False:
        raise ValueError("Not a verified stock Segond runtime")
    source = audit["raw_osis_schema"]
    if (policy["schema_status"] != "reviewed"
            or source["xsd_sha256"] != policy["schema_sha256"]
            or source["xsd_status"] != "validated"
            or source["policy_status"] != "validated"):
        raise ValueError("Reviewed OSIS schema gate not met")
    original = audit["text_only_parallel_heading_review"]
    if (original["retyped_osis_sha256"] != manifest["provenance"]["retyped_markup_osis_sha256"]
            or original["source_osis_sha256"] != manifest["provenance"]["source_osis_sha256"]
            or original["inverse_reconstruction_canonical_xml_byte_equal"] is not True
            or original["heading_text_punctuation_and_order_unchanged"] is not True
            or original["explicit_osisref_targets_removed"] != 0
            or original["text_only_parallel_reference_elements_retyped"] != 2786
            or original["text_only_scope_reference_elements_retyped"] != 25):
        raise ValueError("Reversible source-attested heading edits not verified")
    label = audit["osis_editorial_range_label"]
    if (label["input_sha256"] != original["retyped_osis_sha256"]
            or label["output_sha256"] != manifest["provenance"]["final_candidate_osis_sha256"]
            or label["official_osis_xsd_validated"] is not True):
        raise ValueError("Final labeled OSIS candidate not schema validated")
    merge = audit["authorized_editorial_index_compromise"]
    if (merge["authorized_merge_count"] != 1
            or merge["observed_source_to_reader_keys_exactly_match_authorization"] is not True
            or merge["source_scripture_modified"] is not False
            or merge["reviewed_merges"][0]["authorial_source_key"] != "MRK.10.53"
            or merge["reviewed_merges"][0]["reader_source_key"] != "MRK.10.52"):
        raise ValueError("Unreviewed verse remapping")
    raw = audit["stock_sword_compiled_candidate"]["compiled_raw_markup_review"]
    if raw["status"] != "raw_stock_sword_full_scope_markers_verified_including_intros":
        raise ValueError("Incomplete full-corpus stock SWORD audit")
    preview = audit["xiphos_test_preview_package"]
    if (preview["status"] != "private_stock_sword_zip_reinstall_readback_verified"
            or preview["text_payload_files_byte_identical_to_verified_module"] is not True
            or preview["publisher_original_usfx_sha256"] != audit["original_usfx_sha256"]):
        raise ValueError("Private compiled module was not independently read back")


def install(root: Path, zip_path: Path, report_path: Path, manifest_path: Path) -> None:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["release_tag"] != "lsg-0.1.0" or manifest["module_id"] != "BRLSG1910":
        raise ValueError("Wrong approved release manifest")
    if report_path.is_symlink() or sha(report_path.read_bytes()) != manifest["release_audit_sha256"]:
        raise ValueError("Source-fidelity audit SHA-256 mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    policy = json.loads((root / "config/osis-policy.json").read_text(encoding="utf-8"))
    verify_audit(report, manifest, policy)
    files = verified_members(zip_path, manifest)
    actual_conf = files["mods.d/brlsg1910.conf"]
    if actual_conf != (root / "config/lsg-0.1.0.conf").read_bytes():
        raise ValueError("Public module metadata changed from reviewed release")
    folder = root / "modules/lsg-1910"
    meta_path = folder / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if (meta["quality"]["status"] != "in_review"
            or meta["sword_id"] != manifest["module_id"]
            or meta["quality"]["edition"] != "reader_optimized"
            or meta["versification"] != "Segond"):
        raise ValueError("Expected exactly one authorized edition in review")
    if (folder / "payload").exists() or (folder / "SOURCE_VALIDATION.json").exists():
        raise ValueError("Payload already registered; never replace a published edition")
    if not (folder / "EDITORIAL.md").is_file():
        raise ValueError("Human-readable editorial review is missing")

    # This final OSIS XML was validated against the pinned reviewed XSD
    # by the source-build workflow. This receipt refers to THAT validation
    # only: original publisher USFM/USFX and ordered transformation evidence
    # retain their separate immutable identities.
    source_sha = manifest["provenance"]["final_candidate_osis_sha256"]
    policy_hash = sha(json.dumps(policy, sort_keys=True,
                                 ensure_ascii=False).encode("utf-8"))
    source_validation = dict(
        status="validated", source_kind="bible",
        no_transformation_performed=True,
        source_sha256=source_sha,
        schema_sha256=policy["schema_sha256"],
        policy_sha256=policy_hash,
        provenance_audit_sha256=manifest["release_audit_sha256"],
        note="Validation-only proof of the final temporary OSIS candidate; publisher originals remain immutable.",
    )
    # A text-free, independently source-attested structural delta manifest,
    # not a fabricated copy of publisher Bible text or an alleged print diff.
    original = report["text_only_parallel_heading_review"]
    delta = dict(
        provenance_audit_sha256=manifest["release_audit_sha256"],
        generated_original_osis_sha256=manifest["provenance"]["source_osis_sha256"],
        heading_retyped_osis_sha256=original["retyped_osis_sha256"],
        final_labeled_osis_sha256=source_sha,
        parallel_titles_retyped=2786, scope_titles_retyped=25,
        canonical_xml_inverse_byte_equal=True,
        source_mark_10_53_to_reader_10_52_owner_authorized=True,
        original_source_text_unchanged=True,
        original_note_whitespace_not_byte_identical=True,
    )
    delta_bytes = json.dumps(delta, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    normalization = dict(
        status="structural_edit_verified_not_published",
        edition="reader_optimized", kind="bible",
        full_text_exactly_preserved=True, inline_semantic_tags_preserved=True,
        original_source_unchanged=True, schema_sha256=policy["schema_sha256"],
        source_sha256=manifest["provenance"]["source_osis_sha256"],
        output_sha256=source_sha,
        plan_sha256=sha(manifest_bytes), diff_sha256=sha(delta_bytes),
        operations=[
            dict(kind="retype_verified_targetless_parallel_heading", count=2786),
            dict(kind="retype_verified_targetless_scope_heading", count=25),
            dict(kind="add_reviewed_mark_10_52_53_reader_index_label", count=1),
        ],
        review_asserted_by_plan=manifest["editorial_approval"]["approved_by"] +
            " on " + manifest["editorial_approval"]["date"],
        provenance_audit_sha256=manifest["release_audit_sha256"],
        diff_format="text-free structural change manifest, not a text-bearing patch",
    )

    for name, value in files.items():
        target = folder / "payload" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    for name, value in [
        ("SOURCE_VALIDATION.json", source_validation),
        ("NORMALIZATION_REPORT.json", normalization),
    ]:
        (folder / name).write_text(json.dumps(value, sort_keys=True,
                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "NORMALIZATION_DIFF_MANIFEST.json").write_bytes(delta_bytes)
    (folder / "SOURCE_AUDIT.json").write_bytes(report_path.read_bytes())
    meta["quality"]["status"] = "approved"
    meta_path.write_text(json.dumps(meta, sort_keys=True, ensure_ascii=False,
                                   indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--release-zip", type=Path, required=True)
    p.add_argument("--source-audit", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] /
                   "config/catalogue-import-lsg-0.1.0.json")
    a = p.parse_args()
    install(a.root, a.release_zip, a.source_audit, a.manifest)
    print("Attested LSG 0.1.0 payload has been materialized with independent fingerprints.")


if __name__ == "__main__":
    main()
