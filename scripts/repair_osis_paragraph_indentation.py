#!/usr/bin/env python3
"""Remove XML pretty-print indentation after the first verse milestone of p.

Strict source-hash-bound, byte-scope research overlay. Paragraph structure is
retained. Only an XML newline followed by ASCII indentation spaces immediately
after a p's first numbered verse sID is eligible; no other original source
whitespace is modified. Source bytes are immutable and provenance retained.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re
from xml.parsers import expat

from publisher_osis_usfx_parity import original_osis_verses_and_notes, _nonspace
from repair_osis_source_bytes import _end_of_tag
from source_osis_inventory import _source_tree, OSIS, source_inventory

MAX_BYTES = 128 * 1024 * 1024
FORMATTING = re.compile(r"(?P<newline>\r?\n)(?P<indent> {1,40})(?=\S)")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class ParagraphWhitespaceError(ValueError):
    pass


def _first_verse(p):
    for node in p.iter(OSIS + "verse"):
        if not node.get("eID"):
            return node
    return None


def trim_publisher_paragraph_indentation(xml: bytes, *, expected_sha256: str):
    if (not isinstance(xml, bytes) or not 128 <= len(xml) <= MAX_BYTES or
            not isinstance(expected_sha256, str) or SHA.fullmatch(expected_sha256) is None or
            sha256(xml).hexdigest() != expected_sha256):
        raise ParagraphWhitespaceError("Input is not an exact SHA-pinned OSIS source")
    original_keys, _ = source_inventory(xml)
    original_text, original_notes, _ = original_osis_verses_and_notes(xml)
    tree = _source_tree(xml)
    selected = {}
    counts = Counter()
    for para in tree.iter(OSIS + "p"):
        verse = _first_verse(para)
        if verse is None:
            continue
        if verse.get("sID") is None or verse.get("osisID") != verse.get("sID"):
            raise ParagraphWhitespaceError("Paragraph first verse is not an exact start milestone")
        ref = verse.get("sID")
        m = FORMATTING.match(verse.tail or "")
        if not m:
            counts["paragraphs_without_exact_xml_indent_candidate"] += 1
            continue
        if verse in selected:
            raise ParagraphWhitespaceError("Same numbered verse is first of multiple paragraphs")
        selected[verse] = (ref, m.group(0))
        counts["paragraphs_with_exact_xml_indent"] += 1
        counts["formatting_spaces_removed"] += len(m.group("indent"))
        counts["formatting_newlines_removed"] += 1
        counts["paragraph_start_indent_width_" + str(len(m.group("indent")))] += 1
    parser = expat.ParserCreate(namespace_separator="}")
    nodes = [n for n in tree.iter() if isinstance(n.tag, str)]
    started = [0]
    edits = []

    def begin(name, _attrs):
        idx = started[0]
        started[0] += 1
        if idx >= len(nodes) or nodes[idx].tag != "{" + name:
            raise ParagraphWhitespaceError("OSIS byte parser tree order changed")
        node = nodes[idx]
        if node not in selected:
            return
        end = _end_of_tag(xml, parser.CurrentByteIndex)
        if xml[end-2:end] != b"/>":
            raise ParagraphWhitespaceError("Authorial verse start is not self-closing")
        ref, pattern = selected[node]
        original = pattern.encode("utf-8")
        if xml[end:end+len(original)] != original:
            raise ParagraphWhitespaceError("XML indentation not at exact expected byte")
        edits.append((end, end+len(original), ref))

    def deny(*_args):
        raise ParagraphWhitespaceError("DTD or entity forbidden")
    parser.StartElementHandler = begin
    parser.StartDoctypeDeclHandler = deny
    parser.EntityDeclHandler = deny
    parser.ExternalEntityRefHandler = deny
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(xml, True)
    if started[0] != len(nodes) or len(edits) != len(selected):
        raise ParagraphWhitespaceError("Not all exact XML indentation spans were found")
    edits.sort()
    if any(a[1] > b[0] for a, b in zip(edits, edits[1:])):
        raise ParagraphWhitespaceError("Overlapping source indentation edits")
    corrected = bytearray()
    last = 0
    for start, end, _ref in edits:
        corrected.extend(xml[last:start])
        last = end
    corrected.extend(xml[last:])
    result = bytes(corrected)
    new_keys, _ = source_inventory(result)
    if new_keys != original_keys:
        raise ParagraphWhitespaceError("Scripture key inventory changed")
    changed_text, changed_notes, _ = original_osis_verses_and_notes(result)
    if set(original_text) != set(changed_text):
        raise ParagraphWhitespaceError("Authored text key set changed")
    edited_refs = {ref for _, _, ref in edits}
    for ref, value in original_text.items():
        new = changed_text[ref]
        if ref in edited_refs:
            if _nonspace(value) != _nonspace(new):
                raise ParagraphWhitespaceError("Non-whitespace text changed")
        elif value != new:
            raise ParagraphWhitespaceError("Text outside approved XML indentation changed")
        if original_notes[ref] != changed_notes[ref]:
            raise ParagraphWhitespaceError("Original note text, anchors or targets changed")
    return result, {
        "schema_version": 1,
        "status": "private_reversible_source_xml_formatting_whitespace_only",
        "original_sha256": expected_sha256,
        "new_sha256": sha256(result).hexdigest(),
        "counts": dict(sorted(counts.items())),
        "all_source_nonspace_characters_preserved": True,
        "all_source_note_values_and_positions_preserved": True,
        "original_xml_bytes_untouched": True,
        "native_reader_indentation_reduction_proved": False,
        "authorial_typography_signoff": False,
        "release_approved": False,
    }
