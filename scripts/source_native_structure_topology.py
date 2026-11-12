#!/usr/bin/env python3
"""Source/native p/q opening AND closing topology, using private word anchors.

A semantic event is (book, kind, open and close word/nonwhitespace offsets,
book/verse scope and opening order). We never infer source USFX/OSIS markup
identity from SWORD milestone tag names. The word and nonspace positions are
compared strictly; ambiguous same-position events or shifts across source
versification/intro records are explicitly flagged for review.

This reusable checker consumes independently produced private structural
evidence and returns counts, bounded reference IDs, hashes and safe categories,
NEVER original Bible text, note bodies, raw XML or generated sID/eID strings.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

MAX_BOOKS = 150
MAX_EVENTS = 150_000
MAX_WORDS = 250_000
MAX_SAMPLES = 12
BOOK = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]{0,14}$")
# SWORD native intro identifiers may be Book or Book.Chapter;
# numbered entries include Book.Chapter.Verse and source verse-zero records.
REFERENCE = re.compile(
    r"^[1-4]?[A-Za-z][A-Za-z0-9]{0,14}(?:\.0\.0|\.[1-9][0-9]*(?:\.(?:0|[1-9][0-9]*))?)?$")
SCOPES = {"numbered", "source_between_verses", "native_intro"}
STRUCTURE = {"p", "q"}


class StructureTopologyError(ValueError):
    """Unparseable or ambiguous source/native structural geometry."""


def _anchor(anchor: dict, book: str, word_count: int) -> tuple[int, int, str, str]:
    if not isinstance(anchor, dict):
        raise StructureTopologyError("Missing opening/closing source anchor")
    word, codepoint = (anchor.get("word_ordinal"),
                       anchor.get("nonwhitespace_codepoint_ordinal"))
    ref, scope = anchor.get("reference"), anchor.get("record_scope")
    if (type(word) is not int or not 0 <= word <= word_count
            or type(codepoint) is not int or not 0 <= codepoint <= 2_000_000
            or type(anchor.get("inside_word")) is not bool
            or anchor["inside_word"]
            or not isinstance(ref, str) or not REFERENCE.fullmatch(ref)
            or not (ref == book or ref.startswith(book + "."))
            or scope not in SCOPES):
        raise StructureTopologyError("Invalid private structural anchor")
    return word, codepoint, ref, scope


def _normalize(kind: str, private: dict) -> tuple[dict, Counter]:
    if not isinstance(private, dict) or len(private) > MAX_BOOKS:
        raise StructureTopologyError("Invalid source/native book scope")
    result, counts = {}, Counter()
    for book in sorted(private):
        if not isinstance(book, str) or not BOOK.fullmatch(book):
            raise StructureTopologyError("Unsafe OSIS book code")
        value = private[book]
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise StructureTopologyError("Malformed structural event inventory")
        words, events = value
        if (not isinstance(words, list) or len(words) > MAX_WORDS or
                any(not isinstance(w, str) for w in words) or
                not isinstance(events, list) or len(events) > MAX_EVENTS):
            raise StructureTopologyError("Unbounded private word/event scope")
        safe = []
        stack = []
        prev_open = None
        for idx, event in enumerate(events, 1):
            if not isinstance(event, dict) or event.get("kind") not in STRUCTURE:
                raise StructureTopologyError("Unrecognized original/native p/q event")
            which = event["kind"]
            counts[which + "_opens"] += 1
            close = event.get("close")
            if close is None:
                counts["unclosed_events"] += 1
                continue
            opened = _anchor(event.get("open"), book, len(words))
            closed = _anchor(close, book, len(words))
            counts[which + "_closes"] += 1
            start, end = opened[:2], closed[:2]
            if start > end:
                counts["reversed_open_close_boundaries"] += 1
            if prev_open is not None and start < prev_open:
                counts["openings_out_of_source_order"] += 1
            if prev_open is not None and start == prev_open:
                # Equal anchors cannot reliably distinguish two same-type
                # openings or an empty source element without source IDs.
                counts["same_boundary_opening_order_ambiguous"] += 1
            prev_open = start
            while stack and start >= stack[-1]:
                stack.pop()
            if stack and end > stack[-1]:
                counts["crossing_open_close_events"] += 1
            stack.append(end)
            safe.append({
                "kind":which, "original_event_order":idx,
                "open":opened, "close":closed,
            })
        result[book] = {
            "word_count":len(words),
            # These words are intentionally private. The output uses ONLY
            # the Boolean source/native parity, never the word sequences.
            "private_words":words,
            "events":safe,
        }
        counts["books"] += 1
    return result, counts


def _public_event_hash(books: dict) -> str:
    hashes = sha256()
    for book in sorted(books):
        rows = books[book]["events"]
        content = [book, len(rows), [
            [e["kind"],e["original_event_order"],e["open"],e["close"]]
            for e in rows]]
        data=json.dumps(content,sort_keys=True,separators=(",",":")).encode()
        hashes.update(len(data).to_bytes(4,"big")+data)
    return hashes.hexdigest()


def compare_structural_event_topology(original: dict, compiled: dict) -> dict:
    """Check exact semantic p/q start/end word/punctuation topology and order.

    Original/native milestone names need not be identical. Different
    representation scopes remain REVIEW_REQUIRED even if word boundaries
    match; source-relative layout is never silently certified.
    """
    src, sc = _normalize("source", original)
    nat, nc = _normalize("native", compiled)
    counter=Counter()
    for k,v in sc.items():
        counter["source_"+k]+=v
    for k,v in nc.items():
        counter["native_"+k]+=v
    findings=[]
    same_books=set(src)==set(nat) and bool(src)
    counter["source_only_books"]=len(set(src)-set(nat))
    counter["native_only_books"]=len(set(nat)-set(src))
    for book in sorted(set(src)&set(nat)):
        a,b=src[book],nat[book]
        counter["books_compared"] += 1
        if a["private_words"] != b["private_words"]:
            counter["source_native_word_stream_differences"] += 1
            if len(findings)<MAX_SAMPLES:
                findings.append({"book":book, "problem":"private_main_words_differ"})
            continue
        if len(a["events"]) != len(b["events"]):
            counter["source_native_event_count_differences"] += 1
            if len(findings)<MAX_SAMPLES:
                findings.append({"book":book, "problem":"p_q_open_close_count_differs",
                                 "original_events":len(a["events"]),
                                 "compiled_events":len(b["events"])})
            continue
        for idx,(source_event,native_event) in enumerate(
                zip(a["events"],b["events"]),1):
            if source_event["kind"] != native_event["kind"]:
                counter["event_kind_or_order_differences"] += 1
                problem="event_kind_or_opening_order_differs"
            elif (source_event["open"][:2] != native_event["open"][:2]):
                counter["opening_word_or_codepoint_position_differences"] += 1
                problem="opening_word_or_codepoint_boundary_shift"
            elif (source_event["close"][:2] != native_event["close"][:2]):
                counter["closing_word_or_codepoint_position_differences"] += 1
                problem="closing_word_or_codepoint_boundary_shift"
            else:
                counter["paired_open_close_word_and_codepoint_positions_equal"] += 1
                if (source_event["open"][2:] != native_event["open"][2:]
                        or source_event["close"][2:] != native_event["close"][2:]):
                    counter["record_or_verse_zero_scope_differences_for_review"] += 1
                    if len(findings)<MAX_SAMPLES:
                        findings.append({
                            "book":book,"one_based_event":idx,
                            "problem":"matched_positions_different_verse_record_scope",
                            "original_open_ref":source_event["open"][2],
                            "compiled_open_ref":native_event["open"][2],
                            "original_close_ref":source_event["close"][2],
                            "compiled_close_ref":native_event["close"][2],
                        })
                continue
            if len(findings)<MAX_SAMPLES:
                findings.append({"book":book,"one_based_event":idx,
                                 "kind":source_event["kind"],"problem":problem,
                                 "original_open_ref":source_event["open"][2],
                                 "compiled_open_ref":native_event["open"][2],
                                 "original_close_ref":source_event["close"][2],
                                 "compiled_close_ref":native_event["close"][2]})
    problems=(
        "source_only_books","native_only_books",
        "source_native_word_stream_differences","source_native_event_count_differences",
        "event_kind_or_order_differences",
        "opening_word_or_codepoint_position_differences",
        "closing_word_or_codepoint_position_differences",
        "source_unclosed_events","native_unclosed_events",
        "source_reversed_open_close_boundaries",
        "native_reversed_open_close_boundaries",
        "source_openings_out_of_source_order",
        "native_openings_out_of_source_order",
        "source_crossing_open_close_events",
        "native_crossing_open_close_events",
    )
    for key in problems + ("source_same_boundary_opening_order_ambiguous",
                           "native_same_boundary_opening_order_ambiguous",
                           "record_or_verse_zero_scope_differences_for_review"):
        counter.setdefault(key,0)
    proven_different=bool(any(counter[k] for k in problems))
    ambiguity=bool(
        counter["source_same_boundary_opening_order_ambiguous"]
        or counter["native_same_boundary_opening_order_ambiguous"]
        or counter["record_or_verse_zero_scope_differences_for_review"])
    same_positions=bool(same_books and not proven_different)
    return {
        "schema_version":1,
        "status": (
            "source_native_structural_topology_differs" if proven_different
            else "source_native_structural_topology_positions_equal_scope_review"
            if ambiguity else
            "source_native_structural_topology_positions_equal_not_layout_certificate"
            if same_positions else "blocked_structural_topology_missing_book_evidence"),
        "independently_observed_original_and_compiled_events":True,
        "all_source_native_p_q_open_close_event_topology_match":same_positions,
        "open_and_close_word_and_punctuation_relative_positions_compared":True,
        "source_native_exact_record_scope_verified":bool(
            same_positions and not counter[
                "record_or_verse_zero_scope_differences_for_review"]),
        "same_boundary_event_order_unambiguous":not bool(
            counter["source_same_boundary_opening_order_ambiguous"] or
            counter["native_same_boundary_opening_order_ambiguous"]),
        "source_original_style_and_linebreak_fidelity_verified":False,
        "editorial_or_publication_approved":False,
        "source_and_module_unchanged":True,
        "first_structural_event_findings_reference_only":findings,
        "source_event_fingerprint_sha256":_public_event_hash(src),
        "compiled_event_fingerprint_sha256":_public_event_hash(nat),
        "source_native_event_count_and_topology_categories":dict(sorted(counter.items())),
        "no_scripture_note_body_raw_ids_or_native_xml_exposed":True,
    }
