#!/usr/bin/env python3
"""Verify the ordered *kind* of authored USFX vs native SWORD body openings.

This is deliberately narrower than source↔compiled exact layout equivalence:
a matching p/q order and count does NOT prove matching word positions,
start/end spans, source styles, poetry line breaks, or typography.
No Scripture/title/note content or raw native XML is returned.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from lxml import etree

from source_usfx_structure import audit_source_usfx
from source_native_paragraph_counts import (
    IGNORE_CONTAINER, classify_prefatory_p_sfm,
)

MAX_SAMPLES = 24


class OrderedStructureError(ValueError):
    """Ambiguous source, mapping or compiled event scope cannot be accepted."""


def _within_annotation(node, book):
    parent = node.getparent()
    while parent is not None and parent is not book:
        if isinstance(parent.tag, str) and etree.QName(parent).localname in IGNORE_CONTAINER:
            return True
        parent = parent.getparent()
    return False


def original_body_opening_sequences(xml: bytes, mapping: list[tuple[str, str]]):
    """Private per-book (p/q, source-prior-ref) events, source metadata only."""
    proof = audit_source_usfx(xml)
    if proof["source_structural_issues"]:
        raise OrderedStructureError("Unresolved original source structural anomalies")
    pairs = dict(mapping)
    if (not mapping or len(pairs) != len(mapping)
            or len(set(pairs.values())) != len(mapping)):
        raise OrderedStructureError("Ambiguous original/native book crosswalk")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise OrderedStructureError("Original source cannot be parsed for order") from exc

    private = {}
    counts = Counter()
    seen = set()
    for book in root.iter("book"):
        authorial = book.get("id")
        if not authorial or authorial in seen:
            raise OrderedStructureError("Ambiguous original book identity")
        seen.add(authorial)
        if authorial not in pairs:
            raise OrderedStructureError("Unmapped original authorial book")
        native = pairs[authorial]
        events = []
        chapter = None
        last_verse = None
        for node in book.iter():
            if not isinstance(node.tag, str):
                continue
            tag = etree.QName(node).localname
            if tag == "c":
                chapter = node.get("id")
                last_verse = None
                continue
            if tag == "v":
                last_verse = node.get("id")
                continue
            if tag not in {"p", "q"}:
                continue
            if _within_annotation(node, book):
                counts["source_p_or_q_nested_in_notes_excluded"] += 1
                continue
            if tag == "p" and chapter is None:
                family, _code = classify_prefatory_p_sfm(node.get("sfm"))
                if family == "book_title_style":
                    # Independently accounted for by the authorial prefatory
                    # SFM/title+native book title audit, not discarded.
                    counts["authored_pre_chapter_book_titles_separately_verified"] += 1
                    continue
                counts["non_title_p_before_first_chapter_requires_review"] += 1
            if tag == "q" and chapter is None:
                counts["source_poetry_before_first_chapter_requires_review"] += 1
            ref = (f"{native}.{chapter}.{last_verse}"
                   if chapter is not None and last_verse is not None
                   else f"{native}.{chapter or 0}.0")
            events.append((tag, ref))
            counts[f"source_body_{tag}_openings"] += 1
        private[native] = events

    if seen != set(pairs) or len(seen) != proof["source_book_count"]:
        raise OrderedStructureError("Book inventory differs from the original source")
    return private, dict(sorted(counts.items()))


def compare_ordered_body_openings(source_by_book, native_by_book, source_counts):
    """Compare p vs q opening sequences, not verse or exact word anchors.

    Both arguments contain only private structural event labels/reference IDs.
    Native source/generated IDs and all Bible text remain unobservable.
    """
    source_books = set(source_by_book)
    extra = set(native_by_book) - source_books
    if extra:
        raise OrderedStructureError("Compiled semantic openings in unmapped native book")
    counts = Counter(source_counts)
    examples = []
    src_summary = sha256()
    native_summary = sha256()

    for book in sorted(source_by_book):
        source_events = list(source_by_book[book])
        compiled_events = list(native_by_book.get(book, ()))
        src_types = "".join(e[0] for e in source_events)
        compiled_types = "".join(e[0] for e in compiled_events)
        for items, digest in ((src_types, src_summary), (compiled_types, native_summary)):
            payload = f"{book}:{items}".encode("ascii")
            digest.update(len(payload).to_bytes(4, "big") + payload)
        counts["books_checked"] += 1
        counts["authorial_body_start_events"] += len(src_types)
        counts["native_body_start_events"] += len(compiled_types)
        counts["native_paragraph_starts"] += compiled_types.count("p")
        counts["native_poetry_line_starts"] += compiled_types.count("q")
        if src_types == compiled_types:
            counts["books_with_exact_body_opening_kind_order"] += 1
            continue
        counts["books_with_body_opening_kind_difference"] += 1
        if len(src_types) != len(compiled_types):
            counts["books_with_body_opening_count_difference"] += 1
        else:
            counts["books_with_equal_count_but_reordered_kinds"] += 1
        if len(examples) < MAX_SAMPLES:
            position = next(
                (i for i in range(min(len(src_types),len(compiled_types)))
                 if src_types[i] != compiled_types[i]),
                min(len(src_types),len(compiled_types)),
            )
            orig = (source_events[position] if position < len(source_events) else None)
            native = (compiled_events[position] if position < len(compiled_events) else None)
            examples.append({
                "book":book,
                "first_different_one_based_event_index":position+1,
                "source_kind":orig[0] if orig else "no_more_source_events",
                "native_kind":native[0] if native else "no_more_native_events",
                "original_previous_reference_id":orig[1] if orig else None,
                "compiled_marker_reference_id":native[1] if native else None,
                "source_event_count":len(source_events),
                "native_event_count":len(compiled_events),
            })
    counts.setdefault("books_with_body_opening_kind_difference",0)
    counts.setdefault("books_with_body_opening_count_difference",0)
    counts.setdefault("books_with_equal_count_but_reordered_kinds",0)
    return {
        "schema_version": 1,
        "source_native_body_opening_kind_counts":dict(sorted(counts.items())),
        "source_event_kind_order_sha256":src_summary.hexdigest(),
        "native_event_kind_order_sha256":native_summary.hexdigest(),
        "same_order_and_kind_in_every_mapped_book": (
            counts["books_checked"] == len(source_books)
            and counts["books_with_body_opening_kind_difference"] == 0
        ),
        "first_mismatch_book_references_no_scripture":examples,
        "only_source_authorial_mt_book_titles_excluded_from_body_sequence":True,
        "source_title_elements_verified_in_separate_gate_not_here":False,
        "source_native_exact_word_positions_or_boundary_spans_verified":False,
        "source_native_whitespace_or_full_editorial_layout_verified":False,
        "no_scripture_or_native_milestone_identifiers_in_report":True,
        "originals_rewritten_or_published":False,
    }
