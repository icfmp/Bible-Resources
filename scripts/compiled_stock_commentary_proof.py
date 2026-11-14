#!/usr/bin/env python3
"""Validate a source-attested, unmodified compiled SWORD commentary.

OSIS source XSD/annotateRef rules apply when REBUILDING a commentary from OSIS.
They do not apply to an immutable compiled SWORD stock module when that OSIS
source file is unavailable. For the latter, require independently audited
complete original native raw SWORD identity, SHA-pinned upstream archive,
strict metadata-only curation and byte identity for every compressed member.

This validator has no network access and never manufactures XML evidence.
The actual source download/full-native comparison is performed by the
separate deterministic stock staging pipeline before the proof is produced.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

SHA = re.compile(r"[a-f0-9]{64}\Z")
MANIFEST = re.compile(r"config/commentary-intake/[a-z0-9-]+\.json\Z")
SUFFIXES = ("nt.bzs", "nt.bzv", "nt.bzz", "ot.bzs", "ot.bzv", "ot.bzz")


def compiled_stock_commentary_errors(module_dir: Path, root: Path,
                                     metadata: dict, conf: dict) -> list[str]:
    """Closed-set evidence from the exact original, never a synthetic OSIS."""
    report = module_dir / "SOURCE_VALIDATION.json"
    if (report.is_symlink() or not report.is_file() or
            report.stat().st_size > 64_000):
        return [f"{module_dir.name}: [STOCK_SOURCE_PROOF_MISSING] "
                "Verified compiled source proof is required"]
    try:
        proof = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"{module_dir.name}: [STOCK_SOURCE_PROOF_INVALID] {exc}"]
    if not isinstance(proof, dict):
        return [f"{module_dir.name}: [STOCK_SOURCE_PROOF_INVALID] Expected object"]
    original_manifest = proof.get("source_intake_manifest")
    if (not isinstance(original_manifest, str)
            or not MANIFEST.fullmatch(original_manifest)):
        return [f"{module_dir.name}: [STOCK_SOURCE_IDENTITY_INVALID] "
                "Unreviewed source-manifest path"]
    manifest_path = root / original_manifest
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return [f"{module_dir.name}: [STOCK_SOURCE_IDENTITY_INVALID] Missing pinned original"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"{module_dir.name}: [STOCK_SOURCE_IDENTITY_INVALID] {exc}"]
    if not isinstance(manifest, dict):
        return [f"{module_dir.name}: [STOCK_SOURCE_IDENTITY_INVALID] Manifest not an object"]
    issues = []
    def check(condition: bool, label: str):
        if not condition:
            issues.append(f"{module_dir.name}: [STOCK_SOURCE_PROOF_INVALID] {label}")
    expected = {
        "schema_version": 1,
        "status": "validated",
        "source_kind": "compiled_sword_stock",
        "source_intake_manifest": original_manifest,
        "upstream_module_id": manifest.get("module_id"),
        "curated_module_id": metadata["sword_id"],
        "upstream_version": manifest.get("version"),
        "curated_version": metadata["version"],
        "upstream_archive_sha256": manifest.get("archive_sha256"),
        "upstream_conf_sha256": manifest.get("stock_conf_sha256"),
        "native_raw_corpus_sha256": manifest.get("native_raw_corpus_sha256"),
        "all_original_compressed_files_byte_identical": True,
        "all_native_original_keys_byte_identical": True,
        "only_source_metadata_relabelled": ["section_id", "DataPath", "Version"],
        "no_original_source_text_edited": True,
        "historical_print_or_ccel_parity_claimed": False,
        "gui_other_reader_compatibility_claimed": False,
    }
    for name, val in expected.items():
        check(proof.get(name) == val, name)
    check(manifest.get("category") == "commentary", "original category")
    check(manifest.get("provider") == metadata.get("upstreams", [{}])[0].get("provider"),
          "original provider")
    check(manifest.get("source_page_url") == metadata["origin"]["url"],
          "origin URL does not match original evidence")
    check(manifest.get("rights", {}).get("upstream_license_claim")
          == "Public Domain--Copy Freely", "upstream public-domain claim")
    check(metadata["rights"]["license"] == "Public Domain", "original licence modified")
    check(conf.get("DistributionLicense") == "Public Domain", "SWORD licence changed")
    check(conf.get("ModDrv") == "zCom", "driver must remain original zCom")
    check(conf.get("Versification") == "KJV", "original versification changed")
    check(metadata.get("upstreams", [{}])[0].get("module_id")
          == manifest.get("module_id"), "upstream SWORD identity")
    check(metadata.get("upstreams", [{}])[0].get("last_integrated_version")
          == manifest.get("version"), "upstream version")
    check(metadata.get("upstreams", [{}])[0].get("last_integrated_conf_sha256")
          == manifest.get("stock_conf_sha256"), "upstream conf hash")
    check(proof.get("native_key_count", 0) > 0
          and type(proof.get("native_key_count")) is int, "native key count")
    for name in ("upstream_archive_sha256", "upstream_conf_sha256",
                 "native_raw_corpus_sha256", "curated_conf_sha256"):
        check(isinstance(proof.get(name), str)
              and SHA.fullmatch(proof[name]) is not None, name + " digest")
    data = module_dir / "payload" / "modules/comments/zcom" / metadata["sword_id"].lower()
    expected_files = set(SUFFIXES)
    if data.is_symlink() or not data.is_dir():
        issues.append(f"{module_dir.name}: [STOCK_DATA_MISSING] Original zCom data absent")
    else:
        actual_files = {p.name for p in data.iterdir() if p.is_file()}
        check(actual_files == expected_files and
              not any(p.is_symlink() or not p.is_file() for p in data.iterdir()),
              "unreviewed compressed-file inventory")
    member_hashes = proof.get("compressed_members_sha256_by_filename")
    if not isinstance(member_hashes, dict) or set(member_hashes) != expected_files:
        issues.append(f"{module_dir.name}: [STOCK_SOURCE_PROOF_INVALID] "
                      "Exact six compressed member fingerprints required")
    else:
        for filename in SUFFIXES:
            p = data / filename
            digest = member_hashes[filename]
            check(isinstance(digest, str) and SHA.fullmatch(digest) is not None,
                  filename + " original digest format")
            if not p.is_file() or p.is_symlink():
                issues.append(f"{module_dir.name}: [STOCK_DATA_MISSING] {filename}")
            elif sha256(p.read_bytes()).hexdigest() != digest:
                issues.append(f"{module_dir.name}: [STOCK_CONTENT_CHANGED] {filename}")
    config_file = module_dir / "payload" / "mods.d" / (
        metadata["sword_id"].lower() + ".conf")
    if config_file.is_file() and not config_file.is_symlink():
        check(sha256(config_file.read_bytes()).hexdigest()
              == proof.get("curated_conf_sha256"), "reviewed SWORD metadata bytes")
    else:
        issues.append(f"{module_dir.name}: [STOCK_CONF_MISSING] Reviewed .conf absent")
    return issues
