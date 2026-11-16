#!/usr/bin/env python3
"""Read-only cross-edition SWORD release preflight using existing production gates.

This is NOT another importer, source-audit implementation, or publication
workflow. It invokes the exact source/rights validator, deterministic builder,
catalogue/plan coverage gate and immutable asset verifier already used by
production. It never calls GitHub or modifies a release/catalogue.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from build import build
from catalogue_release_coverage import coverage
from publish_reviewed_release import approved_release
from validate import ROOT, parse_conf, validate


class PreflightError(ValueError):
    """An exact checked-in source, SWORD payload or release plan failed review."""


def inspect_approved_releases(root: Path, module_ids: tuple[str, ...]) -> dict:
    """Verify selected actual curated editions offline, across SWORD drivers.

    Result includes verified fingerprints, never source text, approved legal
    conclusions beyond the pinned receipt, or public publication claims.
    """
    root = Path(root).resolve()
    if (not root.is_dir() or root.is_symlink() or not module_ids
            or len(set(module_ids)) != len(module_ids)
            or any(not isinstance(v, str) or not v or '/' in v or '..' in v
                   for v in module_ids)):
        raise PreflightError("Expected distinct, safe curated module IDs")
    approved, errors = validate(root)
    if errors:
        raise PreflightError("Repository source/rights validation failed: "
                             + "; ".join(errors[:10]))
    by_id = {meta["id"]: (folder, meta) for folder, meta in approved
             if meta["quality"]["status"] == "approved"}
    unknown = set(module_ids) - set(by_id)
    if unknown:
        raise PreflightError("Requested unapproved/missing modules: "
                             + ", ".join(sorted(unknown)))
    with tempfile.TemporaryDirectory(prefix="sword-release-preflight-") as work:
        dist = Path(work) / "dist"
        build(root=root, output=dist)
        release_contract = coverage(root, built=dist)
        plans = {p["module_id"]: p
                 for _, p in release_contract["planned"]}
        legacy = {p["module_id"]: p for p in release_contract["legacy"]}
        evidence = []
        for resource_id in module_ids:
            folder, meta = by_id[resource_id]
            plan = plans.get(resource_id)
            historic = legacy.get(resource_id)
            if (plan is None) == (historic is None):
                raise PreflightError(
                    resource_id + ": ambiguous or missing current release route")
            if plan:
                path = root / "config/release-plans" / (plan["tag"] + ".json")
                checked = approved_release(root, path, dist)
                archive = checked["package"]
                evidence_file = checked["evidence"]
            else:
                # LSG is deliberately a *frozen historical* release binding:
                # its public Pages ZIP and versioned GitHub asset have
                # different, independently pinned checksums. Never make up
                # an active plan or claim the old GitHub ZIP was downloaded.
                archive = dist / "sword/packages" / (meta["sword_id"] + ".zip")
                evidence_file = folder / "SOURCE_VALIDATION.json"
                if not evidence_file.is_file():
                    raise PreflightError(resource_id + ": no source receipt")
                payload = folder / "payload"
                actual = {
                    p.relative_to(payload).as_posix(): p
                    for p in payload.rglob("*") if p.is_file()
                }
                with ZipFile(archive) as package:
                    if (len(package.infolist()) != len(actual)
                            or set(package.namelist()) != set(actual)
                            or package.testzip() is not None
                            or any(p.is_symlink() or package.read(rel) != p.read_bytes()
                                   for rel, p in actual.items())):
                        raise PreflightError(
                            resource_id + ": archived Pages payload member drift")
            conf_paths = list((folder / "payload/mods.d").glob("*.conf"))
            if len(conf_paths) != 1:
                raise PreflightError(resource_id + ": ambiguous native .conf")
            native_id, conf = parse_conf(conf_paths[0])
            if native_id != meta["sword_id"]:
                raise PreflightError(resource_id + ": SWORD header identity mismatch")
            driver = conf.get("ModDrv")
            if driver not in ("RawText", "zText", "RawCom", "RawCom4",
                              "zCom", "zCom4"):
                raise PreflightError(resource_id + ": unsupported driver for this pilot")
            fingerprint = sha256(archive.read_bytes()).hexdigest()
            reference = plan or historic
            expected_hash = (plan["package_sha256"] if plan else
                             historic["catalogue_sha256"])
            expected_size = (plan["package_size_bytes"] if plan else
                             historic["catalogue_size_bytes"])
            if (fingerprint != expected_hash or archive.stat().st_size
                    != expected_size):
                raise PreflightError(
                    resource_id + ": compiled catalogue ZIP differs from frozen release route")
            evidence.append({
                "resource_id": resource_id,
                "sword_id": native_id,
                "category": meta["category"],
                "driver": driver,
                "versification": conf.get("Versification"),
                "version": meta["version"],
                "release_tag": reference["tag"],
                "release_route": ("current_reviewed_plan" if plan
                                  else "frozen_historical_binding"),
                "historical_github_asset_sha256":
                    historic["release_sha256"] if historic else None,
                "historical_github_asset_verified_online": False,
                "package_sha256": fingerprint,
                "package_size_bytes": archive.stat().st_size,
                "source_validation_sha256":
                    sha256(evidence_file.read_bytes()).hexdigest(),
                "source_rights_approved_in_pinned_module":
                    bool(meta["rights"]["redistribution_allowed"]),
                "native_payload_member_identity_verified": True,
                "release_authorization_verified_in_current_plan": bool(plan),
                "frozen_historical_evidence_verified": bool(historic),
                "public_download_checked": False,
            })
    return {
        "status": "OFFLINE_APPROVED_RELEASE_PREFLIGHT_NOT_PUBLICATION",
        "schema_version": 1,
        "modules": evidence,
        "source_text_exported": False,
        "module_content_mutated": False,
        "public_release_created": False,
        "catalogue_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--module-id", action="append", required=True,
                        help="One current approved curated resource ID; repeatable")
    parser.add_argument("--report", type=Path, required=True,
                        help="Metadata-only JSON report path outside source tree")
    args = parser.parse_args()
    report = args.report.resolve()
    if report.is_relative_to(args.root.resolve()):
        parser.error("Preflight receipts must be written outside the repository")
    result = inspect_approved_releases(args.root, tuple(args.module_id))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("Offline SWORD source/release preflight: "
          + ", ".join(v["resource_id"] for v in result["modules"]) + " VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
