#!/usr/bin/env python3
"""Download only registered pilot sources, to temporary workspace, without publishing."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request
from urllib.parse import urlsplit

from pilot_preflight import ROOT, PilotError, MAX_ZIP_BYTES

ALLOWED_HOSTS = {
    "lsg": {"ebible.org", "www.ebible.org"},
    "mhc": {"crosswire.org", "www.crosswire.org", "ftp.crosswire.org"},
}
MAX_REDIRECTS = 5


def validate_url(url: str, pilot: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS[pilot]
            or parts.username or parts.password or parts.port not in (None, 443)
            or parts.fragment):
        raise PilotError(f"{pilot}: URL/redirect outside allowlisted HTTPS hosts")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, pilot: str):
        self.pilot = pilot
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise PilotError("Too many redirects")
        validate_url(newurl, self.pilot)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, destination: Path, pilot: str,
          opener=None) -> dict:
    validate_url(url, pilot)
    if destination.is_symlink() or destination.exists():
        raise PilotError("Refusing to overwrite existing archive or symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    opener = opener or urllib.request.build_opener(SafeRedirect(pilot))
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".pilot-", delete=False) as stream:
            staged = Path(stream.name)
            sha = hashlib.sha256()
            total = 0
            request = urllib.request.Request(
                url, headers={"User-Agent": "BibleResources-PilotPreflight/1.0"}
            )
            with opener.open(request, timeout=60) as response:
                validate_url(response.url, pilot)
                while chunk := response.read(256 * 1024):
                    total += len(chunk)
                    if total > MAX_ZIP_BYTES:
                        raise PilotError(f"{pilot}: archive exceeds {MAX_ZIP_BYTES} bytes")
                    sha.update(chunk)
                    stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, destination)
        return {"url": url, "sha256": sha.hexdigest(), "bytes": total}
    finally:
        if staged is not None and staged.exists():
            staged.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=sorted(ALLOWED_HOSTS), required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config/pilot-sources.json")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise PilotError("Unreviewed pilot config")
    entry = config["pilots"][args.pilot]
    targets = [
        ("sword", entry["sword_zip_url"], args.directory / "sword.zip"),
    ]
    if entry.get("authored_zip_url"):
        targets.append(("authored", entry["authored_zip_url"], args.directory / "authored.zip"))
    result = {}
    for kind, url, dest in targets:
        result[kind] = fetch(url, dest, args.pilot)
    print(json.dumps({"pilot": args.pilot, "downloads": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
