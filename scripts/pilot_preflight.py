#!/usr/bin/env python3
"""Read-only ZIP and SWORD metadata preflight for the two approved pilot IDs.

No texts are normalized, patched, committed or published. Safe ZIP inspection
does not extract untrusted archive members to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

from check_updates import parse_conf

ROOT = Path(__file__).resolve().parents[1]
MAX_ZIP_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 20000
MAX_UNPACKED = 512 * 1024 * 1024
MAX_CONF = 512 * 1024
MAX_RATIO = 10000
APPROVED_DRIVERS = {
    "bible": {"RawText", "zText", "RawText4", "zText4"},
    "commentary": {"RawCom", "RawCom4", "zCom", "zCom4"},
}


class PilotError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(data)
    return hasher.hexdigest()


def inspect_archive(path: Path, *, source_kind: str, expected_module_id: str | None = None,
                    expected_category: str | None = None) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ZIP_BYTES:
        raise PilotError(f"{source_kind}: expected regular ZIP under {MAX_ZIP_BYTES} bytes")
    report = {
        "archive_sha256": sha256_file(path),
        "archive_bytes": path.stat().st_size,
        "source_kind": source_kind,
        "members": [],
    }
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if not members or len(members) > MAX_MEMBERS:
            raise PilotError(f"{source_kind}: invalid archive entry count")
        uncompressed = 0
        seen = set()
        confs = []
        for member in members:
            name = member.filename
            # No absolute paths, backslashes, traversal, symbolic links, or
            # duplicate names: never make assumptions about zip extract().
            pure = PurePosixPath(name)
            if (not name or name.startswith("/") or "\\" in name or
                any(part in {"", ".", ".."} for part in pure.parts) or
                (member.external_attr >> 16) & 0o170000 == 0o120000):
                raise PilotError(f"{source_kind}: unsafe ZIP entry path/type {name!r}")
            folded = name.rstrip("/").casefold()
            if folded in seen:
                raise PilotError(f"{source_kind}: duplicate ZIP path {name!r}")
            seen.add(folded)
            if member.is_dir():
                continue
            if member.flag_bits & 0x1:
                raise PilotError(f"{source_kind}: encrypted ZIP member {name!r}")
            if member.file_size > MAX_UNPACKED or (
                member.file_size > 1024 * 1024 and
                member.file_size > MAX_RATIO * max(member.compress_size, 1)
            ):
                raise PilotError(f"{source_kind}: suspiciously compressed ZIP member {name!r}")
            uncompressed += member.file_size
            if uncompressed > MAX_UNPACKED:
                raise PilotError(f"{source_kind}: archive exceeds unpacked limit")
            if source_kind == "sword" and pure.parent.name == "mods.d" and pure.suffix == ".conf":
                if member.file_size > MAX_CONF:
                    raise PilotError(f"{source_kind}: .conf is too large")
                confs.append(member)
            report["members"].append({
                "name": name,
                "bytes": member.file_size,
                "crc32": f"{member.CRC:08x}",
            })
        report["member_count"] = len(report["members"])
        report["total_unpacked_bytes"] = uncompressed
        if source_kind == "sword":
            if len(confs) != 1:
                raise PilotError(f"sword: expected exactly one mods.d/*.conf, found {len(confs)}")
            conf = confs[0]
            try:
                parsed = parse_conf(archive.read(conf))
            except (UnicodeError, ValueError) as exc:
                raise PilotError(f"sword: invalid .conf ({exc})") from exc
            if expected_module_id is not None and parsed["module_id"].casefold() != expected_module_id.casefold():
                raise PilotError(f"sword: module ID mismatch: {parsed['module_id']!r}, expected {expected_module_id!r}")
            if parsed["category"] != expected_category or parsed["driver"] not in APPROVED_DRIVERS.get(expected_category, set()):
                raise PilotError(f"sword: unexpected category or driver: {parsed['category']}/{parsed['driver']}")
            if not any(PurePosixPath(name).parts[0] == "modules" for name in (m["name"] for m in report["members"])):
                raise PilotError("sword: no modules/ payload in archive")
            report["sword_conf"] = {
                **parsed, "entry": conf.filename, "encoding_checked": "metadata_only"
            }
    return report


def inspect_pilot(pilot: str, sword_archive: Path, authored_archive: Path | None = None,
                  *, config: dict) -> dict:
    if config.get("schema_version") != 1 or pilot not in config.get("pilots", {}):
        raise PilotError("Invalid pilot source configuration or unknown pilot")
    entry = config["pilots"][pilot]
    if bool(authored_archive) != bool(entry.get("authored_zip_url")):
        raise PilotError("Source archive must be supplied exactly when this pilot declares one")
    result = {
        "schema_version": 1,
        "pilot": pilot,
        "provider": entry["provider"],
        "module_id": entry["module_id"],
        "category": entry["category"],
        "source_page": entry["source_url"],
        "reference_urls": {
            "sword": entry["sword_zip_url"],
            "authored": entry.get("authored_zip_url"),
        },
        "approved_for_publication": False,
        "original_bytes_preserved": True,
        "inspection_only": True,
        "sword": inspect_archive(sword_archive, source_kind="sword",
                                 expected_module_id=entry["module_id"],
                                 expected_category=entry["category"]),
    }
    if authored_archive:
        result["authored"] = inspect_archive(authored_archive, source_kind="authored")
        result["authored"]["format_claim"] = entry["authored_format"]
        # Merely having both ZIPs does not prove an actual verse-level match.
        result["source_to_sword_text_verified"] = False
    result["remaining_gates"] = [
        "license and exact edition review",
        "official pinned OSIS/USFM source validation",
        "source-to-SWORD complete text, notes and reference fidelity",
        "versification and missing-verses audit",
        "real diatheke and Bible GTK before/after review",
        "human editorial approval",
    ]
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=("lsg", "mhc"), required=True)
    parser.add_argument("--sword-zip", type=Path, required=True)
    parser.add_argument("--authored-zip", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "config/pilot-sources.json")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        report = inspect_pilot(args.pilot, args.sword_zip, args.authored_zip, config=config)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        report = {"status": "blocked", "pilot": args.pilot, "error": str(exc),
                  "approved_for_publication": False}
        result_code = 1
    else:
        report["status"] = "inspected_not_approved"
        result_code = 0
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(f"Pilot {args.pilot}: {report['status']}; report: {args.report}")
    if result_code:
        print(report["error"], file=sys.stderr)
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
