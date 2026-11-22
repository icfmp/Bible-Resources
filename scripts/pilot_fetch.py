#!/usr/bin/env python3
"""Secure provider-allowlisted download of upstream ZIPs to disposable workspace."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request
from urllib.parse import urlsplit

from pilot_preflight import PilotError, MAX_ZIP_BYTES

ALLOWED_HOSTS = {
    "ebible": {"ebible.org", "www.ebible.org"},
    "crosswire": {"crosswire.org", "www.crosswire.org", "ftp.crosswire.org"},
    "ccel": {"ccel.org", "www.ccel.org"},
}
MAX_REDIRECTS = 5


def validate_url(url: str, provider: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS.get(provider, ())
            or parts.username or parts.password or parts.port not in (None, 443)
            or parts.fragment):
        raise PilotError(f"{provider}: URL/redirect outside allowlisted HTTPS hosts")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, provider: str):
        self.provider = provider
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise PilotError("Too many redirects")
        validate_url(newurl, self.provider)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, destination: Path, provider: str,
          opener=None) -> dict:
    validate_url(url, provider)
    if destination.is_symlink() or destination.exists():
        raise PilotError("Refusing to overwrite existing archive or symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    opener = opener or urllib.request.build_opener(SafeRedirect(provider))
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
                validate_url(response.url, provider)
                while chunk := response.read(256 * 1024):
                    total += len(chunk)
                    if total > MAX_ZIP_BYTES:
                        raise PilotError(f"{provider}: archive exceeds {MAX_ZIP_BYTES} bytes")
                    sha.update(chunk)
                    stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, destination)
        return {"url": url, "sha256": sha.hexdigest(), "bytes": total}
    finally:
        if staged is not None and staged.exists():
            staged.unlink()


