#!/usr/bin/env python3
"""Diagnose note payload storage in released SWORD (metadata only).

Not a content-fidelity approval: note bodies must subsequently be compared
against immutable source OSIS in a separate, fail-closed semantic gate.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import os
from pathlib import Path
import subprocess
import tempfile

from lsg_stock_lemma_parity import ordered_lemma_reader_plan
from pilot_preflight import PilotError
from lsg_osis_parity import OSIS


def summarize_note_storage(rows: list[str], source_books: list) -> dict:
    expected = {book.get("osisID"): sum(1 for _ in book.iter(OSIS + "note"))
                for book in source_books}
    if not expected or len(expected) != len(source_books):
        raise PilotError("Invalid source note book identities")
    per_book = defaultdict(Counter)
    for row in rows:
        parts = row.split("\t")
        if len(parts) != 5 or parts[0] not in expected:
            raise PilotError("Malformed or unknown stock SWORD note diagnostic")
        try:
            numbers = [int(value) for value in parts[1:]]
        except ValueError as exc:
            raise PilotError("Non-integer SWORD note metadata count") from exc
        if any(v < 0 or v > 5000 for v in numbers):
            raise PilotError("Impossible stock SWORD note metadata count")
        per_book[parts[0]].update(dict(zip(
            ("raw_note_elements", "raw_sword_footnote_refs",
             "footnote_entry_attribute_records", "nonempty_note_body_records"),
            numbers)))
    totals = Counter()
    differences = []
    for book, source_count in sorted(expected.items()):
        found = per_book[book]
        totals.update(found)
        if found["raw_note_elements"] != source_count:
            differences.append({
                "book": book, "source_note_elements": source_count,
                "compiled_raw_note_elements": found["raw_note_elements"],
            })
    complete = not differences
    return {
        "status": ("compiled_note_entry_attribute_storage_observed"
                   if complete else "blocked_compiled_note_count_scope"),
        "source_note_elements": sum(expected.values()),
        "compiled_raw_note_elements": totals["raw_note_elements"],
        "raw_sword_footnote_refs": totals["raw_sword_footnote_refs"],
        "footnote_entry_attribute_records": totals["footnote_entry_attribute_records"],
        "nonempty_note_body_records": totals["nonempty_note_body_records"],
        "books_compared": len(expected),
        "books_with_different_note_marker_counts": differences,
        "full_note_text_and_targets_verified": False,
        "compiled_note_caller_and_anchor_verified": False,
        "source_modified": False,
        "published": False,
    }


def probe_compiled_note_storage(candidate: Path, aliases: list[tuple[str, str]],
                                *, sword_root: Path, module_id: str,
                                inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Stock SWORD note probe executable unavailable")
    plan, books = ordered_lemma_reader_plan(candidate, aliases)
    with tempfile.TemporaryDirectory(prefix="stock-note-probe-") as path:
        root = Path(path)
        refs = root / "refs.tsv"
        output = root / "note-counts.tsv"
        refs.write_text("".join("\t".join(item) + "\n" for item in plan),
                        encoding="utf-8")
        try:
            proc = subprocess.run(
                [str(inspector), module_id, str(refs), str(output),
                 "--note-attributes-only"],
                env=dict(os.environ, SWORD_PATH=str(sword_root)),
                capture_output=True, text=True, timeout=200, check=False)
        except subprocess.TimeoutExpired:
            return {"status":"compiled_note_entry_attribute_probe_timeout",
                    "full_note_text_and_targets_verified": False,
                    "published": False}
        if proc.returncode or proc.stdout or proc.stderr or not output.is_file():
            return {"status":"compiled_note_entry_attribute_probe_rejected",
                    "probe_exit_code":proc.returncode,
                    "probe_stderr_bytes":len(proc.stderr),
                    "full_note_text_and_targets_verified":False,
                    "published":False}
        if output.stat().st_size > 3_000_000:
            raise PilotError("Unbounded private SWORD note probe result")
        rows=output.read_text(encoding="utf-8").splitlines()
        if len(rows)!=len(plan):
            raise PilotError("Incomplete SWORD note probe reader key traversal")
        result=summarize_note_storage(rows, books)
    result["reader_entries_inspected"]=len(plan)
    return result
