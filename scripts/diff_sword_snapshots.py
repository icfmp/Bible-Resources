#!/usr/bin/env python3
"""Read-only, text-free comparison of two snapshots of the SAME SWORD module.

A supplement to check_updates.py: remote .conf version/hash checks alone
cannot detect changed binary content. This audit compares actual file bytes,
not the ZIP compression format. It never imports, edits, approves or publishes
a resource. Both snapshots must be independently acquired and source-attested.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import zipfile

from check_updates import parse_conf, version_cmp

MAX_FILES = 20_000
MAX_FILE = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_CONF = 512 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_PATH_LENGTH = 300
MAX_DIFFERENCES = 50
SUPPORTED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
MODULE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")


class SnapshotError(ValueError):
    """Untrustworthy snapshot or an inapplicable same-module comparison."""


def _name(raw: str) -> str:
    if (not raw or len(raw) > MAX_PATH_LENGTH or "\\" in raw
            or raw.startswith("/") or "\x00" in raw
            or any(ord(x) < 32 or ord(x) == 127 for x in raw)):
        raise SnapshotError("Unsafe SWORD member path")
    parts = raw.split("/")
    if any(not p or p in (".", "..") for p in parts):
        raise SnapshotError("Ambiguous or traversing SWORD path")
    if parts[0] not in ("mods.d", "modules") or len(parts) < 2:
        raise SnapshotError("Unexpected path outside SWORD module layout")
    return raw


def _digest_bytes(chunks, size: int) -> str:
    digest = sha256()
    length = 0
    for chunk in chunks:
        length += len(chunk)
        if length > size:
            raise SnapshotError("Member expanded beyond declared safe length")
        digest.update(chunk)
    if length != size:
        raise SnapshotError("Member truncated during hashing")
    return digest.hexdigest()


def _stream_chunks(stream):
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            break
        yield block


def _read_snapshot(path: Path) -> tuple[dict[str, dict], bytes]:
    """Digest every actual SWORD file, bounded. No extraction or code execution."""
    if path.is_symlink() or not path.exists():
        raise SnapshotError("Missing or symlinked SWORD snapshot")
    files: dict[str, dict] = {}
    folded = set()
    config_bytes = None
    total = 0

    def record(name: str, size: int, source):
        nonlocal config_bytes, total
        name = _name(name)
        folded_name = name.casefold()
        if name in files or folded_name in folded:
            raise SnapshotError("Repeated/case-colliding SWORD payload member")
        if size < 0 or size > MAX_FILE or total + size > MAX_TOTAL:
            raise SnapshotError("SWORD payload exceeds size limit")
        if len(files) >= MAX_FILES:
            raise SnapshotError("Too many SWORD payload members")
        with source() as stream:
            checksum = _digest_bytes(_stream_chunks(stream), size)
        files[name] = {"sha256": checksum, "size": size}
        folded.add(folded_name)
        total += size
        if name.startswith("mods.d/"):
            if not name.endswith(".conf") or size > MAX_CONF or config_bytes is not None:
                raise SnapshotError("Expected precisely one bounded .conf file")
            with source() as stream:
                config_bytes = stream.read(MAX_CONF + 1)
            if len(config_bytes) != size:
                raise SnapshotError("SWORD .conf changed while reading")

    if path.is_dir():
        for entry in sorted(path.rglob("*")):
            if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
                raise SnapshotError("Symlink or nonregular SWORD snapshot entry")
            rel = entry.relative_to(path).as_posix()
            if entry.is_dir():
                # Source may contain normal directories but never escape them.
                _name(rel + "/placeholder")
                continue
            record(rel, entry.stat().st_size, lambda p=entry: p.open("rb"))
    elif path.is_file():
        if path.stat().st_size > MAX_ARCHIVE:
            raise SnapshotError("Oversize SWORD ZIP")
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_FILES * 3:
                    raise SnapshotError("Too many ZIP members")
                for info in entries:
                    name = info.filename
                    if info.flag_bits & 0x1:
                        raise SnapshotError("Encrypted SWORD ZIP is not supported")
                    if info.compress_type not in SUPPORTED_COMPRESSION:
                        raise SnapshotError("Unsupported SWORD ZIP compression")
                    unix_mode = (info.external_attr >> 16) & 0xFFFF
                    if unix_mode and stat.S_IFMT(unix_mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                        raise SnapshotError("SWORD ZIP symlink or special member")
                    if info.is_dir():
                        _name(name.rstrip("/") + "/placeholder")
                        continue
                    record(name, info.file_size, lambda i=info: archive.open(i))
        except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
            raise SnapshotError("Corrupt or unreadable SWORD ZIP") from exc
    else:
        raise SnapshotError("SWORD snapshot must be a directory or ZIP")
    if config_bytes is None or not any(p.startswith("modules/") for p in files):
        raise SnapshotError("Missing SWORD configuration or binary module files")
    return files, config_bytes


def _describe(path: Path, module_id: str) -> dict:
    files, conf_bytes = _read_snapshot(path)
    config = parse_conf(conf_bytes)
    if config["module_id"] != module_id:
        raise SnapshotError("SWORD module identity does not match selected edition")
    if not config.get("driver"):
        raise SnapshotError("Missing SWORD ModDrv")
    manifest = sha256()
    for name, entry in sorted(files.items()):
        encoded = name.encode("utf-8")
        manifest.update(len(encoded).to_bytes(4, "big"))
        manifest.update(encoded)
        manifest.update(entry["size"].to_bytes(8, "big"))
        manifest.update(bytes.fromhex(entry["sha256"]))
    return {
        "files": files,
        "file_manifest_sha256": manifest.hexdigest(),
        "config_sha256": config["conf_sha256"],
        "version": config.get("version"),
        "driver": config.get("driver"),
        "versification": config.get("versification") or "KJV",
        "category": config.get("category"),
    }


def compare_snapshots(previous: Path, candidate: Path, module_id: str) -> dict:
    """Only compare one verified module lineage; otherwise refuse the operation."""
    if not MODULE_ID.fullmatch(module_id):
        raise SnapshotError("Invalid expected SWORD module ID")
    prior = _describe(previous, module_id)
    newer = _describe(candidate, module_id)
    a, b = prior["files"], newer["files"]
    old, new = set(a), set(b)
    added = sorted(new - old)
    removed = sorted(old - new)
    changed = sorted(k for k in old & new if a[k] != b[k])
    bin_changed = any(k.startswith("modules/") for k in added + removed + changed)
    config_changed = prior["config_sha256"] != newer["config_sha256"]
    version_order = version_cmp(newer["version"], prior["version"])
    v11n_changed = prior["versification"] != newer["versification"]
    driver_changed = prior["driver"] != newer["driver"]
    same_files = not (added or removed or changed)
    if v11n_changed or driver_changed:
        status = "native_driver_or_versification_changed_requires_review"
    elif same_files:
        status = "file_bytes_identical_not_source_equivalence"
    elif version_order == 0:
        status = ("same_version_binary_payload_changed_requires_review"
                  if bin_changed else "same_version_metadata_changed_requires_review")
    elif version_order == 1:
        status = "newer_upstream_snapshot_requires_review"
    elif version_order == -1:
        status = "older_upstream_snapshot_requires_review"
    else:
        status = "unorderable_version_or_baseline_requires_review"

    return {
        "schema_version": 1,
        "status": status,
        "module_id": module_id,
        "comparison_scope": "same_sword_module_id_file_bytes_only",
        "previous_version": prior["version"],
        "candidate_version": newer["version"],
        "previous_driver": prior["driver"],
        "candidate_driver": newer["driver"],
        "previous_versification": prior["versification"],
        "candidate_versification": newer["versification"],
        "previous_file_manifest_sha256": prior["file_manifest_sha256"],
        "candidate_file_manifest_sha256": newer["file_manifest_sha256"],
        "previous_conf_sha256": prior["config_sha256"],
        "candidate_conf_sha256": newer["config_sha256"],
        "actual_binary_files_changed": bin_changed,
        "config_changed": config_changed,
        "added_file_count": len(added),
        "removed_file_count": len(removed),
        "changed_file_count": len(changed),
        "first_added_paths": added[:MAX_DIFFERENCES],
        "first_removed_paths": removed[:MAX_DIFFERENCES],
        "first_changed_paths": changed[:MAX_DIFFERENCES],
        "full_content_text_compared": False,
        "source_edition_identity_verified": False,
        "authorial_text_or_notes_parity_verified": False,
        "source_redistribution_rights_verified": False,
        "editorial_approval": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.report.exists() or args.report.is_symlink():
            raise SnapshotError("Refusing to overwrite an existing evidence report")
        if not args.report.parent.is_dir() or args.report.parent.is_symlink():
            raise SnapshotError("Existing non-symlink report directory required")
        report = compare_snapshots(args.previous, args.candidate, args.module_id)
        data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".sword-diff-", dir=args.report.parent)
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            if args.report.exists() or args.report.is_symlink():
                raise SnapshotError("Evidence report path appeared during generation")
            os.replace(name, args.report)
        finally:
            Path(name).unlink(missing_ok=True)
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    print(report["status"], "(metadata-only; publication is never authorized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
