#!/usr/bin/env python3
"""Strict, read-only inventory of original USFX structural events (no Scripture).

This is a SOURCE-side audit. It does not establish XML Schema compatibility,
compiled SWORD fidelity, annotation anchor equivalence or publication rights.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

from lxml import etree

MAX_SOURCE = 128 * 1024 * 1024
MAX_BOOKS = 250
MAX_ELEMENTS = 2_000_000
MAX_EXAMPLES = 24
VERSE_ID = re.compile(r"([0-9]+)(?:-([0-9]+))?\Z")

NOTES = frozenset({"f", "fe", "x", "ef", "ex", "note"})
HEADINGS = frozenset({"h", "mt", "mte", "s", "ms", "mr", "r", "d", "cl", "toc", "toca"})
PARAGRAPHS = frozenset({"p", "pi", "pm", "m", "mi", "pc", "pr", "b", "nb", "cls", "para"})
POETRY = frozenset({"q", "qr", "qc", "qa", "qm", "qd", "qs", "qac", "li"})
REFS = frozenset({"ref", "rq", "xt", "xq", "xo", "xot", "xnt", "fr"})


class USFXAuditError(ValueError):
    """Untrusted or undecidable original source: stop, never auto-repair."""


def _name(node):
    return etree.QName(node).localname


def _json_hash(value):
    return sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                            separators=(",", ":")).encode("ascii")).hexdigest()


def audit_source_usfx(xml: bytes) -> dict:
    """Inventory every source element and numbered reference in document order.

    All user-authored text and attribute values remain in private memory.
    The returned receipt contains only counters, structural hashes, and
    canonical reference IDs (not translated Scripture or note bodies).
    """
    if not isinstance(xml, bytes) or not 0 < len(xml) <= MAX_SOURCE:
        raise USFXAuditError("Original USFX is empty or oversized")
    if re.search(rb"<!DOCTYPE\b|<!ENTITY\b", xml, flags=re.IGNORECASE):
        raise USFXAuditError("Original XML includes a DTD or entity declaration")
    try:
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                 no_network=True, recover=False, huge_tree=False)
        doc = etree.ElementTree(etree.fromstring(xml, parser=parser))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise USFXAuditError("Original USFX is not well-formed XML") from exc
    root = doc.getroot()
    if (doc.docinfo.doctype or doc.docinfo.internalDTD or doc.docinfo.externalDTD
            or root.tag != "usfx"):
        raise USFXAuditError("Unexpected original root, DTD or XML namespace")
    if len(root) > MAX_BOOKS + 1000:
        raise USFXAuditError("Oversized root-level source inventory")

    elements = Counter()
    attrs = Counter()
    categories = Counter()
    marker_positions = Counter()
    notes_by_kind = Counter()
    note_callers = Counter()
    first_findings = []
    issues = Counter()
    books = []
    seen_books = set()
    key_hash = sha256()
    event_hash = sha256()
    total_keys = 0
    total_elements = 0

    def problem(code, ref):
        issues[code] += 1
        if len(first_findings) < MAX_EXAMPLES:
            first_findings.append({"category": code, "reference": ref})

    for top in root:
        if not isinstance(top.tag, str):
            continue
        if top.tag != "book":
            elements[top.tag] += 1
            attrs.update(top.attrib)
            if top.tag not in {"languageCode", "rem", "ide"}:
                problem("unreviewed_root_element", "document")
            continue
        book = top
        code = book.get("id")
        if not code or not re.fullmatch(r"[A-Z0-9]{3}", code):
            raise USFXAuditError("Missing or ambiguous original USFX book code")
        if code in seen_books:
            raise USFXAuditError("Duplicate original USFX book code")
        seen_books.add(code)
        if len(seen_books) > MAX_BOOKS:
            raise USFXAuditError("Too many original books")
        chapter = None
        last_chapter = 0
        last_verse = 0
        source_key_count = 0
        chapter_count = 0
        book_events = Counter()
        book_notes = Counter()
        for node in book.iter():
            if not isinstance(node.tag, str):
                continue
            total_elements += 1
            if total_elements > MAX_ELEMENTS:
                raise USFXAuditError("Too many original USFX elements")
            if node is not book and node.tag.startswith("{"):
                problem("unexpected_namespace_element", code)
            tag = _name(node)
            elements[tag] += 1
            attrs.update(etree.QName(a).localname for a in node.attrib)
            ref = f"{code}.{chapter or 0}.{last_verse or 0}"
            if tag == "c":
                raw = node.get("id", "")
                if not raw.isdigit() or int(raw) < 1 or int(raw) > 9999:
                    problem("invalid_chapter_id", ref)
                    continue
                new_chapter = int(raw)
                if new_chapter <= last_chapter:
                    problem("duplicate_or_out_of_order_chapter", f"{code}.{new_chapter}")
                chapter = new_chapter
                last_chapter = new_chapter
                last_verse = 0
                chapter_count += 1
                ref = f"{code}.{chapter}.0"
            elif tag == "v":
                raw = node.get("id", "")
                match = VERSE_ID.fullmatch(raw)
                if chapter is None or not match:
                    problem("missing_chapter_or_nonstandard_verse_id", ref)
                    continue
                start, stop = int(match[1]), int(match[2] or match[1])
                if not 1 <= start <= stop <= 9999 or stop - start > 50:
                    problem("invalid_verse_range", f"{code}.{chapter}.{raw[:32]}")
                    continue
                if start <= last_verse:
                    problem("duplicate_or_out_of_order_verse", f"{code}.{chapter}.{start}")
                for verse in range(start, stop + 1):
                    key = f"{code}.{chapter}.{verse}".encode("ascii")
                    key_hash.update(len(key).to_bytes(2, "big") + key)
                    source_key_count += 1
                    total_keys += 1
                last_verse = stop
                ref = f"{code}.{chapter}.{start}"
                if stop > start:
                    categories["authored_verse_ranges"] += 1
            if tag in NOTES:
                book_notes[tag] += 1
                notes_by_kind[tag] += 1
                marker_positions["notes_before_chapter" if chapter is None else
                                 "notes_in_verse_context"] += 1
                caller = node.get("caller")
                note_callers["automatic_or_unspecified" if caller in (None, "", "+", "-")
                             else "literal"] += 1
                if any(_name(child) in {"c", "v"} for child in node.iterdescendants()
                       if isinstance(child.tag, str)):
                    problem("note_contains_chapter_or_verse_marker", ref)
            if tag in HEADINGS:
                categories["headings"] += 1
                book_events["headings"] += 1
            if tag in PARAGRAPHS:
                categories["paragraphs"] += 1
                book_events["paragraphs"] += 1
            if tag in POETRY:
                categories["poetry"] += 1
                book_events["poetry"] += 1
            if tag in REFS:
                categories["reference_markers"] += 1
                book_events["reference_markers"] += 1
            if tag in {"ref", "x", "ex", "f", "fe", "ef", "note"} and node.get("tgt"):
                categories["elements_with_explicit_targets"] += 1
            if node.get("sfm"):
                categories["elements_with_source_style"] += 1
            # Structural event order fingerprint. Deliberately no Bible text,
            # note body, title text, literal caller, URL or reference content.
            payload = [code, chapter, last_verse, tag,
                       node.get("sfm") if tag not in NOTES else None,
                       node.get("level") if tag in HEADINGS | PARAGRAPHS | POETRY else None,
                       sorted(node.attrib.keys()), bool(node.get("tgt"))]
            b = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
            event_hash.update(len(b).to_bytes(4, "big") + b)
        books.append({"code": code, "chapter_marker_count": chapter_count,
                      "numbered_reference_count": source_key_count,
                      "structural_events": dict(sorted(book_events.items())),
                      "note_kinds": dict(sorted(book_notes.items()))})
    if not books or total_keys == 0:
        raise USFXAuditError("No original Bible book or numbered verse evidence")
    return {
        "schema_version": 1,
        "format": "USFX",
        "original_xml_sha256": sha256(xml).hexdigest(),
        "source_book_count": len(books),
        "all_original_books": books,
        "numbered_source_reference_count": total_keys,
        "ordered_source_reference_sha256": key_hash.hexdigest(),
        "ordered_source_structural_events_sha256": event_hash.hexdigest(),
        "source_element_counts": dict(sorted(elements.items())),
        "source_attribute_counts": dict(sorted(attrs.items())),
        "source_editorial_categories": dict(sorted(categories.items())),
        "source_note_types": dict(sorted(notes_by_kind.items())),
        "note_caller_categories": dict(sorted(note_callers.items())),
        "note_positions": dict(sorted(marker_positions.items())),
        "source_structural_issues": dict(sorted(issues.items())),
        "first_structural_findings_no_scripture": first_findings,
        "no_source_text_or_note_bodies_returned": True,
        "source_mutated": False,
        "official_usfx_schema_validated": False,
        "converted_to_osis": False,
        "publisher_edition_identity_verified": False,
        "compiled_verse_text_or_notes_verified": False,
        "publication_approved": False,
        "status": "blocked_source_structure_findings" if issues else
                  "source_native_structural_inventory_only",
    }
