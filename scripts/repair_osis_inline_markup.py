#!/usr/bin/env python3
"""Research-only repair of explicitly pinned invalid *inline* OSIS tag names.

No Scripture/notes/text/whitespace is edited. Input source must be an exact
SHA-256-pinned, privately assembled research candidate, and the original
publisher SHA must be recorded separately. No source or public release writes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree

from repair_osis_note_links import _source_note_nodes
from source_osis_inventory import OSIS, _source_tree, source_inventory

HEX = re.compile(r"[a-f0-9]{64}\Z")
REF = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")
TAG = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
MAX_XML = 128 * 1024 * 1024


class InlineMarkupRepairError(ValueError):
    """Unsafe, stale, or unreviewed correction."""


def _hash(value: bytes) -> str:
    return sha256(value).hexdigest()


def _state(root):
    return [(n.tag, tuple(sorted(n.attrib.items())), n.text, n.tail)
            for n in root.iter()]


def _require_plan(plan: dict, source: bytes) -> None:
    expected = {
        "schema_version", "purpose", "publisher_original_sha256",
        "private_input_sha256", "resource_id", "note_host", "note_index",
        "old_local_tag", "new_local_tag", "new_type", "expected_count",
        "old_direct_text_sha256", "old_tail_sha256", "evidence_url",
        "reason",
    }
    if (not isinstance(plan, dict) or set(plan) != expected
            or plan["schema_version"] != 1
            or plan["purpose"] != "private_research_not_approved"
            or not isinstance(plan["publisher_original_sha256"], str)
            or not HEX.fullmatch(plan["publisher_original_sha256"])
            or not isinstance(plan["private_input_sha256"], str)
            or not HEX.fullmatch(plan["private_input_sha256"])
            or plan["private_input_sha256"] != _hash(source)
            or not isinstance(plan["resource_id"], str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{1,62}", plan["resource_id"])
            or not isinstance(plan["note_host"], str)
            or not REF.fullmatch(plan["note_host"])
            or type(plan["note_index"]) is not int
            or not 1 <= plan["note_index"] <= 30
            or type(plan["expected_count"]) is not int
            or not 1 <= plan["expected_count"] <= 30
            or not isinstance(plan["old_local_tag"], str)
            or not TAG.fullmatch(plan["old_local_tag"])
            or not isinstance(plan["new_local_tag"], str)
            or plan["new_local_tag"] != "seg"
            or not isinstance(plan["new_type"], str)
            or not re.fullmatch(r"x-[a-z][a-z0-9-]{1,40}", plan["new_type"])
            or not isinstance(plan["reason"], str)
            or len(plan["reason"].strip()) < 20
            or not isinstance(plan["evidence_url"], str)
            or not re.fullmatch(r"https://[^\s/]+/\S+", plan["evidence_url"])):
        raise InlineMarkupRepairError("Malformed or stale research-only inline correction plan")
    for field in ("old_direct_text_sha256", "old_tail_sha256"):
        values = plan[field]
        if (not isinstance(values, list)
                or len(values) != plan["expected_count"]
                or any(not isinstance(v, str) or not HEX.fullmatch(v) for v in values)):
            raise InlineMarkupRepairError("Missing expected original element fingerprint")


def propose(source: bytes, plan: dict) -> tuple[bytes, dict]:
    if not isinstance(source, bytes) or not 128 <= len(source) <= MAX_XML:
        raise InlineMarkupRepairError("Unsupported OSIS source size")
    _require_plan(plan, source)
    root = _source_tree(source)
    orig_keys, orig_meta = source_inventory(source)
    notes = _source_note_nodes(root).get(plan["note_host"], ())
    if len(notes) < plan["note_index"]:
        raise InlineMarkupRepairError("Exact original note host/ordinal not found")
    note = notes[plan["note_index"]-1]
    before = _state(root)
    old_tag = OSIS + plan["old_local_tag"]
    selected = [n for n in note.iter() if n.tag == old_tag]
    total = [n for n in root.iter() if n.tag == old_tag]
    if len(selected) != plan["expected_count"] or len(total) != len(selected):
        raise InlineMarkupRepairError("Old tag has unexpected occurrences outside reviewed note")
    positions = {i for i, n in enumerate(root.iter()) if n in selected}
    if len(positions) != plan["expected_count"]:
        raise InlineMarkupRepairError("Original markup is ambiguous")
    for i, node in enumerate(selected):
        if (node.attrib or len(node) != 0
                or _hash((node.text or "").encode("utf-8")) != plan["old_direct_text_sha256"][i]
                or _hash((node.tail or "").encode("utf-8")) != plan["old_tail_sha256"][i]):
            raise InlineMarkupRepairError("Review-fingerprinted source markup changed")
        node.tag = OSIS + plan["new_local_tag"]
        node.set("type", plan["new_type"])
    after = _state(root)
    if len(before) != len(after):
        raise InlineMarkupRepairError("Markup node inventory changed")
    for index, (old, new) in enumerate(zip(before, after)):
        if old[2:] != new[2:]:
            raise InlineMarkupRepairError("Original text or XML whitespace changed")
        if index in positions:
            if (old[0] != old_tag or old[1] or
                    new[0] != OSIS + plan["new_local_tag"] or
                    new[1] != (("type", plan["new_type"]),)):
                raise InlineMarkupRepairError("Unexpected inline edit")
        elif old[:2] != new[:2]:
            raise InlineMarkupRepairError("Unapproved markup/attribute changed")
    output = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
    verified = _source_tree(output)
    if _state(verified) != after:
        raise InlineMarkupRepairError("Private output serialization changed content")
    final_keys, final_meta = source_inventory(output)
    if orig_keys != final_keys or orig_meta["source_verse_count"] != final_meta["source_verse_count"]:
        raise InlineMarkupRepairError("Original verse inventory changed")
    if len(_source_note_nodes(verified).get(plan["note_host"], ())) != len(notes):
        raise InlineMarkupRepairError("Original note host/ordinal inventory changed")
    return output, {
        "schema_version": 1,
        "status": "private_technical_inline_repair_proposed_not_approved",
        "resource_id": plan["resource_id"],
        "publisher_original_sha256": plan["publisher_original_sha256"],
        "private_input_sha256": _hash(source),
        "private_output_sha256": _hash(output),
        "note_host": plan["note_host"],
        "note_index": plan["note_index"],
        "edit_count": len(selected),
        "old_tag": plan["old_local_tag"],
        "new_tag": plan["new_local_tag"],
        "new_type": plan["new_type"],
        "all_element_text_and_tails_byte_character_equal": True,
        "all_unreviewed_attributes_and_element_tags_equal": True,
        "all_verse_keys_and_note_ordinals_preserved": True,
        "source_original_overwritten": False,
        "schema_validation_tested": False,
        "native_sword_compiled_and_tested": False,
        "editorial_approval": False,
        "released": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "plan", "output", "report"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    paths = (args.source, args.plan, args.output, args.report)
    if (len({x.resolve() for x in paths}) != 4
            or any(x.is_symlink() for x in paths)
            or any(x.exists() for x in paths[2:])
            or any(not x.is_file() for x in paths[:2])
            or not args.output.parent.is_dir()
            or not args.report.parent.is_dir()
            or args.source.stat().st_size > MAX_XML
            or args.plan.stat().st_size > 1024 * 1024):
        p.error("Unsafe input, output, or alias")
    output, receipt = propose(
        args.source.read_bytes(), json.loads(args.plan.read_text(encoding="utf-8")))
    args.output.write_bytes(output)
    args.report.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print("Private inline repair checked; no authored material released")


if __name__ == "__main__":
    main()
