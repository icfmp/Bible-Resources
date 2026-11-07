#!/usr/bin/env python3
"""Fetch the two exactly pinned official XSDs into a disposable local directory.

A successful download is NOT approval of any Bible or commentary source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request
from urllib.parse import urlsplit

from guard_osis import ROOT, MAX_SCHEMA_BYTES, _schema, StructureFailure

OFFICIAL_MAIN = "https://www.crosswire.org/~dmsmith/osis/osisCore.2.1.1-cw-latest.xsd"
OFFICIAL_DEP = "https://www.w3.org/2001/xml.xsd"


def pinned_fetch(url: str, expected_sha: str, target: Path) -> None:
    if url not in {OFFICIAL_MAIN, OFFICIAL_DEP}:
        raise ValueError("Unexpected schema source URL")
    if target.is_symlink():
        raise ValueError("Refusing symlink as a schema cache path")
    expected_host = urlsplit(url).hostname
    if target.exists():
        data = target.read_bytes()
    else:
        request = urllib.request.Request(
            url, headers={"User-Agent": "BibleResources-PinnedOSIS/1.0"})
        with urllib.request.urlopen(request, timeout=40) as response:
            if (urlsplit(response.url).scheme != "https" or
                    urlsplit(response.url).hostname != expected_host):
                raise ValueError("Unexpected XSD download redirect")
            data = response.read(MAX_SCHEMA_BYTES + 1)
    if not data or len(data) > MAX_SCHEMA_BYTES or hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError(f"Official XSD bytes do not match pinned SHA-256: {url}")
    if not target.exists():
        staged = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".xsd-", delete=False) as f:
                staged = Path(f.name)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(staged, target)
        finally:
            if staged and staged.exists():
                staged.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    policy = json.loads((ROOT / "config/osis-policy.json").read_text(encoding="utf-8"))
    if policy.get("schema_status") != "reviewed":
        raise ValueError("Schema not reviewed")
    deps = policy.get("schema_dependencies", [])
    if len(deps) != 1 or deps[0].get("download_url") != OFFICIAL_DEP:
        raise ValueError("Unknown official schema dependency declaration")
    args.directory.mkdir(parents=True, exist_ok=True)
    source = args.directory / "osisCore.2.1.1-cw-latest.xsd"
    pinned_fetch(OFFICIAL_MAIN, policy["schema_sha256"], source)
    dependency = args.directory / deps[0]["local_filename"]
    pinned_fetch(OFFICIAL_DEP, deps[0]["sha256"], dependency)
    _schema(policy, source)
    print(json.dumps({
        "status": "reviewed_XSD_and_dependency_verified",
        "source": OFFICIAL_MAIN,
        "sha256": policy["schema_sha256"],
        "dependency": OFFICIAL_DEP,
        "dependency_sha256": deps[0]["sha256"],
        "no_bible_text_validated": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
