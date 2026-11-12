#!/usr/bin/env python3
"""Private, source-SHA-bound OSIS note-link repair probe. NOT a release.

Only source-identified reference@osisRef may change; all Scripture, note
content, XML text and editorial boundaries must remain exactly unchanged.
A proposal is not editorial approval. Never overwrite the original.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree

from publisher_osis_usfx_parity import original_osis_verses_and_notes
from source_osis_inventory import OSIS, _source_tree, source_inventory
from source_native_osis_target_addressability import _classify_one

HEX = re.compile(r"[a-f0-9]{64}\Z")
KEY = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")
INDEXED = frozenset(("indexed_verse", "indexed_chapter", "indexed_book",
                      "indexed_ordered_full_range"))


class LinkRepairError(ValueError):
    """Unreviewed repair or source scope; never guess a destination."""


def _source_note_nodes(root):
    """Map original source note host+ordinal across OSIS verse milestones."""
    notes = {}
    books = root.findall(".//" + OSIS + "div[@type='book']")
    if not 1 <= len(books) <= 250:
        raise LinkRepairError("Unrecognized book inventory")
    for book in books:
        active = None

        def walk(node, depth=0):
            nonlocal active
            if depth > 256:
                raise LinkRepairError("Unsafe XML depth")
            if node.tag == OSIS + "note":
                if active is not None:
                    notes.setdefault(active, []).append(node)
                return
            if node.tag == OSIS + "verse":
                start, end, key = node.get("sID"), node.get("eID"), node.get("osisID")
                if end:
                    if end != active or start or key:
                        raise LinkRepairError("Invalid authorial verse closing")
                    active = None
                    return
                if active is not None or not isinstance(key, str) or not KEY.fullmatch(key):
                    raise LinkRepairError("Invalid authorial verse opening")
                if start and start != key:
                    raise LinkRepairError("Invalid authorial verse milestone")
                active = key
                if not start:
                    for child in node:
                        walk(child, depth + 1)
                    active = None
                return
            for child in node:
                walk(child, depth + 1)
        walk(book)
        if active is not None:
            raise LinkRepairError("Unclosed authorial verse scope")
    return notes


def _index(root):
    keys, _ = source_inventory(etree.tostring(root, encoding="UTF-8"))
    ranks = {key: n for n, key in enumerate(keys.splitlines())}
    books, chapters = {}, {}
    for key, n in ranks.items():
        book, chapter, _ = key.split(".")
        for name, lookup in ((book, books), (book + "." + chapter, chapters)):
            if name not in lookup:
                lookup[name] = (n, n)
            else:
                lookup[name] = (lookup[name][0], n)
    return ranks, chapters, books


def _signature(root):
    """Exact original element order, all text/tails and all non-link attrs."""
    return tuple((node.tag, node.text, node.tail,
                  tuple(sorted((k, v) for k, v in node.attrib.items()
                               if not (node.tag == OSIS + "reference" and k == "osisRef"))))
                 for node in root.iter())


def _validate_plan(plan, source):
    if (not isinstance(plan, dict) or set(plan) != {
            "schema_version", "purpose", "resource_id", "source_sha256", "edits"}
            or plan["schema_version"] != 1
            or plan["purpose"] != "research_only_not_approved"
            or not isinstance(plan["source_sha256"], str)
            or not HEX.fullmatch(plan["source_sha256"])
            or plan["source_sha256"] != sha256(source).hexdigest()
            or not isinstance(plan["resource_id"], str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", plan["resource_id"])
            or not isinstance(plan["edits"], list)
            or not 1 <= len(plan["edits"]) <= 100):
        raise LinkRepairError("Plan missing pinned original or research-only status")
    seen = set()
    for edit in plan["edits"]:
        if (not isinstance(edit, dict)
                or set(edit) != {"note_host", "note_index", "old_target", "new_target",
                                 "action", "reason", "evidence_url"}
                or not isinstance(edit["note_host"], str)
                or not KEY.fullmatch(edit["note_host"])
                or type(edit["note_index"]) is not int
                or not 1 <= edit["note_index"] <= 30
                or not isinstance(edit["old_target"], str)
                or not 1 <= len(edit["old_target"]) <= 1024
                or edit["action"] not in {"replace_target", "disable_absent_target"}
                or not isinstance(edit["reason"], str) or len(edit["reason"].strip()) < 16
                or not isinstance(edit["evidence_url"], str)
                or not re.fullmatch(r"https://[^\s/]+/\S+", edit["evidence_url"])):
            raise LinkRepairError("Unreviewed host, target, action or evidence")
        if (edit["action"] == "disable_absent_target" and edit["new_target"] is not None
                or edit["action"] == "replace_target" and
                (not isinstance(edit["new_target"], str) or
                 not edit["new_target"] or edit["new_target"] == edit["old_target"])):
            raise LinkRepairError("Malformed technical target operation")
        ident = (edit["note_host"], edit["note_index"], edit["old_target"])
        if ident in seen:
            raise LinkRepairError("Duplicated technical repair")
        seen.add(ident)


def propose(source: bytes, plan: dict) -> tuple[bytes, dict]:
    if not isinstance(source, bytes) or not 128 <= len(source) <= 128*1024*1024:
        raise LinkRepairError("Invalid original OSIS length")
    _validate_plan(plan, source)
    root = _source_tree(source)
    _verses, original_notes, _metadata = original_osis_verses_and_notes(source)
    mapped_notes = _source_note_nodes(root)
    if (set(mapped_notes) != {k for k, v in original_notes.items() if v}
            or any(len(mapped_notes.get(key, [])) != len(v)
                   for key, v in original_notes.items())):
        raise LinkRepairError("Independent source-note host inventories disagree")
    before = _signature(root)
    ranks, chapters, books = _index(root)
    edited = set()
    changes = []
    for edit in plan["edits"]:
        note_set = mapped_notes.get(edit["note_host"], ())
        if len(note_set) < edit["note_index"]:
            raise LinkRepairError("Original note host/ordinal does not exist")
        note = note_set[edit["note_index"]-1]
        candidates = [n for n in note.iterdescendants(OSIS + "reference")
                      if n.get("osisRef") == edit["old_target"]]
        if len(candidates) != 1:
            raise LinkRepairError("Expected original link must occur exactly once in note")
        node = candidates[0]
        anchor = root.getroottree().getpath(node)
        if anchor in edited:
            raise LinkRepairError("Overlapping corrections")
        edited.add(anchor)
        old_kind, _, _ = _classify_one(edit["old_target"], ranks, chapters, books)
        if edit["action"] == "replace_target":
            components = edit["new_target"].split()
            if not 1 <= len(components) <= 100 or any(
                    _classify_one(token, ranks, chapters, books)[0] not in INDEXED
                    for token in components):
                raise LinkRepairError("Proposed destination is not addressable")
            node.set("osisRef", edit["new_target"])
        else:
            if old_kind != "unindexed_verse_existing_book":
                raise LinkRepairError("Cannot disable an indexed or unknown target")
            del node.attrib["osisRef"]
        changes.append({"note_host": edit["note_host"],
                        "note_index": edit["note_index"],
                        "action": edit["action"],
                        "original_target_shape": old_kind,
                        "corrected_target_index_verified":
                            edit["action"] == "replace_target",
                        "editorial_signoff": False})
    if _signature(root) != before:
        raise LinkRepairError("Original prose, XML whitespace or markup changed")
    output = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
    verified = _source_tree(output)
    if _signature(verified) != before:
        raise LinkRepairError("Serialized proposal changed original content")
    prior = [(n.tag, n.get("osisRef")) for n in _source_tree(source).iter()]
    after = [(n.tag, n.get("osisRef")) for n in verified.iter()]
    changed = [i for i, (a, b) in enumerate(zip(prior, after)) if a != b]
    if (len(prior) != len(after) or len(changed) != len(changes)
            or any(prior[i][0] != OSIS + "reference"
                   or after[i][0] != OSIS + "reference" for i in changed)):
        raise LinkRepairError("Unexpected changed source attributes")
    _after_verses, afterward, _ = original_osis_verses_and_notes(output)
    if (set(afterward) != set(original_notes)
            or any(len(v) != len(afterward[key])
                   for key, v in original_notes.items())):
        raise LinkRepairError("Authorial verse or note count changed")
    return output, {
        "schema_version": 1,
        "status": "private_unapproved_source_note_link_probe",
        "resource_id": plan["resource_id"],
        "original_sha256": sha256(source).hexdigest(),
        "private_research_output_sha256": sha256(output).hexdigest(),
        "change_count": len(changes),
        "bounded_changes": changes,
        "all_original_text_and_whitespace_characters_preserved": True,
        "all_original_element_tags_and_other_attributes_preserved": True,
        "all_verse_keys_and_note_ordinals_preserved": True,
        "original_overwritten": False,
        "scripture_or_note_text_uploaded": False,
        "real_reader_navigation_tested": False,
        "editorial_or_release_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "plan", "output", "receipt"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    paths = (args.source, args.plan, args.output, args.receipt)
    if (len({p.resolve() for p in paths}) != 4
            or any(p.is_symlink() for p in paths)
            or any(p.exists() for p in paths[2:])
            or any(not p.is_file() for p in paths[:2])
            or args.source.stat().st_size > 128 * 1024 * 1024
            or args.plan.stat().st_size > 1024 * 1024):
        parser.error("Unsafe, aliased or previously existing input/output")
    output, result = propose(args.source.read_bytes(),
                             json.loads(args.plan.read_text(encoding="utf-8")))
    args.output.write_bytes(output)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print("Private original-note link proposal checked; no Scripture exposed or released")


if __name__ == "__main__":
    main()
