#!/usr/bin/env python3
"""Apply owner-reviewed, source-pinned OSIS reference repairs to a separate candidate.

Original publisher USFX, approved cleaned OSIS and published binaries are NEVER
written. Every change is an exact, reviewed reference-node byte patch. Intro
prose stays verbatim except independently documented source-heading typos.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape

from lxml import etree
from normalize_bible_references import (
    OSIS, OPEN_REFERENCE, ReviewError, _bytes, _parse,
    _complete_printed_destinations,
)

MAX_SOURCE = 128 * 1024 * 1024


def _label(value: str) -> str:
    return " ".join(value.split())


def _source_book(node):
    for ancestor in node.iterancestors():
        if ancestor.tag == OSIS + "div" and ancestor.get("type") == "book":
            return ancestor.get("osisID")
    raise ReviewError("Reference outside identifiable source book")


def _source_origin(note):
    anchors = [n for n in note if n.tag == OSIS + "reference"
               and n.get("type") == "annotateRef"
               and n.get("subType") == "x-origin"]
    if len(anchors) != 1:
        raise ReviewError("Source note does not have one original verse anchor")
    return _label("".join(anchors[0].itertext()))


def _require_verses(target: str, verse_ids: set[str]) -> None:
    if not isinstance(target, str) or not target or len(target) > 4096:
        raise ReviewError("Invalid OSIS target")
    for token in target.split():
        ends = token.split("-")
        if len(ends) not in (1, 2) or any(x not in verse_ids for x in ends):
            raise ReviewError("Missing actual source verse: " + token)
        if len(ends) == 2:
            a, b = ends
            if (a.rsplit(".", 1)[0] != b.rsplit(".", 1)[0] or
                    int(a.rsplit(".", 1)[1]) > int(b.rsplit(".", 1)[1])):
                raise ReviewError("Unsupported or reversed source range")


def apply_plan(original: bytes, plan: dict, aliases: dict,
               original_usfx_sha256: str) -> tuple[bytes, dict]:
    if (plan.get("schema_version") != 1
            or plan.get("status") != "owner_authorized_isolated_editorial_candidate"
            or plan.get("approved_for_candidate_only") is not True
            or plan.get("publication_or_master_replacement_approved") is not False
            or plan.get("input_sha256") != sha256(original).hexdigest()
            or plan.get("original_usfx_zip_sha256") != original_usfx_sha256):
        raise ReviewError("Stale input or unapproved publisher/editorial source change")
    edits = plan.get("edits")
    if not isinstance(edits, list) or not 1 <= len(edits) <= 100:
        raise ReviewError("Reviewed source-correction plan is empty or excessive")
    root = _parse(original)
    if root.tag != OSIS + "osis":
        raise ReviewError("Expected canonical OSIS")
    refs = list(root.iter(OSIS + "reference"))
    openers = list(OPEN_REFERENCE.finditer(original))
    if len(refs) != len(openers):
        raise ReviewError("Serialized reference count differs from parsed XML")
    verse_ids = {token for v in root.iter(OSIS + "verse")
                 for token in (v.get("osisID") or "").split()}
    patches = []
    seen = set()
    kinds = {"cross_reference_fragment": 0,
             "introduction_text_correction": 0,
             "introduction_link_split": 0}
    for edit in edits:
        if not isinstance(edit, dict) or edit.get("type") not in kinds:
            raise ReviewError("Unknown or malformed editorial edit")
        index = edit.get("reference_index")
        if (type(index) is not int or not 0 <= index < len(refs)
                or index in seen):
            raise ReviewError("Duplicate or invalid anchored original reference index")
        seen.add(index)
        node = refs[index]
        opening = openers[index]
        if (len(node) != 0 or node.text is None or
                node.get("osisRef") is not None or
                _source_book(node) != edit.get("book") or
                _label(node.text) != edit.get("original_label")):
            raise ReviewError("Original reference text, node index or book identity changed")
        close = original.find(b"</reference>", opening.end())
        if (close < 0 or
                (index + 1 < len(openers) and close >= openers[index+1].start()) or
                original[opening.end():close] != escape(node.text).encode("utf-8")):
            raise ReviewError("Ambiguous, escaped or nested original reference span")
        kind = edit["type"]
        if kind == "cross_reference_fragment":
            note = node.getparent()
            if (note.tag != OSIS + "note" or
                    note.get("type") != "crossReference" or
                    note.get("n") != edit.get("source_note_caller") or
                    _source_origin(note) != edit.get("source_origin") or
                    dict(node.attrib)):
                raise ReviewError("Source cross-reference callout/origin drift")
            before, after = edit.get("old_fragment"), edit.get("new_fragment")
            if (not isinstance(before, str) or not isinstance(after, str) or
                    not before or not after or before == after or
                    node.text.count(before) != 1):
                raise ReviewError("Editorial replacement is ambiguous or unchanged")
            new_text = node.text.replace(before, after, 1)
            if _label(new_text) != edit.get("new_label"):
                raise ReviewError("Full reviewed replacement label mismatch")
            target, reason, _ = _complete_printed_destinations(
                _label(new_text), aliases, verse_ids,
                disambiguated_chapter_commas=True,
                named_single_chapter_refs=True)
            if (target is None or
                    edit.get("printed_target_osis") not in target.split() or
                    not edit.get("original_printed_scan_page") or
                    not edit.get("printed_note_callout") or
                    not edit.get("printed_fragment") or
                    edit.get("editorial_decision") !=
                    "source_specific_fragment_repaired_in_separate_candidate"):
                raise ReviewError("Unsubstantiated printed-target replacement: " + str(reason))
            _require_verses(target, verse_ids)
            markup = '<reference osisRef="' + target + '">' + escape(new_text) + '</reference>'
        else:
            if (node.getparent().tag != OSIS + "item" or
                    dict(node.attrib) != {"subType": "x-introduction"}):
                raise ReviewError("Unexpected source introduction metadata")
            new_text = edit.get("new_label")
            if not isinstance(new_text, str) or not new_text:
                raise ReviewError("Missing exact reviewed introduction text")
            if kind == "introduction_text_correction":
                if (node.text == new_text or
                        edit.get("editorial_decision") !=
                        "correct_source_heading_typo_in_separate_candidate" or
                        not edit.get("evidence_url")):
                    raise ReviewError("Unapproved original introduction-text correction")
            elif node.text != new_text:
                raise ReviewError("Structural-only introduction must preserve all prose")
            segments = edit.get("segments")
            if not isinstance(segments, list) or not 1 <= len(segments) <= 8:
                raise ReviewError("No reviewed introduction citation segments")
            parts = []
            offset = 0
            for part in segments:
                snippet, target = part.get("literal"), part.get("osis_ref")
                if (not isinstance(snippet, str) or not snippet or
                        new_text.count(snippet) != 1):
                    raise ReviewError("Missing or repeated source introduction substring")
                pos = new_text.find(snippet, offset)
                if pos < offset:
                    raise ReviewError("Unordered or overlapping introduction references")
                _require_verses(target, verse_ids)
                parts.append(escape(new_text[offset:pos]))
                parts.append('<reference subType="x-introduction" osisRef="' +
                             target + '">' + escape(snippet) + '</reference>')
                offset = pos + len(snippet)
            parts.append(escape(new_text[offset:]))
            markup = "".join(parts)
        patches.append((opening.start(), close + len(b"</reference>"),
                        markup.encode("utf-8"), kind))
        kinds[kind] += 1
    patches.sort()
    output = []
    cursor = 0
    for start, end, replacement, _kind in patches:
        if start < cursor or start >= end:
            raise ReviewError("Overlapping reviewed original source edits")
        output.extend((original[cursor:start], replacement))
        cursor = end
    output.append(original[cursor:])
    candidate = b"".join(output)
    after = _parse(candidate)
    before_verses = [(e.get("osisID"), e.get("sID"), e.get("eID"))
                     for e in root.iter(OSIS + "verse")]
    after_verses = [(e.get("osisID"), e.get("sID"), e.get("eID"))
                    for e in after.iter(OSIS + "verse")]
    if before_verses != after_verses:
        raise ReviewError("Canonical verse identity/order changed")
    old_notes = list(root.iter(OSIS + "note"))
    new_notes = list(after.iter(OSIS + "note"))
    if (len(old_notes) != len(new_notes) or
            any(dict(a.attrib) != dict(b.attrib)
                for a, b in zip(old_notes, new_notes, strict=True))):
        raise ReviewError("Original note count/callouts changed")
    receipt = {
        "kind": "owner_reviewed_source_bound_editorial_candidate",
        "input_sha256": sha256(original).hexdigest(),
        "candidate_sha256": sha256(candidate).hexdigest(),
        "original_usfx_zip_sha256": original_usfx_sha256,
        "edits_executed": len(patches),
        "reference_fragment_edits": kinds["cross_reference_fragment"],
        "intro_source_text_corrections": kinds["introduction_text_correction"],
        "intro_structural_link_splits": kinds["introduction_link_split"],
        "original_bytes_outside_exact_reference_patches_preserved": True,
        "verse_order_and_index_preserved": True,
        "note_number_and_metadata_preserved": True,
        "original_cleaned_master_or_release_modified": False,
        "publication_approved": False,
        "edited_reference_indices": sorted(seen),
    }
    return candidate, receipt


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "plan", "original-usfx", "alias-witness", "output", "report"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    protected = [args.input, args.plan, args.original_usfx, args.alias_witness]
    if (args.output.resolve() in {f.resolve() for f in (*protected, args.report)} or
            args.report.resolve() in {f.resolve() for f in protected}):
        p.error("Input and output locations must be independent")
    try:
        original = _bytes(args.input, MAX_SOURCE)
        upstream_hash = sha256(_bytes(args.original_usfx, MAX_SOURCE)).hexdigest()
        plan = json.loads(_bytes(args.plan, 256 * 1024))
        raw = json.loads(_bytes(args.alias_witness, 256 * 1024))
        aliases = raw.get("aliases", {})
        variants = raw.get("source_attested_digital_variants", {})
        if (raw.get("schema_version") != 1 or len(aliases) != 66 or
                variants.get("witness_usfx_zip_sha256") != upstream_hash):
            raise ReviewError("Source edition alias table does not match pinned witness")
        aliases = {**aliases, **variants.get("aliases", {})}
        result, receipt = apply_plan(original, plan, aliases, upstream_hash)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".reviewed-editorial-", dir=args.output.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(result)
            os.replace(temp, args.output)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        args.report.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        print("Isolated editorial candidate, not published:", receipt)
        return 0
    except (ReviewError, OSError, ValueError, etree.XMLSyntaxError) as e:
        p.exit(2, f"Editorial candidate rejected: {e}\n")


if __name__ == "__main__":
    raise SystemExit(main())
