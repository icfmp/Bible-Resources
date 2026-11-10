#!/usr/bin/env python3
"""Read-only triage of source USFX vs stock SWORD verse/intro record anchors.

This classifies *where* a previously word-aligned p/q opening or closing was
serialized. A previous-verse USFX marker and next-verse SWORD milestone
might share a legitimate interverse lexical boundary; that is only a
CANDIDATE encoding explanation, not an editorial equivalence certificate.

Only original/native book/verse IDs, integer word ordinals and allowlisted
finding categories may leave this module. No Bible, notes, raw XML or sIDs.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json

from stable_sword_refs import KEY
from sword_native_inventory import INTRO
from source_native_word_boundaries import WORD

MAX_SAMPLES = 32
MAX_PER_KIND = 3


class ScopeTriageError(ValueError):
    """Cannot safely classify original/native structural record positions."""


def _safe_ref(reference: str, book: str) -> bool:
    return (isinstance(reference, str) and reference.split(".", 1)[0] == book
            and (KEY.fullmatch(reference) is not None
                 or INTRO.fullmatch(reference) is not None))


def _verses_from_source(source_verses: dict, book: str, original_words: list[str]):
    """Original reference order, with independent lexical book/verse proof."""
    rows = []
    words = []
    length = 0
    prev = (-1, -1)
    for ref, text in source_verses.items():
        if ref.split(".", 1)[0] != book:
            continue
        match = KEY.fullmatch(ref)
        if match is None or not isinstance(text, str):
            raise ScopeTriageError("Untrusted original numbered verse reference")
        key = (int(match.group(2)), int(match.group(3)))
        if key <= prev:
            raise ScopeTriageError("Original verse list is not in authored order")
        prev = key
        tokens = WORD.findall(text)
        rows.append((ref, length, length + len(tokens), key[0], key[1]))
        words.extend(tokens)
        length += len(tokens)
    if not rows or words != original_words:
        raise ScopeTriageError("Source verse words differ from original book word stream")
    return rows


def _relative_coordinate(rows, ordinal):
    """Return a bounded set of legitimate source verse/intro record slots.

    Ambiguous zero-word verses and intervening zero-word verses deliberately
    prevent any automatic adjacent-marker interpretation.
    """
    if not isinstance(ordinal, int) or ordinal < 0 or ordinal > rows[-1][2]:
        raise ScopeTriageError("Invalid original book lexical word position")
    interior = [ref for ref, start, end, _ch, _v in rows
                if start < ordinal < end]
    if len(interior) > 1:
        raise ScopeTriageError("Overlapping original verse lexical intervals")
    if interior:
        return {"type": "inside_verse", "allowed": frozenset(interior)}

    adjacent = [(ref, start, end, ch, verse) for ref, start, end, ch, verse in rows
                if start == ordinal or end == ordinal]
    if not adjacent:
        raise ScopeTriageError("Word ordinal does not occur in authored verse text")
    # If an empty source verse participates in this position, the record
    # serialization is not proven by a single preceding/following pair.
    if len(adjacent) > 2 or any(start == end for _, start, end, _, _ in adjacent):
        return {"type": "ambiguous_empty_or_multiple_verses",
                "allowed": frozenset(ref for ref, *_ in adjacent)}
    allowed = {ref for ref, *_ in adjacent}
    first_by_chapter = {}
    for ref, start, _end, ch, _v in rows:
        first_by_chapter.setdefault(ch, (ref, start))
    for ch, (first_ref, first_start) in first_by_chapter.items():
        if first_start == ordinal:
            prefix = first_ref.rsplit(".", 2)[0]
            allowed.update((f"{prefix}.{ch}", f"{prefix}.{ch}.0"))
    if ordinal == 0:
        prefix = rows[0][0].split(".", 1)[0]
        allowed.update((prefix, f"{prefix}.0.0"))
    return {"type": "authored_verse_boundary", "allowed": frozenset(allowed)}


def _type_of_ref(ref):
    if KEY.fullmatch(ref) is not None:
        return "numbered"
    if INTRO.fullmatch(ref) is not None:
        return "intro"
    raise ScopeTriageError("Untrusted structural event record ID")


def _classify(source_point, native_point, coordinate, rows):
    src = source_point["reference"]
    native = native_point["reference"]
    src_scope = source_point["record_scope"]
    native_scope = native_point["record_scope"]
    if src == native and src_scope == native_scope:
        return "identical_record_and_scope"
    if src == native:
        if coordinate["type"] != "authored_verse_boundary":
            return "same_ref_scope_tag_diff_outside_clear_verse_boundary_review"
        return "same_record_different_source_native_scope_tag_candidate"

    if coordinate["type"] == "inside_verse":
        return "different_record_inside_authored_verse_review"
    if coordinate["type"] == "ambiguous_empty_or_multiple_verses":
        return "ambiguous_zero_word_verse_or_multiple_boundary_review"
    if src not in coordinate["allowed"] or native not in coordinate["allowed"]:
        return "record_outside_immediate_source_boundary_review"

    src_type, native_type = _type_of_ref(src), _type_of_ref(native)
    if src_type == "intro" or native_type == "intro":
        if src_type == native_type:
            return "source_native_verse_zero_intro_alias_candidate"
        return "chapter_or_book_intro_vs_numbered_boundary_candidate"

    # Both are independently attested numbered entries sharing precisely
    # this authored word boundary. Orientation is a diagnostic only.
    lookup = {ref: index for index, (ref, *_parts) in enumerate(rows)}
    if lookup[src] < lookup[native]:
        return "authorial_previous_native_next_numbered_verse_candidate"
    if lookup[src] > lookup[native]:
        return "authorial_next_native_previous_numbered_verse_candidate"
    raise ScopeTriageError("Distinct source/native references have same ordinal")


REVIEW_TYPES = frozenset({
    "same_ref_scope_tag_diff_outside_clear_verse_boundary_review",
    "different_record_inside_authored_verse_review",
    "ambiguous_zero_word_verse_or_multiple_boundary_review",
    "record_outside_immediate_source_boundary_review",
})


def compare_body_record_scopes(source, native, source_verses: dict):
    """Require independently identical full-book word sequences and p/q spans.

    Both source/native values are *private* results of the separate original
    USFX and native SWORD scanners. Only bounded source/native canonical
    reference identifiers and enum categories escape.
    """
    if not source or set(source) != set(native):
        raise ScopeTriageError("Unmapped original/native book event coverage")
    counters = Counter()
    fingerprint = sha256()
    samples_by_kind = {}
    for book in sorted(source):
        source_words, original_events = source[book]
        native_words, native_events = native[book]
        if source_words != native_words or len(original_events) != len(native_events):
            raise ScopeTriageError("Source and compiled book word/event streams differ")
        if not _safe_ref(f"{book}.1.1", book):
            raise ScopeTriageError("Untrusted mapped canonical book")
        rows = _verses_from_source(source_verses, book, source_words)
        counters["books_checked"] += 1
        for position, (src_event, cmp_event) in enumerate(
            zip(original_events, native_events), 1
        ):
            if src_event["kind"] != cmp_event["kind"]:
                raise ScopeTriageError("Source/native event kinds are not ordered identically")
            counters["events_compared"] += 1
            any_shift = False
            for endpoint in ("open", "close"):
                left = src_event.get(endpoint)
                right = cmp_event.get(endpoint)
                if not isinstance(left, dict) or not isinstance(right, dict):
                    raise ScopeTriageError("Missing original/native event endpoint")
                if (left["inside_word"] or right["inside_word"] or
                        left["word_ordinal"] != right["word_ordinal"]):
                    raise ScopeTriageError("Word boundary mismatch blocks scope triage")
                if not _safe_ref(left["reference"], book) or not _safe_ref(right["reference"], book):
                    raise ScopeTriageError("Untrusted event source/native record ID")
                coord = _relative_coordinate(rows, left["word_ordinal"])
                status = _classify(left, right, coord, rows)
                counters[f"{endpoint}_class_{status}"] += 1
                if status != "identical_record_and_scope":
                    any_shift = True
                    counters["different_record_or_scope_endpoints"] += 1
                if status in REVIEW_TYPES:
                    counters["unexplained_or_ambiguous_endpoints_needing_review"] += 1
                if status != "identical_record_and_scope":
                    payload = json.dumps(
                        [book, position, endpoint, status, left["word_ordinal"],
                         left["reference"], right["reference"]],
                        separators=(",", ":"), ensure_ascii=True).encode()
                    fingerprint.update(len(payload).to_bytes(4, "big") + payload)
                    if (sum(len(v) for v in samples_by_kind.values()) < MAX_SAMPLES
                            and len(samples_by_kind.setdefault(status, [])) < MAX_PER_KIND):
                        samples_by_kind[status].append({
                            "book":book, "one_based_event_index":position,
                            "endpoint":endpoint, "structure_kind":src_event["kind"],
                            "source_reference":left["reference"],
                            "native_reference":right["reference"],
                            "word_ordinal":left["word_ordinal"],
                            "finding":status,
                        })
            if any_shift:
                counters["events_with_different_record_or_scope"] += 1
    counters.setdefault("unexplained_or_ambiguous_endpoints_needing_review", 0)
    counters.setdefault("events_with_different_record_or_scope", 0)
    samples = [row for kind in sorted(samples_by_kind)
               for row in samples_by_kind[kind]][:MAX_SAMPLES]
    return {
        "schema_version":1,
        "status": ("record_scope_candidate_classification_requires_editorial_review"
                   if not counters["unexplained_or_ambiguous_endpoints_needing_review"]
                   else "some_record_scope_shifts_remain_unclassified"),
        "source_native_scope_counts":dict(sorted(counters.items())),
        "first_scope_difference_references_only":samples,
        "scope_difference_fingerprint_sha256":fingerprint.hexdigest(),
        "every_event_endpoint_classified_at_source_word_position":True,
        "unexplained_or_ambiguous_endpoints":counters[
            "unexplained_or_ambiguous_endpoints_needing_review"],
        "candidate_compiler_record_shifts_are_not_editorial_equivalence":True,
        "unchanged_punctuation_linebreak_and_whitespace_positions_unverified":True,
        "source_text_notes_and_native_milestone_ids_not_exposed":True,
        "editorial_or_publication_approved":False,
    }
