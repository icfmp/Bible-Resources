#!/usr/bin/env python3
"""Build an isolated, non-release, user-installable SWORD trial package.

Only invoked after the complete source-attested stock-SWORD fidelity gates
pass on the exact compiler output. Copy the verified module *bytes* unchanged
into a uniquely named reader module: never overwrite the publisher module ID.
The private ZIP is retained only for the explicit user-requested Xiphos test,
not committed or added to the public Bible Resources catalogue.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile

from pilot_preflight import PilotError
from private_sword_bundle import audit_private_sword_installation, _validate_package_files

SOURCE_ID = "fraLSG1910eb"
TRIAL_ID = "BRLSG1910Preview3"
STORAGE_NAME = "brlsg1910preview3"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_xiphos_preview(source_root: Path, destination: Path, *,
                          original_usfx_sha256: str) -> dict:
    """Retain validated test ZIP outside original compiler temp root.

    The ZIP contains text-bearing data, unlike all existing public CI
    reports. The caller is responsible for limiting artifact retention and
    never publishing as a release or catalogue entry.
    """
    if not isinstance(original_usfx_sha256,str) or len(original_usfx_sha256)!=64:
        raise PilotError("Immutable publisher source digest absent")
    try:
        int(original_usfx_sha256,16)
    except ValueError as exc:
        raise PilotError("Invalid immutable publisher source digest") from exc
    original = source_root/"modules/texts/rawtext/fralsg1910eb"
    original_conf = source_root/"mods.d/fralsg1910eb.conf"
    if (not original.is_dir() or original.is_symlink()
            or not original_conf.is_file() or original_conf.is_symlink()
            or destination.exists()):
        raise PilotError("Unsafe preview source or existing destination")
    if not original_conf.read_text(encoding="utf-8").startswith("[fraLSG1910eb]\n"):
        raise PilotError("Compiled SWORD source configuration was not verified")

    with tempfile.TemporaryDirectory(prefix="lsg-preview-staging-") as folder:
        stage=Path(folder)
        copy=stage/"modules/texts/rawtext"/STORAGE_NAME
        copy.parent.mkdir(parents=True)
        shutil.copytree(original,copy,symlinks=True)
        source_files=sorted(p.relative_to(original) for p in original.rglob("*")
                            if p.is_file() or p.is_symlink())
        copy_files=sorted(p.relative_to(copy) for p in copy.rglob("*")
                          if p.is_file() or p.is_symlink())
        if source_files!=copy_files or not source_files:
            raise PilotError("Staged preview SWORD binary inventory differs")
        for rel in source_files:
            a,b=original/rel,copy/rel
            if a.is_symlink() or b.is_symlink() or _hash(a)!=_hash(b):
                raise PilotError("Preview packaging altered source SWORD data bytes")
        conf=stage/"mods.d"/(TRIAL_ID.lower()+".conf")
        conf.parent.mkdir(parents=True)
        conf.write_text(
            "["+TRIAL_ID+"]\n"
            "Description=Louis Segond 1910 - Bible Resources (PREVIEW 3)\n"
            "About=PREVIEW de test non publiee. Segond 1910 eBible. "
            "Marc 10:52 contient aussi le verset 53 de la source. "
            "Conserver la source originale. "
            "La numerotation peut afficher seulement 52.\n"
            "Version=0.0.3-preview\n"
            "DataPath=./modules/texts/rawtext/"+STORAGE_NAME+"/\n"
            "ModDrv=RawText\n"
            "Encoding=UTF-8\n"
            "Lang=fr\n"
            "SourceType=OSIS\n"
            "GlobalOptionFilter=OSISLemma\n"
            "GlobalOptionFilter=OSISStrongs\n"
            "GlobalOptionFilter=OSISFootnotes\n"
            "GlobalOptionFilter=OSISScripref\n"
            "GlobalOptionFilter=OSISHeadings\n"
            "Versification=Segond\n"
            "DistributionLicense=Public Domain\n",
            encoding="utf-8")
        members=_validate_package_files(stage,TRIAL_ID)
        if len(members)!=len(source_files)+1:
            raise PilotError("Preview module content count mismatch")
        destination.parent.mkdir(parents=True,exist_ok=True)
        metadata=audit_private_sword_installation(
            stage,TRIAL_ID,reader="diatheke",output_archive=destination)
        if metadata["status"]!="private_stock_sword_zip_reinstall_readback_verified":
            raise PilotError("Preview install/readback is not verified")
        metadata["preview_module_id"]=TRIAL_ID
        metadata["source_module_id"]=SOURCE_ID
        metadata["publisher_original_usfx_sha256"]=original_usfx_sha256
        metadata["text_payload_files_byte_identical_to_verified_module"]=True
        metadata["release_or_catalogue_published"]=False
        metadata["test_only_download_intended"]=True
        return metadata
