#!/usr/bin/env python3
"""Research-only CCEL source anchor ↔ stock SWORD occupied-slot reconciliation.

This checks whether each original commentary *reference span* has at least one
candidate occupied native SWORD key. It DOES NOT prove SWORD entry boundaries,
matching commentary content, quotations, notes, punctuation, paragraph
positions, authorial edition identity or permission to redistribute.

The two originals are SHA-pinned, read in disposable storage, and never emitted.
All original scripCom attribute values stay private; only SHA hashes, counts
and source line numbers for potential anomalies leave the process.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from lxml import etree

from commentary_intake import SHA, load_manifest
from commentary_native_inventory import inventory
from commentary_xml_witness import MAX_XML, OSIS_LOC, WORK_REF
from pilot_fetch import fetch, validate_url
from pilot_preflight import PilotError

MAX_MARKERS = 100_000
MAX_ANOMALIES = 200

def parse_source_markers(original: bytes) -> tuple[list[dict], dict]:
    if not 1000 <= len(original) <= MAX_XML:
        raise PilotError("Original XML outside reviewed byte limits")
    try:
        root = etree.fromstring(
            original,
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                huge_tree=False, recover=False, remove_blank_text=False
            )
        )
    except (ValueError, etree.XMLSyntaxError):
        # Never leak fragments or lines of original commentary in errors.
        raise PilotError("Original commentary XML could not be safely parsed") from None
    refs: list[dict] = []
    ordered = sha256()
    kinds = Counter()
    work_hashes = set()
    duplicate_count = 0
    seen_raw = set()
    unreviewed = []
    for node in root.iter():
        if isinstance(node, etree._Entity):
            raise PilotError("Original XML has unresolved entities; full reference scan blocked")
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        if len(refs) >= MAX_MARKERS:
            raise PilotError("Original commentary has more markers than the reviewed limit")
        raw = node.get("osisRef", "")
        if len(raw) > 512:
            raise PilotError("Unbounded original commentary annotation reference")
        digest = sha256(raw.encode("utf-8")).hexdigest()
        ordered.update(raw.encode("utf-8") + b"\0")
        if raw in seen_raw:
            duplicate_count += 1
        seen_raw.add(raw)
        entry = {"source_marker": len(refs) + 1,
                 "source_line": node.sourceline,
                 "reference_sha256": digest,
                 "book": None, "kind": "unreviewed",
                 "start": None, "end": None}
        match = WORK_REF.fullmatch(raw)
        if match:
            work, body = match.groups()
            work_hashes.add(sha256(work.encode("utf-8")).hexdigest())
            parts = body.split("-")
            if len(parts) in (1, 2):
                endpoints = [OSIS_LOC.fullmatch(part) for part in parts]
                if all(endpoints):
                    first = endpoints[0]
                    book, chapter, verse = first.groups()
                    if len(endpoints) == 1:
                        entry.update(book=book,
                            kind="chapter" if verse is None else "verse",
                            start=(int(chapter), int(verse or 1)),
                            end=(int(chapter), 9999 if verse is None else int(verse)))
                    else:
                        second = endpoints[1]
                        last_book, last_chapter, last_verse = second.groups()
                        if (book == last_book and verse is not None
                                and last_verse is not None
                                and (int(chapter), int(verse)) <= (int(last_chapter), int(last_verse))):
                            entry.update(book=book, kind="range",
                                start=(int(chapter), int(verse)),
                                end=(int(last_chapter), int(last_verse)))
        kinds[entry["kind"]] += 1
        if entry["kind"] == "unreviewed" and len(unreviewed) < MAX_ANOMALIES:
            unreviewed.append({k:entry[k] for k in
                               ("source_marker", "source_line", "reference_sha256")})
        refs.append(entry)
    if not refs:
        raise PilotError("No identifiable original commentary anchors in XML")
    return refs, {
        "source_marker_total": len(refs),
        "source_markers_by_kind": dict(sorted(kinds.items())),
        "source_distinct_work_prefix_count": len(work_hashes),
        "source_duplicate_osisref_count": duplicate_count,
        "ordered_original_reference_sha256": ordered.hexdigest(),
        "unreviewed_source_ref_samples": unreviewed,
        "source_ref_values_not_exported": True,
    }


def reconcile_occupied_slots(refs: list[dict], occupied_rows: list[tuple[str, str]]) -> dict:
    """A candidate slot within a source span is a necessary, NOT sufficient, match."""
    numbered: dict[str, list[tuple[int,int]]] = defaultdict(list)
    intros = set()
    seen = set()
    for kind, key in occupied_rows:
        if (kind, key) in seen:
            raise PilotError("Duplicate native index record in reconciliation input")
        seen.add((kind, key))
        if kind == "K":
            parts = key.split(".")
            if len(parts) != 3:
                raise PilotError("Malformed native numbered slot")
            book, chapter, verse = parts
            numbered[book].append((int(chapter), int(verse)))
        elif kind == "I":
            parts = key.split(".")
            if len(parts) in (2,3) and parts[1].isdigit():
                intros.add((parts[0], int(parts[1])))
        elif kind != "U":
            raise PilotError("Unreviewed native SWORD key class")
    for book in numbered:
        numbered[book].sort()
        if len(set(numbered[book])) != len(numbered[book]):
            raise PilotError("Duplicate native book+verse key")
    classes = Counter()
    books = Counter()
    unmatched = []
    occupied_union = set()
    chapter_intro_matches = 0
    john316_source_spans = 0
    for entry in refs:
        kind = entry["kind"]
        if kind == "unreviewed":
            classes["unreviewed_source_grammar"] += 1
            continue
        book = entry["book"]
        start, end = entry["start"], entry["end"]
        if book == "John" and start <= (3,16) <= end:
            john316_source_spans += 1
        slots = numbered.get(book, [])
        left, right = bisect_left(slots, start), bisect_right(slots, end)
        intro_present = kind == "chapter" and (book, start[0]) in intros
        if intro_present:
            chapter_intro_matches += 1
        if left < right or intro_present:
            classes["candidate_native_occupied_slot_in_original_span"] += 1
            books[book] += 1
            occupied_union.update((book, c, v) for c,v in slots[left:right])
        else:
            classes["no_occupied_slot_found_in_original_span"] += 1
            if len(unmatched) < MAX_ANOMALIES:
                unmatched.append({
                    "source_marker": entry["source_marker"],
                    "source_line": entry["source_line"],
                    "source_reference_sha256": entry["reference_sha256"],
                    "reference_class": kind,
                    "book": book,
                })
    return {
        "source_anchor_candidate_status": "reference_span_occupancy_only_not_content_or_entry_equivalence",
        "source_markers_with_candidate_native_occupied_slot": classes[
            "candidate_native_occupied_slot_in_original_span"],
        "source_markers_without_candidate_native_occupied_slot": classes[
            "no_occupied_slot_found_in_original_span"],
        "source_markers_with_unreviewed_reference_grammar": classes[
            "unreviewed_source_grammar"],
        "chapter_markers_with_native_chapter_intro_candidate": chapter_intro_matches,
        "original_book_codes_with_candidate_slots": len(books),
        "original_books_with_candidate_slots_count_by_book": dict(sorted(books.items())),
        "distinct_stock_numbered_slots_inside_any_original_span": len(occupied_union),
        "stock_occupied_numbered_slots_outside_all_original_spans":
            sum(len(s) for s in numbered.values()) - len(occupied_union),
        "john_3_16_original_markers_covering_reference": john316_source_spans,
        "john_3_16_exact_native_slot_occupied": ("K","John.3.16") in seen,
        "unmatched_candidate_anchor_samples": unmatched,
        "all_source_text_and_quoted_scripture_compared": False,
        "actual_authorial_commentary_entry_boundaries_compared": False,
        "source_to_sword_notes_and_structure_compared": False,
        "comments_and_content_equivalence_verified": False,
        "original_reference_values_rewritten": False,
        "copyright_and_redistribution_approved": False,
        "published": False,
    }


def run(resource_id: str, *, inspector: Path, directory: Path | None = None) -> dict:
    manifest = load_manifest(resource_id, directory)
    config = manifest.get("commentary_source", {})
    url = config.get("xml_witness_url")
    expected = config.get("xml_witness_sha256")
    if not isinstance(url,str) or not isinstance(expected,str) or not SHA.fullmatch(expected):
        raise PilotError("Source XML URL and SHA-256 must be independently reviewed and pinned")
    parsed = urlsplit(url)
    if parsed.hostname not in {"ccel.org","www.ccel.org"} or not parsed.path.endswith(".xml") or parsed.query:
        raise PilotError("Unreviewed original commentary XML source URL")
    validate_url(url, "ccel")
    with tempfile.TemporaryDirectory(prefix="commentary-anchor-audit-") as tmp:
        path = Path(tmp)/"source.xml"
        receipt = fetch(url, path, "ccel")
        if receipt["sha256"] != expected:
            raise PilotError("Original commentary XML source drifted from pinned SHA-256")
        refs, source = parse_source_markers(path.read_bytes())
        # One independent stock archive download/installation/index enumeration.
        native = inventory(resource_id, inspector=inspector, directory=directory, include_rows=True)
        rows = native.pop("native_occupied_rows_for_in_memory_reconciliation")
        actual = reconcile_occupied_slots(refs, rows)
    if source["source_marker_total"] != sum(source["source_markers_by_kind"].values()):
        raise PilotError("Original marker counts fail full traversal accounting")
    if (source["ordered_original_reference_sha256"] !=
            config.get("xml_source_reference_ordered_sha256", source["ordered_original_reference_sha256"])):
        # Optional exact ordered reference pin only: never rewrite the source.
        raise PilotError("Original source reference marker order changed")
    return {
        "schema_version": 1,
        "resource_id": resource_id,
        "status": "reference_slot_reconciliation_observed_not_text_parity",
        "original_xml_sha256": expected,
        "stock_sword_zip_sha256": native["original_zip_sha256"],
        "stock_sword_conf_sha256": native["original_conf_sha256"],
        "stock_native_occupied_index_sha256": native["ordered_occupied_key_sha256"],
        "stock_native_occupied_numbered_slots": native["occupied_numbered_slots"],
        "stock_native_occupied_intro_slots": native["occupied_intro_slots"],
        "source": source,
        "reconciliation": actual,
        "rights_approved": False, "editorial_approved": False,
        "full_source_to_compiled_parity": False,
        "originals_modified": False, "originals_published": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--native-inspector", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = run(args.resource_id, inspector=args.native_inspector)
        code = 0
    except (ValueError, OSError, RuntimeError) as exc:
        result = {
            "schema_version": 1, "resource_id": args.resource_id,
            "status": "blocked", "reason": str(exc),
            "originals_published": False,
            "full_source_to_compiled_parity": False
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Commentary anchor reconciliation: " + result["status"] +
          "; metadata-only report")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
