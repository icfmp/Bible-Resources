#!/usr/bin/env python3
"""Acquire a declared independent commentary text witness without publishing it.

All source bytes stay in disposable runner storage. Observes UTF-8 encoding,
line/paragraph signals and the immutable SHA-256. No excerpt, line,
private source text or false source-to-binary equivalence enters the report.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from commentary_intake import load_manifest, SHA
from pilot_fetch import fetch, validate_url
from pilot_preflight import PilotError

MAX_TEXT = 40 * 1024 * 1024
MAX_LINE = 2 * 1024 * 1024


def witness_signals(data: bytes) -> dict:
    if not (1000 <= len(data) <= MAX_TEXT):
        raise PilotError("Commentary source text is empty or exceeds 40 MiB limit")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise PilotError("Independent commentary text is not valid UTF-8; encoding review required") from exc
    if "\x00" in content:
        raise PilotError("Unexpected NUL inside commentary source")
    lines = content.splitlines()
    if len(lines) < 10 or max(map(len, lines)) > MAX_LINE:
        raise PilotError("Unreviewed original commentary line structure")
    blanks = sum(not line.strip() for line in lines)
    return {
        "utf8_decoded_without_loss": True,
        "source_byte_count": len(data),
        "source_sha256": sha256(data).hexdigest(),
        "lines": len(lines),
        "blank_lines": blanks,
        "nonblank_lines": len(lines) - blanks,
        "longest_line_characters": max(map(len, lines)),
        "newline_crlf": data.count(b"\r\n"),
        "newline_lf": data.count(b"\n"),
        "newline_cr": data.count(b"\r") - data.count(b"\r\n"),
        "original_source_structure_verified": False,
        "original_edition_identity_verified": False,
        "source_to_compiled_sword_parity_verified": False,
        "source_text_disclosed": False,
    }


def inspect_witness(resource_id: str, *, directory: Path | None = None) -> dict:
    manifest = load_manifest(resource_id, directory)
    url = manifest["authorial_witness_url"]
    parsed = urlsplit(url)
    if parsed.hostname not in {"ccel.org", "www.ccel.org"} or not parsed.path.endswith(".txt") or parsed.query:
        raise PilotError("Only exact, independently reviewed CCEL plaintext witness URLs currently accepted")
    validate_url(url, "ccel")
    commentary = manifest.get("commentary_source")
    if not isinstance(commentary, dict):
        raise PilotError("Missing separate authorial source identity record")
    expected = commentary.get("authored_source_sha256")
    if expected is not None and (not isinstance(expected, str) or not SHA.fullmatch(expected)):
        raise PilotError("Unreviewed authorial source SHA-256 pin")
    with tempfile.TemporaryDirectory(prefix="commentary-witness-") as temp:
        path = Path(temp) / "original.txt"
        receipt = fetch(url, path, "ccel")
        if receipt["bytes"] > MAX_TEXT:
            raise PilotError("Original commentary exceeds 40 MiB approved source ceiling")
        if expected is not None and receipt["sha256"] != expected:
            raise PilotError("Publisher text witness drifted from reviewed source SHA-256")
        signals = witness_signals(path.read_bytes())
        if signals["source_sha256"] != receipt["sha256"]:
            raise PilotError("Original source changed during inspection")
    return {
        "status": "source_bytes_pinned_unverified_edition" if expected else "source_observed_unverified_edition",
        "resource_id": resource_id,
        "source_url": url,
        "pinned_source_sha256_matches": expected is not None,
        **signals,
        "rights_redistribution_approved": False,
        "text_original_to_sword_verified": False,
        "content_unchanged": True,
        "published": False
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        report = inspect_witness(args.resource_id)
        status = 0
    except (ValueError, RuntimeError, OSError) as exc:
        report = {"status": "blocked", "error": str(exc),
                  "resource_id": args.resource_id, "published": False}
        status = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Commentary source witness: " + report["status"] + " — metadata-only")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
