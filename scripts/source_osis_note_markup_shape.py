#!/usr/bin/env python3
"""Inspect original OSIS note markup shape without emitting authorial prose.

Diagnostic only: this is not a converter, source patch, HTML inference, or
editorial validation. The exact original stays immutable in private storage.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree

from repair_osis_note_links import _source_note_nodes
from source_osis_inventory import _source_tree

MAX_SOURCE = 128 * 1024 * 1024
REF = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")
TAG = re.compile(r"[a-z][A-Za-z0-9_-]{0,39}\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")


class SourceMarkupShapeError(ValueError):
    pass


def _text_shape(value):
    return {
        "codepoint_count": len(value or ""),
        "nonspace_codepoint_count": sum(not c.isspace() for c in value or ""),
        "sha256": sha256((value or "").encode("utf-8")).hexdigest(),
    }


def _local(element):
    return etree.QName(element).localname


def inspect_markup(source: bytes, *, expected_sha256: str, host: str,
                   note_index: int, local_tag: str) -> dict:
    if (not isinstance(source, bytes) or not 128 <= len(source) <= MAX_SOURCE or
            not isinstance(expected_sha256, str) or not HEX.fullmatch(expected_sha256) or
            sha256(source).hexdigest() != expected_sha256):
        raise SourceMarkupShapeError("Unpinned source bytes or unreasonable input")
    if (not isinstance(host, str) or not REF.fullmatch(host) or
            type(note_index) is not int or not 1 <= note_index <= 30 or
            not isinstance(local_tag, str) or not TAG.fullmatch(local_tag)):
        raise SourceMarkupShapeError("Unreviewed host, note ordinal, or tag")
    root = _source_tree(source)
    notes = _source_note_nodes(root).get(host, ())
    if note_index > len(notes):
        raise SourceMarkupShapeError("Original authorial note host/ordinal absent")
    note = notes[note_index - 1]
    matched = [n for n in note.iter() if isinstance(n.tag, str)
               and _local(n) == local_tag]
    if not 1 <= len(matched) <= 30:
        raise SourceMarkupShapeError("Expected bounded original source markup absent")
    global_count = sum(1 for n in root.iter()
                       if isinstance(n.tag, str) and _local(n) == local_tag)
    shapes = []
    for n in matched:
        p = n.getparent()
        siblings = list(p)
        pos = siblings.index(n)
        shapes.append({
            "local_tag": _local(n),
            "namespace": etree.QName(n).namespace or "",
            "parent_local_tag": _local(p),
            "position_in_parent": pos,
            "previous_sibling_tag": _local(siblings[pos-1]) if pos else None,
            "next_sibling_tag": _local(siblings[pos+1]) if pos+1 < len(siblings) else None,
            "attribute_keys": sorted(n.attrib),
            "attribute_value_lengths": {key: len(value) for key, value in sorted(n.attrib.items())},
            "attribute_value_hashes": {
                key: sha256(value.encode("utf-8")).hexdigest()
                for key, value in sorted(n.attrib.items())
            },
            "direct_text": _text_shape(n.text),
            "following_tail": _text_shape(n.tail),
            "child_local_tags": [_local(child) for child in n
                                 if isinstance(child.tag, str)],
            "descendant_count": sum(1 for _ in n.iter())-1,
        })
    return {
        "schema_version": 1,
        "status": "original_source_unknown_note_tag_shape_only",
        "source_sha256": expected_sha256,
        "host": host,
        "note_index": note_index,
        "tag": local_tag,
        "occurrences_in_note": len(matched),
        "occurrences_in_whole_source": global_count,
        "bounded_shapes": shapes,
        "scripture_and_note_prose_exposed": False,
        "source_or_note_modified": False,
        "editorial_meaning_confirmed": False,
        "technical_repair_approved": False,
        "release_approved": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--note-index", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if (args.source.is_symlink() or not args.source.is_file() or
            args.source.stat().st_size > MAX_SOURCE or
            args.report.exists() or args.report.is_symlink() or
            not args.report.parent.is_dir() or
            args.source.resolve() == args.report.resolve()):
        parser.error("Unsafe input or output")
    report = inspect_markup(args.source.read_bytes(), expected_sha256=args.sha256,
                            host=args.host, note_index=args.note_index,
                            local_tag=args.tag)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print("Exact-source note tag structure inspected without Bible content")


if __name__ == "__main__":
    main()
