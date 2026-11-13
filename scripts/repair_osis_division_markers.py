#!/usr/bin/env python3
"""Reversibly encode verified leading editorial divisions as OSIS milestones.

Research-only. Never strip all '*' or whitespace globally: only replace
literal section/stanza marks at a verified authored p/l opening. Preserves
the precise original sign as a 'marker' attribute, so it is no longer
inline Scripture prose. Reject unknown cases instead of guessing.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re
from xml.parsers import expat

from lxml import etree

from publisher_osis_usfx_parity import original_osis_verses_and_notes, _nonspace
from repair_osis_source_bytes import _end_of_tag
from source_osis_inventory import _source_tree, OSIS, source_inventory

PREFIX = re.compile(r"(?P<spaces>[ \t\r\n]*)(?P<mark>\*\*|\*)(?!\*)")
MAX_BYTES = 128 * 1024 * 1024
KINDS = {"paragraph": "x-subject-division", "poetry": "x-stanza-division"}


class DivisionRepairError(ValueError):
    pass


def _first_authored_verse(element):
    for verse in element.iter(OSIS + "verse"):
        if not verse.get("eID"):
            return verse.get("sID") or verse.get("osisID")
    return None


def _candidates(original: bytes):
    root = _source_tree(original)
    paragraph_first = set()
    poetry_first = set()
    for node in root.iter():
        if node.tag == OSIS + "p":
            ref = _first_authored_verse(node)
            if ref:
                paragraph_first.add(ref)
        elif node.tag in {OSIS + "l", OSIS + "lg"}:
            ref = _first_authored_verse(node)
            if ref:
                poetry_first.add(ref)
    candidates = {}
    skipped = Counter()
    unresolved = []
    for verse in root.iter(OSIS + "verse"):
        ref = verse.get("sID") or verse.get("osisID")
        if verse.get("eID") or not ref:
            continue
        match = PREFIX.match(verse.tail or "")
        if not match:
            continue
        if ref in candidates:
            raise DivisionRepairError("Repeated authored verse marker")
        sign = match.group("mark")
        rest = (verse.tail or "")[match.end():]
        if sign == "*" and (rest.startswith("[") or rest.startswith("Dieu") or
                             rest.startswith("Seigneur")):
            skipped["protected_textual_symbol"] += 1
            continue
        if ref in paragraph_first:
            kind = "paragraph"
        elif ref in poetry_first:
            kind = "poetry"
        else:
            unresolved.append(ref)
            continue
        candidates[ref] = (verse, kind, sign, match.group("spaces"))
    if unresolved:
        raise DivisionRepairError(
            "Original source has leading marks without approved p/l semantics: " +
            ", ".join(unresolved[:8]))
    return root, candidates, skipped


def patch_divisions(source: bytes, *, expected_sha256: str):
    if (not isinstance(source, bytes) or not 128 <= len(source) <= MAX_BYTES or
            not re.fullmatch(r"[a-f0-9]{64}", expected_sha256) or
            sha256(source).hexdigest() != expected_sha256):
        raise DivisionRepairError("Source SHA mismatch or invalid input")
    original_keys, _ = source_inventory(source)
    original_verses, original_notes, _ = original_osis_verses_and_notes(source)
    root, candidates, skipped = _candidates(source)
    nodes = [n for n in root.iter() if isinstance(n.tag, str)]
    selected = {n: (ref, kind, mark, spaces)
                for ref, (n, kind, mark, spaces) in candidates.items()}
    parser = expat.ParserCreate(namespace_separator="}")
    started = [0]
    patches = []

    def begin(name, _attributes):
        pos = parser.CurrentByteIndex
        index = started[0]
        started[0] += 1
        if index >= len(nodes) or nodes[index].tag != "{" + name:
            raise DivisionRepairError("Original byte and XML element order differ")
        node = nodes[index]
        if node not in selected:
            return
        ref, kind, mark, spaces = selected[node]
        end = _end_of_tag(source, pos)
        if source[end-2:end] != b"/>":
            raise DivisionRepairError("Expected unclosed verse start milestone")
        old = (spaces + mark).encode("utf-8")
        if source[end:end+len(old)] != old:
            raise DivisionRepairError("Unexpected original marker byte placement")
        # Every marker survives exactly as an OSIS editorial attribute.
        replacement = ('<milestone type="' + KINDS[kind] +
                       '" marker="' + mark + '"/>').encode("ascii")
        patches.append((end, end+len(old), replacement, ref, kind, mark))

    def deny(*_args):
        raise DivisionRepairError("DTD or external entities are forbidden")

    parser.StartElementHandler = begin
    parser.StartDoctypeDeclHandler = deny
    parser.EntityDeclHandler = deny
    parser.ExternalEntityRefHandler = deny
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(source, True)
    if started[0] != len(nodes) or len(patches) != len(candidates):
        raise DivisionRepairError("Incomplete approved marker coverage")
    patches.sort()
    if any(a[1] > b[0] for a, b in zip(patches, patches[1:])):
        raise DivisionRepairError("Overlapping source changes")
    result = bytearray()
    last = 0
    for start, end, replacement, *_ in patches:
        result.extend(source[last:start])
        result.extend(replacement)
        last = end
    result.extend(source[last:])
    corrected = bytes(result)
    new_root = _source_tree(corrected)
    markers = [(n.get("type"), n.get("marker")) for n in new_root.iter(OSIS + "milestone")
               if n.get("type") in set(KINDS.values())]
    expected = [(KINDS[kind], mark) for *_, kind, mark in patches]
    if sorted(markers) != sorted(expected):
        raise DivisionRepairError("Original editorial marker metadata not preserved")
    corrected_keys, _ = source_inventory(corrected)
    if corrected_keys != original_keys:
        raise DivisionRepairError("Original numbered verse identifiers changed")
    transformed_verses, transformed_notes, _ = original_osis_verses_and_notes(corrected)
    if original_verses.keys() != transformed_verses.keys() or \
            original_notes.keys() != transformed_notes.keys():
        raise DivisionRepairError("Source verses or note hosts changed")
    edits_by_ref = {ref: mark for _, _, _, ref, _, mark in patches}
    for ref, authored in original_verses.items():
        transformed = transformed_verses[ref]
        if ref in edits_by_ref:
            if _nonspace(authored) != edits_by_ref[ref] + _nonspace(transformed):
                raise DivisionRepairError("Verse content changed beyond recorded division")
        elif authored != transformed:
            raise DivisionRepairError("Unreviewed authored verse content changed")
        before, after = original_notes[ref], transformed_notes[ref]
        if len(before) != len(after):
            raise DivisionRepairError("Lost authored note")
        for a, b in zip(before, after):
            if {k: v for k, v in a.items() if k != "point"} != \
                    {k: v for k, v in b.items() if k != "point"}:
                raise DivisionRepairError("Note body, caller, type or target changed")
            # Note lexical offsets move by the exact marker length (1/2 chars).
            expected_shift = len(edits_by_ref.get(ref, ""))
            if a["point"] - b["point"] != expected_shift:
                raise DivisionRepairError("Unexplained note anchor position shift")
    counts = Counter(kind for _, _, _, _, kind, _ in patches)
    return corrected, {
        "schema_version": 1,
        "status": "research_only_byte_patched_editorial_divisions_not_published",
        "source_sha256": expected_sha256,
        "candidate_sha256": sha256(corrected).hexdigest(),
        "converted_markers_by_kind": dict(sorted(counts.items())),
        "source_literal_marker_metadata_equal": True,
        "protected_unchanged_marker_counts": dict(sorted(skipped.items())),
        "unapproved_source_reference_changes": 0,
        "verse_prose_modifications_outside_recorded_symbols": 0,
        "all_original_notes_and_machine_targets_preserved": True,
        "note_anchor_shifts_exactly_accounted_for": True,
        "source_binary_overwritten": False,
        "native_sword_readback_verified": False,
        "reader_visual_accepted": False,
        "release_authorized": False,
    }
