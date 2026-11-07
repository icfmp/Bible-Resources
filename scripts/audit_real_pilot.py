#!/usr/bin/env python3
"""Read-only structural fingerprint report for actual LSG/MHC pilot resources.

This intentionally does not claim an original OSIS XML extraction from a
compiled SWORD module. Reports module/key metadata, and separately USFM
authoring source signatures when supplied. No original text is published.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

from pilot_preflight import ROOT, inspect_archive, PilotError

USFM_MARKER = re.compile(r"\\(id|c|v|p|m|q[1-9]?|s[1-9]?|f|x)\b")
# These labels are *heuristic* output-format signals; the 'internal' format
# produced by diatheke is not necessarily a valid OSIS source document.
DISPLAY_MARKERS = {
    "paragraph": re.compile(r"<p(?:\s|>)|<div[^>]*type=['\"]x-p", re.IGNORECASE),
    "poetry_line": re.compile(r"<l(?:\s|>)|type=['\"]x-line", re.IGNORECASE),
    "note": re.compile(r"<note(?:\s|>)", re.IGNORECASE),
    "reference": re.compile(r"<reference(?:\s|>)", re.IGNORECASE),
    "emphasis": re.compile(r"<hi(?:\s|>)", re.IGNORECASE),
    "original_word": re.compile(r"<w(?:\s|>)", re.IGNORECASE),
}


def usfm_summary(archive_path: Path) -> dict:
    inspected = inspect_archive(archive_path, source_kind="authored")
    counts = Counter()
    files = []
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            if PurePosixPath(entry.filename).suffix.lower() not in {".usfm", ".sfm"}:
                continue
            raw = archive.read(entry)
            # The source might be encoded differently; never silently
            # interpret unreadable text as valid UTF-8.
            try:
                content = raw.decode("utf-8-sig")
            except UnicodeError as exc:
                raise PilotError(f"Authored USFM is not UTF-8: {entry.filename}") from exc
            by_marker = Counter(USFM_MARKER.findall(content))
            counts.update(by_marker)
            files.append({
                "path":entry.filename,
                "bytes":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
                "marker_counts":dict(sorted(by_marker.items())),
            })
    if not files:
        raise PilotError("No USFM text files in registered source archive")
    return {
        "archive_sha256": inspected["archive_sha256"],
        "files_with_usfm": len(files),
        "marker_totals": dict(sorted(counts.items())),
        "file_fingerprints": sorted(files, key=lambda f:f["path"]),
        "content_not_compared_to_sword": True,
    }


def scan_sword_entries(pilot: str, archive_path: Path, *,
                       config: dict, diatheke=None) -> dict:
    conf = config["pilots"][pilot]
    archive_info = inspect_archive(
        archive_path, source_kind="sword",
        expected_module_id=conf["module_id"],
        expected_category=conf["category"],
    )
    exe = diatheke or shutil.which("diatheke")
    if not exe:
        raise PilotError("diatheke is required for a real SWORD entry scan")
    samples = []
    with tempfile.TemporaryDirectory(prefix="bible-resources-source-audit-") as temp:
        root = Path(temp)
        with zipfile.ZipFile(archive_path) as archive:
            for item in archive_info["members"]:
                name = item["name"]
                destination = root / PurePosixPath(name)
                if not destination.resolve().is_relative_to(root.resolve()):
                    raise PilotError("Unsafe source entry in ZIP")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as input_file, destination.open("xb") as output_file:
                    shutil.copyfileobj(input_file, output_file, length=262144)
        env = dict(os.environ, SWORD_PATH=str(root))
        for key in conf["sample_references"]:
            proc = subprocess.run(
                [exe, "-b", conf["module_id"], "-k", key, "-f", "internal"],
                capture_output=True, check=False, timeout=30, env=env,
            )
            # Do NOT emit raw text or stderr: these may contain the entire
            # entry. Hash only and report a boolean check for accessible keys.
            data = proc.stdout
            decoded = data.decode("utf-8", errors="replace")
            samples.append({
                "reference": key,
                "successful": proc.returncode == 0 and bool(data.strip()),
                "return_code": proc.returncode,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "render_markup_signal_counts": {
                    name: len(marker.findall(decoded))
                    for name, marker in DISPLAY_MARKERS.items()
                },
                "not_original_xml_source": True,
            })
    return {
        "archive_sha256": archive_info["archive_sha256"],
        "module_id": conf["module_id"],
        "category": archive_info["sword_conf"]["category"],
        "language": archive_info["sword_conf"]["language"],
        "versification": archive_info["sword_conf"]["versification"],
        "source_type_declared": archive_info["sword_conf"]["source_type"],
        "driver": archive_info["sword_conf"]["driver"],
        "version": archive_info["sword_conf"]["version"],
        "samples": samples,
        "has_all_sample_keys": all(x["successful"] for x in samples),
        "content_not_normalized": True,
    }


def run(pilot: str, sword_zip: Path, *, authored_zip: Path | None = None,
        config_path: Path = ROOT/"config/pilot-sources.json", diatheke=None) -> dict:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if pilot not in config.get("pilots", {}):
        raise PilotError("Unexpected pilot identifier")
    report = {
        "schema_version": 1, "pilot":pilot,
        "status": "read_only_source_inventory",
        "sword": scan_sword_entries(pilot, sword_zip, config=config, diatheke=diatheke),
        "no_source_modifications": True,
        "published_content": False,
        "full_content_fidelity_verified": False,
        "strict_osis_source_validation_passed": False,
    }
    if authored_zip:
        report["authored_usfm"] = usfm_summary(authored_zip)
    report["remaining"] = [
        "confirm actual source / compiled edition identity",
        "validate original OSIS if original OSIS is available",
        "compare all verse text, punctuation, notes and annotations",
        "verify real SWORD compiled round trip",
        "perform GTK before/after visual checks",
        "record editor approval and redistribution rights",
    ]
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=["lsg","mhc"], required=True)
    parser.add_argument("--sword-zip", type=Path, required=True)
    parser.add_argument("--authored-zip", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.pilot, args.sword_zip, authored_zip=args.authored_zip)
        status = 0 if result["sword"]["has_all_sample_keys"] else 1
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile,
            subprocess.TimeoutExpired) as exc:
        result = {"status":"blocked","pilot":args.pilot,
                  "reason":str(exc),"no_source_modifications":True}
        status = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(f"Real pilot source audit: {result['status']} — {args.report}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
