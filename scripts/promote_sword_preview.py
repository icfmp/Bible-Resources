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
DRIVER_LAYOUT = {
    "RawText": ("rawtext", ("nt", "nt.vss", "ot", "ot.vss")),
    "zText": ("ztext", tuple(
        f"{book}.{extension}"
        for book in ("nt", "ot")
        for extension in ("bzs", "bzv", "bzz")
    )),
}
MAX_ARCHIVE_MEMBER_BYTES = 40_000_000
MAX_TOTAL_DATA_BYTES = 240_000_000


def _require_config_fields(raw: bytes, *, module_id: str, path: str,
                           driver: str, versification: str,
                           final: bool = False) -> dict[str, str]:
    """Check effective SWORD metadata without collapsing repeated option filters."""
    if len(raw) > 16_000:
        raise ValueError("SWORD module metadata too large")
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != f"[{module_id}]" or any(
            line.startswith("[") and line.endswith("]") for line in lines[1:]):
        raise ValueError("Unverified SWORD metadata section identity")
    sensitive = ("DataPath", "ModDrv", "Versification", "Encoding",
                 "BlockType", "CompressType", "Version",
                 "DistributionLicense", "CipherKey")
    seen = {}
    for line in lines[1:]:
        if "=" not in line or line.lstrip().startswith(("#", ";")):
            continue
        name, value = line.split("=", 1)
        if name in sensitive:
            if name in seen:
                raise ValueError("Duplicate critical SWORD metadata field")
            seen[name] = value
    expected = {
        "DataPath": "./" + path,
        "ModDrv": driver,
        "Versification": versification,
        "Encoding": "UTF-8",
    }
    if any(seen.get(k) != v for k, v in expected.items()):
        raise ValueError("Module driver, path, charset or versification differs")
    if seen.get("CipherKey") is not None:
        raise ValueError("Encrypted SWORD module cannot be promoted")
    if driver == "zText":
        if (seen.get("BlockType") not in {"BOOK", "CHAPTER", "VERSE"}
                or seen.get("CompressType") not in {"ZIP", "LZSS", "BZIP2", "XZ"}):
            raise ValueError("Unknown compressed SWORD block type")
    if final and (not seen.get("DistributionLicense")
                  or not seen.get("Version")):
        raise ValueError("Reviewed final metadata must declare rights and version")
    return seen



def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def promote(source: Path, destination: Path, *, expected_source_sha256: str,
            source_id: str, destination_id: str, config: Path,
            driver: str = "RawText", versification: str = "Segond") -> dict:
    if not all(MODULE_ID.fullmatch(s) for s in (source_id, destination_id)):
        raise ValueError("Invalid SWORD module ID")
    if source_id == destination_id or not re.fullmatch(r"[a-f0-9]{64}", expected_source_sha256):
        raise ValueError("Unverified or identical module identity")
    if source.resolve() == destination.resolve() or destination.exists() or destination.is_symlink():
        raise ValueError("Refusing an unsafe or existing output path")
    if source.is_symlink() or config.is_symlink():
        raise ValueError("Symlinked package/config is forbidden")
    if driver not in DRIVER_LAYOUT or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9]{1,31}", versification):
        raise ValueError("Unknown SWORD driver or versification")
    layout, filenames = DRIVER_LAYOUT[driver]
    original = source.read_bytes()
    if digest(original) != expected_source_sha256:
        raise ValueError("SWORD source ZIP SHA-256 changed")
    old_dir = f"modules/texts/{layout}/{source_id.lower()}/"
    new_dir = f"modules/texts/{layout}/{destination_id.lower()}/"
    expected = {f"mods.d/{source_id.lower()}.conf", *(old_dir + f for f in filenames)}
    with ZipFile(source) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(expected):
            raise ValueError("Corrupt or unexpected SWORD ZIP")
        if set(archive.namelist()) != expected:
            raise ValueError("Unexpected SWORD input inventory")
        if any(i.is_dir() or ((i.external_attr >> 16) & 0o170000)
               not in (0, 0o100000) or i.file_size > MAX_ARCHIVE_MEMBER_BYTES
               for i in archive.infolist()):
            raise ValueError("Unsafe ZIP member")
        if sum(i.file_size for i in archive.infolist()) > MAX_TOTAL_DATA_BYTES:
            raise ValueError("Oversized SWORD ZIP")
        source_fields = _require_config_fields(
            archive.read(f"mods.d/{source_id.lower()}.conf"),
            module_id=source_id, path=old_dir, driver=driver,
            versification=versification)
        data = {new_dir + f: archive.read(old_dir + f) for f in filenames}
    revised = config.read_bytes()
    destination_fields = _require_config_fields(
        revised, module_id=destination_id, path=new_dir,
        driver=driver, versification=versification, final=True)
    if driver == "zText" and any(
            source_fields[k] != destination_fields[k]
            for k in ("BlockType", "CompressType")):
        raise ValueError("Compressed SWORD algorithm or block size changed")
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
        "driver": driver,
        "versification": versification,
        "published": False,
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
    parser.add_argument("--driver", choices=sorted(DRIVER_LAYOUT), default="RawText")
    parser.add_argument("--versification", default="Segond")
    arguments = parser.parse_args()
    result = promote(arguments.source, arguments.output,
                     expected_source_sha256=arguments.expected_sha256,
                     source_id=arguments.source_id, destination_id=arguments.module_id,
                     config=arguments.config, driver=arguments.driver,
                     versification=arguments.versification)
    import json
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
