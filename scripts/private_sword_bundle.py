#!/usr/bin/env python3
"""Reproducible *private-only* stock-SWORD module ZIP self-test.

Package is generated under a TemporaryDirectory, then installed in a second
isolated SWORD_PATH and independently read by the released stock SWORD engine.
The ZIP contains ordinary mods.d/ and modules/ entries and is NEVER uploaded
by CI, committed, or declared publication-ready. Public diagnostics contain
file counts and hashes only, no Scripture, annotation or module bytes.
"""
from __future__ import annotations

import configparser
from hashlib import sha256
from pathlib import Path
import re
import shutil
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from pilot_preflight import PilotError
from pilot_subprocess import query,present_key

MODULE_ID=re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,79}$")
MAX_FILES=100
MAX_TOTAL_BYTES=300_000_000
ZIP_TIMESTAMP=(1980,1,1,0,0,0)


def _sha(path:Path) -> str:
    digest=sha256()
    with path.open("rb") as file:
        while chunk:=file.read(1024*1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_package_files(root:Path,module_id:str) -> list[tuple[str,Path]]:
    root=root.resolve(strict=True)
    if not MODULE_ID.fullmatch(module_id):
        raise PilotError("Invalid stock-SWORD package module ID")
    conf=root/"mods.d"/(module_id.lower()+".conf")
    if not conf.is_file() or conf.is_symlink():
        raise PilotError("SWORD module configuration is absent or symlinked")
    text=conf.read_text(encoding="utf-8")
    # SWORD configurations legitimately repeat GlobalOptionFilter.
    # Preserve those without accepting duplicate security-sensitive keys.
    from collections import Counter
    critical=Counter()
    for line in text.splitlines():
        stripped=line.strip()
        if not stripped or stripped.startswith(("#",";","[")):
            continue
        key=stripped.split("=",1)[0].strip().casefold()
        if key in {"datapath","moddrv","versification","distributionlicense"}:
            critical[key]+=1
    if (critical["datapath"]!=1 or critical["moddrv"]!=1
            or any(count>1 for count in critical.values())):
        raise PilotError("Duplicate or missing required SWORD config field")
    parser=configparser.ConfigParser(interpolation=None,strict=False)
    parser.optionxform=str
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        raise PilotError("Malformed SWORD module configuration") from exc
    if parser.sections()!=[module_id]:
        raise PilotError("SWORD module configuration identity does not match")
    section=parser[module_id]
    data_path=section.get("DataPath","")
    if (not data_path.startswith("./modules/")
            or not data_path.endswith("/")
            or "\\" in data_path
            or any(p in ("","..",".") for p in data_path[2:].strip("/").split("/"))
            or section.get("ModDrv") not in ("RawText","zText","RawCom","zCom")):
        raise PilotError("Unsafe/unrecognized SWORD module storage path")
    data_dir=root/data_path[2:]
    if not data_dir.is_dir() or data_dir.is_symlink():
        raise PilotError("Missing actual SWORD module data directory")
    files=[conf]
    files.extend(sorted(p for p in data_dir.rglob("*") if p.is_file() or p.is_symlink()))
    if len(files)<2 or len(files)>MAX_FILES:
        raise PilotError("Unexpected number of packaged SWORD module files")
    relative=[]
    size=0
    for file in files:
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root):
            raise PilotError("Refusing package symlink or out-of-root file")
        rel=file.relative_to(root).as_posix()
        if rel.startswith("/") or any(v in ("","..",".") for v in rel.split("/")):
            raise PilotError("Unsafe ZIP member path")
        size+=file.stat().st_size
        relative.append((rel,file))
    if size==0 or size>MAX_TOTAL_BYTES:
        raise PilotError("SWORD module package payload exceeds allowed bounds")
    return sorted(relative)


def _zip_private_module(root:Path,module_id:str,destination:Path) -> dict:
    files=_validate_package_files(root,module_id)
    with ZipFile(destination,"w",compression=ZIP_DEFLATED,compresslevel=9) as z:
        for relative,path in files:
            info=ZipInfo(relative,date_time=ZIP_TIMESTAMP)
            info.compress_type=ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            info.create_system=3
            z.writestr(info,path.read_bytes(),compress_type=ZIP_DEFLATED,
                       compresslevel=9)
    return {
        "module_file_count":len(files),
        "uncompressed_module_bytes":sum(p.stat().st_size for _,p in files),
        "zip_bytes":destination.stat().st_size,
        "zip_sha256":_sha(destination),
        "source_file_sha256":{name:_sha(path) for name,path in files},
    }


def _extract_into_isolated_sword_home(archive:Path,target:Path,
                                      hashes:dict[str,str]) -> None:
    with ZipFile(archive) as z:
        if set(z.namelist()) != set(hashes) or z.testzip() is not None:
            raise PilotError("SWORD module ZIP inventory/CRC does not match")
        for info in z.infolist():
            path=info.filename
            if (info.is_dir() or path.startswith("/")
                    or any(part in ("","..",".") for part in path.split("/"))
                    or info.file_size>MAX_TOTAL_BYTES):
                raise PilotError("Unsafe SWORD ZIP member encountered")
            output=target/path
            output.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as source,output.open("xb") as dest:
                shutil.copyfileobj(source,dest)
            if _sha(output)!=hashes[path]:
                raise PilotError("SWORD ZIP extraction altered module bytes")


def audit_private_sword_installation(
    root:Path,module_id:str,*, reader:str="diatheke",
    samples:tuple[str,...],
    output_archive:Path | None=None
) -> dict:
    """Prove standard ZIP layout and engine readback; discard ZIP immediately."""
    if (not isinstance(samples, (tuple, list)) or not samples
            or len(samples)>128 or any(not isinstance(passage,str)
                or not passage.strip() or len(passage)>120
                for passage in samples)):
        raise PilotError("SWORD package smoke requires bounded, explicit edition-specific passages")
    with tempfile.TemporaryDirectory(prefix="private-sword-bundle-") as tmp:
        private=Path(tmp)
        archive=private/"candidate.zip"
        build=_zip_private_module(root,module_id,archive)
        with tempfile.TemporaryDirectory(prefix="isolated-sword-install-") as install:
            target=Path(install)
            _extract_into_isolated_sword_home(
                archive,target,build["source_file_sha256"])
            if set(n for n,_ in _validate_package_files(target,module_id)) != set(
                    build["source_file_sha256"]):
                raise PilotError("Isolated SWORD ZIP installation is incomplete")
            probes=[]
            for passage in samples:
                original_code,original=query(
                    module_id,passage,fmt="plain",root=root,
                    exe=reader,limit=256*1024,timeout=30)
                installed_code,installed=query(
                    module_id,passage,fmt="plain",root=target,
                    exe=reader,limit=256*1024,timeout=30)
                identical=(original_code==installed_code==0
                           and original==installed
                           and present_key(passage,installed,installed_code))
                probes.append({
                    "reference":passage,
                    "installed_output_sha256":sha256(installed).hexdigest(),
                    "readback_identical_to_unpacked_module":identical,
                })
            if not all(p["readback_identical_to_unpacked_module"] for p in probes):
                raise PilotError("Isolated ZIP reinstall changed SWORD reader output")
        if output_archive is not None:
            if output_archive.exists() or output_archive.is_symlink():
                raise PilotError("Refusing to overwrite an existing test module ZIP")
            output_archive.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(archive,output_archive)
            if _sha(output_archive)!=build["zip_sha256"]:
                output_archive.unlink(missing_ok=True)
                raise PilotError("Exported preview ZIP digest differs from validated ZIP")
    return {
        "status":"private_stock_sword_zip_reinstall_readback_verified",
        "module_id":module_id,
        "zip_sha256":build["zip_sha256"],
        "zip_bytes":build["zip_bytes"],
        "package_member_count":build["module_file_count"],
        "package_uncompressed_bytes":build["uncompressed_module_bytes"],
        "package_manifest_sha256":sha256(
            "".join(k+" "+v+"\n" for k,v in sorted(
                build["source_file_sha256"].items())).encode()).hexdigest(),
        "independent_passage_readbacks":probes,
        "all_source_file_bytes_verified_after_extraction":True,
        "packaged_to_standard_mods_d_and_modules_paths":True,
        "standard_frontend_visual_rendering_verified":False,
        "rights_and_editorial_release_approved":False,
        "zip_discarded_without_upload_or_publication":output_archive is None,
        "test_zip_retained_for_owner_review":output_archive is not None,
        "published":False,
    }
