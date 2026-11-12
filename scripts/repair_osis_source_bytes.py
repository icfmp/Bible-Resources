#!/usr/bin/env python3
"""Patch only reviewed machine attributes/tags in exact ORIGINAL OSIS bytes.

CrossWire osis2mod has shown different poetry behavior after whole-document
lxml serialization, despite identical XML character content. Preserve every
unrelated original *byte*, including markup serialization, for compilation.
This is research-only, never an autonomous editorial or publication approval.
"""
from __future__ import annotations

from hashlib import sha256
import re
from xml.parsers import expat

from lxml import etree

from repair_osis_note_links import _source_note_nodes, propose as propose_links
from repair_osis_inline_markup import propose as propose_inline, _state
from source_osis_inventory import _source_tree, OSIS

ATTR = re.compile(rb'(?P<ws>\s+)osisRef(?P<eq>\s*=\s*)(?P<q>["\x27])(?P<value>[^"\x27]*)(?P=q)')


class LexicalPatchError(ValueError):
    pass


def _end_of_tag(xml: bytes, start: int) -> int:
    if xml[start:start+1] != b"<":
        raise LexicalPatchError("Expected original element start byte")
    quoted = None
    for i in range(start+1, min(start+4096, len(xml))):
        ch = xml[i]
        if quoted is None:
            if ch in (34, 39):
                quoted = ch
            elif ch == 62:  # >
                return i + 1
        elif ch == quoted:
            quoted = None
    raise LexicalPatchError("Oversized or ambiguous original opening tag")


def _element_targets(root, link_plan, inline_plan):
    scope = _source_note_nodes(root)
    targets = {}
    for edit in link_plan["edits"]:
        notes = scope.get(edit["note_host"], ())
        if len(notes) < edit["note_index"]:
            raise LexicalPatchError("No such reviewed note host")
        note = notes[edit["note_index"]-1]
        selected = [n for n in note.iterdescendants(OSIS + "reference")
                    if n.get("osisRef") == edit["old_target"]]
        if len(selected) != 1 or selected[0] in targets:
            raise LexicalPatchError("Ambiguous reviewed reference occurrence")
        targets[selected[0]] = ("reference", edit)
    notes = scope.get(inline_plan["note_host"], ())
    if len(notes) < inline_plan["note_index"]:
        raise LexicalPatchError("Reviewed inline note host absent")
    note = notes[inline_plan["note_index"]-1]
    inline = [n for n in note.iter() if n.tag == OSIS + inline_plan["old_local_tag"]]
    if len(inline) != inline_plan["expected_count"]:
        raise LexicalPatchError("Unexpected reviewed inline tag count")
    if sum(1 for n in root.iter() if n.tag == OSIS + inline_plan["old_local_tag"]) != len(inline):
        raise LexicalPatchError("Unreviewed inline tag elsewhere")
    for n in inline:
        if n in targets:
            raise LexicalPatchError("Overlapping markup change")
        targets[n] = ("inline", inline_plan)
    return targets


def patch_exact_original(original: bytes, link_plan: dict, inline_plan: dict):
    """Return research-only XML preserving all bytes except 11 attrs/4 tag tokens.

    The established semantic editors independently verify each host, SHA,
    original link, note text and target before this lexical representation.
    """
    if not isinstance(original, bytes) or len(original) > 128*1024*1024:
        raise LexicalPatchError("Unreasonable pinned source size")
    canonical_links, links_receipt = propose_links(original, link_plan)
    canonical_full, inline_receipt = propose_inline(canonical_links, inline_plan)
    root = _source_tree(original)
    semantic_expected = _state(_source_tree(canonical_full))
    selected = _element_targets(root, link_plan, inline_plan)
    nodes = [n for n in root.iter() if isinstance(n.tag, str)]
    parser = expat.ParserCreate(namespace_separator="}")
    patches = []
    stack = []
    started = [0]

    def fulltag(name):
        return "{" + name if "}" in name else name

    def begin(name, _attributes):
        i = started[0]
        started[0] += 1
        if i >= len(nodes):
            raise LexicalPatchError("Original byte parser has extra elements")
        node = nodes[i]
        if node.tag != fulltag(name):
            raise LexicalPatchError("Byte/XML tree element order differs")
        pos = parser.CurrentByteIndex
        stack.append(node)
        action = selected.get(node)
        if action is None:
            return
        old = original[pos:_end_of_tag(original, pos)]
        kind, edit = action
        if kind == "inline":
            if old != b"<" + edit["old_local_tag"].encode("ascii") + b">":
                raise LexicalPatchError("Unexpected original inline tag serialization")
            patches.append((pos, pos+len(old),
                            b'<seg type="' + edit["new_type"].encode("ascii") + b'">',
                            "inline_start"))
            return
        if node.tag != OSIS + "reference":
            raise LexicalPatchError("Wrong original reference kind")
        matches = list(ATTR.finditer(old))
        if len(matches) != 1:
            raise LexicalPatchError("Original reference attribute is ambiguous")
        match = matches[0]
        raw = match.group("value")
        if raw.decode("utf-8") != edit["old_target"]:
            raise LexicalPatchError("Unrecognized original escaped target")
        if edit["action"] == "replace_target":
            patches.append((pos+match.start("value"), pos+match.end("value"),
                            edit["new_target"].encode("utf-8"), "target_replace"))
        else:
            patches.append((pos+match.start(), pos+match.end(), b"", "absent_target_remove"))

    def end(name):
        if not stack:
            raise LexicalPatchError("Unbalanced original XML element")
        node = stack.pop()
        if node.tag != fulltag(name):
            raise LexicalPatchError("Closing element tag mismatch")
        action = selected.get(node)
        if action is None or action[0] != "inline":
            return
        pos = parser.CurrentByteIndex
        expected = b"</" + action[1]["old_local_tag"].encode("ascii") + b">"
        if original[pos:pos+len(expected)] != expected:
            raise LexicalPatchError("Unexpected original closing tag serialization")
        patches.append((pos, pos+len(expected), b"</seg>", "inline_end"))

    def deny(*_args):
        raise LexicalPatchError("Original DTD or external entity is not supported")

    parser.StartElementHandler = begin
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = deny
    parser.EntityDeclHandler = deny
    parser.ExternalEntityRefHandler = deny
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(original, True)
    except expat.ExpatError as exc:
        raise LexicalPatchError("Original lexical XML parse failed") from exc
    if stack or started[0] != len(nodes):
        raise LexicalPatchError("Original element stream incomplete")
    if len(patches) != 2*inline_receipt["edit_count"] + links_receipt["change_count"]:
        raise LexicalPatchError("Unexpected count of reviewed lexical replacements")
    patches.sort(key=lambda p: p[0])
    last = 0
    output = bytearray()
    for start, endpos, new, _kind in patches:
        if start < last or endpos > len(original):
            raise LexicalPatchError("Overlapping lexical source byte changes")
        output.extend(original[last:start])
        output.extend(new)
        last = endpos
    output.extend(original[last:])
    final = bytes(output)
    actual = _source_tree(final)
    if _state(actual) != semantic_expected:
        raise LexicalPatchError("Byte-level candidate does not match independently verified semantic changes")
    if "".join(root.itertext()) != "".join(actual.itertext()):
        raise LexicalPatchError("Original Scripture or note text was changed")
    categories = {}
    for _start, _end, _new, kind in patches:
        categories[kind] = categories.get(kind, 0) + 1
    if categories != {
        "inline_start": 2, "inline_end": 2,
        "target_replace": 8, "absent_target_remove": 3,
    }:
        # This is a *research-only* composition of the two explicit plans,
        # not a generic hard-coded translation-specific compiler rule.
        raise LexicalPatchError("Unexpected edition plan operation inventory")
    return final, {
        "schema_version": 1,
        "status": "source_byte_preserving_private_technical_repair_not_published",
        "publisher_original_sha256": sha256(original).hexdigest(),
        "candidate_sha256": sha256(final).hexdigest(),
        "approved_byte_span_changes_only": categories,
        "all_unedited_original_bytes_identical": True,
        "entire_authored_character_data_unchanged": True,
        "semantic_equivalence_to_existing_reviewed_repair_probes": True,
        "actual_sword_native_fidelity_tested": False,
        "editorially_approved": False,
        "released": False,
    }
