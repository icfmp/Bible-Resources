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
    expected = {
        "inline_start": inline_plan["expected_count"],
        "inline_end": inline_plan["expected_count"],
        "target_replace": sum(e["action"] == "replace_target"
                              for e in link_plan["edits"]),
        "absent_target_remove": sum(e["action"] == "disable_absent_target"
                                    for e in link_plan["edits"]),
    }
    if categories != {key: count for key, count in expected.items() if count}:
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



def patch_reviewed_osis_reference_attributes(
        original: bytes, plan: dict, native_verse_keys: set[str],
) -> tuple[bytes,dict]:
    """Byte-local, private-only source reference correction.

    Generic OSIS references, including commentary outside notes. Selection
    requires a source SHA, XML line, old attribute, original visible label
    SHA and enclosing authored book. Each proposed new target must resolve
    in an actual independently read native SWORD verse inventory.

    This is a technical *trial*, never a license to change a historical
    edition, publish its electronic text or trust a guessed authorial label.
    """
    import json
    if not isinstance(original,bytes) or not 100 <= len(original) <= 128*1024*1024:
        raise LexicalPatchError("Invalid original OSIS byte size")
    if (not isinstance(plan,dict) or set(plan)!={"schema_version","status",
             "source_sha256","edits"} or plan["schema_version"]!=1
            or plan["status"]!="research_only_private_not_release"
            or plan["source_sha256"]!=sha256(original).hexdigest()
            or not isinstance(plan["edits"],list)
            or not 1 <= len(plan["edits"]) <= 100):
        raise LexicalPatchError("Missing or unpinned private link-repair proposal")
    native_pattern=re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*\.[1-9]\d*")
    if (not isinstance(native_verse_keys,set) or not native_verse_keys
            or any(native_pattern.fullmatch(v) is None for v in native_verse_keys)):
        raise LexicalPatchError("Real verse inventory is not independently validated")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    try:
        root=etree.fromstring(original,parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise LexicalPatchError("Invalid original OSIS") from exc
    if root.tag != OSIS+"osis":
        raise LexicalPatchError("Unexpected original OSIS root")
    plans={}
    for edit in plan["edits"]:
        fields={"original_line","source_book","old_target","new_target",
                "visible_label_sha256","evidence_url"}
        if not isinstance(edit,dict) or set(edit)!=fields:
            raise LexicalPatchError("Malformed source-bound reference correction")
        line=edit["original_line"]
        old=edit["old_target"]
        new=edit["new_target"]
        book=edit["source_book"]
        if (type(line) is not int or line < 1 or not isinstance(old,str)
                or not old or len(old)>300 or not isinstance(new,str)
                or new==old or not isinstance(book,str) or len(book)>20
                or not isinstance(edit["evidence_url"],str)
                or not edit["evidence_url"].startswith("https://")
                or not re.fullmatch(r"[0-9a-f]{64}",
                                    edit["visible_label_sha256"])):
            raise LexicalPatchError("Invalid original-target identity or evidence")
        targets=new.split()
        if (not targets or len(targets)>100
                or any(native_pattern.fullmatch(x) is None or
                       x not in native_verse_keys for x in targets)):
            raise LexicalPatchError("Proposed link contains an unindexed SWORD verse")
        identity=(line,book,old)
        if identity in plans:
            raise LexicalPatchError("Duplicate source link review anchor")
        plans[identity]=edit
    selected={}
    for node in root.iter(OSIS+"reference"):
        old=node.get("osisRef")
        if not old:
            continue
        book=next((a.get("osisID") for a in node.iterancestors()
                   if a.tag==OSIS+"div" and a.get("type")=="book"),None)
        key=(node.sourceline,book,old)
        if key not in plans:
            continue
        if key in selected.values():
            raise LexicalPatchError("Multiple references match one source anchor")
        label="".join(node.itertext()).strip()
        if sha256(label.encode("utf-8")).hexdigest()!=plans[key]["visible_label_sha256"]:
            raise LexicalPatchError("Visible printed source label does not match approval proof")
        selected[node]=key
    if len(selected)!=len(plans):
        raise LexicalPatchError("One or more reviewed original links were not found")
    elements=[e for e in root.iter() if isinstance(e.tag,str)]
    exp=expat.ParserCreate(namespace_separator="}")
    numbered=[0]
    patch=[]
    def full(name):
        return "{"+name if "}" in name else name
    def begin(name,_attrs):
        offset=numbered[0]
        numbered[0]+=1
        if offset >= len(elements) or elements[offset].tag!=full(name):
            raise LexicalPatchError("XML event order differs from original byte stream")
        node=elements[offset]
        if node not in selected:
            return
        opening_start=exp.CurrentByteIndex
        original_tag=original[opening_start:_end_of_tag(original,opening_start)]
        refs=list(ATTR.finditer(original_tag))
        if len(refs)!=1:
            raise LexicalPatchError("Reviewed source reference attribute ambiguous")
        match=refs[0]
        identity=selected[node]
        try:
            observed=match.group("value").decode("utf-8")
        except UnicodeError as exc:
            raise LexicalPatchError("Malformed original reference attribute") from exc
        if observed!=identity[2]:
            raise LexicalPatchError("Original source lexeme has unexpected byte serialization")
        patch.append((opening_start+match.start("value"),
                      opening_start+match.end("value"),
                      plans[identity]["new_target"].encode("ascii"),node))
    def deny(*_args):
        raise LexicalPatchError("DTD/entities prohibited in link patch")
    exp.StartElementHandler=begin
    exp.StartDoctypeDeclHandler=deny
    exp.EntityDeclHandler=deny
    exp.ExternalEntityRefHandler=lambda *_args: 0
    try:
        exp.Parse(original,True)
    except expat.ExpatError as exc:
        raise LexicalPatchError("Original lexical OSIS is not parsable") from exc
    if numbered[0]!=len(elements) or len(patch)!=len(plans):
        raise LexicalPatchError("Reviewed source link spans incomplete")
    position=0
    output=bytearray()
    for start,end,replacement,_ in sorted(patch,key=lambda r:r[0]):
        if start<position or start>=end or end>len(original):
            raise LexicalPatchError("Overlapping original source byte spans")
        output.extend(original[position:start])
        output.extend(replacement)
        position=end
    output.extend(original[position:])
    cleaned=bytes(output)
    try:
        candidate=etree.fromstring(cleaned,parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise LexicalPatchError("Edited OSIS failed lexical reparse") from exc
    before=[n for n in root.iter() if isinstance(n.tag,str)]
    after=[n for n in candidate.iter() if isinstance(n.tag,str)]
    if len(before)!=len(after):
        raise LexicalPatchError("Link repair altered source XML element count")
    edit_by_index={before.index(n):plans[key]["new_target"]
                   for n,key in selected.items()}
    for i,(old,new) in enumerate(zip(before,after)):
        if old.tag!=new.tag or old.text!=new.text or old.tail!=new.tail:
            raise LexicalPatchError("Link repair changed source text or markup")
        original_attrs=dict(old.attrib)
        expected=dict(original_attrs)
        if i in edit_by_index:
            expected["osisRef"]=edit_by_index[i]
        if dict(new.attrib)!=expected:
            raise LexicalPatchError("Unexpected non-link attribute change")
    return cleaned,{
        "schema_version":1,
        "status":"PRIVATE_REVIEWED_MACHINE_LINK_PREVIEW_NOT_APPROVED_FOR_RELEASE",
        "original_sha256":sha256(original).hexdigest(),
        "private_candidate_sha256":sha256(cleaned).hexdigest(),
        "exact_reference_attribute_only_changes":len(patch),
        "entire_original_commentary_characters_unchanged":True,
        "all_other_original_xml_elements_and_attributes_unchanged":True,
        "new_verse_targets_present_in_real_native_index":True,
        "editorially_authorized":False,
        "published":False,
    }
