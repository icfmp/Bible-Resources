#!/usr/bin/env python3
"""Render authored references to intentionally absent verses as plain note text.

Private, plan-driven lexical overlay on the already reviewed corrected OSIS.
The publisher source stays immutable. No note characters, tails, Scripture,
caller labels, verse keys, or unrelated XML bytes may change. The purpose is
to remove misleading link styling in independent readers, not to infer any
missing verse or approve a public edition.
"""
from __future__ import annotations

from hashlib import sha256
import re
from xml.parsers import expat

from repair_osis_note_links import _source_note_nodes
from repair_osis_source_bytes import _end_of_tag
from source_osis_inventory import OSIS, _source_tree


class UnlinkedLabelError(ValueError):
    """Source/plan mismatch or an unsafe reference conversion."""


START = re.compile(rb"<reference\s*>")
PLAIN_START = b'<seg type="x-unlinked-reference">'
PLAIN_END = b"</seg>"


def render_absent_references_plain(
    publisher_original: bytes, repaired: bytes, link_plan: dict
) -> tuple[bytes, dict]:
    """Replace only plan-approved unaddressable reference element wrappers.

    The preceding repair layer has already removed the old nonexistent
    osisRef. That alone is insufficient in some readers: an unlinked OSIS
    <reference> may still look clickable. Use a typed ordinary OSIS segment.
    """
    if (not isinstance(publisher_original, bytes)
            or not isinstance(repaired, bytes)
            or len(repaired) > 128 * 1024 * 1024
            or not isinstance(link_plan, dict)
            or link_plan.get("purpose") != "research_only_not_approved"
            or link_plan.get("source_sha256") != sha256(publisher_original).hexdigest()):
        raise UnlinkedLabelError("Unpinned original source or private corrected candidate")
    edits = [item for item in link_plan.get("edits", [])
             if item.get("action") == "disable_absent_target"]
    if not 1 <= len(edits) <= 100:
        raise UnlinkedLabelError("No bounded approved omitted-verse label cases")
    original_tree = _source_tree(publisher_original)
    corrected_tree = _source_tree(repaired)
    original_notes = _source_note_nodes(original_tree)
    corrected_notes = _source_note_nodes(corrected_tree)
    selected = {}
    for edit in edits:
        host, ordinal, old_target = (
            edit["note_host"], edit["note_index"], edit["old_target"])
        old_items = original_notes.get(host, [])
        new_items = corrected_notes.get(host, [])
        if (type(ordinal) is not int or ordinal < 1
                or ordinal > len(old_items) or ordinal > len(new_items)):
            raise UnlinkedLabelError("Authorial note host/ordinal changed")
        old_note = old_items[ordinal - 1]
        new_note = new_items[ordinal - 1]
        old_refs = list(old_note.iterdescendants(OSIS + "reference"))
        new_refs = list(new_note.iterdescendants(OSIS + "reference"))
        old_hits = [i for i, node in enumerate(old_refs)
                    if node.get("osisRef") == old_target]
        if (len(old_hits) != 1 or len(old_refs) != len(new_refs)
                or "".join(old_note.itertext()) != "".join(new_note.itertext())):
            raise UnlinkedLabelError("Note target/reference inventory differs")
        old_ref = old_refs[old_hits[0]]
        fixed_ref = new_refs[old_hits[0]]
        if (dict(old_ref.attrib) != {"osisRef": old_target}
                or fixed_ref.attrib or len(old_ref) or len(fixed_ref)
                or (old_ref.text, old_ref.tail) != (fixed_ref.text, fixed_ref.tail)
                or not (old_ref.text or "").strip()):
            raise UnlinkedLabelError("Unsafe or ambiguous absent-verse link wrapper")
        if fixed_ref in selected:
            raise UnlinkedLabelError("Duplicate omitted-verse link wrapper")
        selected[fixed_ref] = (host, ordinal)
    nodes = [node for node in corrected_tree.iter() if isinstance(node.tag, str)]
    patches, stack = [], []
    index = [0]
    seen = set()
    parser = expat.ParserCreate(namespace_separator="}")

    def qualified(name):
        return "{" + name if "}" in name else name

    def begin(name, _attrs):
        i = index[0]
        index[0] += 1
        if i >= len(nodes) or nodes[i].tag != qualified(name):
            raise UnlinkedLabelError("Lexical and parsed XML element orders differ")
        node = nodes[i]
        stack.append(node)
        if node not in selected:
            return
        offset = parser.CurrentByteIndex
        tag_bytes = repaired[offset:_end_of_tag(repaired, offset)]
        if not START.fullmatch(tag_bytes):
            raise UnlinkedLabelError("Nonempty original unlinked reference opening tag")
        patches.append((offset, offset + len(tag_bytes),
                        PLAIN_START, "plain_start"))
        seen.add(node)

    def end(name):
        if not stack:
            raise UnlinkedLabelError("Unbalanced document scope")
        node = stack.pop()
        if node.tag != qualified(name):
            raise UnlinkedLabelError("Mismatched XML closing tag")
        if node not in selected:
            return
        offset = parser.CurrentByteIndex
        closing = b"</reference>"
        if repaired[offset:offset + len(closing)] != closing:
            raise UnlinkedLabelError("Unexpected old reference closing serialization")
        patches.append((offset, offset + len(closing),
                        PLAIN_END, "plain_end"))

    def deny(*_args):
        raise UnlinkedLabelError("DTD or external entity not permitted")

    parser.StartElementHandler = begin
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = deny
    parser.EntityDeclHandler = deny
    parser.ExternalEntityRefHandler = deny
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(repaired, True)
    except expat.ExpatError as exc:
        raise UnlinkedLabelError("Corrected candidate XML parse failed") from exc
    if (stack or index[0] != len(nodes) or len(seen) != len(edits)
            or len(patches) != 2 * len(edits)):
        raise UnlinkedLabelError("Missing or duplicate exact XML element conversion")
    patches.sort(key=lambda x: x[0])
    current, result = 0, bytearray()
    for start, end, replacement, _kind in patches:
        if start < current or end > len(repaired):
            raise UnlinkedLabelError("Overlapping lexical replacement")
        result.extend(repaired[current:start])
        result.extend(replacement)
        current = end
    result.extend(repaired[current:])
    final = bytes(result)
    after_tree = _source_tree(final)
    prior_nodes = [node for node in corrected_tree.iter() if isinstance(node.tag, str)]
    final_nodes = [node for node in after_tree.iter() if isinstance(node.tag, str)]
    if len(prior_nodes) != len(final_nodes):
        raise UnlinkedLabelError("Any XML element loss is forbidden")
    for old, new in zip(prior_nodes, final_nodes):
        if (old.text, old.tail) != (new.text, new.tail):
            raise UnlinkedLabelError("Any authored note or Scripture character changed")
        if old in selected:
            if (new.tag != OSIS + "seg"
                    or dict(new.attrib) != {"type": "x-unlinked-reference"}):
                raise UnlinkedLabelError("Omitted label was not converted into plain segment")
        elif old.tag != new.tag or dict(old.attrib) != dict(new.attrib):
            raise UnlinkedLabelError("Unexpected unrelated markup or attribute change")
    if ("".join(original_tree.itertext()) != "".join(after_tree.itertext())):
        raise UnlinkedLabelError("Original publisher character content changed")
    return final, {
        "status": "private_unlinked_omitted_verse_labels_not_released",
        "original_publisher_sha256": sha256(publisher_original).hexdigest(),
        "prior_research_candidate_sha256": sha256(repaired).hexdigest(),
        "new_research_candidate_sha256": sha256(final).hexdigest(),
        "explicit_plain_label_count": len(edits),
        "unrelated_original_bytes_identical": True,
        "all_original_characters_preserved": True,
        "original_absent_verse_keys_not_fabricated": True,
        "independent_reader_plain_style_verified": False,
        "editorial_or_release_approved": False,
    }
