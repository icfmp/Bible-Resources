#!/usr/bin/env python3
"""Read-only USFX → OSIS editorial note fidelity audit.

Preserve the distinction between textually identical cross-reference labels,
resolved machine links, callout glyphs, and note position in the verse.
This module NEVER rewrites either source and never exports note text.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import unicodedata

from lxml import etree

from lsg_sword_compare import NON_VERSE_TEXT_ELEMENTS, NON_VERSE_PARAGRAPH_STYLES
from pilot_preflight import PilotError

OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SOURCE_NOTE_TAGS = frozenset(("x", "f", "fe", "ex", "ef"))


def _name(node) -> str:
    return etree.QName(node).localname if isinstance(node.tag, str) else ""


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _space(value: str) -> str:
    return " ".join(_nfc(value).split())


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()



def _raw_space_difference(source_parts, candidate_parts) -> str:
    """Explain raw note differences without discarding their significance."""
    if source_parts == candidate_parts:
        return "exact"
    if (len(source_parts) != len(candidate_parts)
            or [x[0] for x in source_parts] != [x[0] for x in candidate_parts]):
        return "changed_component_structure"
    if all(a[1].strip() == b[1].strip()
           for a, b in zip(source_parts, candidate_parts)):
        return "leading_or_trailing_whitespace_only"
    if all(_space(a[1]) == _space(b[1])
           for a, b in zip(source_parts, candidate_parts)):
        return "internal_whitespace_changed"
    return "content_changed"


def _read_note(node, *, usfx: bool, word_index: int) -> dict:
    """Keep text private. Compare only independently labeled note components."""
    parts = []
    raw_parts = []
    unknown = []
    source_link_count = 0
    target_link_count = 0
    links = []
    predecessor = node.getprevious()
    preceding_text = (predecessor.tail if predecessor is not None
                      else node.getparent().text if node.getparent() is not None
                      else None)
    before_note_spacing = bool(preceding_text) and preceding_text[-1].isspace()
    extra_attrs = sorted(k for k in node.attrib
                         if k not in (("caller",) if usfx
                                      else ("type", "subType", "placement", "n", "marker")))
    if usfx:
        kind = _name(node)
        kind_ok = kind in SOURCE_NOTE_TAGS
        caller = node.get("caller")
    else:
        kind = ("x" if node.get("type") == "crossReference"
                and node.get("subType") is None else
                "ex" if node.get("type") == "crossReference"
                and node.get("subType") == "x-extended" else
                "f" if node.get("placement") == "foot" else
                "fe" if node.get("placement") == "end" else
                "ef" if node.get("subType") == "x-extended"
                and node.get("placement") == "foot" else "?")
        kind_ok = kind != "?"
        caller = node.get("n") or node.get("marker") or node.get("caller")
    if node.text and _space(node.text):
        parts.append(("unmarked", _space(node.text)))
        raw_parts.append(("unmarked", _nfc(node.text)))
    for child in node:
        if not isinstance(child.tag, str):
            unknown.append("#non-element")
            continue
        tag = _name(child)
        if usfx:
            category = {"xo": "origin", "xt": "target"}.get(tag)
        else:
            category = None
            if tag == "reference":
                if (child.get("type") == "annotateRef"
                        and child.get("subType") == "x-origin"):
                    category = "origin"
                elif not child.get("type") and not child.get("subType"):
                    category = "target"
        if category is None:
            unknown.append(tag)
            category = "unsupported:" + tag
        if any(isinstance(grandchild.tag, str) for grandchild in child.iterdescendants()):
            unknown.append("nested:" + tag)
        if usfx:
            fields = set(child.attrib) - ({"link-ref"} if tag == "xt" else set())
            if fields:
                unknown.extend("attribute:" + x for x in sorted(fields))
            link = child.get("link-ref")
            if link is not None:
                source_link_count += 1
                links.append((category, link))
        else:
            fields = set(child.attrib) - ({"osisRef", "type", "subType"}
                                          if tag == "reference" else set())
            if fields:
                unknown.extend("attribute:" + x for x in sorted(fields))
            link = child.get("osisRef")
            if link is not None:
                target_link_count += 1
                links.append((category, link))
        body = "".join(child.itertext())
        parts.append((category, _space(body)))
        raw_parts.append((category, _nfc(body)))
        if child.tail and _space(child.tail):
            parts.append(("unmarked", _space(child.tail)))
            raw_parts.append(("unmarked", _nfc(child.tail)))
    return {
        "kind": kind, "kind_ok": kind_ok,
        "parts": tuple(parts), "raw_parts": tuple(raw_parts),
        "unknown": tuple(unknown), "extra_attrs": tuple(extra_attrs),
        "caller": caller,
        "links": tuple(links),
        "source_link_count": source_link_count,
        "target_link_count": target_link_count,
        "word_index": word_index,
        "space_immediately_before_note":before_note_spacing,
        # Internal-only DOM reference for read-only structural diagnostics.
        # audit_notes never serializes this element into its public report.
        "_xml_node":node,
    }


def _collect_usfx(root) -> tuple[dict, int]:
    if _name(root) != "usfx":
        raise PilotError("Note audit requires the original USFX document")
    notes = defaultdict(list)
    outside = 0
    for book in root.iter("book"):
        code = book.get("id")
        chapter = None
        current = None
        word_index = 0

        def walk(node):
            nonlocal chapter, current, word_index, outside
            if not isinstance(node.tag, str):
                return
            kind = _name(node)
            if kind == "c":
                raw = node.get("id")
                if not raw or not raw.isdigit():
                    raise PilotError("Unreviewed USFX chapter in note audit")
                chapter = int(raw)
            elif kind == "v":
                raw = node.get("id")
                if not chapter or not raw or not raw.isdigit():
                    raise PilotError("Unreviewed USFX verse in note audit")
                current = (code, chapter, int(raw))
                word_index = 0
            elif kind == "ve":
                current = None
            if kind in SOURCE_NOTE_TAGS:
                if current is None:
                    outside += 1
                else:
                    notes[current].append(_read_note(node, usfx=True,
                                                     word_index=word_index))
                return
            if (kind in NON_VERSE_TEXT_ELEMENTS or
                    (kind == "p" and (node.get("sfm") or node.get("style"))
                     in NON_VERSE_PARAGRAPH_STYLES)):
                return
            if kind == "w" and current is not None:
                word_index += 1
            for child in node:
                walk(child)

        walk(book)
    return notes, outside


def _collect_osis(root) -> tuple[dict, int]:
    if isinstance(root, etree._ElementTree):
        root = root.getroot()
    if root.tag != OSIS + "osis":
        raise PilotError("Note audit requires the generated OSIS document")
    notes = defaultdict(list)
    outside = 0
    for book in root.iter(OSIS + "div"):
        if book.get("type") != "book":
            continue
        current = None
        word_index = 0

        def walk(node):
            nonlocal current, word_index, outside
            if isinstance(node, etree._Comment):
                return
            if not isinstance(node.tag, str):
                raise PilotError("Unexpected non-element in OSIS note audit")
            kind = _name(node)
            if kind == "verse":
                opening = node.get("osisID") or node.get("sID")
                closing = node.get("eID")
                if opening:
                    current = opening
                    word_index = 0
                elif closing:
                    if current != closing:
                        raise PilotError("Mismatched OSIS verse milestone in note audit")
                    current = None
                else:
                    raise PilotError("Unreviewed OSIS verse milestone")
                return
            if kind == "note":
                if current is None:
                    outside += 1
                else:
                    notes[current].append(_read_note(node, usfx=False,
                                                     word_index=word_index))
                return
            if kind in {"title", "header", "revisionDesc", "description"}:
                return
            if kind == "w" and current is not None:
                word_index += 1
            for child in node:
                walk(child)
        walk(book)
        if current is not None:
            raise PilotError("Unclosed OSIS verse milestone in note audit")
    return notes, outside


def audit_notes(source_root, osis_root, book_mapping: dict[str, str]) -> dict:
    """Audit each note and every component in source order, by verse and slot.

    No note body or caller string is serialized into the diagnostic report.
    """
    source, source_outside = _collect_usfx(source_root)
    target, target_outside = _collect_osis(osis_root)
    all_refs = set(source)
    counts_equal = 0
    matched_parts = 0
    raw_parts_equal = 0
    matched_anchor = 0
    matched_caller = 0
    matched_kind = 0
    matched_links = 0
    source_notes = sum(map(len, source.values()))
    target_notes = sum(map(len, target.values()))
    source_link_count = 0
    target_link_count = 0
    caller_count = 0
    unknown_count = 0
    mismatch_counts = Counter()
    note_whitespace_classes = Counter()
    before_note_separator_cases=Counter()
    first_missing_note_separators=[]
    samples = []
    for key in sorted(all_refs):
        code, chapter, verse = key
        ref = f"{book_mapping[code]}.{chapter}.{verse}"
        original = source[key]
        converted = target.get(ref, [])
        if len(original) == len(converted):
            counts_equal += 1
        else:
            mismatch_counts["note_count"] += 1
        for position, (a, b) in enumerate(zip(original, converted), 1):
            source_link_count += a["source_link_count"]
            target_link_count += b["target_link_count"]
            caller_count += (a["caller"] is not None)
            unknown_count += len(a["unknown"]) + len(b["unknown"])
            has_source_space=a["space_immediately_before_note"]
            has_candidate_space=b["space_immediately_before_note"]
            if has_source_space and has_candidate_space:
                prefix="present_in_both"
            elif has_source_space:
                prefix="missing_from_candidate"
                if len(first_missing_note_separators)<50:
                    first_missing_note_separators.append({
                        "reference":f"{code}.{chapter}.{verse}",
                        "note_ordinal":position,
                        "source_word_anchor":a["word_index"],
                        "candidate_word_anchor":b["word_index"],
                    })
            elif has_candidate_space:
                prefix="added_in_candidate"
            else:
                prefix="absent_in_both"
            before_note_separator_cases[prefix]+=1
            checks = {
                "preceding_separator_presence":has_source_space==has_candidate_space,
                "component_text": a["parts"] == b["parts"],
                "raw_component_text": a["raw_parts"] == b["raw_parts"],
                "word_anchor": a["word_index"] == b["word_index"],
                "caller": a["caller"] == b["caller"],
                "kind": (a["kind_ok"] and b["kind_ok"]
                         and a["kind"] == b["kind"]),
                "explicit_link": a["links"] == b["links"],
                "reviewed_markup": not (a["unknown"] or b["unknown"]
                                       or a["extra_attrs"] or b["extra_attrs"]),
            }
            note_whitespace_classes[_raw_space_difference(
                a["raw_parts"], b["raw_parts"])] += 1
            matched_parts += checks["component_text"]
            raw_parts_equal += checks["raw_component_text"]
            matched_anchor += checks["word_anchor"]
            matched_caller += checks["caller"]
            matched_kind += checks["kind"]
            # Empty source/target link lists are not proof of any link.
            matched_links += bool(a["source_link_count"] or b["target_link_count"]) and checks["explicit_link"]
            for label, matches in checks.items():
                if not matches:
                    mismatch_counts[label] += 1
            if (not all(checks.values())) and len(samples) < 60:
                samples.append({
                    "reference": f"{code}.{chapter}.{verse}",
                    "note_ordinal": position,
                    "failed_checks": sorted(k for k, v in checks.items() if not v),
                    "source_component_count": len(a["parts"]),
                    "candidate_component_count": len(b["parts"]),
                    "source_text_hash": _sha(repr(a["parts"])),
                    "candidate_text_hash": _sha(repr(b["parts"])),
                    "source_word_anchor": a["word_index"],
                    "candidate_word_anchor": b["word_index"],
                    "source_attribute_names": list(a["extra_attrs"]),
                    "candidate_attribute_names": list(b["extra_attrs"]),
                    "unreviewed_source_marker_names": list(a["unknown"]),
                    "unreviewed_candidate_marker_names": list(b["unknown"]),
                })
        # When counts differ, the unmatched notes must fail closed.
        for a in original[len(converted):]:
            source_link_count += a["source_link_count"]
            caller_count += (a["caller"] is not None)
        for b in converted[len(original):]:
            target_link_count += b["target_link_count"]
    all_target_keys = set(target)
    expected_target_keys = {f"{book_mapping[c]}.{ch}.{v}"
                            for c, ch, v in all_refs}
    target_only_keys = all_target_keys - expected_target_keys
    if target_only_keys:
        mismatch_counts["notes_on_other_target_verses"] = len(target_only_keys)
    paired = sum(min(len(vals), len(target.get(
        f"{book_mapping[c]}.{ch}.{v}", []))) for (c, ch, v), vals in source.items())
    unpaired = source_notes - paired + target_notes - paired
    strict_success = (not mismatch_counts and not unpaired
                      and not source_outside and not target_outside
                      and source_notes == target_notes)
    return {
        "source_note_count": source_notes,
        "candidate_note_count": target_notes,
        "paired_note_count": paired,
        "unpaired_note_count": unpaired,
        "source_notes_outside_verses": source_outside,
        "candidate_notes_outside_verses": target_outside,
        "matching_note_component_text": matched_parts,
        "matching_raw_note_component_text": raw_parts_equal,
        "matching_note_word_anchors": matched_anchor,
        "matching_note_caller_markers": matched_caller,
        "matching_note_kinds": matched_kind,
        "matching_explicit_machine_link_note_slots": matched_links,
        "explicit_machine_target_verification_applicable": source_link_count > 0,
        "source_explicit_link_count": source_link_count,
        "candidate_explicit_link_count": target_link_count,
        "source_notes_with_caller_marker": caller_count,
        "unsupported_note_substructures": unknown_count,
        "mismatch_counts": dict(sorted(mismatch_counts.items())),
        "raw_note_difference_categories": dict(sorted(note_whitespace_classes.items())),
        "preceding_note_separator_presence_cases":dict(sorted(before_note_separator_cases.items())),
        "first_missing_preceding_note_separators":first_missing_note_separators,
        "first_mismatches": samples,
        "all_note_contents_metadata_and_positions_verified": strict_success,
        "textual_target_references_verified": (
            matched_parts == paired and paired == source_notes == target_notes
            and not source_outside and not target_outside),
        "limitation": (
            "Cross-reference target strings are compared literally after NFC "
            "and whitespace collapse. This does not resolve them to canonical "
            "Bible passage IDs. Strict fidelity additionally requires callout "
            "markers, in-verse anchors, metadata and all nested markup."
        ),
    }
