#!/usr/bin/env python3
"""Exact source-to-stable-SWORD comparison of explicit OSIS reference targets.

This verifies only the authored reference osisRef attribute sequence,
including empty target attributes. SWORD-generated Footnote.refList values
are derived reader suggestions and are NOT authoritative source annotations.
Compiled attributes are written only to disposable temp storage; public
reports contain counts, reference-free hashes, and book identities.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from html import unescape
from pathlib import Path
import os
import subprocess
import tempfile
import unicodedata

from lsg_osis_parity import OSIS
from lsg_stock_lemma_parity import _books, ordered_lemma_reader_plan
from pilot_preflight import PilotError


def _value(value: str) -> str:
    return unicodedata.normalize("NFC", unescape(value))


def _digest(values: list[str]) -> str:
    digest = sha256()
    for value in values:
        payload = value.encode("utf-8")
        digest.update(len(payload).to_bytes(4, "big"))
        digest.update(payload)
    return digest.hexdigest()


def compare_compiled_explicit_reference_targets(
    candidate: Path, raw_rows: list[str]
) -> dict:
    """Reject changed, missing, reordered or newly invented OSIS reference keys."""
    books = _books(candidate)
    book_ids = [b.get("osisID") for b in books]
    compiled: dict[str, list[str]] = defaultdict(list)
    for row in raw_rows:
        parts = row.split("\t")
        if len(parts) != 2 or parts[0] not in book_ids:
            raise PilotError("Malformed compiled reference target inventory")
        compiled[parts[0]].append(_value(parts[1]))

    matched_books = 0
    source_tags = compiled_tags = 0
    source_explicit = compiled_explicit = 0
    differences = []
    for book in books:
        book_id = book.get("osisID")
        source = [_value(n.get("osisRef") or "")
                  for n in book.iter(OSIS + "reference")]
        actual = compiled[book_id]
        source_tags += len(source)
        compiled_tags += len(actual)
        source_explicit += sum(bool(s) for s in source)
        compiled_explicit += sum(bool(s) for s in actual)
        if source == actual:
            matched_books += 1
        else:
            mismatch = next((i + 1 for i, (a, b)
                             in enumerate(zip(source, actual)) if a != b),
                            min(len(source), len(actual)) + 1)
            if len(differences) < 66:
                differences.append({
                    "book": book_id,
                    "source_reference_tags": len(source),
                    "compiled_reference_tags": len(actual),
                    "first_different_reference_position": mismatch,
                    "source_ordered_attribute_sha256": _digest(source),
                    "compiled_ordered_attribute_sha256": _digest(actual),
                })
    success = matched_books == len(books) and source_tags == compiled_tags
    return {
        "status": ("compiled_ordered_explicit_osisref_values_verified"
                   if success else "blocked_compiled_explicit_osisref_mismatch"),
        "books_compared": len(books),
        "books_with_exact_ordered_osisref_values": matched_books,
        "source_reference_tags": source_tags,
        "compiled_reference_tags": compiled_tags,
        "source_explicit_machine_target_values": source_explicit,
        "compiled_explicit_machine_target_values": compiled_explicit,
        "first_differing_books": differences,
        "derived_sword_footnote_reflists_are_not_source_targets": True,
        "reader_generated_target_semantics_verified": False,
        "human_reference_target_accuracy_verified": False,
        "source_modified": False,
        "published": False,
    }


def audit_compiled_explicit_reference_targets(
    candidate: Path, aliases: list[tuple[str, str]], *,
    sword_root: Path, module_id: str, inspector: Path
) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Stock SWORD reference target inspector missing")
    plan, _books_in_order = ordered_lemma_reader_plan(candidate, aliases)
    with tempfile.TemporaryDirectory(prefix="stock-reference-values-") as tmp:
        root = Path(tmp)
        keys = root / "ref-plan.tsv"
        private = root / "reference-osisref-only.tsv"
        keys.write_text(
            "".join("\t".join(row) + "\n" for row in plan),
            encoding="utf-8"
        )
        try:
            process = subprocess.run(
                [str(inspector), module_id, str(keys), str(private),
                 "--reference-targets-only"],
                env=dict(os.environ, SWORD_PATH=str(sword_root)),
                capture_output=True, text=True, timeout=180, check=False
            )
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Compiled SWORD reference inspection timed out") from exc
        if (process.returncode or process.stdout or process.stderr
                or not private.is_file()
                or private.stat().st_size > 10_000_000):
            raise PilotError(
                "Compiled SWORD reference attribute inspection failed "
                f"(exit {process.returncode})"
            )
        rows = private.read_text(encoding="utf-8").splitlines()
        report = compare_compiled_explicit_reference_targets(candidate, rows)
    report["reader_entries_inspected"] = len(plan)
    return report
