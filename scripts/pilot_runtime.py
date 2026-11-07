#!/usr/bin/env python3
"""Extract a safely preflighted SWORD ZIP into a disposable directory and probe diatheke.

Diagnostic-only. No normalized output, no user installation, no content artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile

from pilot_preflight import ROOT, inspect_archive, PilotError
from pilot_subprocess import query, present_key


def run_reader(pilot: str, archive_path: Path, *, config: dict,
               diatheke: str | None = None) -> dict:
    entry = config["pilots"][pilot]
    confirmed = inspect_archive(
        archive_path, source_kind="sword",
        expected_module_id=entry["module_id"],
        expected_category=entry["category"],
    )
    exe = diatheke or shutil.which("diatheke")
    if not exe:
        raise PilotError("diatheke missing: real SWORD reader verification cannot be skipped")
    checks = []
    with tempfile.TemporaryDirectory(prefix="bible-resources-pilot-") as temp:
        target = Path(temp)
        with zipfile.ZipFile(archive_path) as archive:
            for record in confirmed["members"]:
                # Never use extractall(): only members reviewed by inspect_archive.
                name = record["name"]
                member = archive.getinfo(name)
                destination = target / PurePosixPath(name)
                if not destination.resolve().is_relative_to(target.resolve()):
                    raise PilotError("Path left the disposable test root")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, destination.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=256 * 1024)
        for reference in entry["sample_references"]:
            return_code, body = query(
                entry["module_id"], reference, fmt="plain", root=target, exe=exe
            )
            success = present_key(reference, body, return_code)
            checks.append({
                "reference": reference,
                "diatheke_returncode": return_code,
                "has_readable_content": success,
                "output_sha256": hashlib.sha256(body).hexdigest(),
                "output_bytes": len(body),
            })
    return {
        "pilot": pilot,
        "module_id": entry["module_id"],
        "source_archive_sha256": confirmed["archive_sha256"],
        "status": "reader_probe_passed" if all(x["has_readable_content"] for x in checks)
                  else "reader_probe_incomplete",
        "checked_references": checks,
        "content_not_published": True,
        "editorial_fidelity_not_yet_verified": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=("lsg", "mhc"), required=True)
    parser.add_argument("--sword-zip", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    config = json.loads((ROOT / "config/pilot-sources.json").read_text(encoding="utf-8"))
    try:
        report = run_reader(args.pilot, args.sword_zip, config=config)
    except (OSError, ValueError, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        report = {"pilot": args.pilot, "status": "blocked", "reason": str(exc)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"Pilot reader probe: {report['status']}")
    return 0 if report["status"] == "reader_probe_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
