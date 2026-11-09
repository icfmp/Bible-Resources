#!/usr/bin/env python3
"""Collect actual, source-independent stable libsword Bible reader keys.

Requires a trusted, locally compiled scripts/sword_native_index.cpp helper.
Never use OSIS source keys to infer which native reader slots are populated.
The text-free report is a *producer input*, not editorial or release approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from stable_sword_refs import (
    KEY, SYSTEM, STABLE_VERSION, parse_keys, parse_registry,
    module_payload_digest,
)

MODULE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}$")
INTRO = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.0\.0|\.[1-9][0-9]*(?:\.0)?)?$")
MAX_INDEX_ROWS = 350_000
MAX_STDOUT_BYTES = 16 * 1024 * 1024


class NativeIndexError(ValueError):
    """Native payload/registry or actual reader evidence cannot be trusted."""


def parse_native_rows(text: str, expected_module: str) -> tuple[str, str, dict]:
    """Parse strict text-free output directly from the running stock libSWORD."""
    lines = text.splitlines()
    if len(lines) < 4 or len(lines) > MAX_INDEX_ROWS:
        raise NativeIndexError("Missing, empty or implausibly large native inventory")
    meta = lines[0].split("\t")
    if (len(meta) != 5 or meta[0] != "M" or meta[1] != expected_module
            or not SYSTEM.fullmatch(meta[2]) or not STABLE_VERSION.fullmatch(meta[3])
            or meta[4] not in ("RawText", "zText")):
        raise NativeIndexError("Missing or unsupported native module/engine header")
    _, module_id, system, version, driver = meta
    trailer = lines[-1].split("\t")
    if len(trailer) != 5 or trailer[0] != "S":
        raise NativeIndexError("Missing terminal complete-inventory counts")
    try:
        counts = tuple(int(v) for v in trailer[1:])
    except ValueError as exc:
        raise NativeIndexError("Malformed native completion counts") from exc
    if any(v < 0 for v in counts):
        raise NativeIndexError("Negative native index totals")
    registry: list[str] = []
    populated: list[str] = []
    intros: list[str] = []
    opaque_top: list[str] = []
    active: tuple[str, int, int] | None = None
    last_ref = 0
    last_intro = set()
    for row in lines[1:-1]:
        cells = row.split("\t")
        kind = cells[0]
        if kind == "R" and len(cells) == 5:
            if cells[1] != system:
                raise NativeIndexError("Installed registry name disagrees with module")
            registry.append("\t".join(cells[1:]))
            active = None
        elif kind == "K" and len(cells) == 2:
            m = KEY.fullmatch(cells[1])
            if m is None:
                raise NativeIndexError("Invalid native populated verse reference")
            pos = (m.group(1), int(m.group(2)), int(m.group(3)))
            if active is None:
                raise NativeIndexError("Populated reader key before native registry row")
            if pos[:2] != active[:2] or pos[2] <= last_ref:
                raise NativeIndexError("Unordered or cross-chapter native populated key")
            populated.append(cells[1])
            last_ref = pos[2]
        elif kind == "U" and len(cells) == 3 and cells[1] == "TOP":
            if cells[2] != str(len(opaque_top) + 1):
                raise NativeIndexError("Duplicate or skipped anonymous native TOP ordinal")
            opaque_top.append("TOP")
        elif kind == "I" and len(cells) == 2:
            if not INTRO.fullmatch(cells[1]) or cells[1] in last_intro:
                raise NativeIndexError("Malformed or duplicate native intro key")
            intros.append(cells[1])
            last_intro.add(cells[1])
        else:
            raise NativeIndexError("Unknown native inventory row type")
        if kind == "R":
            _, book, chapter, maximum = cells[1:]
            if not KEY.fullmatch(f"{book}.{chapter}.{maximum}"):
                raise NativeIndexError("Invalid native registered chapter/ceiling")
            active = (book, int(chapter), int(maximum))
            last_ref = 0
    registry_text = "".join(item + "\n" for item in registry)
    populated_text = "".join(item + "\n" for item in populated)
    parsed_registry = parse_registry(registry_text, system)
    if not populated:
        raise NativeIndexError("Stock SWORD module contains no populated Bible verses")
    keys = parse_keys(populated_text)
    if (len(parsed_registry) != len(registry)
            or len(keys) != len(populated)
            or counts != (len(registry), len(populated), len(intros), len(opaque_top))):
        raise NativeIndexError("Native reader registry/key/intron totals disagree")
    for book, chapter, verse in keys:
        if verse > parsed_registry.get((book, chapter), 0):
            raise NativeIndexError("Native populated key is not in installed registry")
    # Intros are deliberately separate from ordinary verses and cannot be
    # fed to stable_sword_refs.parse_keys, which excludes numeric verse zero.
    report = {
        "schema_version": 1,
        "status": "native_stock_sword_verse_index_inventoried_not_release_approved",
        "module_id": module_id,
        "native_versification": system,
        "reader_engine": "libsword",
        "reader_version": version,
        "module_driver": driver,
        "engine_release": "stable",
        "registry_source": "installed_sword_versification_mgr",
        "native_registry_chapter_count": len(parsed_registry),
        "native_occupied_numbered_verse_count": len(populated),
        "native_occupied_verse_zero_intro_count": len(intros),
        "native_nonaddressable_populated_top_count": len(opaque_top),
        "native_anonymous_top_content_parity_verified": False,
        "native_occupied_intro_references": intros,
        "native_reader_keys_sha256": sha256(populated_text.encode()).hexdigest(),
        "native_registry_sha256": sha256(registry_text.encode()).hexdigest(),
        "source_osis_verified": False,
        "source_to_reader_index_parity_verified": False,
        "source_text_notes_markup_fidelity_verified": False,
        "reader_visual_rendering_verified": False,
        "editorially_approved": False,
        "published": False,
    }
    return populated_text, registry_text, report


def _validate_payload(module: Path, module_id: str) -> tuple[Path, str, str]:
    if not MODULE_ID.fullmatch(module_id):
        raise NativeIndexError("Invalid SWORD module ID")
    if module.is_symlink() or not module.is_dir():
        raise NativeIndexError("Missing or symlinked module directory")
    payload = module / "payload"
    conf_dir = payload / "mods.d"
    if conf_dir.is_symlink() or not conf_dir.is_dir():
        raise NativeIndexError("Missing or symlinked SWORD configuration directory")
    configs = list(conf_dir.iterdir())
    if (len(configs) != 1 or configs[0].is_symlink() or not configs[0].is_file()
            or configs[0].name != module_id.lower() + ".conf"):
        raise NativeIndexError("Expected exactly one matching native SWORD module config")
    conf = configs[0].read_text(encoding="utf-8-sig")
    if f"[{module_id}]" not in conf.splitlines():
        raise NativeIndexError("Module ID differs from native SWORD conf")
    fields = {}
    for line in conf.splitlines():
        value = line.strip()
        if not value or value.startswith(("[", "#", ";")):
            continue
        if "=" not in line:
            raise NativeIndexError("Malformed SWORD config line")
        k, v = (part.strip() for part in line.split("=", 1))
        if k in ("ModDrv", "Versification"):
            if k in fields:
                raise NativeIndexError("Repeated SWORD driver or v11n declaration")
            fields[k] = v
    if fields.get("ModDrv") not in ("RawText", "zText"):
        raise NativeIndexError("Only actual stock Bible RawText/zText are supported")
    if fields.get("Versification", "KJV") and not SYSTEM.fullmatch(
            fields.get("Versification", "KJV")):
        raise NativeIndexError("Invalid declared native versification")
    return payload, fields["ModDrv"], fields.get("Versification", "KJV")


def collect_native_inventory(
    inspector: Path, module: Path, module_id: str, *, timeout: int = 120
) -> tuple[str, str, dict]:
    if inspector.is_symlink() or not inspector.is_file():
        raise NativeIndexError("Missing or symlinked trusted stock-SWORD inspector")
    payload, driver, declared_system = _validate_payload(module, module_id)
    input_hash = module_payload_digest(module)
    env = dict(os.environ, SWORD_PATH=str(payload.resolve(strict=True)))
    try:
        result = subprocess.run(
            [str(inspector.resolve(strict=True)), module_id],
            env=env, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeIndexError("Native stock-SWORD reader unavailable or timed out") from exc
    if result.returncode != 0:
        # This *compiled trusted helper* emits only the native reference
        # identifier and VerseKey numeric fields, never Scripture text.
        diagnostic = result.stderr.decode("utf-8", errors="replace")
        native_line = next((line for line in diagnostic.splitlines()
                            if line.startswith("Unrecognized native key: ")), "")
        safe_line = "".join(ch for ch in native_line
                            if ch.isascii() and (ch.isalnum() or ch in " ._():-/"))
        suffix = f"; {safe_line[:160]}" if safe_line else ""
        raise NativeIndexError(f"Stock-SWORD native inspector blocked (exit {result.returncode}){suffix}")
    if len(result.stdout) > MAX_STDOUT_BYTES or len(result.stderr) > 256_000:
        raise NativeIndexError("Native inventory exceeds output bounds")
    try:
        keys, registry, report = parse_native_rows(
            result.stdout.decode("utf-8"), module_id)
    except UnicodeError as exc:
        raise NativeIndexError("Non-UTF-8 native reference inventory") from exc
    if report["module_driver"] != driver or report["native_versification"] != declared_system:
        raise NativeIndexError("Native driver or v11n disagrees with pinned payload config")
    if module_payload_digest(module) != input_hash:
        raise NativeIndexError("SWORD module changed during native inventory scan")
    report["module_payload_sha256"] = input_hash
    report["native_inspector_sha256"] = sha256(inspector.read_bytes()).hexdigest()
    return keys, registry, report


def _write_evidence(files: list[tuple[Path, bytes]], module: Path) -> None:
    dests = [p.resolve() for p, _ in files]
    module_root = module.resolve(strict=True)
    if len(dests) != len(set(dests)) or any(p.is_relative_to(module_root) for p in dests):
        raise NativeIndexError("Duplicate or source-module-overwriting evidence output paths")
    if any(p.exists() or p.is_symlink() for p, _ in files):
        raise NativeIndexError("Refusing to overwrite existing index proof")
    if any(p.parent.is_symlink() or not p.parent.is_dir() for p, _ in files):
        raise NativeIndexError("Proof output parent must already exist")
    temps = []
    committed = []
    try:
        for p, content in files:
            fd, name = tempfile.mkstemp(dir=p.parent, prefix=".native-index-")
            temps.append(Path(name))
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for (p, _), temp in zip(files, temps):
            if p.exists() or p.is_symlink():
                raise NativeIndexError("Proof output path appeared while writing")
            os.replace(temp, p)
            committed.append(p)
    except BaseException:
        for p in committed:
            p.unlink(missing_ok=True)
        raise
    finally:
        for p in temps:
            p.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspector", required=True, type=Path)
    parser.add_argument("--module-directory", required=True, type=Path)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--reader-keys-output", required=True, type=Path)
    parser.add_argument("--registry-tsv-output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        keys, registry, report = collect_native_inventory(
            args.inspector, args.module_directory, args.module_id)
        _write_evidence([
            (args.reader_keys_output, keys.encode("utf-8")),
            (args.registry_tsv_output, registry.encode("utf-8")),
            (args.report, (json.dumps(report, indent=2, sort_keys=True)
                           + "\n").encode("utf-8")),
        ], args.module_directory)
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    print(f"Native libsword indexed {report['native_occupied_numbered_verse_count']}"
          f" occupied ordinary keys in {report['native_registry_chapter_count']}"
          f" registered chapters. No source/editorial approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
