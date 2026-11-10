#!/usr/bin/env python3
"""Read-only authorial USFX to actual stock SWORD p/q boundary-word audit.

A *word boundary* means the ordinal of the preceding complete Scripture
word in its book (and a flag if inside a word). It is NOT byte position,
punctuation location, linebreak fidelity, or proof of all editorial styles.
We never copy any Scripture, note, title, or native sID into public receipts.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter
from hashlib import sha256
import json
import re

from lxml import etree

from native_milestone_pair_audit import _strict_root, NativeMilestoneAuditError, TOP
from source_native_paragraph_counts import classify_prefatory_p_sfm
from source_usfx_structure import audit_source_usfx
from stable_sword_refs import KEY
from sword_native_inventory import INTRO

WORD = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)
SOURCE_NOT_MAIN = frozenset({
    "f", "fe", "x", "note", "ef", "ex", "s", "s1", "s2", "s3", "s4",
    "ms", "ms1", "ms2", "mt", "mt1", "mt2", "mr", "d", "cl",
    "r", "rem", "vp", "va", "cp", "ca",
})
MAX_SAMPLES = 24
MAX_WORDS_PER_BOOK = 150_000
MAX_EVENTS_PER_BOOK = 100_000
MAX_SOURCE_BYTES = 128 * 1024 * 1024


class BoundaryAuditError(ValueError):
    """Source/native correspondence cannot be safely proven."""


def _parsed_original(xml: bytes):
    if not 0 < len(xml) < MAX_SOURCE_BYTES or b"<!DOCTYPE" in xml.upper():
        raise BoundaryAuditError("Original source XML is empty, unsafe or oversized")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise BoundaryAuditError("Original source XML is invalid") from exc
    if root.tag != "usfx" or any(isinstance(x, etree._Entity) for x in root.iter()):
        raise BoundaryAuditError("Original source root/entities are unsupported")
    return root


class _BookWords:
    def __init__(self):
        self.fragments = []
        self.length = 0

    def append(self, text):
        if text:
            self.fragments.append(text)
            self.length += len(text)

    def resolve(self, entries):
        text = "".join(self.fragments)
        spans = [(m.start(), m.end()) for m in WORD.finditer(text)]
        if len(spans) > MAX_WORDS_PER_BOOK:
            raise BoundaryAuditError("Word stream exceeds per-book safety limit")
        ends = [end for _, end in spans]
        result = []
        for event in entries:
            def boundary(raw):
                pos = raw["char_offset"]
                ordinal = bisect_right(ends, pos)
                inside = bool(ordinal < len(spans)
                              and spans[ordinal][0] < pos < spans[ordinal][1])
                return {"word_ordinal":ordinal, "inside_word":inside,
                        "reference":raw["ref"], "record_scope":raw["scope"]}
            result.append({"kind":event["kind"],
                           "open":boundary(event["open"]),
                           "close":boundary(event["close"]) if event.get("close") else None})
        return WORD.findall(text), result


def original_usfx_body_boundaries(xml: bytes, mapping, source_verses):
    """Independent authorial XML start/end positions with verse-text parity."""
    audit = audit_source_usfx(xml)
    if audit["source_structural_issues"]:
        raise BoundaryAuditError("Original source structural anomalies")
    crosswalk = dict(mapping)
    if (not crosswalk or len(crosswalk) != len(mapping)
            or len(set(crosswalk.values())) != len(mapping)):
        raise BoundaryAuditError("Ambiguous authorial book mapping")
    root = _parsed_original(xml)
    books = {}
    counts = Counter()
    seen = set()

    for book in root.iter("book"):
        src_id = book.get("id")
        if src_id in seen or src_id not in crosswalk:
            raise BoundaryAuditError("Duplicated or unmapped original book")
        seen.add(src_id)
        target = crosswalk[src_id]
        words = _BookWords()
        events = []
        chapter = None
        current = None
        last_ref = f"{target}.0.0"
        verse_chunks = {}

        def append(fragment):
            if current is not None and fragment:
                words.append(fragment)
                verse_chunks[current].append(fragment)

        def ref():
            return last_ref

        def anchor():
            return {"char_offset":words.length,"ref":ref(),
                    "scope":"numbered" if current is not None else "source_between_verses"}

        def visit(node, depth=0):
            nonlocal chapter, current, last_ref
            if depth > 256:
                raise BoundaryAuditError("Excessive source XML nesting")
            if not isinstance(node.tag, str):
                return
            tag = etree.QName(node).localname
            style = node.get("sfm", "")
            if (tag in SOURCE_NOT_MAIN or (tag == "p" and style == "sp")
                    or (tag == "p" and chapter is None
                        and classify_prefatory_p_sfm(style)[0] == "book_title_style")):
                if any(isinstance(c.tag, str) and etree.QName(c).localname in {"c","v"}
                       for c in node.iterdescendants()):
                    raise BoundaryAuditError("Excluded source heading contains verse markers")
                if tag == "p" and chapter is None:
                    counts["source_book_titles_accounted_elsewhere"] += 1
                return
            if tag == "c":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0:
                    raise BoundaryAuditError("Invalid original chapter marker")
                chapter = int(value)
                current = None
                last_ref = f"{target}.{chapter}.0"
            elif tag == "v":
                value = node.get("id", "")
                if chapter is None or not value.isdecimal() or int(value) <= 0:
                    raise BoundaryAuditError("Invalid original verse marker")
                current = f"{target}.{chapter}.{int(value)}"
                if current in verse_chunks:
                    raise BoundaryAuditError("Repeated authorial verse marker")
                verse_chunks[current] = []
                last_ref = current
                words.append("\n")  # disallow accidental joins across verses
            elif tag == "ve":
                current = None
                return

            entry = None
            if tag in {"p","q"}:
                if len(events) >= MAX_EVENTS_PER_BOOK:
                    raise BoundaryAuditError("Too many authorial structural events")
                entry = {"kind":tag,"open":anchor()}
                events.append(entry)
                counts[f"source_{tag}_opens"] += 1

            if tag not in {"c","v"}:
                append(node.text)
            for child in node:
                visit(child, depth+1)
                append(child.tail)
            if entry is not None:
                entry["close"] = anchor()
                counts[f"source_{tag}_closes"] += 1

        visit(book)
        if set(verse_chunks) != {v for v in source_verses if v.startswith(target + ".")}:
            raise BoundaryAuditError("Source boundary audit verse scope differs from full text audit")
        if any("".join(parts) != source_verses[key] for key,parts in verse_chunks.items()):
            raise BoundaryAuditError("Source boundary reader does not reproduce actual verse text")
        books[target] = words.resolve(events)
    if seen != set(crosswalk) or len(seen) != audit["source_book_count"]:
        raise BoundaryAuditError("Incomplete authorial book scope")
    return books, dict(sorted(counts.items()))


class NativeBodyBoundaries:
    """Private real SWORD native body events and per-book lexical positions."""

    def __init__(self):
        self.books = {}
        self.active = {}
        self.counts = Counter()
        self.seen = set()

    def observe(self, record_kind, ref, raw):
        if record_kind not in {"I","K","U"}:
            raise BoundaryAuditError("Unknown native record kind")
        if record_kind == "U":
            if not TOP.fullmatch(ref) or (record_kind,ref) in self.seen:
                raise BoundaryAuditError("Untrusted or duplicated native TOP reference")
            self.seen.add((record_kind,ref))
            self.counts["unaddressable_native_top_records"] += 1
            # TOP records are part of the original SWORD iterator. They
            # cannot be silently dropped: independently inspect whether
            # they actually contain body p/q openings, closings or containers.
            # A TOP holding only unrelated root/intro metadata is not a
            # missing Scripture body boundary.
            try:
                top = _strict_root(raw)
            except NativeMilestoneAuditError as exc:
                raise BoundaryAuditError("Unparseable original TOP fragment") from exc

            def walk_top(node):
                if not isinstance(node.tag,str):
                    return
                tag = etree.QName(node).localname
                if tag in {"title","note"}:
                    return
                is_body=(tag=="l" or
                         (tag=="div" and node.get("type")=="x-p"))
                if is_body:
                    self.counts["unaddressable_top_body_event_occurrences"] += 1
                for child in node:
                    walk_top(child)
            walk_top(top)
            self.counts["parseable_native_top_records"] += 1
            return
        if ((record_kind == "I" and not INTRO.fullmatch(ref))
                or (record_kind == "K" and not KEY.fullmatch(ref))
                or (record_kind,ref) in self.seen):
            raise BoundaryAuditError("Untrusted or duplicated native reference")
        self.seen.add((record_kind,ref))
        book = ref.split(".",1)[0]
        store = self.books.setdefault(book, {"words":_BookWords(),"events":[]})
        words = store["words"]
        if record_kind == "K":
            words.append("\n")
        try:
            root = _strict_root(raw)
        except NativeMilestoneAuditError as exc:
            raise BoundaryAuditError("Native fragment is not safely parsed") from exc

        def anchor():
            return {"char_offset":words.length,"ref":ref,
                    "scope":"native_intro" if record_kind=="I" else "numbered"}

        def walk(node, depth=0):
            if depth > 256:
                raise BoundaryAuditError("Excessive native XML nesting")
            if not isinstance(node.tag, str):
                return
            tag = etree.QName(node).localname
            if tag in {"note","title"}:
                return
            kind = ("p" if tag=="div" and node.get("type")=="x-p" else
                    "q" if tag=="l" else None)
            if kind is not None:
                sid,eid = node.get("sID"), node.get("eID")
                if sid is not None and eid is not None:
                    raise BoundaryAuditError("Native marker contains opening and closing ID")
                if sid is not None:
                    key = (book,tag,sid)
                    if key in self.active:
                        raise BoundaryAuditError("Repeated active native opening")
                    if len(store["events"]) >= MAX_EVENTS_PER_BOOK:
                        raise BoundaryAuditError("Too many native opening events")
                    item = {"kind":kind,"open":anchor()}
                    store["events"].append(item)
                    self.active[key] = item
                    self.counts[f"native_{kind}_opens"] += 1
                elif eid is not None:
                    key=(book,tag,eid)
                    item=self.active.pop(key,None)
                    if item is None:
                        raise BoundaryAuditError("Orphan native structural closing")
                    item["close"] = anchor()
                    self.counts[f"native_{kind}_closes"] += 1
                else:
                    self.counts["native_body_container_without_milestone"] += 1
            if node.text and record_kind=="K":
                words.append(node.text)
            for child in node:
                walk(child,depth+1)
                if child.tail and record_kind=="K":
                    words.append(child.tail)

        walk(root)

    def finish(self):
        if self.active:
            raise BoundaryAuditError("Native structural opening without ending")
        books={}
        for book,store in self.books.items():
            books[book] = store["words"].resolve(store["events"])
        return books, dict(sorted(self.counts.items()))


def compare_body_boundary_word_positions(source, native, original_counts, native_counts):
    """Compare matching source/native structural events with text-only ordinals."""
    counts=Counter(original_counts)
    counts.update(native_counts)
    samples=[]
    src_digest=sha256()
    native_digest=sha256()
    if set(source) != set(native):
        missing_source=sorted(set(native)-set(source))
        missing_native=sorted(set(source)-set(native))
    else:
        missing_source=missing_native=[]
    for book in sorted(set(source)&set(native)):
        source_words, src_events = source[book]
        native_words, nat_events = native[book]
        counts["books_compared"] += 1
        for tag,words,events,digest in (
            ("source",source_words,src_events,src_digest),
            ("native",native_words,nat_events,native_digest)
        ):
            canonical = [(e["kind"],e["open"]["word_ordinal"],
                          e["close"]["word_ordinal"] if e["close"] else None)
                         for e in events]
            payload = json.dumps([book,canonical],separators=(",",":"),ensure_ascii=True).encode()
            digest.update(len(payload).to_bytes(4,"big")+payload)
            counts[f"{tag}_words"] += len(words)
            counts[f"{tag}_events"] += len(events)
        if source_words != native_words:
            counts["books_with_different_original_and_compiled_word_sequences"] += 1
            if len(samples)<MAX_SAMPLES:
                samples.append({"book":book,"problem":"source_native_words_differ"})
            continue
        if len(src_events)!=len(nat_events):
            counts["books_with_mismatched_event_counts"] += 1
            if len(samples)<MAX_SAMPLES:
                samples.append({"book":book,"problem":"event_counts_differ",
                                "source_count":len(src_events),"native_count":len(nat_events)})
            continue
        different=False
        for index,(a,b) in enumerate(zip(src_events,nat_events),1):
            if a["kind"]!=b["kind"]:
                counts["event_kind_mismatches"] += 1
                problem="event_kind_differs"
            elif a["close"] is None or b["close"] is None:
                counts["unpaired_or_missing_event_end"] += 1
                problem="missing_end_boundary"
            elif (a["open"]["inside_word"] or a["close"]["inside_word"]
                  or b["open"]["inside_word"] or b["close"]["inside_word"]):
                counts["events_with_boundary_inside_lexical_word"] += 1
                problem="word_split_by_structural_boundary"
            elif a["open"]["word_ordinal"]!=b["open"]["word_ordinal"]:
                counts["opening_word_position_mismatches"] += 1
                problem="different_open_word_ordinal"
            elif a["close"]["word_ordinal"]!=b["close"]["word_ordinal"]:
                counts["closing_word_position_mismatches"] += 1
                problem="different_close_word_ordinal"
            else:
                counts["same_kind_event_word_start_and_end_positions_match"] += 1
                if (a["open"]["reference"] != b["open"]["reference"]
                        or a["close"]["reference"] != b["close"]["reference"]
                        or a["open"]["record_scope"] != b["open"]["record_scope"]
                        or a["close"]["record_scope"] != b["close"]["record_scope"]):
                    # Moving a boundary across a verse or into chapter-zero
                    # can be a compilation representation difference.
                    # Preserve that fact for editorial examination rather
                    # than calling it an exact source location match.
                    counts["same_word_ordinals_but_original_native_record_scope_differs"] += 1
                    if len(samples) < MAX_SAMPLES:
                        samples.append({
                            "book":book, "one_based_event":index,
                            "kind":a["kind"],
                            "problem":"matching_word_ordinals_different_record_scope",
                            "source_open_ref":a["open"]["reference"],
                            "native_open_ref":b["open"]["reference"],
                            "source_close_ref":a["close"]["reference"],
                            "native_close_ref":b["close"]["reference"],
                        })
                continue
            different=True
            if len(samples)<MAX_SAMPLES:
                samples.append({"book":book,"one_based_event":index,
                                "kind":a["kind"],
                                "problem":problem,
                                "source_open_word":a["open"]["word_ordinal"],
                                "native_open_word":b["open"]["word_ordinal"],
                                "source_close_word":a["close"]["word_ordinal"] if a["close"] else None,
                                "native_close_word":b["close"]["word_ordinal"] if b["close"] else None,
                                "source_ref":a["open"]["reference"],
                                "native_ref":b["open"]["reference"]})
        if different:
            counts["books_with_word_boundary_mismatches"] += 1
        else:
            counts["books_with_matching_word_boundaries"] += 1
    counts["native_books_without_source_mapping"] = len(missing_source)
    counts["source_books_without_native_counterpart"] = len(missing_native)
    for field in ("opening_word_position_mismatches","closing_word_position_mismatches",
                  "event_kind_mismatches","events_with_boundary_inside_lexical_word",
                  "unpaired_or_missing_event_end","books_with_word_boundary_mismatches",
                  "books_with_mismatched_event_counts",
                  "books_with_different_original_and_compiled_word_sequences"):
        counts.setdefault(field,0)
    complete=(len(source)>0 and set(source)==set(native)
              and not counts["unaddressable_top_body_event_occurrences"]
              and (counts["parseable_native_top_records"] ==
                   counts["unaddressable_native_top_records"])
              and not counts["native_body_container_without_milestone"]
              and not any(counts[k] for k in (
                  "opening_word_position_mismatches","closing_word_position_mismatches",
                  "event_kind_mismatches","events_with_boundary_inside_lexical_word",
                  "unpaired_or_missing_event_end","books_with_word_boundary_mismatches",
                  "books_with_mismatched_event_counts",
                  "books_with_different_original_and_compiled_word_sequences")))
    return {
        "schema_version":1,
        "status": ("all_p_q_word_start_end_positions_match_diagnostic_only"
                   if complete else "source_native_word_boundary_difference_or_unknown"),
        "original_vs_compiled_event_word_position_counts":dict(sorted(counts.items())),
        "first_source_native_boundary_findings_reference_ordinals_only":samples,
        "source_word_boundary_event_sequence_sha256":src_digest.hexdigest(),
        "native_word_boundary_event_sequence_sha256":native_digest.hexdigest(),
        "all_mapped_book_p_q_start_end_word_ordinals_match":complete,
        "word_position_only_not_character_punctuation_or_whitespace_fidelity":True,
        "identical_book_word_ordinals_not_exact_verse_record_or_markup_placement":True,
        "source_native_verse_zero_intro_representation_review_still_required":True,
        "source_native_original_style_and_linebreak_fidelity_unverified":True,
        "unaddressable_native_top_body_markup_or_unmilestoned_blocks_cannot_pass":True,
        "top_records_only_screened_for_p_q_body_markup_not_all_editorial_content":True,
        "no_source_text_note_content_or_native_ids_exposed":True,
        "originals_unchanged_no_publication":True,
    }
