#!/usr/bin/env python3
"""Read-only generic ZIP and SWORD metadata preflight for source intake.

No texts are normalized, patched, committed or published. Safe ZIP inspection
does not extract untrusted archive members to disk.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
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


