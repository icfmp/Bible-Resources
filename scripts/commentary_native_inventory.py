#!/usr/bin/env python3
"""Metadata-only native commentary key coverage from a stock SWORD zCom/RawCom.

Requires a locally compiled, trusted native inspector. The inspector prints
only occupied reference keys. These are SWORD *slots*, not proof of original
annotation ranges, headings, content fidelity or publishing rights.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

from commentary_intake import load_manifest
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive

MAX_OUTPUT = 12 * 1024 * 1024
KEY = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$")
INTRO = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.0\.0|\.[1-9][0-9]*(?:\.0)?)?$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SYSTEM = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,31}$")
DRIVERS = {"RawCom", "RawCom4", "zCom", "zCom4"}


def parse_index(output: bytes, module_id: str, *, include_rows: bool = False) -> dict:
    if len(output) > MAX_OUTPUT:
        raise PilotError("Native commentary index output exceeded reviewed bound")
    try:
        lines = output.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise PilotError("Non-ASCII native key evidence") from exc
    if len(lines) < 3 or len(lines) > 350000:
        raise PilotError("Empty/implausible native commentary inventory")
    meta = lines[0].split("\t")
    if (len(meta) != 5 or meta[0] != "M" or meta[1] != module_id
            or not SYSTEM.fullmatch(meta[2]) or not VERSION.fullmatch(meta[3])
            or meta[4] not in DRIVERS):
        raise PilotError("Invalid native commentary module/version/driver header")
    trailer = lines[-1].split("\t")
    if len(trailer) != 5 or trailer[0] != "S" or any(not v.isdigit() for v in trailer[1:]):
        raise PilotError("Missing/inconsistent complete inventory trailer")
    visited, num, intr, anonymous = (int(v) for v in trailer[1:])
    seen = set()
    counts = Counter()
    by_book = Counter()
    ordered = sha256()
    keys = []
    for line in lines[1:-1]:
        cells = line.split("\t")
        if len(cells) != 2 or cells[0] not in ("K", "I", "U"):
            raise PilotError("Unreviewed native commentary evidence row")
        kind, key = cells
        if (kind == "K" and not KEY.fullmatch(key)
                or kind == "I" and not INTRO.fullmatch(key)
                or kind == "U" and not re.fullmatch(r"TOP:[1-9][0-9]*", key)):
            raise PilotError("Invalid commentary slot reference")
        if (kind, key) in seen:
            raise PilotError(f"Duplicate native commentary slot key: {kind} {key}")
        seen.add((kind, key))
        counts[kind] += 1
        if kind != "U":
            book = key.split(".")[0]
            by_book[book] += 1
        keys.append((kind, key))
        ordered.update(line.encode("ascii") + b"\n")
    if (counts["K"], counts["I"], counts["U"]) != (num, intr, anonymous):
        raise PilotError("Native commentary slot totals differ from completion trailer")
    if not (1 <= num <= visited <= 300000) or not (1 <= len(by_book) <= 100) or anonymous > 10000:
        raise PilotError("Implausible native commentary occupancy or canon")
    # This is an occupied-key hash only. Shared physical zCom blocks and
    # overlapping annotation ranges cannot be inferred from hasEntry().
    result = {
        "status": "occupied_slot_inventory_not_entry_parity",
        "module_id": meta[1], "native_versification": meta[2],
        "libsword_version": meta[3], "driver": meta[4],
        "scanned_registry_slots": visited,
        "occupied_numbered_slots": num,
        "occupied_intro_slots": intr,
        "occupied_anonymous_top_slots": anonymous,
        "books_with_occupied_slots": len(by_book),
        "occupied_slots_by_book": dict(sorted(by_book.items())),
        "ordered_occupied_key_sha256": ordered.hexdigest(),
        "probe_john_3_16_native_occupied": ("K", "John.3.16") in seen,
        "comments_as_passage_ranges_verified": False,
        "source_to_native_text_fidelity_verified": False,
        "complete_commentary_entry_count_verified": False,
        "no_commentary_text_exported": True,
    }
    if include_rows:
        # Keys remain PRIVATE in callers: never serialize these into a
        # public receipt unless their precise disclosure is intentional.
        result["native_occupied_rows_for_in_memory_reconciliation"] = keys
    return result


def inventory(resource_id: str, *, inspector: Path, directory: Path | None = None,
              include_rows: bool = False) -> dict:
    manifest = load_manifest(resource_id, directory)
    expected = manifest.get("archive_sha256")
    if not expected:
        raise PilotError("Pinned CrossWire SWORD ZIP SHA-256 is required before native index audit")
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Trusted compiled native commentary inspector missing")
    with tempfile.TemporaryDirectory(prefix="commentary-native-") as temp:
        root = Path(temp)
        zip_path = root / "original.zip"
        download = fetch(manifest["sword_zip_url"], zip_path, manifest["provider"])
        if download["sha256"] != expected:
            raise PilotError("Upstream SWORD package drift; native scan aborted before untrusted extraction")
        scanned = inspect_archive(zip_path, source_kind="sword",
                                  expected_module_id=manifest["module_id"],
                                  expected_category="commentary")
        conf = scanned["sword_conf"]
        if conf["version"] != manifest["version"] or conf["language"] != manifest["language"]:
            raise PilotError("SWORD identity or language drift")
        install_root = root / "installed"
        install_root.mkdir()
        with zipfile.ZipFile(zip_path) as z:
            for rec in scanned["members"]:
                name = rec["name"]
                path = install_root / PurePosixPath(name)
                if not path.resolve().is_relative_to(install_root.resolve()):
                    raise PilotError("Untrusted SWORD ZIP member escapes isolated installation")
                path.parent.mkdir(parents=True, exist_ok=True)
                if not name.endswith("/"):
                    with z.open(name) as src, path.open("xb") as dst:
                        shutil.copyfileobj(src, dst, length=256 * 1024)
        env = dict(os.environ, SWORD_PATH=str(install_root))
        try:
            run = subprocess.run([str(inspector), manifest["module_id"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 timeout=50, env=env, check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Native commentary inspector exceeded 50-second safety limit") from exc
        if run.returncode:
            raise PilotError(f"Native commentary inspector failed with nonzero exit code {run.returncode}")
        report = parse_index(run.stdout, manifest["module_id"], include_rows=include_rows)
        if report["native_versification"] != (conf["versification"] or "KJV"):
            raise PilotError("Stock engine versification differs from effective declared SWORD module registry")
        if report["driver"] != conf["driver"]:
            raise PilotError("Native driver differs from stock module .conf")
        report.update(
            original_zip_sha256=download["sha256"],
            original_zip_bytes=download["bytes"],
            original_conf_sha256=conf["conf_sha256"],
            compiled_source_original_comparison="not_performed",
            rights_review_status="research_only",
            published=False,
        )
        return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--native-inspector", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = inventory(args.resource_id, inspector=args.native_inspector)
        code = 0
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        result = {"status": "blocked", "resource_id": args.resource_id,
                  "error": str(exc), "published": False}
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("Commentary native index: " + result["status"] + " — metadata-only receipt")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
