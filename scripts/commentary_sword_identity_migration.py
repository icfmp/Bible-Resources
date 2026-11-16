#!/usr/bin/env python3
"""Preflight an intentionally renamed SWORD commentary without changing releases.

The reader-facing SWORD module ID is not the curated catalogue resource ID.
This migration is not a same-ID update: the former curated SWORD ID can remain
installed, while the proposed new ID may collide with the original provider.
The plan is metadata-only and NEVER substitutes for the complete native
SWORD/source audit, owner approval or final package checksum.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,79}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")


def _read(root: Path, path: str) -> dict:
    file = root / path
    if (file.is_symlink() or not file.is_file()
            or file.stat().st_size > 256_000
            or ".." in Path(path).parts):
        raise ValueError("Unsafe or unavailable migration evidence")
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Migration evidence must be a JSON object")
    return data


def proposed_sword_identity_migration(
        root: Path, *, resource_id: str, review_path: str) -> dict:
    """Compare reviewed successor ID to the original active catalogue identity.

    The same historic release tag remains protected and the next package
    identity is merely reported, not committed, installed or published.
    """
    if (not isinstance(root, Path) or not root.is_dir() or root.is_symlink()
            or not isinstance(resource_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", resource_id)
            or review_path != "config/commentary-intake/" + resource_id + "-reviewed-links.json"):
        raise ValueError("Untrusted commentary migration request")
    original = _read(root, "modules/" + resource_id + "/metadata.json")
    review = _read(root, review_path)
    catalogue = _read(root, "catalog/v1/catalog.json")
    if (original.get("id") != resource_id
            or original.get("category") != "commentary"
            or original.get("quality", {}).get("status") != "approved"
            or not isinstance(original.get("upstreams"), list)
            or not isinstance(original.get("origin"), dict)
            or not isinstance(catalogue.get("modules"), list)
            or review.get("resource_id") != resource_id
            or review.get("release_authorized") is not False
            or review.get("package_staging_only") is not True):
        raise ValueError("Successor must be independently reviewed before activation")
    previous_id = original.get("sword_id")
    next_id = review.get("proposed_next_sword_id")
    previous_version = original.get("version")
    next_version = review.get("proposed_next_version")
    source_id = review.get("source_module_id")
    if (not all(isinstance(x, str) and ID.fullmatch(x)
                for x in (previous_id, next_id, source_id))
            or previous_id.casefold() == next_id.casefold()
            or source_id != next_id
            or not all(isinstance(x, str) and VERSION.fullmatch(x)
                       for x in (previous_version, next_version))
            or previous_version == next_version
            or not isinstance(review.get("source_archive_sha256"), str)
            or not SHA.fullmatch(review["source_archive_sha256"])
            or review["source_archive_sha256"] not in
               original["origin"].get("source_revision", "")
            or not any(isinstance(x, dict) and x.get("module_id") == source_id
                       for x in original["upstreams"])):
        raise ValueError("Unproven successor source/provider identity or version")
    active = [x for x in catalogue["modules"]
              if isinstance(x, dict) and x.get("id") == resource_id]
    plans = sorted((root / "config/release-plans").glob("*.json"))
    matches = []
    for path in plans:
        candidate = _read(root, "config/release-plans/" + path.name)
        if candidate.get("module_id") == resource_id:
            matches.append(candidate)
    if len(active) != 1 or len(matches) != 1:
        raise ValueError("A successor requires one active catalogue entry and plan")
    old = matches[0]
    current = active[0]
    if (current.get("sword_id") != previous_id
            or current.get("version") != previous_version
            or old.get("sword_id") != previous_id
            or old.get("version") != previous_version
            or old.get("module_id") != resource_id
            or old.get("tag") not in (path.stem for path in plans)
            or old.get("zip_name") != previous_id + "-" + previous_version + ".zip"
            or not isinstance(current.get("download"), dict)
            or current["download"].get("sha256") != old.get("package_sha256")
            or current["download"].get("size_bytes") != old.get("package_size_bytes")
            or current["download"].get("url") !=
               "https://icfmp.github.io/Bible-Resources/sword/packages/" + previous_id + ".zip"):
        raise ValueError("Immutable old release plan/catalogue not source-identical")
    prefix = old["tag"].removesuffix("-" + previous_version)
    if (not prefix or prefix == old["tag"]
            or not re.fullmatch(r"[a-z][a-z0-9-]{1,64}", prefix)):
        raise ValueError("Cannot derive a safe successor release tag")
    for module in catalogue["modules"]:
        if not isinstance(module, dict):
            raise ValueError("Invalid catalogue module row")
        other_id = module.get("sword_id")
        if (module.get("id") != resource_id
                and isinstance(other_id, str)
                and other_id.casefold() == next_id.casefold()):
            raise ValueError("Proposed new SWORD ID already belongs to another curated module")
    new_conf = "mods.d/" + next_id.lower() + ".conf"
    return {
        "status": "PRIVATE_SWORD_ID_MIGRATION_PREFLIGHT_NOT_RELEASE",
        "resource_id": resource_id,
        "previous_sword_id": previous_id,
        "proposed_sword_id": next_id,
        "previous_version": previous_version,
        "proposed_version": next_version,
        "old_release_tag_must_remain_immutable": old["tag"],
        "old_versioned_asset_must_remain_immutable": old["zip_name"],
        "proposed_new_release_tag": prefix + "-" + next_version,
        "proposed_new_versioned_asset": next_id + "-" + next_version + ".zip",
        "proposed_single_catalogue_download":
            "https://icfmp.github.io/Bible-Resources/sword/packages/" + next_id + ".zip",
        "proposed_conf_member": new_conf,
        "proposed_data_path": "modules/comments/zcom/" + next_id.lower() + "/",
        "reuses_original_provider_id": next_id == source_id,
        "may_replace_upstream_module_in_installed_sword_library": True,
        "previous_curated_sword_id_will_not_auto_uninstall": True,
        "fresh_version_specific_description_or_omission_required": True,
        "final_release_date_selected": False,
        "final_package_checksum_known": False,
        "catalogue_changed": False,
        "public_release_authorized": False,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--review", required=True)
    args = parser.parse_args()
    result = proposed_sword_identity_migration(
        ROOT, resource_id=args.resource_id, review_path=args.review
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
