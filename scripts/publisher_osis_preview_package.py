#!/usr/bin/env python3
"""Deterministic, disposable stock-SWORD zText preview ZIP for *reader testing*.

No source XML or compiler logs. A successful ZIP is not a publication, nor
does it approve title typography, notes navigation or editorial semantics.
All inputs must have independently passed the pinned full-corpus parity gate.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

STAMP=(1980,1,1,0,0,0)
MODULE=re.compile(r"[A-Za-z][A-Za-z0-9_]{2,48}\Z")
V11N=re.compile(r"[A-Za-z][A-Za-z0-9]{1,31}\Z")
COMPRESSED_FILES=frozenset(
    f"{section}.{extension}"
    for section in ("ot","nt") for extension in ("bzs","bzv","bzz"))
MAX_DATA_SIZE=32*1024*1024


class PreviewPackageError(ValueError):
    """Refuse an unverified or unsafe standard SWORD preview payload."""


def sha_file(path):
    return sha256(path.read_bytes()).hexdigest()


def _expected(payload, module_id, versification):
    if not MODULE.fullmatch(module_id) or not V11N.fullmatch(versification):
        raise PreviewPackageError("Invalid tested module identity or versification")
    if payload.is_symlink() or not payload.is_dir():
        raise PreviewPackageError("Missing original tested SWORD root")
    name=module_id.lower()
    expected_conf=f"mods.d/{name}.conf"
    prefix=f"modules/texts/ztext/{name}/"
    required={expected_conf}|{prefix+x for x in COMPRESSED_FILES}
    actual=set()
    for path in payload.rglob("*"):
        if path.is_symlink():
            raise PreviewPackageError("Symlinked module content")
        if path.is_file():
            actual.add(path.relative_to(payload).as_posix())
        elif not path.is_dir():
            raise PreviewPackageError("Unexpected module object")
    if actual!=required:
        raise PreviewPackageError("Incomplete or unexpected zText package inventory")
    content={}
    for key in sorted(required):
        file=payload/key
        if file.stat().st_size==0 or file.stat().st_size>MAX_DATA_SIZE:
            raise PreviewPackageError("Empty or oversized stock SWORD payload")
        content[key]=file.read_bytes()
    conf=content[expected_conf].decode("utf-8")
    checks=(
        conf.startswith(f"[{module_id}]\n"),
        f"DataPath=./{prefix}\n" in conf,
        "ModDrv=zText\n" in conf,
        f"Versification={versification}\n" in conf,
        "Encoding=UTF-8\n" in conf,
        "Version=0.0.0-research\n" in conf,
        "research-only" in conf,
    )
    if not all(checks):
        raise PreviewPackageError("No exact research-only source metadata")
    return content


def package_preview(payload: Path, output: Path, module_id: str,
                    versification: str):
    """Copy verified candidate bytes into a stable zip; fail rather than repair."""
    if output.is_symlink() or output.exists() or not output.parent.is_dir():
        raise PreviewPackageError("Refusing unsafe preview destination")
    if output.parent.is_symlink() or output.resolve().is_relative_to(payload.resolve()):
        raise PreviewPackageError("Package may not overwrite its input")
    content=_expected(payload,module_id,versification)
    try:
        with ZipFile(output,"x",compression=ZIP_DEFLATED,compresslevel=9) as zip_out:
            for key,data in sorted(content.items()):
                info=ZipInfo(key,STAMP)
                info.create_system=3
                info.external_attr=0o100644 << 16
                info.compress_type=ZIP_DEFLATED
                zip_out.writestr(info,data,compress_type=ZIP_DEFLATED,
                                 compresslevel=9)
        with ZipFile(output) as zipped:
            if zipped.testzip() is not None or set(zipped.namelist())!=set(content):
                raise PreviewPackageError("ZIP verification failed")
            if any(zipped.read(k)!=v for k,v in content.items()):
                raise PreviewPackageError("ZIP altered the audited module payload")
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return {
        "status":"exact_audited_source_bytes_packaged_for_reader_testing_only",
        "preview_only":True,
        "release_approved":False,
        "module_id":module_id,
        "versification":versification,
        "zip_sha256":sha_file(output),
        "zip_bytes":output.stat().st_size,
        "module_file_count":len(content),
        "all_module_files_byte_identical_to_audited_candidate":True,
        "member_sha256":{key:sha256(value).hexdigest()
                         for key,value in sorted(content.items())},
        "independent_reader_tested":False,
        "editorial_review_completed":False,
        "published":False,
    }
