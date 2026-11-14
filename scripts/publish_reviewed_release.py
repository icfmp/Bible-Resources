#!/usr/bin/env python3
"""Publish or independently verify GitHub Releases from owner-approved plans.

Source content is never transformed here. Use the already validated,
deterministically built SWORD catalogue ZIP and its reviewed source proof.
Existing tagged releases are immutable: compare, never overwrite assets.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[a-f0-9]{64}\Z")
TAG = re.compile(r"[a-z][a-z0-9-]{2,80}\Z")
SAFE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,63}-(?:[0-9]+\.){2}[0-9]+\.zip\Z")
HEX_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
ALLOWED_FIELDS = {
    "schema_version", "tag", "module_id", "sword_id", "version",
    "title", "zip_name", "package_sha256", "package_size_bytes",
    "notes_path", "evidence_path", "editorial_path", "authorization",
}
AUTH_FIELDS = {"reviewed_by", "decision", "evidence_url", "source_rights"}


class ReleaseError(ValueError):
    """A public release is not fully authorized or its bytes differ."""


def within_root(root: Path, candidate: str, prefix: str) -> Path:
    """Allow only normal reviewed paths under an exact repository directory."""
    if (not isinstance(candidate, str) or candidate.startswith("/")
            or ".." in Path(candidate).parts or "\\" in candidate
            or not candidate.startswith(prefix + "/")):
        raise ReleaseError("Unsafe release evidence path")
    path = root / candidate
    if (path.is_symlink() or not path.is_file()
            or not path.resolve().is_relative_to(root.resolve())):
        raise ReleaseError("Required reviewed release evidence does not exist")
    return path


def approved_release(root: Path, plan_file: Path, built: Path) -> dict:
    """Verify plan, source approval, catalogue identity and real ZIP bytes.

    The repository validator already checks every approved SWORD payload and
    its original data proof. This validates the release-specific manifest
    without modifying a single authorial data member.
    """
    if plan_file.is_symlink() or not plan_file.is_file():
        raise ReleaseError("Unsafe release plan")
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or set(plan) != ALLOWED_FIELDS:
        raise ReleaseError("Unknown or incomplete release plan")
    if (plan["schema_version"] != 1
            or not isinstance(plan["tag"], str) or not TAG.fullmatch(plan["tag"])
            or not isinstance(plan["version"], str) or not HEX_VERSION.fullmatch(plan["version"])
            or not isinstance(plan["zip_name"], str) or not SAFE_NAME.fullmatch(plan["zip_name"])
            or not isinstance(plan["package_sha256"], str)
            or not SHA.fullmatch(plan["package_sha256"])
            or type(plan["package_size_bytes"]) is not int
            or not 0 < plan["package_size_bytes"] <= 100 * 1024 * 1024):
        raise ReleaseError("Release ID, archive fingerprint or version invalid")
    if plan["tag"] != f"{plan['module_id'].replace('-crosswire','')}-{plan['version']}" and not plan["tag"].endswith("-" + plan["version"]):
        raise ReleaseError("Release tag and curated version differ")
    if (not isinstance(plan["title"], str) or not plan["title"].strip()
            or len(plan["title"]) > 140):
        raise ReleaseError("Missing public release title")
    auth = plan["authorization"]
    if (not isinstance(auth, dict) or set(auth) != AUTH_FIELDS
            or not all(isinstance(v,str) and v.strip() for v in auth.values())
            or "PENDING" in auth["reviewed_by"].upper()
            or not auth["evidence_url"].startswith("https://github.com/")):
        raise ReleaseError("Explicit source-specific owner review missing")
    module_id = plan["module_id"]
    if (not isinstance(module_id,str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}",module_id)):
        raise ReleaseError("Invalid module ID")
    mdir = root / "modules" / module_id
    metadata = json.loads(within_root(root,f"modules/{module_id}/metadata.json","modules")
                          .read_text(encoding="utf-8"))
    if (metadata["id"] != module_id or metadata["sword_id"] != plan["sword_id"]
            or metadata["version"] != plan["version"]
            or metadata["quality"]["status"] != "approved"
            or metadata["rights"]["redistribution_allowed"] is not True):
        raise ReleaseError("Release conflicts with reviewed source/rights/edition")
    evidence = within_root(root,plan["evidence_path"],f"modules/{module_id}")
    editorial = within_root(root,plan["editorial_path"],f"modules/{module_id}")
    notes = within_root(root,plan["notes_path"],"docs/releases")
    proof = json.loads(evidence.read_text(encoding="utf-8"))
    if (not isinstance(proof, dict) or proof.get("status") != "validated"
            or not editorial.read_text(encoding="utf-8").strip()
            or len(notes.read_bytes()) < 100):
        raise ReleaseError("Original-source evidence or release notes not reviewed")
    catalogue = json.loads((root / "catalog/v1/catalog.json").read_text(encoding="utf-8"))
    entries = [m for m in catalogue["modules"] if m["id"] == module_id]
    if len(entries) != 1:
        raise ReleaseError("Curated module not uniquely present in official catalogue")
    entry = entries[0]
    if (entry["sword_id"] != plan["sword_id"] or entry["version"] != plan["version"]
            or entry["download"]["sha256"] != plan["package_sha256"]
            or entry["download"]["size_bytes"] != plan["package_size_bytes"]):
        raise ReleaseError("Source-pinned release plan differs from approved catalogue")
    package = built / "sword/packages" / f"{plan['sword_id']}.zip"
    if (not package.is_file() or package.is_symlink()
            or package.stat().st_size != plan["package_size_bytes"]
            or sha256(package.read_bytes()).hexdigest() != plan["package_sha256"]):
        raise ReleaseError("Actual built release ZIP differs from approved immutable bytes")
    # Independent member-level comparison to the current reviewed
    # repository's SWORD payload, not just catalogue metadata.
    payload = mdir / "payload"
    actual = {str(p.relative_to(payload)):p
              for p in payload.rglob("*") if p.is_file()}
    with ZipFile(package) as z:
        names=z.namelist()
        if (len(names) != len(actual) or set(names) != set(actual)
                or z.testzip() is not None):
            raise ReleaseError("SWORD ZIP has missing, extra or corrupt members")
        for name, p in actual.items():
            if p.is_symlink() or z.read(name) != p.read_bytes():
                raise ReleaseError("Original SWORD payload differs from final release archive")
    return dict(plan=plan, package=package, evidence=evidence, notes=notes)


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh",*args],check=check,text=True,
                          capture_output=True,timeout=120)


def publish_one(approved: dict, *, repository: str, target_sha: str) -> None:
    plan = approved["plan"]
    tag = plan["tag"]
    with tempfile.TemporaryDirectory(prefix="verified-release-") as workspace:
        out = Path(workspace)
        src = out / plan["zip_name"]
        shutil.copyfile(approved["package"],src)
        (out/"SHA256SUMS.txt").write_text(
            f"{plan['package_sha256']}  {plan['zip_name']}\n",encoding="ascii")
        shutil.copyfile(approved["evidence"],out/"SOURCE_VALIDATION.json")
        (out/"RELEASE_PROVENANCE.json").write_text(
            json.dumps({
                "schema_version":1, "tag":tag, "module_id":plan["module_id"],
                "sword_id":plan["sword_id"], "version":plan["version"],
                "package_sha256":plan["package_sha256"],
                "package_size_bytes":plan["package_size_bytes"],
                "authorization":plan["authorization"],
                "source_validation_sha256":sha256(approved["evidence"].read_bytes()).hexdigest(),
                "reproducible_builder":"scripts/build.py",
            },indent=2,sort_keys=True) + "\n",encoding="utf-8")
        found = gh("release","view",tag,"--repo",repository,
                   "--json","assets","--jq",".assets[].name",check=False)
        if found.returncode == 0:
            required={plan["zip_name"],"SOURCE_VALIDATION.json",
                      "RELEASE_PROVENANCE.json","SHA256SUMS.txt"}
            if set(found.stdout.splitlines()) != required:
                raise ReleaseError("Existing GitHub Release has unreviewed or missing assets")
        else:
            gh("release","create",tag,str(src),str(out/"SHA256SUMS.txt"),
               str(out/"SOURCE_VALIDATION.json"),
               str(out/"RELEASE_PROVENANCE.json"),
               "--repo",repository,"--target",target_sha,
               "--title",plan["title"],"--notes-file",str(approved["notes"]))
        download = out / "redownloaded"
        download.mkdir()
        gh("release","download",tag,"--repo",repository,
           "--pattern",plan["zip_name"],"--dir",str(download))
        remote = download / plan["zip_name"]
        if (not remote.is_file() or remote.read_bytes() != src.read_bytes()
                or sha256(remote.read_bytes()).hexdigest()!=plan["package_sha256"]):
            raise ReleaseError("Independently downloaded GitHub Release ZIP checksum differs")
        print(f"Verified GitHub Release {tag}: immutable {plan['sword_id']} "
              f"ZIP SHA-256 {plan['package_sha256']}")


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--built",type=Path,required=True)
    parser.add_argument("--repository",required=True)
    parser.add_argument("--target-sha",required=True)
    parser.add_argument("--verify-only",action="store_true")
    args=parser.parse_args()
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",args.repository)
            or not SHA.fullmatch(args.target_sha)):
        raise ReleaseError("Unsafe destination or unreviewed release commit")
    plans = sorted((args.root/"config/release-plans").glob("*.json"))
    if not plans:
        raise ReleaseError("No authorized public GitHub Release plan exists")
    verified=[approved_release(args.root,plan,args.built) for plan in plans]
    for item in verified:
        if args.verify_only:
            print(f"Verified authorized release plan {item['plan']['tag']} "
                  "(no public write)")
        else:
            publish_one(item,repository=args.repository,target_sha=args.target_sha)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
