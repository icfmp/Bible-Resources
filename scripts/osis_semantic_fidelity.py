#!/usr/bin/env python3
"""Edition-neutral, read-only OSIS source→candidate semantic fidelity audit.

This is NOT a compiled-SWORD readback. The separate native SWORD proof and
actual source-to-reader content comparison remain mandatory for issue #28.
Both inputs must first independently pass the project's pinned OSIS XSD gate.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from lxml import etree

from source_osis_inventory import (
    _read_source, _source_tree, source_inventory, SourceInventoryError, OSIS,
)

# Include all source-authorial structural positions, rather than silently
# assuming matching words/verses implies matching poetry or footnote layout.
STRUCTURE = frozenset({
    "div", "chapter", "verse", "title", "p", "lg", "l", "q", "hi",
    "seg", "note", "reference", "w", "lb", "milestone", "list", "item",
    "table", "row", "cell", "transChange", "foreign", "divineName",
})
MAX_BOOKS = 250
MAX_FINDINGS = 80


class FidelityError(ValueError):
    """Malformed or unsupported source must block, never be repaired."""


class DigestSequence:
    """Hash a list of ordered structured items with unambiguous framing."""

    def __init__(self):
        self._hash = sha256()
        self.count = 0

    def append(self, value):
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        self._hash.update(len(raw).to_bytes(8, "big"))
        self._hash.update(raw)
        self.count += 1

    def hexdigest(self):
        return self._hash.hexdigest()


def _attributes(node):
    # Include every attribute, not only known lemma/note/osisRef names.
    return sorted(node.attrib.items())


def _visible_lexical_text(node) -> str:
    return "".join(node.itertext())


def _book_semantics(book: etree._Element) -> dict:
    name = book.get("osisID")
    if not name:
        raise FidelityError("OSIS book lacks an osisID")
    main_hash, note_hash = sha256(), sha256()
    lanes = {key: DigestSequence() for key in (
        "lexical_words", "note_bodies_callers_positions",
        "explicit_reference_targets", "ordered_structure_boundaries",
        "ordered_all_markup",
    )}
    counts = Counter()
    main_chars = 0
    note_chars = 0
    words = 0

    def walk(node: etree._Element, *, in_note=False, depth=0):
        nonlocal main_chars, note_chars, words
        if depth > 256:
            raise FidelityError(f"{name}: OSIS nesting exceeds safe bound")
        if not isinstance(node.tag, str):
            # XML comments/processing instructions are part of the immutable
            # original byte SHA, but not authored Bible text or OSIS markup.
            return
        if not node.tag.startswith(OSIS):
            raise FidelityError(f"{name}: unexpected foreign OSIS markup")
        local = etree.QName(node).localname
        nested_note = local == "note"
        if nested_note and in_note:
            raise FidelityError(f"{name}: nested notes require source review")
        attrs = _attributes(node)
        counts[local] += 1
        if sum(counts.values()) > 3_500_000:
            raise FidelityError(f"{name}: too many semantic markup elements")
        # A logical structural boundary is linked to the cumulative *book*
        # lexical-word ordinal and exact text offset. Preserve milestone
        # start/end direction and ID; no automatic OSIS canonicalization.
        is_marker = local in STRUCTURE
        has_sid = "sID" in node.attrib
        has_eid = "eID" in node.attrib
        if has_sid and has_eid:
            raise FidelityError(f"{name}: simultaneous sID and eID")
        if (has_sid and not node.get("sID")) or (has_eid and not node.get("eID")):
            raise FidelityError(f"{name}: empty structural milestone identifier")
        opening = not has_eid
        closing = not has_sid
        if is_marker:
            lanes["ordered_structure_boundaries"].append(
                ["+" if opening else "-", local, words, main_chars, attrs])
        lanes["ordered_all_markup"].append(["+", local, attrs])
        if local == "w":
            words += 1
            lanes["lexical_words"].append(
                [words, _visible_lexical_text(node), attrs])
        if local == "note":
            lanes["note_bodies_callers_positions"].append(
                [words, main_chars, _visible_lexical_text(node), attrs])
        if local == "reference":
            # Missing osisRef, empty osisRef and explicit target differ;
            # never use SWORD-derived Footnote.refList as authored osisRef.
            lanes["explicit_reference_targets"].append(
                [words, main_chars, node.get("osisRef"), attrs,
                 _visible_lexical_text(node)])

        target_is_note = in_note or nested_note

        def record_text(piece: str | None, *, note_text: bool):
            nonlocal main_chars, note_chars
            if piece is None:
                return
            encoded = piece.encode("utf-8")
            if note_text:
                note_hash.update(encoded)
                note_chars += len(piece)
            else:
                main_hash.update(encoded)
                main_chars += len(piece)

        record_text(node.text, note_text=target_is_note)
        for child in node:
            walk(child, in_note=target_is_note, depth=depth + 1)
            record_text(child.tail, note_text=target_is_note)
        if is_marker and opening and closing:
            lanes["ordered_structure_boundaries"].append(
                ["-", local, words, main_chars, attrs])
        lanes["ordered_all_markup"].append(["-", local, attrs])

    walk(book)
    return {
        "book": name,
        "main_text_characters": main_chars,
        "main_text_exact_utf8_sha256_after_xml_entity_decoding": main_hash.hexdigest(),
        "note_text_characters": note_chars,
        "note_text_exact_utf8_sha256_after_xml_entity_decoding": note_hash.hexdigest(),
        "source_word_tag_count": words,
        "source_note_tag_count": lanes["note_bodies_callers_positions"].count,
        "source_explicit_reference_tag_count": lanes["explicit_reference_targets"].count,
        "markup_counts": dict(sorted(counts.items())),
        "lanes": {
            key: {"events": ledger.count, "sha256": ledger.hexdigest()}
            for key, ledger in sorted(lanes.items())
        },
    }


def semantic_snapshot(raw: bytes) -> dict:
    """Build a privacy-safe per-book fingerprint. Zero inferred source verses."""
    # Reuse the separate strict numeric key inventory, but do not claim that
    # matching keys proves lexical, note, reference or layout parity.
    _, key_info = source_inventory(raw)
    root = _source_tree(raw)
    books = [node for node in root.iter(OSIS + "div")
             if node.get("type") == "book"]
    if not books or len(books) > MAX_BOOKS:
        raise FidelityError("Missing or excessive OSIS books")
    seen = set()
    signatures = []
    for book in books:
        name = book.get("osisID")
        if name in seen:
            raise FidelityError("Repeated OSIS book ID")
        seen.add(name)
        signatures.append(_book_semantics(book))
    if [b["book"] for b in signatures] != [b["book"] for b in key_info["books"]]:
        raise FidelityError("OSIS source/key book order mismatch")
    return {
        "schema_version": 1,
        "stage": "source_osis_semantic_inventory_only",
        "source_osis_sha256": sha256(raw).hexdigest(),
        "source_authored_keys_sha256": key_info["source_keys_sha256"],
        "source_authored_verse_count": key_info["source_verse_count"],
        "source_book_count": len(signatures),
        "books": signatures,
        "original_source_unchanged": True,
        "official_osis_schema_validated": False,
        "stock_sword_compiled_content_verified": False,
        "upstream_usfm_usfx_to_osis_verified": False,
        "rights_reviewed": False,
        "reader_rendering_verified": False,
        "approved_for_publication": False,
    }


def compare_semantics(source: bytes, candidate: bytes) -> dict:
    """Exact source-to-source checks; report differences rather than rewriting."""
    a = semantic_snapshot(source)
    b = semantic_snapshot(candidate)
    indexed_a = {book["book"]: book for book in a["books"]}
    indexed_b = {book["book"]: book for book in b["books"]}
    affected = []
    differing_lanes = Counter()
    for name in dict.fromkeys([*indexed_a, *indexed_b]):
        old = indexed_a.get(name)
        new = indexed_b.get(name)
        if old is None or new is None:
            affected.append({"book": name, "problem": "book_added_or_removed"})
            differing_lanes["book_presence"] += 1
            continue
        fields = []
        for field in (
            "main_text_exact_utf8_sha256_after_xml_entity_decoding",
            "note_text_exact_utf8_sha256_after_xml_entity_decoding",
            "source_word_tag_count", "source_note_tag_count",
            "source_explicit_reference_tag_count", "markup_counts",
        ):
            if old[field] != new[field]:
                fields.append(field)
        for lane in old["lanes"]:
            if old["lanes"][lane] != new["lanes"][lane]:
                fields.append(lane)
        if fields:
            for field in fields:
                differing_lanes[field] += 1
            if len(affected) < MAX_FINDINGS:
                affected.append({"book": name, "different_lanes": fields})
    same_book_order = list(indexed_a) == list(indexed_b)
    same_authorial_keys = (
        a["source_authored_keys_sha256"] == b["source_authored_keys_sha256"])
    if not same_book_order:
        differing_lanes["book_order"] += 1
    if not same_authorial_keys:
        differing_lanes["verse_keys"] += 1
    exact = (not differing_lanes)
    return {
        "schema_version": 1,
        "status": ("source_to_candidate_semantics_exact"
                   if exact else "blocked_source_to_candidate_semantic_drift"),
        "source_osis_sha256": a["source_osis_sha256"],
        "candidate_osis_sha256": b["source_osis_sha256"],
        "source_book_count": a["source_book_count"],
        "candidate_book_count": b["source_book_count"],
        "source_authored_verse_count": a["source_authored_verse_count"],
        "candidate_authored_verse_count": b["source_authored_verse_count"],
        "book_order_exact": same_book_order,
        "authorial_verse_keys_exact": same_authorial_keys,
        "books_with_changes": len(affected),
        "first_affected_books": affected,
        "different_lanes_book_counts": dict(sorted(differing_lanes.items())),
        "raw_xml_bytes_identical": source == candidate,
        "xml_entity_representation_or_comments_checked_by_original_sha": True,
        "compiled_stock_sword_reader_semantics_verified": False,
        "authorial_usfm_usfx_conversion_verified": False,
        "official_schema_validation_separately_required": True,
        "approved_for_publication": False,
    }


def _write_new_report(path: Path, source: Path, candidate: Path, report: dict):
    target = path.resolve()
    if (path.exists() or path.is_symlink() or not path.parent.is_dir()
            or path.parent.is_symlink()
            or target in (source.resolve(), candidate.resolve())):
        raise FidelityError("Refusing unsafe or existing report output")
    data = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".osis-semantic-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        if path.exists() or path.is_symlink():
            raise FidelityError("Report destination appeared during generation")
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-osis", required=True, type=Path)
    p.add_argument("--candidate-osis", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    try:
        source = _read_source(args.source_osis)
        candidate = _read_source(args.candidate_osis)
        report = compare_semantics(source, candidate)
        _write_new_report(args.report, args.source_osis,
                          args.candidate_osis, report)
    except (SourceInventoryError, OSError, ValueError, UnicodeError) as exc:
        p.error(str(exc))
    print(report["status"])
    return 0 if report["status"] == "source_to_candidate_semantics_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
