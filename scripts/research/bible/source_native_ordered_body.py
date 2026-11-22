"""Compare already inventoried OSIS/native paragraph and poetry opening events.

The originating OSIS structural census and independent native markup
readback are performed by their own strict readers. This helper compares
only event *kinds and order*, never infers missing source boundaries,
authors' typography, or publication approval.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256

MAX_SAMPLES = 24


class OrderedStructureError(ValueError):
    """Ambiguous source/native event scope must not be accepted."""


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
        "explicit_prechapter_book_title_styles_separately_accounted_for":False,
        "original_to_native_book_title_match_not_verified_by_this_screen":True,
        "source_native_exact_word_positions_or_boundary_spans_verified":False,
        "source_native_whitespace_or_full_editorial_layout_verified":False,
        "no_scripture_or_native_milestone_identifiers_in_report":True,
        "originals_rewritten_or_published":False,
    }
