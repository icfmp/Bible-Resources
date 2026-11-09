#!/usr/bin/env python3
"""Promote a fully verified private SWORD trial ZIP without changing its data.

Both archive identities and exact source content must be pinned by the caller.
This tool NEVER compiles, rewrites, renumbers or patches Scripture. It replaces
only the module's published identity, storage path and reviewed .conf metadata.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

MODULE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")
STAMP = (1980, 1, 1, 0, 0, 0)
DATA_FILES = ("nt", "nt.vss", "ot", "ot.vss")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def promote(source: Path, destination: Path, *, expected_source_sha256: str,
            source_id: str, destination_id: str, config: Path) -> dict:
    if not all(MODULE_ID.fullmatch(s) for s in (source_id, destination_id)):
        raise ValueError("Invalid SWORD module ID")
    if source_id == destination_id or not re.fullmatch(r"[a-f0-9]{64}", expected_source_sha256):
        raise ValueError("Unverified or identical module identity")
    if source.resolve() == destination.resolve() or destination.exists() or destination.is_symlink():
        raise ValueError("Refusing an unsafe or existing output path")
    if source.is_symlink() or config.is_symlink():
        raise ValueError("Symlinked package/config is forbidden")
    original = source.read_bytes()
    if digest(original) != expected_source_sha256:
        raise ValueError("SWORD source ZIP SHA-256 changed")
    old_dir = f"modules/texts/rawtext/{source_id.lower()}/"
    new_dir = f"modules/texts/rawtext/{destination_id.lower()}/"
    expected = {f"mods.d/{source_id.lower()}.conf", *(old_dir + f for f in DATA_FILES)}
    with ZipFile(source) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(expected):
            raise ValueError("Corrupt or unexpected SWORD ZIP")
        if set(archive.namelist()) != expected:
            raise ValueError("Unexpected SWORD input inventory")
        if any(i.is_dir() or (i.external_attr >> 16) & 0o170000 == 0o120000
               for i in archive.infolist()):
            raise ValueError("Unsafe ZIP member")
        original_conf = archive.read(f"mods.d/{source_id.lower()}.conf").decode("utf-8")
        if not original_conf.startswith(f"[{source_id}]\n") or (
            "DataPath=./" + old_dir) not in original_conf:
            raise ValueError("Unattested source module identity")
        data = {new_dir + f: archive.read(old_dir + f) for f in DATA_FILES}
    revised = config.read_bytes()
    decoded = revised.decode("utf-8")
    if (not decoded.startswith(f"[{destination_id}]\n")
            or decoded.count("DataPath=") != 1 or ("DataPath=./"+new_dir+"\n") not in decoded
            or "ModDrv=RawText\n" not in decoded
            or "Versification=Segond\n" not in decoded
            or "Encoding=UTF-8\n" not in decoded
            or decoded.count("DistributionLicense=") != 1):
        raise ValueError("Final SWORD metadata is not the reviewed intended identity")
    data[f"mods.d/{destination_id.lower()}.conf"] = revised
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(destination, "x", compression=ZIP_DEFLATED, compresslevel=9) as out:
            for name, value in sorted(data.items()):
                info = ZipInfo(name, STAMP)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                out.writestr(info, value, compress_type=ZIP_DEFLATED, compresslevel=9)
        with ZipFile(destination) as out:
            if out.testzip() is not None or set(out.namelist()) != set(data):
                raise ValueError("Release ZIP did not re-extract correctly")
            if any(out.read(name) != value for name, value in data.items()):
                raise ValueError("Release packaging modified content")
        if digest(source.read_bytes()) != expected_source_sha256:
            raise ValueError("Source ZIP changed during promotion")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {
        "status": "exact_sword_payload_promoted_with_reviewed_metadata",
        "module_id": destination_id,
        "source_zip_sha256": expected_source_sha256,
        "release_zip_sha256": digest(destination.read_bytes()),
        "release_zip_bytes": destination.stat().st_size,
        "data_byte_equal": True,
        "per_file_sha256": {name: digest(data[name]) for name in sorted(data) if name.startswith(new_dir)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    result = promote(arguments.source, arguments.output,
                     expected_source_sha256=arguments.expected_sha256,
                     source_id=arguments.source_id, destination_id=arguments.module_id,
                     config=arguments.config)
    import json
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
