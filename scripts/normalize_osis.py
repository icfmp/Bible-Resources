#!/usr/bin/env python3
"""Apply explicitly approved, strictly text-preserving OSIS layout edits.

No heuristic editing and no implicit deletion. Applies a source-hash-bound,
reviewer-asserted recipe to a *different* output path. Revalidates source and
result with the pinned official OSIS schema and reviewed content policy.
Original source stays byte-for-byte unchanged.

These operations do not change words, inline markup, verse/entry IDs, notes or
source data. The original input remains the rollback artifact.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from lxml import etree

from guard_osis import (
    MAX_SOURCE_BYTES, StructureFailure, inspect as inspect_osis,
    parse_xml, require_regular_file, write_report, ROOT,
)
from guard_commentary import inspect_commentary, COMMENTARY_POLICY

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
HEX = re.compile(r"^[0-9a-f]{64}$")
URL = re.compile(r"^https://[^/\s]+/.+")
NON_STRUCTURAL = {"p", "lg", "l"}  # Only these containers may be added/replaced.
OPERATIONS = {"split_paragraph", "split_before_child", "group_poetry_lines"}
SAFE_LINE_CHILDREN = {NS + name for name in {
    "verse", "hi", "note", "reference", "q", "w", "transChange",
    "divineName", "seg", "lb", "milestone", "speaker",
}}


class EditorialError(ValueError):
    pass


def checksum(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def element_hash(element) -> str:
    return checksum(etree.tostring(element, encoding="UTF-8", with_tail=False))


def element_address(element) -> list[int]:
    """Stable positional path in a source-hash-pinned XML document."""
    address = []
    while (parent := element.getparent()) is not None:
        address.append(parent.index(element))
        element = parent
    return list(reversed(address))


def _locate(root, address) -> object:
    if not isinstance(address, list) or len(address) > 100:
        raise EditorialError("Invalid source node_path")
    node = root
    for offset in address:
        if type(offset) is not int or offset < 0 or offset >= len(node):
            raise EditorialError(f"Unknown node_path position: {address!r}")
        node = node[offset]
    return node


def _approved_plan(plan: dict, original: bytes, kind: str) -> None:
    if plan.get("schema_version") != 1 or plan.get("kind") != kind:
        raise EditorialError("Plan version/category mismatch")
    if plan.get("source_sha256") != checksum(original):
        raise EditorialError("Stale source: plan SHA-256 does not match original bytes")
    if plan.get("approved_for_structural_edits") is not True:
        raise EditorialError("Explicit editorial approval is required")
    if plan.get("edition") not in {"faithful", "reader_optimized"}:
        raise EditorialError("Plan must name the faithful or reader_optimized edition")
    review = plan.get("review")
    if not isinstance(review, dict):
        raise EditorialError("Editorial review record is required")
    reviewer = review.get("reviewed_by")
    if (not isinstance(reviewer, str) or len(reviewer.strip()) < 2 or
            reviewer.strip().casefold() in {"pending", "unknown", "tbd"} or
            not isinstance(review.get("decision"), str) or
            len(review["decision"].strip()) < 12 or
            not isinstance(review.get("evidence_url"), str) or
            not URL.fullmatch(review["evidence_url"])):
        raise EditorialError("Require real reviewer, editorial decision and HTTPS evidence")
    rights = plan.get("rights")
    if (not isinstance(rights, dict) or
            rights.get("redistribution_allowed") is not True or
            not isinstance(rights.get("evidence_url"), str) or
            not URL.fullmatch(rights["evidence_url"]) or
            "example." in rights["evidence_url"]):
        raise EditorialError("Document verified redistribution rights before generating a derivative")
    if plan["edition"] == "reader_optimized" and rights.get("derivatives_allowed") is not True:
        raise EditorialError("Reader-optimized edition requires documented derivative rights")
    edits = plan.get("edits")
    if not isinstance(edits, list) or not 1 <= len(edits) <= 500:
        raise EditorialError("Plan requires 1-500 explicit, reviewed structural edits")
    seen = set()
    for idx, edit in enumerate(edits):
        if not isinstance(edit, dict) or edit.get("operation") not in OPERATIONS:
            raise EditorialError(f"Unreviewed operation at index {idx}")
        if (not isinstance(edit.get("reason"), str) or
                len(edit["reason"].strip()) < 12 or
                not isinstance(edit.get("source_reference"), str) or
                not edit["source_reference"].strip()):
            raise EditorialError(f"Edit {idx} needs source verse/entry key and meaningful reason")
        if (not isinstance(edit.get("expected_element_sha256"), str)
                or not HEX.fullmatch(edit["expected_element_sha256"])):
            raise EditorialError(f"Edit {idx} needs SHA-256 anchored to source subtree")
        paths = ([edit.get("node_path")] if edit["operation"] in {
                    "split_paragraph", "split_before_child"
                 } else edit.get("node_paths"))
        if not isinstance(paths, list) or not paths:
            raise EditorialError(f"Edit {idx} has no positional source paths")
        for path in paths:
            if not isinstance(path, list) or not all(type(x) is int for x in path):
                raise EditorialError(f"Edit {idx} has malformed source path")
            ident = tuple(path)
            if ident in seen:
                raise EditorialError("Overlapping edits to the same source node are not supported")
            seen.add(ident)


def _fingerprint(doc) -> tuple:
    root = doc.getroot()
    # The string of ALL XML character content, including original whitespace
    # and inline formatting tails, must remain exactly identical.
    source_text = "".join(root.itertext())
    # All element types and attributes except the specifically approved p/lg/l
    # layout containers must stay in the same order. This catches accidental
    # loss of verse IDs, notes, cross references and word/Strong annotations.
    items = []
    for node in root.iter():
        if not isinstance(node.tag, str):
            raise EditorialError("Unreviewed XML comment or processing instruction")
        if node.tag not in {NS + t for t in NON_STRUCTURAL}:
            items.append((node.tag, tuple(sorted(node.attrib.items()))))
    return source_text, tuple(items)


def _check_node(edit, node, *, operation):
    expected = edit["expected_element_sha256"]
    if element_hash(node) != expected:
        raise EditorialError(f"Stale {operation} anchor at {edit.get('node_path') or edit.get('node_paths')}: source subtree hash changed")


def _split_paragraph(root, edit) -> dict:
    node = _locate(root, edit.get("node_path"))
    if node.tag != NS + "p" or node.attrib or len(node) or not isinstance(node.text, str):
        raise EditorialError("split_paragraph supports only a plain unannotated OSIS <p>")
    _check_node(edit, node, operation="split_paragraph")
    marker = edit.get("right_starts_with")
    if not isinstance(marker, str) or not marker or node.text.count(marker) != 1:
        raise EditorialError("Paragraph split marker must occur exactly once in direct text")
    split = node.text.index(marker)
    left, right = node.text[:split], node.text[split:]
    if not left.strip() or not right.strip():
        raise EditorialError("Refusing empty paragraph after split")
    parent = node.getparent()
    if parent is None:
        raise EditorialError("Cannot split document root")
    sibling = etree.Element(NS + "p")
    sibling.text = right
    sibling.tail = node.tail
    node.text = left
    node.tail = None
    parent.insert(parent.index(node) + 1, sibling)
    return {"operation": "split_paragraph", "source_reference": edit["source_reference"],
            "left_characters": len(left), "right_characters": len(right)}


def _split_before_child(root, edit) -> dict:
    node = _locate(root, edit.get("node_path"))
    if node.tag != NS + "p" or node.attrib:
        raise EditorialError("split_before_child requires an unannotated paragraph")
    _check_node(edit, node, operation="split_before_child")
    child_index = edit.get("child_index")
    if type(child_index) is not int or not 0 <= child_index < len(node):
        raise EditorialError("split_before_child needs an existing direct child_index")
    # Move complete inline subtrees, never split or reassign notes, words,
    # references or verse milestones. The full source and schema gates
    # additionally prohibit invalid line/paragraph nesting.
    if any(child.tag not in SAFE_LINE_CHILDREN for child in node):
        raise EditorialError("Unreviewed paragraph child for structural split")
    parent = node.getparent()
    if parent is None:
        raise EditorialError("Cannot split document root")
    sibling = etree.Element(NS + "p")
    sibling.tail = node.tail
    node.tail = None
    for child in list(node)[child_index:]:
        sibling.append(child)
    if (not "".join(node.itertext()).strip() or
            not "".join(sibling.itertext()).strip()):
        raise EditorialError("Refusing empty paragraph after splitting inline nodes")
    parent.insert(parent.index(node) + 1, sibling)
    return {"operation":"split_before_child",
            "source_reference":edit["source_reference"],
            "moved_child_nodes":len(sibling)}


def _group_poetry(root, edit) -> dict:
    paths = edit.get("node_paths")
    if not isinstance(paths, list) or not 2 <= len(paths) <= 100:
        raise EditorialError("group_poetry_lines needs 2-100 consecutive unannotated paragraphs")
    nodes = [_locate(root, addr) for addr in paths]
    if len({id(node) for node in nodes}) != len(nodes):
        raise EditorialError("Repeated poetry nodes")
    if any(node.tag != NS + "p" or node.attrib or
           any(child.tag not in SAFE_LINE_CHILDREN for child in node) or
           not "".join(node.itertext()).strip() for node in nodes):
        raise EditorialError("Poetry grouping needs unannotated paragraphs with only reviewed inline markup")
    # The hash is over all selected direct paragraphs in their original order.
    combined = b"\0".join(etree.tostring(n, encoding="UTF-8", with_tail=False) for n in nodes)
    if checksum(combined) != edit["expected_element_sha256"]:
        raise EditorialError("Poetry group source hash mismatch")
    parent = nodes[0].getparent()
    if parent is None or any(n.getparent() is not parent for n in nodes):
        raise EditorialError("Poetry paragraphs must share one parent")
    start = parent.index(nodes[0])
    if [parent.index(n) for n in nodes] != list(range(start, start + len(nodes))):
        raise EditorialError("Poetry paragraphs must be consecutive in source order")
    stanza = etree.Element(NS + "lg")
    last_tail = nodes[-1].tail
    for index, node in enumerate(nodes):
        line = etree.SubElement(stanza, NS + "l")
        line.text = node.text
        for child in list(node):
            line.append(child)
        line.tail = node.tail if index < len(nodes) - 1 else None
    stanza.tail = last_tail
    for node in nodes:
        parent.remove(node)
    parent.insert(start, stanza)
    return {"operation": "group_poetry_lines", "source_reference": edit["source_reference"],
            "lines": len(nodes)}


def apply_plan(source_path: Path, plan_path: Path, output_path: Path,
               *, schema_path: Path, kind: str, osis_policy: Path = ROOT / "config/osis-policy.json",
               commentary_policy: Path = COMMENTARY_POLICY,
               diff_path: Path | None = None) -> dict:
    source_path, plan_path, output_path = (Path(p).absolute()
                                          for p in (source_path, plan_path, output_path))
    if source_path == output_path or source_path.is_symlink() or (
        output_path.exists() or output_path.is_symlink()):
        raise EditorialError("Output must be a new path, never source or existing file")
    if diff_path is not None:
        diff_path = Path(diff_path).absolute()
        if diff_path in {source_path, output_path, plan_path} or diff_path.exists():
            raise EditorialError("Diff must be a new, separate local-only path")
    original = require_regular_file(source_path, MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
    plan_bytes = require_regular_file(plan_path, 1024 * 1024, "PLAN_UNAVAILABLE")
    try:
        plan = json.loads(plan_bytes)
    except (UnicodeError, ValueError) as exc:
        raise EditorialError("Malformed JSON plan") from exc
    _approved_plan(plan, original, kind)

    validate = inspect_commentary if kind == "commentary" else inspect_osis
    if kind == "commentary":
        before = validate(source_path, schema_path, osis_policy, commentary_policy)
    else:
        before = validate(source_path, schema_path, osis_policy)
    original_doc = parse_xml(source_path, original, "MALFORMED_XML")
    doc = parse_xml(source_path, original, "MALFORMED_XML")
    baseline_text, baseline_items = _fingerprint(original_doc)
    operations = []
    for edit in plan["edits"]:
        if edit["operation"] == "split_paragraph":
            operations.append(_split_paragraph(doc.getroot(), edit))
        elif edit["operation"] == "split_before_child":
            operations.append(_split_before_child(doc.getroot(), edit))
        else:
            operations.append(_group_poetry(doc.getroot(), edit))
    after_text, after_items = _fingerprint(doc)
    if baseline_text != after_text or baseline_items != after_items:
        raise EditorialError("Integrity failure: original text or semantic markup changed")
    result_bytes = etree.tostring(doc, encoding="UTF-8", xml_declaration=True,
                                  pretty_print=False)
    if result_bytes == original:
        raise EditorialError("No structural difference produced by plan")
    # Reparse independently and validate the new bytes (not just a mutable
    # in-memory document). Temporary file is removed even if validation fails.
    with tempfile.TemporaryDirectory(prefix="bible-osis-normalize-") as temp:
        candidate = Path(temp) / "candidate.osis.xml"
        candidate.write_bytes(result_bytes)
        if kind == "commentary":
            after = validate(candidate, schema_path, osis_policy, commentary_policy)
            if before["annotation_reference_sha256"] != after["annotation_reference_sha256"]:
                raise EditorialError("Commentary annotated-reference mapping changed")
        else:
            after = validate(candidate, schema_path, osis_policy)
        candidate_doc = parse_xml(candidate, result_bytes, "MALFORMED_XML")
        if _fingerprint(candidate_doc) != (baseline_text, baseline_items):
            raise EditorialError("Serialized output changed semantic content")

    diff = "".join(difflib.unified_diff(
        original.decode("utf-8-sig").splitlines(keepends=True),
        result_bytes.decode("utf-8").splitlines(keepends=True),
        fromfile="original.xml", tofile="reader-edition.xml",
    ))
    report = {
        "schema_version": 1,
        "status": "structural_edit_verified_not_published",
        "source_path": str(source_path),
        "output_path": str(output_path),
        "kind": kind,
        "edition": plan["edition"],
        "source_sha256": checksum(original),
        "output_sha256": checksum(result_bytes),
        "plan_sha256": checksum(plan_bytes),
        "schema_sha256": before["schema_sha256"],
        "source_validation_sha256": checksum(json.dumps(before, sort_keys=True).encode()),
        "output_validation_sha256": checksum(json.dumps(after, sort_keys=True).encode()),
        "text_sha256": checksum(baseline_text.encode("utf-8")),
        "inline_semantic_tags_preserved": True,
        "full_text_exactly_preserved": True,
        "original_source_unchanged": source_path.read_bytes() == original,
        "review_asserted_by_plan": plan["review"]["reviewed_by"],
        "review_evidence_url": plan["review"]["evidence_url"],
        "rights_evidence_url": plan["rights"]["evidence_url"],
        "operations": operations,
        "diff_sha256": checksum(diff.encode("utf-8")),
        "diff_lines": len(diff.splitlines()),
        "rollback": "Recreate the edition from the unmodified original source and its recorded SHA-256",
        "approved_for_publication": False,
        "real_SWORD_round_trip_passed": False,
    }
    if not report["original_source_unchanged"]:
        raise EditorialError("Original source unexpectedly changed")
    # Atomic publication of *local candidate file*, never of a module.
    # No existing file is overwritten. Both audit paths are private/local.
    wrote_output = False
    wrote_diff = False
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("xb") as stream:
            wrote_output = True
            stream.write(result_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        if diff_path is not None:
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            with diff_path.open("x", encoding="utf-8") as stream:
                wrote_diff = True
                stream.write(diff)
                stream.flush()
                os.fsync(stream.fileno())
    except Exception:
        # Never leave an incomplete candidate after a diff/write error.
        if wrote_diff:
            diff_path.unlink(missing_ok=True)
        if wrote_output:
            output_path.unlink(missing_ok=True)
        raise
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--kind", choices=("bible", "commentary"), required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--osis-policy", type=Path, default=ROOT / "config/osis-policy.json")
    parser.add_argument("--commentary-policy", type=Path, default=COMMENTARY_POLICY)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--diff", type=Path, help="Private text-bearing unified diff; never upload without rights review")
    args = parser.parse_args(argv)
    try:
        report = apply_plan(args.source, args.plan, args.output, schema_path=args.schema,
                            kind=args.kind, osis_policy=args.osis_policy,
                            commentary_policy=args.commentary_policy, diff_path=args.diff)
        status = 0
    except (OSError, ValueError, StructureFailure, etree.LxmlError) as exc:
        report = {"status": "blocked", "error": str(exc),
                  "original_source_unchanged": True, "approved_for_publication": False}
        status = 1
    write_report(args.report, report)
    print(f"OSIS normalizer: {report['status']}; report: {args.report}")
    return status


if __name__ == "__main__":
    sys.exit(main())
