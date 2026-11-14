#!/usr/bin/env python3
"""Fail closed if the official catalogue lacks a matching versioned GitHub Release.

This is a RELEASE-COVERAGE contract, not a new source importer.
Every approved catalogue module must be backed by ONE:
- a source-specific approved release plan for the *exact same* catalogue ZIP,
  whose GitHub Release will be created/verified BEFORE Pages can be deployed;
- an explicitly frozen historical release record with independently pinned
  versioned ZIP and catalogue bytes. Legacy differences are never silently
  converted into assertions of content equivalence.

The historical list is a migration record only: new modules need approved
plans. No network access is needed for PR/local validation; the Pages
workflow separately checks actual downloaded GitHub release assets.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
TAG = re.compile(r"[a-z][a-z0-9-]+-(?:[0-9]+\.){2}[0-9]+\Z")


class ReleaseCoverageError(ValueError):
    """Catalogue and its GitHub-release authorizations are out of sync."""


def read_json(path: Path, *, limit: int = 3_000_000):
    """Read a bounded, non-symlinked trusted repository declaration."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ReleaseCoverageError(f"Missing or unsafe release evidence: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ReleaseCoverageError(f"Invalid release evidence: {path}: {exc}") from exc


def check_digest(value: object, where: str) -> None:
    if not isinstance(value,str) or not SHA.fullmatch(value):
        raise ReleaseCoverageError(f"{where}: missing exact SHA-256")


def check_size(value: object, where: str) -> None:
    if type(value) is not int or not 0 < value <= 100 * 1024 * 1024:
        raise ReleaseCoverageError(f"{where}: invalid package size")


def coverage(root: Path = ROOT, *, built: Path | None = None) -> dict:
    """Resolve exactly one immutable release route per approved catalogue entry.

    Never infer approval from presence of a ZIP or a matching display title.
    The source-specific plan verifier adds rights and actual member parity.
    """
    root = Path(root)
    snapshot = read_json(root / "catalog/v1/catalog.json")
    if (not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1
            or not isinstance(snapshot.get("modules"), list)):
        raise ReleaseCoverageError("Missing reviewed catalogue snapshot")
    items = snapshot["modules"]
    ids = [m.get("id") for m in items if isinstance(m,dict)]
    if len(ids) != len(items) or len(set(ids)) != len(ids):
        raise ReleaseCoverageError("Duplicate or invalid catalogue identities")
    present = {m["id"]:m for m in items}
    approved = {}
    for d in (root/"modules").iterdir():
        if not d.is_dir() or d.is_symlink():
            continue
        m = read_json(d/"metadata.json",limit=64_000)
        if m.get("quality",{}).get("status") != "approved":
            continue
        if m.get("id") != d.name or m.get("sword_id") is None:
            raise ReleaseCoverageError(f"{d}: approved module identity mismatch")
        approved[d.name]=m
    if set(present)!=set(approved):
        raise ReleaseCoverageError("Approved modules and catalogue snapshot differ")
    plans = {}
    plan_dir = root/"config/release-plans"
    for file in sorted(plan_dir.glob("*.json")):
        plan = read_json(file,limit=64_000)
        key = plan.get("module_id") if isinstance(plan,dict) else None
        if not isinstance(key,str) or not NAME.fullmatch(key) or key in plans:
            raise ReleaseCoverageError("Duplicate or invalid reviewed release plan")
        if file.name != plan.get("tag","") + ".json":
            raise ReleaseCoverageError(f"{file}: release plan filename must match tag")
        plans[key]=(file,plan)
    legacy = read_json(root/"config/release-legacy-bindings.json",limit=64_000)
    if (not isinstance(legacy,dict) or set(legacy)!={"schema_version","purpose","reviewed_by","entries"}
            or legacy["schema_version"]!=1 or not legacy["reviewed_by"]
            or not isinstance(legacy["entries"],list)):
        raise ReleaseCoverageError("Unreviewed or malformed historical release registry")
    legacy_by_id={}
    allowed_legacy={
        "module_id","sword_id","version","tag","asset_name",
        "release_sha256","release_size_bytes",
        "catalogue_sha256","catalogue_size_bytes","legacy_package_differs",
        "evidence_url","notes",
    }
    for old in legacy["entries"]:
        if not isinstance(old,dict) or set(old)!=allowed_legacy:
            raise ReleaseCoverageError("Incomplete or unexpected historical release record")
        key=old["module_id"]
        if key in legacy_by_id or not isinstance(key,str) or not NAME.fullmatch(key):
            raise ReleaseCoverageError("Duplicate historical release module")
        if not old["notes"] or not old["evidence_url"].startswith(
                "https://github.com/icfmp/Bible-Resources/releases/tag/"):
            raise ReleaseCoverageError("Missing exact historical rights/release evidence")
        check_digest(old["release_sha256"],key+" historical release")
        check_digest(old["catalogue_sha256"],key+" historical Pages")
        check_size(old["release_size_bytes"],key+" historical release")
        check_size(old["catalogue_size_bytes"],key+" historical Pages")
        differs=(old["release_sha256"] != old["catalogue_sha256"]
                 or old["release_size_bytes"] != old["catalogue_size_bytes"])
        if type(old["legacy_package_differs"]) is not bool or differs!=old["legacy_package_differs"]:
            raise ReleaseCoverageError("Historical package difference must be explicitly recorded")
        legacy_by_id[key]=old
    if set(plans)&set(legacy_by_id):
        raise ReleaseCoverageError("An edition must not have two publication routes")
    if set(plans)|set(legacy_by_id) != set(present):
        missing=set(present)-(set(plans)|set(legacy_by_id))
        extras=(set(plans)|set(legacy_by_id))-set(present)
        raise ReleaseCoverageError(
            f"Every approved module requires a versioned GitHub Release: missing={sorted(missing)}, extras={sorted(extras)}")
    all_tags=[]
    for key, entry in present.items():
        m=approved[key]
        if (entry.get("sword_id") != m["sword_id"]
                or entry.get("version") != m["version"]
                or not isinstance(entry.get("download"),dict)):
            raise ReleaseCoverageError(f"{key}: catalogue and approved module diverged")
        download=entry["download"]
        check_digest(download.get("sha256"),key+" catalogue")
        check_size(download.get("size_bytes"),key+" catalogue")
        url=("https://icfmp.github.io/Bible-Resources/sword/packages/"
             + m["sword_id"] + ".zip")
        if download.get("url")!=url:
            raise ReleaseCoverageError(f"{key}: unreviewed catalogue package URL")
        if key in plans:
            plan=plans[key][1]
            if (plan.get("schema_version")!=1 or
                plan.get("module_id")!=key or
                plan.get("sword_id")!=m["sword_id"] or
                plan.get("version")!=m["version"] or
                plan.get("package_sha256")!=download["sha256"] or
                plan.get("package_size_bytes")!=download["size_bytes"] or
                not isinstance(plan.get("authorization"),dict) or
                not plan["authorization"].get("reviewed_by")):
                raise ReleaseCoverageError(f"{key}: planned GitHub Release does not match catalogue and approval")
            tag=plan.get("tag")
        else:
            old=legacy_by_id[key]
            tag=old["tag"]
            if (old["sword_id"]!=m["sword_id"] or old["version"]!=m["version"]
                    or old["catalogue_sha256"]!=download["sha256"]
                    or old["catalogue_size_bytes"]!=download["size_bytes"]
                    or old["evidence_url"] !=
                    "https://github.com/icfmp/Bible-Resources/releases/tag/"+tag
                    or old["asset_name"] != m["sword_id"]+"-"+m["version"]+".zip"):
                raise ReleaseCoverageError(f"{key}: historical release no longer matches approved edition")
        if not isinstance(tag,str) or not TAG.fullmatch(tag) or not tag.endswith("-"+m["version"]):
            raise ReleaseCoverageError(f"{key}: release tag/version mismatch")
        all_tags.append(tag)
        if built is not None:
            package=Path(built)/"sword/packages"/(m["sword_id"]+".zip")
            if (not package.is_file() or package.is_symlink()
                    or package.stat().st_size!=download["size_bytes"]
                    or sha256(package.read_bytes()).hexdigest()!=download["sha256"]):
                raise ReleaseCoverageError(f"{key}: actual generated package differs from approved catalogue")
    if len(set(all_tags))!=len(all_tags):
        raise ReleaseCoverageError("Two different resources claim the same release tag")
    return {"planned":list(plans.values()),"legacy":list(legacy_by_id.values()),
            "module_count":len(present)}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--built",type=Path)
    args=parser.parse_args()
    result=coverage(built=args.built)
    print("Verified exact release coverage for "
          f"{result['module_count']} approved resources: "
          f"{len(result['planned'])} full current release plan(s), "
          f"{len(result['legacy'])} pinned historical version(s)")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
