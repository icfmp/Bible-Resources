#!/usr/bin/env python3
"""Read-only comparison of local, curated and upstream SWORD module versions."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.request
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE = 16 * 1024 * 1024
MAX_CONF = 512 * 1024
MAX_MODULES = 15000
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")
VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+)*(?:[-+][A-Za-z0-9.-]+)?$")


def version_cmp(a: str | None, b: str | None) -> int | None:
    """Compare only unambiguous dotted numeric versions."""
    if not a or not b or not VERSION_PATTERN.fullmatch(a) or not VERSION_PATTERN.fullmatch(b):
        return None
    if any(x in s for s in (a, b) for x in "-+"):
        return 0 if a == b else None
    av = [int(x) for x in a.split(".")]
    bv = [int(x) for x in b.split(".")]
    av += [0] * (max(len(av), len(bv)) - len(av))
    bv += [0] * (max(len(av), len(bv)) - len(bv))
    return (av > bv) - (av < bv)


def parse_conf(data: bytes) -> dict:
    """Read SWORD .conf, preserving first occurrence of keys with repeated History lines."""
    content = data.decode("utf-8-sig", errors="replace")
    values = {}
    module_id = None
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            if module_id is None:
                module_id = line[1:-1]
            continue
        if "=" in line and module_id:
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip())
    if not module_id or not ID_PATTERN.fullmatch(module_id):
        raise ValueError("Invalid SWORD module identifier")
    # Metadata for read-only cross-repository candidate comparison. These
    # values are clues, never proof that two SWORD modules contain the same
    # copyrighted edition or the same binary data.
    driver = values.get("ModDrv", "")
    category = (
        "bible" if driver in {"RawText", "RawText4", "zText", "zText4"} else
        "commentary" if driver in {"RawCom", "RawCom4", "zCom", "zCom4", "HREFCom"} else
        "dictionary" if driver in {"RawLD", "RawLD4", "zLD"} else
        "general_book" if driver in {"RawGenBook", "RawFiles"} else "unknown"
    )
    return {
        "module_id": module_id,
        "version": values.get("Version"),
        "conf_sha256": hashlib.sha256(data).hexdigest(),
        "install_source": values.get("InstallSourceID") or values.get("InstallSourceCaption"),
        "category": category,
        "description": values.get("Description"),
        "language": values.get("Lang"),
        "versification": values.get("Versification"),
        "driver": driver,
        "source_type": values.get("SourceType"),
        "text_source": values.get("TextSource"),
        "distribution_license": values.get("DistributionLicense"),
    }


def https_read(url: str, maximum: int) -> bytes:
    if urlsplit(url).scheme != "https":
        raise ValueError("Only HTTPS upstream URLs are allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "BibleResources-UpstreamCheck/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        if urlsplit(response.url).scheme != "https":
            raise ValueError("Redirected to non-HTTPS URL")
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("Upstream response exceeds size limit")
    return data


def archive_catalog(data: bytes) -> dict[str, dict]:
    """Read metadata inside a tar.gz without extracting remote archive paths."""
    if len(data) > MAX_ARCHIVE:
        raise ValueError("Catalog exceeds size limit")
    found = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) > 2 * MAX_MODULES:
            raise ValueError("Too many catalog entries")
        for entry in members:
            path = PurePosixPath(entry.name.removeprefix("./")).parts
            if not entry.isfile() or len(path) != 2 or path[0] != "mods.d" or not path[1].endswith(".conf") or entry.size > MAX_CONF:
                continue
            stream = archive.extractfile(entry)
            if stream is None:
                continue
            conf = parse_conf(stream.read(MAX_CONF + 1))
            key = conf["module_id"].casefold()
            if key in found:
                raise ValueError("Duplicate SWORD module ID in upstream catalog")
            found[key] = conf
            if len(found) > MAX_MODULES:
                raise ValueError("Too many modules")
    return found


def installed_catalog(roots: list[Path]) -> tuple[dict[str, dict], list[str]]:
    versions, warnings = {}, []
    for root in roots:
        if not root.is_dir():
            warnings.append(f"Local root not found: {root}")
            continue
        for path in sorted((root / "mods.d").glob("*.conf")):
            try:
                conf = parse_conf(path.read_bytes())
                key = conf["module_id"].casefold()
                if key in versions:
                    warnings.append(f"Duplicate installed module: {conf['module_id']}")
                else:
                    versions[key] = conf | {"path": str(path)}
            except (OSError, ValueError) as exc:
                warnings.append(f"Invalid local config {path}: {exc}")
    return versions, warnings


def read_manifests(root: Path) -> list[dict]:
    items = []
    for path in sorted((root / "modules").glob("*/metadata.json")):
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


def provider_catalog(provider: dict) -> dict[str, dict]:
    return archive_catalog(https_read(provider.get("catalogue_url") or urljoin(provider["base_url"], "mods.d.tar.gz"), MAX_ARCHIVE))


def fetch_direct_conf(provider: dict, module_id: str, conf_filename: str | None = None) -> dict:
    filename = conf_filename or module_id.lower() + ".conf"
    if filename != PurePosixPath(filename).name or not re.fullmatch(r"[A-Za-z0-9_-]+\.conf", filename):
        raise ValueError("Unsafe upstream config filename")
    result = parse_conf(https_read(urljoin(provider["base_url"], "mods.d/" + filename), MAX_CONF))
    if result["module_id"].casefold() != module_id.casefold():
        raise ValueError("Upstream module ID mismatch")
    return result


def reviewed_upstream_reconciliation(link: dict, remote: dict | None) -> dict | None:
    """Match an explicitly reviewed *exact upstream release*, not PR status.

    SWORD .conf version/hash only identifies the release recorded during manual
    content review. The scheduled checker does NOT fetch or rehash binaries.
    """
    if not remote:
        return None
    for entry in link.get("reconciliations", []):
        if (entry.get("upstream_version") == remote.get("version")
                and entry.get("upstream_conf_sha256") == remote.get("conf_sha256")):
            return entry
    return None


def compare_link(link: dict, remote: dict | None) -> str:
    if remote is None:
        return "missing_upstream"
    comparison = version_cmp(remote.get("version"), link["last_integrated_version"])
    if comparison is None:
        return "needs_review"
    if comparison < 0:
        return "upstream_older_than_baseline"
    reconciliation = reviewed_upstream_reconciliation(link, remote)
    if reconciliation and reconciliation.get("result") == "equivalent_to_curated":
        return "our_contribution_returned_upstream"
    if comparison > 0:
        return "upstream_update_available"
    if link.get("last_integrated_conf_sha256") and link["last_integrated_conf_sha256"] != remote["conf_sha256"]:
        return "upstream_metadata_changed"
    return "up_to_date"


def check(providers: list[dict], manifests: list[dict], installed: dict,
          *, fetch_catalog=provider_catalog, fetch_conf=fetch_direct_conf,
          external_sources: list[dict] | None = None) -> dict:
    status, inventories, rows = {}, {}, []
    lookup = {p["id"]: p for p in providers}
    for provider in providers:
        pid = provider["id"]
        if not provider["enabled"]:
            status[pid] = {"status": "disabled", "reason": provider.get("notes", "")}
            continue
        try:
            inventories[pid] = fetch_catalog(provider)
            status[pid] = {"status": "ok", "modules_in_catalog": len(inventories[pid])}
        except Exception as exc:
            status[pid] = {"status": "unavailable", "error": str(exc)}
            inventories[pid] = {}

    for module in manifests:
        local = installed.get(module["sword_id"].casefold())
        row = {
            "id": module["id"],
            "sword_id": module["sword_id"],
            "curated_version": module["version"],
            "installed_version": local["version"] if local else None,
            "installed_source": local.get("install_source") if local else None,
            "installed_path": local.get("path") if local else None,
            "upstreams": [],
        }
        # No comparison of installed versus curated without verifying edition identity.
        for link in module.get("upstreams", []):
            provider = lookup.get(link["provider"])
            item = {
                "provider": link["provider"],
                "module_id": link["module_id"],
                "last_integrated_version": link["last_integrated_version"],
            }
            if not provider or not provider["enabled"]:
                item["status"] = "provider_disabled_or_unknown"
                row["upstreams"].append(item)
                continue
            remote = inventories[provider["id"]].get(link["module_id"].casefold())
            if status[provider["id"]]["status"] == "ok":
                item["checked_via"] = "sword_catalog"
            # eBible may update individual .conf files before its tar.gz index.
            try:
                remote = fetch_conf(provider, link["module_id"], link.get("conf_filename"))
                item["checked_via"] = "direct_conf"
            except Exception as exc:
                item["direct_check_warning"] = str(exc)
            if remote is None and status[provider["id"]]["status"] != "ok":
                item["status"] = "upstream_unavailable"
            else:
                item["status"] = compare_link(link, remote)
            item["upstream_version"] = remote.get("version") if remote else None
            item["upstream_conf_sha256"] = remote.get("conf_sha256") if remote else None
            contributions = link.get("contributions", [])
            if contributions:
                item["our_contributions"] = [
                    {"url": c["url"], "state": c["state"]}
                    for c in contributions
                ]
            reconciliation = reviewed_upstream_reconciliation(link, remote)
            if reconciliation and item["status"] not in {
                "upstream_unavailable", "provider_disabled_or_unknown", "upstream_older_than_baseline"
            }:
                item["reviewed_reconciliation"] = {
                    "result": reconciliation["result"],
                    "contribution_url": reconciliation["contribution_url"],
                    "evidence_url": reconciliation["evidence_url"],
                    "reviewed_by": reconciliation["reviewed_by"],
                    "review_scope": "recorded_exact_upstream_version_and_conf",
                }
            if (item["status"] in {"upstream_update_available", "upstream_metadata_changed"}
                    and any(c.get("state") in {"accepted", "released"} for c in contributions)):
                item["possible_return_of_our_contribution"] = True
                item["review_required"] = True
            if reconciliation and reconciliation.get("result") == "contains_other_changes":
                # Our change may be present, but all additional changes still
                # need ordinary edition/source/rights/fidelity review.
                item["review_required"] = True
            row["upstreams"].append(item)
        rows.append(row)
    return {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "providers": status,
        "external_sources": {source["id"]: {
            "kind": source["kind"], "status": source["monitoring"],
            "reason": source.get("notes", "")
        } for source in (external_sources or [])},
        "modules": rows,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed-root", type=Path, action="append", default=[])
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    config = json.loads((args.root / "config/upstreams.json").read_text(encoding="utf-8"))
    providers = [x for x in config["providers"] if not args.provider or x["id"] in args.provider]
    installed, warnings = installed_catalog(args.installed_root)
    report = check(providers, read_manifests(args.root), installed,
                   external_sources=config.get("external_sources", []))
    report["local_warnings"] = warnings
    result = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(f"Wrote {args.output}: {len(report['modules'])} tracked curated modules")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
