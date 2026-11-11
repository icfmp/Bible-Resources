#!/usr/bin/env python3
"""Source-OSIS to compiled-SWORD paragraph/poetry boundary verification.

Authorial source and native binary are inspected separately. Only source
book names, kinds, counts, integer non-whitespace codepoint positions and
hashes may appear in reports. Never change publisher text or copy raw XML.
Detailed whitespace typography, headings, note annotations and reader visuals
remain separate acceptance gates.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json

from lxml import etree

from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY
from source_native_maintext_probe import native_raw_main_text

BODY = frozenset({"p", "l", "lg"})
EXCLUDED = frozenset({"note", "title", "header"})
MAX_EVENTS = 300_000
MAX_EXAMPLES = 20
MAX_RAW = 2 * 1024 * 1024


class OSISBodyBoundaryError(ValueError):
    """Original/native body structure cannot be independently verified."""


def _name(node):
    return etree.QName(node).localname if isinstance(node.tag, str) else ""


def _event_kind(node, *, native):
    tag = _name(node)
    if native and tag == "div" and node.get("type") == "x-p":
        return "p"
    if tag in BODY:
        return tag
    return None


def _event_endpoints(node):
    sid, eid = node.get("sID"), node.get("eID")
    if sid is not None and eid is not None:
        raise OSISBodyBoundaryError("Contradictory body milestone endpoints")
    if sid is not None:
        if not sid:
            raise OSISBodyBoundaryError("Empty body start identifier")
        return ("open",)
    if eid is not None:
        if not eid:
            raise OSISBodyBoundaryError("Empty body end identifier")
        return ("close",)
    return ("open", "close")


def source_osis_body_events(xml: bytes, verses: dict[str, str]):
    """Reconstruct source p/l/lg endpoints at exact authored book text ordinals.

    The independent source verse scanner supplies the expected actual text;
    missing or shifted verse text fails rather than forging coordinates.
    """
    if not verses or any(KEY.fullmatch(ref) is None for ref in verses):
        raise OSISBodyBoundaryError("Missing validated publisher main-text inventory")
    root = _source_tree(xml)
    books = [n for n in root.iter(OSIS + "div") if n.get("type") == "book"]
    if not books:
        raise OSISBodyBoundaryError("No publisher OSIS books")
    events = {}
    all_seen = set()
    for book in books:
        bookid = book.get("osisID")
        if (not isinstance(bookid, str) or bookid in events
                or not bookid.isascii() or not bookid.isalnum()):
            raise OSISBodyBoundaryError("Duplicate or invalid source book scope")
        active = None
        ordinal = 0
        reconstructed = {}
        current_events = []

        def append(fragment):
            nonlocal ordinal
            if active is not None and fragment:
                reconstructed[active].append(fragment)
                ordinal += sum(not c.isspace() for c in fragment)

        def visit(node, depth=0):
            nonlocal active
            if depth > 256:
                raise OSISBodyBoundaryError("Deep source body markup")
            if not isinstance(node.tag, str):
                return
            kind = _event_kind(node, native=False)
            if _name(node) in EXCLUDED:
                if any(n.tag == OSIS + "verse" for n in node.iterdescendants()):
                    raise OSISBodyBoundaryError("Source editorial markup wraps numbering")
                return
            endpoints = _event_endpoints(node) if kind else ()
            if "open" in endpoints:
                current_events.append((kind, "open", ordinal))
            container = False
            if node.tag == OSIS + "verse":
                end = node.get("eID")
                if end is not None:
                    if active != end:
                        raise OSISBodyBoundaryError("Mispaired source verse close")
                    active = None
                    return
                ref = node.get("osisID")
                if (not ref or KEY.fullmatch(ref) is None
                        or not ref.startswith(bookid + ".")
                        or active is not None or ref in reconstructed):
                    raise OSISBodyBoundaryError("Invalid or overlapping source verse")
                active = ref
                reconstructed[ref] = []
                container = node.get("sID") is None
            append(node.text)
            for child in node:
                visit(child, depth + 1)
                append(child.tail)
            if container:
                active = None
            if "close" in endpoints:
                current_events.append((kind, "close", ordinal))
            if len(current_events) > MAX_EVENTS:
                raise OSISBodyBoundaryError("Source body event count unsafe")

        visit(book)
        if active is not None:
            raise OSISBodyBoundaryError("Unclosed source verse before end of book")
        for ref, parts in reconstructed.items():
            if ref not in verses:
                raise OSISBodyBoundaryError("Source body scanner saw unknown numbered reference")
            text = "".join(parts)
            if "".join(text.split()) != "".join(verses[ref].split()):
                raise OSISBodyBoundaryError("Source body scanner disagrees with verse text")
        all_seen.update(reconstructed)
        expected_ord = sum(len("".join(t.split())) for ref, t in verses.items()
                           if ref.startswith(bookid + "."))
        if ordinal != expected_ord:
            raise OSISBodyBoundaryError("Source book codepoint extent differs from inventory")
        events[bookid] = current_events
    if all_seen != set(verses):
        raise OSISBodyBoundaryError("Source body events do not span complete Bible")
    return events


class NativeOSISBodyBoundaryScan:
    """Stream actual K/I/U records; never retain compiled Scripture or IDs."""

    def __init__(self, source_verses: dict[str, str], source_events: dict):
        if not source_verses or not source_events:
            raise OSISBodyBoundaryError("Source structural evidence missing")
        self._verses = source_verses
        self._expected = source_events
        self._offset = defaultdict(int)
        self._events = defaultdict(list)
        self._seen = set()
        self._last = {}
        self._other = Counter()

    def observe(self, kind: str, ref: str, raw: bytes):
        if not isinstance(raw, bytes) or len(raw) > MAX_RAW:
            raise OSISBodyBoundaryError("Invalid native raw original size")
        if kind == "K":
            if KEY.fullmatch(ref) is None or ref not in self._verses or ref in self._seen:
                raise OSISBodyBoundaryError("Missing, duplicate or unsafe native verse")
            self._seen.add(ref)
        elif kind not in {"I", "U"}:
            raise OSISBodyBoundaryError("Unexpected native record category")
        if kind == "U":
            book = None
        else:
            book = ref.split(".", 1)[0]
            if book not in self._expected:
                raise OSISBodyBoundaryError("Native intro or verse outside publisher canon")
        try:
            root = etree.fromstring(
                b"<private_root>" + raw + b"</private_root>",
                etree.XMLParser(resolve_entities=False, load_dtd=False,
                                no_network=True, recover=False, huge_tree=False))
        except (etree.XMLSyntaxError, ValueError) as exc:
            raise OSISBodyBoundaryError("Unparseable original native body XML") from exc
        if any(isinstance(n, etree._Entity) for n in root.iter()):
            raise OSISBodyBoundaryError("Unexpected native XML entity")

        local = []
        text = []
        start = self._offset[book] if book is not None else 0
        index = 0

        def add(fragment):
            nonlocal index
            if kind == "K" and fragment:
                text.append(fragment)
                index += sum(not c.isspace() for c in fragment)

        def visit(node, depth=0):
            if depth > 256:
                raise OSISBodyBoundaryError("Deep native source markup")
            if not isinstance(node.tag, str):
                return
            tag = _name(node)
            if tag in EXCLUDED:
                return
            ekind = _event_kind(node, native=True)
            endpoints = _event_endpoints(node) if ekind else ()
            if "open" in endpoints:
                local.append((ekind, "open", start + index))
            add(node.text)
            for child in node:
                visit(child, depth + 1)
                add(child.tail)
            if "close" in endpoints:
                local.append((ekind, "close", start + index))

        visit(root)
        if kind == "U":
            if local:
                raise OSISBodyBoundaryError("Opaque native TOP carries unaddressable body structure")
            self._other["anonymous_TOP_records_without_body_events"] += 1
            return
        if kind == "K":
            expected = "".join(c for c in self._verses[ref] if not c.isspace())
            actual = "".join(c for part in text for c in part if not c.isspace())
            # Independent parser and raw entry main-text extractor must agree.
            extracted, _discarded = native_raw_main_text(raw)
            if actual != expected or actual != "".join(c for c in extracted if not c.isspace()):
                raise OSISBodyBoundaryError("Native body scanner text differs from source/reader")
            self._offset[book] += index
        else:
            self._other["intro_records_screened"] += 1
        self._events[book].extend(local)
        if len(self._events[book]) > MAX_EVENTS:
            raise OSISBodyBoundaryError("Native structural stream too large")

    def finish(self):
        if self._seen != set(self._verses):
            raise OSISBodyBoundaryError("Incomplete compiled verse scope")
        for book in self._expected:
            count = sum(len("".join(t.split())) for ref, t in self._verses.items()
                        if ref.startswith(book + "."))
            if self._offset[book] != count:
                raise OSISBodyBoundaryError("Native book extent differs from original text")
        source_digest, native_digest = sha256(), sha256()
        counts = Counter()
        samples = []
        for book in self._expected:
            a = self._expected[book]
            b = self._events.get(book, [])
            counts["books_compared"] += 1
            counts["source_events_total"] += len(a)
            counts["native_events_total"] += len(b)
            if a == b:
                counts["books_with_identical_event_kinds_endpoints_and_positions"] += 1
            else:
                counts["books_with_different_body_events"] += 1
                if len(samples) < MAX_EXAMPLES:
                    first = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]),
                                 min(len(a), len(b)))
                    item = {
                        "book": book, "first_different_event_one_based": first + 1,
                        "source_event_count": len(a), "native_event_count": len(b),
                    }
                    if first < len(a):
                        item["source_kind"] = a[first][0]
                        item["source_endpoint"] = a[first][1]
                        item["source_ordinal"] = a[first][2]
                    if first < len(b):
                        item["native_kind"] = b[first][0]
                        item["native_endpoint"] = b[first][1]
                        item["native_ordinal"] = b[first][2]
                    samples.append(item)
            for h, data in ((source_digest, a), (native_digest, b)):
                blob = json.dumps([book, data], separators=(",", ":"), ensure_ascii=True).encode()
                h.update(len(blob).to_bytes(4, "big") + blob)
        ok = counts["books_with_different_body_events"] == 0
        return {
            "schema_version": 1,
            "status": ("all_source_native_body_p_l_lg_events_equal_at_book_nonspace_positions"
                       if ok else "source_native_body_event_kind_or_position_differences"),
            "counts": dict(sorted(counts.items())),
            "first_mismatching_books_and_nonspace_positions": samples,
            "source_event_fingerprint_sha256": source_digest.hexdigest(),
            "native_event_fingerprint_sha256": native_digest.hexdigest(),
            "native_nonaddressable_record_screen": dict(sorted(self._other.items())),
            "source_to_compiled_exact_p_l_lg_event_position_parity_verified": ok,
            "literal_whitespace_and_visual_typography_unverified": True,
            "book_titles_verse_zero_note_layout_or_publication_approved": False,
            "original_xml_or_sword_text_or_ids_exposed": False,
        }
