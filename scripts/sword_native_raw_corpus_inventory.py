#!/usr/bin/env python3
"""Hash every actual native stock-SWORD raw entry without exposing Bible text.

Private C++ helper writes length-framed unfiltered XML bytes ONLY into this
Python subprocess pipe. Only SHA-256, IDs, counts and explicit unverified proof
flags are written to JSON. A matching digest is a compiled-corpus identity
fingerprint, NOT independently validated source-text fidelity.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from stable_sword_refs import KEY, module_payload_digest
from sword_native_inventory import (
    INTRO, _validate_payload, collect_native_inventory,
)

MAX_HEADER = 160
MAX_FRAMES = 300_000
MAX_RAW_ENTRY = 2 * 1024 * 1024
MAX_BYTES = 512 * 1024 * 1024
TOP = re.compile(r"^TOP:[1-9][0-9]*$")


class RawCorpusError(ValueError):
    """The complete native raw corpus could not be proved read or indexed."""


def _ordered_manifest_entry(type_: str, name: str, raw: bytes) -> bytes:
    # Unambiguous length framing ensures no name/tag boundary collisions.
    parts = (type_.encode("ascii"), name.encode("ascii"),
             len(raw).to_bytes(8, "big"), bytes.fromhex(sha256(raw).hexdigest()))
    return b"".join(len(p).to_bytes(4, "big") + p for p in parts)


def parse_native_raw_corpus(stream) -> tuple[dict, list[str], list[str], list[str]]:
    """Stream actual unfiltered native raw bytes. Never write those to logs."""
    total = Counter()
    unique = {"K": set(), "I": set(), "U": set()}
    ordinary: list[str] = []
    introductions: list[str] = []
    anonymous: list[str] = []
    whole = sha256()
    by_book = {}
    total_raw_bytes = 0
    seen_terminal = False
    for _ in range(MAX_FRAMES + 1):
        line = stream.readline(MAX_HEADER + 1)
        if not line or len(line) > MAX_HEADER or not line.endswith(b"\n"):
            raise RawCorpusError("Truncated, oversized or unterminated private raw frame header")
        try:
            fields = line[:-1].decode("ascii").split("\t")
        except UnicodeError as exc:
            raise RawCorpusError("Malformed non-ASCII native frame header") from exc
        type_ = fields[0]
        if type_ == "S":
            if len(fields) != 5 or any(not x.isdigit() for x in fields[1:]):
                raise RawCorpusError("Malformed native raw end-of-scan totals")
            actual = tuple(int(x) for x in fields[1:])
            expected = (total["K"] + total["I"] + total["U"],
                        total["K"], total["I"], total["U"])
            if actual != expected or actual[0] == 0 or actual[1] == 0:
                raise RawCorpusError("Native raw end-of-scan counts are inconsistent")
            if stream.read(1):
                raise RawCorpusError("Extra data after terminal raw scan summary")
            seen_terminal = True
            break
        if type_ not in ("K", "I", "U") or len(fields) != 3:
            raise RawCorpusError("Invalid native raw record type or field count")
        reference, size_string = fields[1], fields[2]
        if not size_string.isdigit():
            raise RawCorpusError("Invalid native raw byte length")
        size = int(size_string)
        if size > MAX_RAW_ENTRY or size + total_raw_bytes > MAX_BYTES:
            raise RawCorpusError("Native raw entry/corpus exceeds size bound")
        if ((type_ == "K" and KEY.fullmatch(reference) is None)
                or (type_ == "I" and INTRO.fullmatch(reference) is None)
                or (type_ == "U" and TOP.fullmatch(reference) is None)):
            raise RawCorpusError("Invalid occupied native location identifier")
        if reference in unique[type_]:
            raise RawCorpusError("Repeated occupied native raw location")
        unique[type_].add(reference)
        if type_ == "U" and reference != f"TOP:{total['U'] + 1}":
            raise RawCorpusError("Noncontiguous opaque TOP native location order")
        remaining = size
        entry = sha256()
        # Keep source bytes in a bounded transient buffer for encoding checks.
        raw_chunks = []
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise RawCorpusError("Truncated native raw entry bytes")
            entry.update(chunk)
            raw_chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(raw_chunks)
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise RawCorpusError("Non-UTF-8 native raw Scripture entry") from exc
        total_raw_bytes += size
        total[type_] += 1
        if type_ == "K":
            ordinary.append(reference)
        elif type_ == "I":
            introductions.append(reference)
        else:
            anonymous.append(reference)
        book = reference.split(".", 1)[0] if type_ != "U" else "_ANONYMOUS_TOP"
        if book not in by_book:
            by_book[book] = {"hasher": sha256(), "entry_counts": Counter(),
                             "raw_bytes": 0, "first": reference, "last": reference}
        info = by_book[book]
        info["entry_counts"][type_] += 1
        info["raw_bytes"] += size
        info["last"] = reference
        record = _ordered_manifest_entry(type_, reference, raw)
        whole.update(record)
        info["hasher"].update(record)
    if not seen_terminal:
        raise RawCorpusError("Native stock SWORD scan did not terminate completely")
    report = {
        "schema_version": 1,
        "status": "actual_full_native_raw_corpus_hashed_not_source_parity_approved",
        "actual_occupied_numbered_entry_count": total["K"],
        "actual_occupied_intro_entry_count": total["I"],
        "actual_occupied_anonymous_top_entry_count": total["U"],
        "all_actual_raw_entries_scanned": sum(total.values()),
        "actual_native_unfiltered_raw_bytes_total": total_raw_bytes,
        "all_native_raw_entries_ordered_sha256": whole.hexdigest(),
        "books_and_opaque_top": [
            {"book": book,
             "occupied_numbered_entries": info["entry_counts"]["K"],
             "occupied_intro_entries": info["entry_counts"]["I"],
             "opaque_top_entries": info["entry_counts"]["U"],
             "first_native_ref": info["first"],
             "last_native_ref": info["last"],
             "native_raw_bytes_total": info["raw_bytes"],
             "ordered_raw_entries_sha256": info["hasher"].hexdigest()}
            for book, info in by_book.items()
        ],
        "source_original_authorial_text_compared": False,
        "exact_text_punctuation_and_spacing_fidelity_verified": False,
        "note_body_caller_reference_fidelity_verified": False,
        "ordered_original_markup_lexical_and_layout_verified": False,
        "native_intro_text_matches_original_verified": False,
        "source_to_compiled_versification_concordance_verified": False,
        "rights_and_editorial_approval": False,
        "published": False,
    }
    return report, ordinary, introductions, anonymous


def inspect_native_raw_corpus(
    module: Path, module_id: str, native_raw_binary: Path,
    native_index_binary: Path
) -> dict:
    if native_raw_binary.is_symlink() or not native_raw_binary.is_file():
        raise RawCorpusError("Missing or linked trusted full-native-raw binary")
    payload, driver, system = _validate_payload(module, module_id)
    before = module_payload_digest(module)
    # Independently collect the true native index from a separate C++ helper.
    keys, _registry, proof = collect_native_inventory(
        native_index_binary, module, module_id, timeout=240)
    env = dict(os.environ, SWORD_PATH=str(payload.resolve(strict=True)))
    process = None
    try:
        process = subprocess.Popen(
            [str(native_raw_binary.resolve(strict=True)), module_id],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        if process.stdout is None:
            raise RawCorpusError("Cannot privately capture native raw content stream")
        report, ordinary, intros, anonymous = parse_native_raw_corpus(process.stdout)
        process.stdout.close()
        try:
            status = process.wait(timeout=240)
        except subprocess.TimeoutExpired as exc:
            raise RawCorpusError("Native full corpus reader timed out") from exc
        if status != 0:
            raise RawCorpusError(f"Native full corpus raw reader failed (exit {status})")
    except BaseException:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        raise
    if (ordinary != keys.splitlines()
            or intros != proof["native_occupied_intro_references"]
            or len(anonymous) != proof["native_nonaddressable_populated_top_count"]
            or report["actual_occupied_numbered_entry_count"] !=
                proof["native_occupied_numbered_verse_count"]):
        raise RawCorpusError("Native full corpus diverges from independently inventoried reader keys")
    if before != module_payload_digest(module):
        raise RawCorpusError("Actual compiled SWORD module changed during raw inventory")
    report["module_id"] = module_id
    report["module_driver"] = driver
    report["module_native_versification"] = system
    report["module_payload_sha256"] = before
    report["native_raw_inspector_sha256"] = sha256(native_raw_binary.read_bytes()).hexdigest()
    report["independent_native_key_inspector_sha256"] = sha256(native_index_binary.read_bytes()).hexdigest()
    report["exact_all_occupied_native_keys_matched_independent_index"] = True
    report["independent_native_index_digest"] = proof["native_reader_keys_sha256"]
    report["native_engine_version"] = proof["reader_version"]
    return report


def write_new_metadata_report(
    destination: Path, module: Path, report: dict
) -> None:
    if (destination.is_symlink() or destination.exists()
            or not destination.parent.is_dir() or destination.parent.is_symlink()
            or destination.resolve().is_relative_to(module.resolve())):
        raise RawCorpusError("Unsafe or existing native corpus report destination")
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, path = tempfile.mkstemp(prefix=".native-corpus-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.exists() or destination.is_symlink():
            raise RawCorpusError("Native corpus report path appeared before publication")
        os.replace(path, destination)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--module-directory", required=True, type=Path)
    p.add_argument("--module-id", required=True)
    p.add_argument("--native-raw-binary", required=True, type=Path)
    p.add_argument("--native-index-binary", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    try:
        report = inspect_native_raw_corpus(
            args.module_directory, args.module_id,
            args.native_raw_binary, args.native_index_binary)
        write_new_metadata_report(args.report, args.module_directory, report)
    except (OSError, ValueError, UnicodeError) as exc:
        p.error(str(exc))
    print("Independently hashed", report["all_actual_raw_entries_scanned"],
          "actual stock-SWORD raw entries, without emitting Bible text. "
          "Source parity and publication remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
