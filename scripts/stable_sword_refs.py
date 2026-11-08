#!/usr/bin/env python3
"""Fail-closed reference-index screening for stock, released SWORD engines.

Inputs are text-free verse references collected *independently* from the
publisher source and the compiled module's actual resolved reader keys.
Never infer the latter from osis2mod exit status or from a source-key list.
This is not a Bible-text, notes, formatting, or visual fidelity assertion.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)$")
SYSTEM = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,31}$")
STABLE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA = re.compile(r"^[a-f0-9]{64}$")


def parse_keys(text: str) -> set[tuple[str, int, int]]:
    result = set()
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty verse-key inventory")
    for number, line in enumerate(lines, 1):
        match = KEY.fullmatch(line)
        if match is None:
            raise ValueError(f"Invalid verse key on line {number}")
        key = (match.group(1), int(match.group(2)), int(match.group(3)))
        if key in result:
            raise ValueError(f"Duplicate verse key on line {number}")
        result.add(key)
    return result


def parse_registry(text: str, system: str) -> dict[tuple[str, int], int]:
    if not SYSTEM.fullmatch(system):
        raise ValueError("Invalid SWORD versification name")
    registry = {}
    for number, line in enumerate(text.splitlines(), 1):
        cells = line.split("\t")
        if len(cells) != 4:
            raise ValueError(f"Malformed installed SWORD registry line {number}")
        name, book, chapter, maximum = cells
        if not SYSTEM.fullmatch(name) or not KEY.fullmatch(f"{book}.{chapter}.{maximum}"):
            raise ValueError(f"Invalid registered SWORD chapter on line {number}")
        if name != system:
            continue
        key = (book, int(chapter))
        if key in registry:
            raise ValueError(f"Duplicate registered SWORD chapter on line {number}")
        registry[key] = int(maximum)
    if not registry:
        raise ValueError(f"Versification {system} is absent from installed SWORD")
    return registry


def module_payload_digest(module_directory: Path) -> str:
    """Bind the report to the entire installed payload, including its .conf."""
    root = module_directory / "payload"
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Missing or linked SWORD payload")
    entries = sorted(root.rglob("*"))
    if not entries or any(p.is_symlink() for p in entries):
        raise ValueError("Empty or linked SWORD payload")
    files = [p for p in entries if p.is_file()]
    if not files:
        raise ValueError("No SWORD module files")
    digest = hashlib.sha256()
    for p in files:
        rel = p.relative_to(root).as_posix().encode("utf-8")
        raw = p.read_bytes()
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def inspect_references(source: set[tuple[str, int, int]],
                       resolved_reader: set[tuple[str, int, int]],
                       registry: dict[tuple[str, int], int]) -> dict:
    """Reject inaccessible, merged or noncanonical verse indices.

    Extra unused *registry* slots are reported, not filled with Scripture.
    An extra populated reader key is different and blocks release.
    """
    outside = sorted(ref for ref in source
                     if ref[2] > registry.get((ref[0], ref[1]), 0))
    missing = sorted(source - resolved_reader)
    unexpected = sorted(resolved_reader - source)
    occupied = Counter((book, chapter) for book, chapter, verse in source
                       if verse <= registry.get((book, chapter), 0))
    unused_slots = sum(maximum - occupied.get(key, 0)
                       for key, maximum in registry.items())
    return {
        "status": ("stable_reference_index_verified"
                   if not (outside or missing or unexpected) else "blocked"),
        "source_reference_count": len(source),
        "resolved_reader_reference_count": len(resolved_reader),
        "outside_registered_versification_count": len(outside),
        "source_references_unreachable_count": len(missing),
        "unexpected_populated_reader_references_count": len(unexpected),
        "unoccupied_registered_slots_count": unused_slots,
        "first_outside_refs": ["%s.%d.%d" % x for x in outside[:20]],
        "first_unreachable_refs": ["%s.%d.%d" % x for x in missing[:20]],
        "first_unexpected_reader_refs": ["%s.%d.%d" % x for x in unexpected[:20]],
        "exact_reference_key_parity": not (outside or missing or unexpected),
        "text_notes_markup_and_visuals_verified": False,
    }


def proof_errors(module_directory: Path, versification: str,
                 source_osis_sha256: str) -> list[str]:
    """Publication assertion gate; independent CI must produce the report."""
    path = module_directory / "SWORD_COMPATIBILITY.json"
    try:
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError("unsafe/oversize compatibility report")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"{path}: [SWORD_COMPATIBILITY_MISSING] {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: [SWORD_COMPATIBILITY_INVALID] Expected object"]
    errors = []
    if (data.get("status") != "stable_reference_index_verified"
            or data.get("exact_reference_key_parity") is not True
            or data.get("outside_registered_versification_count") != 0
            or data.get("source_references_unreachable_count") != 0
            or data.get("unexpected_populated_reader_references_count") != 0
            or type(data.get("source_reference_count")) is not int
            or data["source_reference_count"] < 1
            or data.get("source_reference_count") != data.get("resolved_reader_reference_count")):
        errors.append(f"{path}: [SWORD_INDEX_NOT_VERIFIED] Full source-versus-reader key equality required")
    if (data.get("versification") != versification
            or data.get("reader_engine") != "libsword"
            or not isinstance(data.get("reader_version"), str)
            or not STABLE_VERSION.fullmatch(data["reader_version"])
            or data.get("engine_release") != "stable"
            or data.get("registry_source") != "installed_sword_versification_mgr"):
        errors.append(f"{path}: [SWORD_UNSUPPORTED_RUNTIME] Released standard SWORD registry proof required")
    if (not isinstance(source_osis_sha256, str)
            or not SHA.fullmatch(source_osis_sha256)
            or data.get("source_osis_sha256") != source_osis_sha256):
        errors.append(f"{path}: [SWORD_SOURCE_PROOF_STALE] Source digest does not match validated OSIS")
    try:
        payload_sha = module_payload_digest(module_directory)
    except (OSError, ValueError) as exc:
        errors.append(f"{path}: [SWORD_PAYLOAD_PROOF_INVALID] {exc}")
    else:
        if data.get("module_payload_sha256") != payload_sha:
            errors.append(f"{path}: [SWORD_PAYLOAD_PROOF_STALE] Compiled payload has changed")
    if (not isinstance(data.get("reviewed_by"), str)
            or len(data["reviewed_by"].strip()) < 2
            or data["reviewed_by"].strip().upper() == "PENDING"):
        errors.append(f"{path}: [SWORD_INDEX_REVIEW_MISSING] Reviewer sign-off required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-keys", type=Path, required=True)
    parser.add_argument("--resolved-reader-keys", type=Path, required=True)
    parser.add_argument("--registry-tsv", type=Path, required=True)
    parser.add_argument("--versification", required=True)
    parser.add_argument("--reader-version", required=True)
    parser.add_argument("--source-osis-sha256", required=True)
    parser.add_argument("--module-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not STABLE_VERSION.fullmatch(args.reader_version):
        parser.error("A released numeric libsword version is required, not HEAD/dev")
    if not SHA.fullmatch(args.source_osis_sha256):
        parser.error("Validated original OSIS SHA-256 is required")
    try:
        src = parse_keys(args.source_keys.read_text(encoding="utf-8"))
        reader = parse_keys(args.resolved_reader_keys.read_text(encoding="utf-8"))
        registry = parse_registry(args.registry_tsv.read_text(encoding="utf-8"),
                                  args.versification)
        payload_hash = module_payload_digest(args.module_directory)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    report = inspect_references(src, reader, registry)
    report.update({
        "versification": args.versification,
        "reader_engine": "libsword",
        "reader_version": args.reader_version,
        "engine_release": "stable",
        "registry_source": "installed_sword_versification_mgr",
        "source_osis_sha256": args.source_osis_sha256,
        "module_payload_sha256": payload_hash,
        "reviewed_by": "PENDING",
    })
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("SWORD stable reference index:", report["status"])
    return 0 if report["status"] == "stable_reference_index_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
