#!/usr/bin/env python3
"""Bounded, timeout-safe diatheke query runner shared by pilot diagnostics.

The diatheke -k flag is a terminal query flag; output options MUST precede it.
No stdout text or stderr is persisted in reports.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import selectors
import subprocess
import time

from pilot_preflight import PilotError

MAX_OUTPUT = 4 * 1024 * 1024
TIMEOUT = 40


def query(module_id: str, reference: str, *, fmt: str, root: Path,
          exe: str = "diatheke", limit: int = MAX_OUTPUT,
          timeout: int = TIMEOUT, options: str = "") -> tuple[int, bytes]:
    if fmt not in {"internal", "plain"} or not isinstance(module_id,str) or not module_id:
        raise PilotError("Unreviewed SWORD reader request")
    if not isinstance(reference,str) or not reference or len(reference) > 120:
        raise PilotError("Invalid bounded SWORD key")
    allowed_options = set("nfmhcvalsrbwgeixtM")
    if not isinstance(options,str) or not set(options).issubset(allowed_options) or (
            len(options) != len(set(options))):
        raise PilotError("Invalid explicit SWORD filter request")
    cmd = [exe, "-b", module_id, "-f", fmt]
    if options:
        cmd.extend(("-o", options))
    cmd.extend(("-k", reference))  # -k MUST BE LAST!
    environment = dict(os.environ, SWORD_PATH=str(root))
    process = subprocess.Popen(
        cmd, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    result = bytearray()
    try:
        deadline = time.monotonic() + timeout
        selector = selectors.DefaultSelector()
        with selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PilotError("SWORD request timed out")
                events = selector.select(remaining)
                if not events:
                    raise PilotError("SWORD request timed out")
                block = os.read(process.stdout.fileno(), 65536)
                if not block:
                    break
                result.extend(block)
                if len(result) > limit:
                    raise PilotError(f"SWORD reader returned more than {limit} bytes for one key")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise PilotError("SWORD request timed out")
        code = process.wait(timeout=remaining)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout:
            process.stdout.close()
    return code, bytes(result)


def present_key(reference: str, data: bytes, code: int) -> bool:
    """Conservative sanity check, not proof of verse identity or content."""
    if code != 0 or not data.strip():
        return False
    lower = data[:1000].lower()
    return not any(x in lower for x in (
        b"not found", b"not a valid", b"no modules", b"usage: diatheke",
        b"unknown option", b"error:", b"not available",
    ))
