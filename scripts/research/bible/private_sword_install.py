"""Safely install one vetted stock SWORD Bible ZIP into an isolated research root.

Shared helper for read-only source/native inspections; never authorizes release.
""" 
from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import zipfile

from check_updates import parse_conf
from diff_sword_snapshots import _read_snapshot
from stable_sword_refs import module_payload_digest


class PrivateSwordInstallError(ValueError):
    """An archive cannot be safely installed as one stock Bible module."""


def _safe_single_module(zip_path: Path, root: Path) -> str:
    """Copy an already safety-vetted ZIP into a private isolated SWORD root."""
    if not zip_path.is_file() or zip_path.is_symlink():
        raise PrivateSwordInstallError("Missing or symlinked original SWORD ZIP")
    indexed, conf_bytes = _read_snapshot(zip_path)
    conf = parse_conf(conf_bytes)
    name = conf["module_id"]
    conf_path = f"mods.d/{name.lower()}.conf"
    if conf_path not in indexed:
        raise PrivateSwordInstallError("No exact, single native module .conf")
    if conf["driver"] not in {"RawText", "zText"}:
        raise PrivateSwordInstallError("Original source is not a supported Bible SWORD driver")
    root.mkdir(parents=True, exist_ok=False)
    payload = root / "payload"
    payload.mkdir()
    with zipfile.ZipFile(zip_path) as archive:
        for member in sorted(indexed):
            target = payload / member
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.read(member)
            proof = indexed[member]
            if len(raw) != proof["size"] or sha256(raw).hexdigest() != proof["sha256"]:
                raise PrivateSwordInstallError("Source archive changed between checks")
            target.write_bytes(raw)
    if module_payload_digest(root) == "":
        raise PrivateSwordInstallError("Empty installed SWORD module digest")
    return {"module_id": name, "original_version": conf.get("version"),
            "original_driver": conf["driver"],
            "original_versification": conf.get("versification") or "KJV"}
