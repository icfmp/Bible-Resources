#!/usr/bin/env python3
"""Read-only, edition-parameterized commentary intake.

Stage 1 inspects a reviewed manifest without downloads. "observe" inventories
the mutable upstream ZIP and stock SWORD module to obtain its true fingerprint.
Stage 2 requires that fingerprint to be independently pinned first.

This is NOT source-to-SWORD parity, rights clearance, normalization or release.
No original commentary text is printed, written to reports, or uploaded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit
import zipfile

from audit_real_pilot import scan_sword_entries
from check_updates import ID_PATTERN
from pilot_fetch import fetch, validate_url
from pilot_preflight import ROOT, PilotError, inspect_archive

ID = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
COMMENTARY_DRIVERS = {"RawCom", "RawCom4", "zCom", "zCom4"}


def load_manifest(resource_id: str, directory: Path | None = None) -> dict:
    """Never let a remote resource name become an arbitrary filesystem path."""
    if not ID.fullmatch(resource_id):
        raise PilotError("Unsafe commentary resource ID")
    root = directory or ROOT / "config/commentary-intake"
    path = root / (resource_id + ".json")
    if path.is_symlink() or not path.is_file():
        raise PilotError("Commentary manifest missing or symlink")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required_strings = ("resource_id", "module_id", "title", "language",
                        "version", "provider", "source_page_url",
                        "sword_zip_url", "authorial_witness_url")
    if manifest.get("schema_version") != 1 or manifest.get("category") != "commentary":
        raise PilotError("Unsupported commentary manifest schema/category")
    if any(not isinstance(manifest.get(k), str) or not manifest[k] for k in required_strings):
        raise PilotError("Missing commentary identity, provider or evidence URL")
    if manifest["resource_id"] != resource_id or not ID_PATTERN.fullmatch(manifest["module_id"]):
        raise PilotError("Manifest/resource ID mismatch")
    if not re.fullmatch(r"[a-z]{2,3}", manifest["language"]):
        raise PilotError("Unreviewed commentary language")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", manifest["version"]):
        raise PilotError("Expected upstream version must be pinned to a numeric release")
    provider = manifest["provider"]
    if provider not in ("crosswire",):
        raise PilotError("Commentary provider not yet enabled for secure downloads")
    validate_url(manifest["sword_zip_url"], provider)
    url = urlsplit(manifest["sword_zip_url"])
    if not url.path.endswith("/" + manifest["module_id"] + ".zip") or url.query:
        raise PilotError("SWORD package URL does not match exact declared module ID")
    for name in ("source_page_url", "authorial_witness_url"):
        parsed = urlsplit(manifest[name])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise PilotError("Non-HTTPS source evidence")
    sha = manifest.get("archive_sha256")
    if sha is not None and (not isinstance(sha, str) or not SHA.fullmatch(sha)):
        raise PilotError("Archive pin must be null or a lowercase SHA-256")
    references = manifest.get("sample_references")
    if (not isinstance(references, list) or not (2 <= len(references) <= 20)
            or any(not isinstance(ref, str) or not (1 <= len(ref) <= 100) for ref in references)):
        raise PilotError("Need 2–20 bounded reader sample references")
    rights = manifest.get("rights")
    if not isinstance(rights, dict) or rights.get("status") != "research_only" or rights.get("owner_approved") is not False:
        raise PilotError("Intake stage is research-only; rights approval is a separate gate")
    if not rights.get("evidence_url"):
        raise PilotError("Rights evidence URL required")
    return manifest


def inspect_resource(resource_id: str, stage: str, *, directory: Path | None = None,
                     reader: str | None = None) -> dict:
    manifest = load_manifest(resource_id, directory=directory)
    if stage == "auto":
        stage = "2" if manifest["archive_sha256"] is not None else "observe"
    report = {
        "schema_version": 1,
        "resource_id": resource_id,
        "module_id": manifest["module_id"],
        "stage": stage,
        "source_page_url": manifest["source_page_url"],
        "authorial_witness_url": manifest["authorial_witness_url"],
        "source_edition_equivalence": "unverified",
        "copyright_and_redistribution_approved": False,
        "editorial_approved": False,
        "published": False,
        "full_original_to_module_parity": False,
        "no_text_transformed": True,
        "remaining_gates": [
            "Verify publisher's exact digital edition and rights including corrections",
            "Pin independent original source/witness and prove its edition identity",
            "Full commentary coverage, range keys and source-to-binary text/structure parity",
            "Independent Xiphos and AndBible checks",
            "Human technical, editorial and legal sign-off before release"
        ],
    }
    if stage == "1":
        report["status"] = "metadata_review_required"
        report["archive_pin_present"] = manifest["archive_sha256"] is not None
        report["download_performed"] = False
        return report
    if stage not in ("observe", "2"):
        raise PilotError("Only commentary stage 1, original observation and pinned stage 2 are implemented")
    if stage == "2" and manifest["archive_sha256"] is None:
        raise PilotError("Stage 2 requires independently reviewed, pinned upstream ZIP SHA-256 before download")
    with tempfile.TemporaryDirectory(prefix="commentary-intake-") as temp:
        archive = Path(temp) / "sword.zip"
        receipt = fetch(manifest["sword_zip_url"], archive, manifest["provider"])
        if stage == "2" and receipt["sha256"] != manifest["archive_sha256"]:
            raise PilotError("Original SWORD archive SHA-256 changed; do not silently repin")
        metadata = inspect_archive(archive, source_kind="sword",
                                   expected_module_id=manifest["module_id"],
                                   expected_category="commentary")
        conf = metadata["sword_conf"]
        if conf["version"] != manifest["version"] or conf["language"] != manifest["language"]:
            raise PilotError("Original SWORD .conf release identity/language mismatch")
        if conf["driver"] not in COMMENTARY_DRIVERS:
            raise PilotError("Unexpected original commentary driver")
        # A licensor's declaration is metadata evidence, NOT a legal determination.
        if "public domain" not in (conf["distribution_license"] or "").lower():
            raise PilotError("Actual .conf lacks the declared Public Domain license claim")
        scanner_config = {"pilots": {resource_id: {
            "module_id": manifest["module_id"],
            "category": "commentary",
            "sample_references": manifest["sample_references"],
        }}}
        reader_exe = reader or shutil.which("diatheke")
        if not reader_exe:
            raise PilotError("Actual diatheke reader required for commentary observation")
        sample = scan_sword_entries(resource_id, archive, config=scanner_config,
                                    diatheke=reader_exe)
        # A 19-byte `John 3:16` response can be just a reference echo.
        # This is an advisory signal, not proof the author omitted material:
        # the commentary may be indexed by an enclosing passage range.
        for probe in sample["samples"]:
            probe["short_response_needs_entry_mapping_review"] = probe["bytes"] < 64
        confirmed = all(probe["successful"] and not probe["short_response_needs_entry_mapping_review"]
                        for probe in sample["samples"])
        report.update({
            "status": "observed_not_approved" if stage == "observe"
                      else "pinned_sword_observed_source_comparison_pending",
            "download_performed": True,
            "archive_sha256": receipt["sha256"],
            "archive_bytes": receipt["bytes"],
            "archive_pin_matches": stage == "2",
            "sword_conf": conf,
            "archive_member_count": metadata["member_count"],
            "unpacked_bytes": metadata["total_unpacked_bytes"],
            "reader_samples": sample["samples"],
            "reader_samples_all_present": confirmed,
            "reader_samples_needing_mapping_review": [
                probe["reference"] for probe in sample["samples"]
                if probe["short_response_needs_entry_mapping_review"]
            ],
            "source_to_sword_comparison_performed": False,
        })
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--stage", choices=("1", "observe", "2", "auto"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = inspect_resource(args.resource_id, args.stage)
        code = 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        report = {
            "schema_version": 1, "resource_id": args.resource_id,
            "stage": args.stage, "status": "blocked",
            "diagnostic": str(exc), "published": False,
            "no_text_transformed": True
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"Commentary intake {args.resource_id}: {report['status']}; metadata-only report {args.report}")
    if code:
        print(report["diagnostic"], file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
