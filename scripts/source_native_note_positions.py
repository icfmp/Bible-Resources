#!/usr/bin/env python3
"""Exact numbered-note caller *positions* in original USFX and stock SWORD.

Independent, strict, read-only source/native XML readers. This audit compares
Unicode non-whitespace character ordinals in the verified verse body. It does
not infer note labels, editorial reference semantics, or navigation targets.
No Scripture, note contents, raw markup, or generated IDs reach the report.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json

from lxml import etree

from stable_sword_refs import KEY

MAX_XML = 128 * 1024 * 1024
MAX_VERSE = 2 * 1024 * 1024
MAX_SAMPLES = 16
SOURCE_NOTES = frozenset({"f", "fe", "x", "ef", "ex", "note"})
SOURCE_HEAD = frozenset({
    "s", "s1", "s2", "s3", "s4", "ms", "ms1", "ms2",
    "mt", "mt1", "mt2", "mr", "d", "cl", "r", "rem",
})
SOURCE_LABELS = frozenset({"vp", "va", "cp", "ca"})


class NoteAnchorError(ValueError):
    """Source/native note anchor or prerequisite is unverified."""


def _parse(data: bytes, root_name: str, *, fragment=False):
    if not isinstance(data, bytes) or not 0 < len(data) <= (
            MAX_VERSE if fragment else MAX_XML):
        raise NoteAnchorError("Empty or excessive source/native XML")
    if b"<!DOCTYPE" in data.upper() or b"<?xml" in data.lower():
        raise NoteAnchorError("Unreviewed source/native declarations")
    if fragment:
        data = b"<private_root>" + data + b"</private_root>"
    try:
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                 no_network=True, recover=False, huge_tree=False)
        root = etree.fromstring(data, parser)
    except etree.XMLSyntaxError as exc:
        raise NoteAnchorError("Invalid source/native XML") from exc
    if root.tag != root_name or any(
            isinstance(n, etree._Entity) for n in root.iter()):
        raise NoteAnchorError("Unexpected XML root or unresolved entity")
    return root


def _nonspace(text: str) -> str:
    return "".join(char for char in text if not char.isspace())


def original_usfx_note_anchors(
    xml: bytes, mapping: list[tuple[str, str]],
    source_verses: dict[str, str], source_notes: dict,
) -> dict[str, tuple[int, ...]]:
    """Reconstruct *every* authorial numbered verse, collect note-gap ordinals.

    Requires independent main-text and note inventories as prerequisites.
    Anything ambiguous fails closed; no special edition or verse exceptions.
    """
    root = _parse(xml, "usfx")
    pairs = dict(mapping)
    if (not pairs or len(pairs) != len(mapping)
            or len(set(pairs.values())) != len(mapping)):
        raise NoteAnchorError("Ambiguous original book crosswalk")
    chunks: dict[str, list[str]] = {}
    anchors: dict[str, list[int]] = {}
    seen = set()
    for book in root.iter("book"):
        code = book.get("id")
        if code not in pairs or code in seen:
            raise NoteAnchorError("Missing, duplicated or unmapped book")
        seen.add(code)
        chapter = None
        active = None
        position = 0

        def append(fragment):
            nonlocal position
            if active is not None and fragment:
                chunks[active].append(fragment)
                position += sum(not c.isspace() for c in fragment)

        def visit(node, depth=0):
            nonlocal chapter, active, position
            if depth > 256:
                raise NoteAnchorError("Excessive source nesting")
            if not isinstance(node.tag, str):
                return
            tag = etree.QName(node).localname
            if tag in SOURCE_NOTES:
                if any(isinstance(x.tag, str)
                       and etree.QName(x).localname in {"v", "c"}
                       for x in node.iterdescendants()):
                    raise NoteAnchorError("Numbering inside a note")
                if active is not None:
                    anchors[active].append(position)
                return
            if (tag in SOURCE_HEAD or tag in SOURCE_LABELS
                    or (tag == "p" and node.get("sfm") == "sp")):
                if any(isinstance(x.tag, str)
                       and etree.QName(x).localname in {"v", "c"}
                       for x in node.iterdescendants()):
                    raise NoteAnchorError("Numbering inside an excluded heading")
                return
            if tag == "ve":
                active = None
                return
            if tag == "c":
                raw = node.get("id", "")
                if not raw.isdecimal() or int(raw) < 1:
                    raise NoteAnchorError("Unrecognized original chapter")
                chapter, active = int(raw), None
            elif tag == "v":
                raw = node.get("id", "")
                if chapter is None or not raw.isdecimal() or int(raw) < 1:
                    raise NoteAnchorError("Unrecognized original verse")
                active = f"{pairs[code]}.{chapter}.{int(raw)}"
                if active in chunks:
                    raise NoteAnchorError("Duplicate original numbered verse")
                chunks[active] = []
                anchors[active] = []
                position = 0
            if tag not in {"c", "v"}:
                append(node.text)
            for child in node:
                visit(child, depth + 1)
                append(child.tail)

        visit(book)
    if seen != set(pairs) or set(chunks) != set(source_verses):
        raise NoteAnchorError("Incomplete source verse/book inventory")
    for ref, parts in chunks.items():
        if (KEY.fullmatch(ref) is None
                or "".join(parts) != source_verses[ref]):
            raise NoteAnchorError("Independent source main text reconstruction disagrees")
        if len(source_verses[ref].encode("utf-8")) > MAX_VERSE:
            raise NoteAnchorError("Oversized original verse")
        if len(anchors[ref]) != len(source_notes.get(ref, ())):
            raise NoteAnchorError("Original note order/count disagrees with independent audit")
    return {ref: tuple(points) for ref, points in anchors.items()}


def native_note_anchor_positions(raw: bytes, source_verse_text: str) -> tuple[int, ...]:
    """Read original stock XML with note body/title excluded from verse text."""
    root = _parse(raw, "private_root", fragment=True)
    chunks = []
    points = []
    position = 0

    def append(fragment):
        nonlocal position
        if fragment:
            chunks.append(fragment)
            position += sum(not c.isspace() for c in fragment)

    def visit(node, depth=0):
        if depth > 256:
            raise NoteAnchorError("Excessive native XML nesting")
        if not isinstance(node.tag, str):
            return
        tag = etree.QName(node).localname
        if tag == "note":
            if any(isinstance(x.tag, str)
                   and etree.QName(x).localname == "note"
                   for x in node.iterdescendants()):
                raise NoteAnchorError("Nested native notes")
            points.append(position)
            return
        if tag == "title":
            return
        append(node.text)
        for child in node:
            visit(child, depth + 1)
            append(child.tail)

    visit(root)
    if _nonspace("".join(chunks)) != _nonspace(source_verse_text):
        raise NoteAnchorError("Source/native note anchor main-text prerequisite differs")
    return tuple(points)


class NumberedNoteAnchorAudit:
    def __init__(self, source_positions: dict, source_verses: dict):
        if not source_positions or set(source_positions) != set(source_verses):
            raise NoteAnchorError("Incomplete original note anchor inventory")
        self.source = source_positions
        self.source_verses = source_verses
        self.seen = set()
        self.counts = Counter()
        self.samples = []
        self.digest = sha256()

    def observe(self, ref: str, native_raw: bytes):
        if ref not in self.source or ref in self.seen:
            raise NoteAnchorError("Unmapped or duplicate native numbered reference")
        self.seen.add(ref)
        try:
            compiled = native_note_anchor_positions(
                native_raw, self.source_verses[ref])
        except NoteAnchorError:
            self.counts["unparseable_or_nonspace_prerequisite_failed"] += 1
            if len(self.samples) < MAX_SAMPLES:
                self.samples.append({"reference":ref,
                                     "finding":"unparseable_or_text_prerequisite_failed"})
            return
        authored = self.source[ref]
        if len(authored) != len(compiled):
            self.counts["verses_with_note_count_difference"] += 1
            if len(self.samples) < MAX_SAMPLES:
                self.samples.append({"reference":ref,
                                     "finding":"note_count_difference",
                                     "source_notes":len(authored),
                                     "native_notes":len(compiled)})
            return
        self.counts["numbered_verses_checked"] += 1
        self.counts["numbered_note_anchors_checked"] += len(authored)
        for i, (a, b) in enumerate(zip(authored, compiled), start=1):
            payload = json.dumps([ref,i,a,b],separators=(",",":")).encode()
            self.digest.update(len(payload).to_bytes(4,"big")+payload)
            if a == b:
                self.counts["matching_note_anchor_nonspace_codepoint_ordinals"] += 1
            else:
                self.counts["moved_note_anchor_nonspace_codepoint_ordinals"] += 1
                if len(self.samples) < MAX_SAMPLES:
                    self.samples.append({
                        "reference":ref, "one_based_note":i,
                        "finding":"moved_note_anchor_nonspace_codepoint_ordinal",
                        "source_ordinal":a, "native_ordinal":b,
                    })

    def finish(self):
        if self.seen != set(self.source):
            raise NoteAnchorError("Incomplete original/native indexed note anchor scan")
        for name in (
            "unparseable_or_nonspace_prerequisite_failed",
            "verses_with_note_count_difference",
            "numbered_note_anchors_checked",
            "matching_note_anchor_nonspace_codepoint_ordinals",
            "moved_note_anchor_nonspace_codepoint_ordinals",
        ):
            self.counts.setdefault(name,0)
        success = (
            self.counts["unparseable_or_nonspace_prerequisite_failed"] == 0
            and self.counts["verses_with_note_count_difference"] == 0
            and self.counts["moved_note_anchor_nonspace_codepoint_ordinals"] == 0
            and self.counts["numbered_note_anchors_checked"] == sum(
                len(v) for v in self.source.values())
        )
        return {
            "schema_version":1,
            "status": ("all_numbered_note_nonspace_anchors_match"
                       if success else "unresolved_numbered_note_anchor_difference"),
            "all_numbered_note_nonspace_anchor_positions_match":success,
            "original_compiled_note_anchor_counts":dict(sorted(self.counts.items())),
            "first_note_anchor_findings_reference_ordinals_only":self.samples,
            "ordered_note_anchor_position_comparison_sha256":self.digest.hexdigest(),
            "source_native_note_caller_label_and_reference_targets_unverified":True,
            "note_body_whitespace_and_typography_unverified":True,
            "no_scripture_note_content_or_raw_xml_in_report":True,
            "not_publication_or_editorial_approval":True,
        }
