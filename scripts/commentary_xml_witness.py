#!/usr/bin/env python3
"""Read-only structural discovery of an independent commentary XML witness.

This is an inventory, NOT an OSIS/ThML validation or source/compiled parity.
Original XML bytes and text stay exclusively on a disposable runner.
Only tag/attribute NAMES, counts and cryptographic fingerprints are reported.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from lxml import etree

from commentary_intake import SHA, load_manifest
from pilot_fetch import fetch, validate_url
from pilot_preflight import PilotError

MAX_XML = 32 * 1024 * 1024
MAX_TAG_TYPES = 128
MAX_ELEMENTS = 600_000
XML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]{0,95}$")
OSIS_PART = r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*"
OSIS_SINGLE = re.compile(r"^" + OSIS_PART + r"$")
OSIS_RANGE = re.compile(r"^(" + OSIS_PART + r")-(" + OSIS_PART + r")$")

def _safe_reference_shape(value: str) -> str:
    # This is deliberately not a reference or a commentary excerpt.
    # Only character classes and punctuation survive the fingerprint.
    if len(value) > 400:
        return "UNREVIEWED_LONG_REFERENCE"
    shape = "".join("A" if c.isalpha() else "9" if c.isdigit() else c
                    for c in value)
    shape = re.sub(r"A+", "A", shape)
    shape = re.sub(r"9+", "9", shape)
    return shape[:100]


def _ref_category(value: str) -> str:
    if not value:
        return "missing"
    if OSIS_SINGLE.fullmatch(value):
        return "one_fully_qualified_verse"
    match = OSIS_RANGE.fullmatch(value)
    if match:
        return ("same_book_verse_range" if match[1].split(".")[0] == match[2].split(".")[0]
                else "cross_book_range_requires_review")
    return "other_unreviewed_reference_grammar"


def safe_name(tag: str) -> str:
    """Keep local XML tag or attribute names, never their values."""
    if not isinstance(tag, str):
        raise PilotError("Unreviewed XML node/attribute type")
    name = tag.rsplit("}", 1)[-1]
    if not XML_NAME.fullmatch(name):
        raise PilotError("Unknown or unsafe XML node/attribute name")
    return name


def xml_structure(data: bytes) -> dict:
    if not 1000 <= len(data) <= MAX_XML:
        raise PilotError("Original XML absent or exceeds 32 MiB safety limit")
    if b"\x00" in data or b"<![CDATA[" in data[:512] and b"<?xml" not in data[:512]:
        raise PilotError("Unexpected original XML encoding or header")
    try:
        parser = etree.XMLParser(
            resolve_entities=False, no_network=True, load_dtd=False,
            huge_tree=False, remove_blank_text=False, remove_comments=False,
            recover=False,
        )
        root = etree.fromstring(data, parser=parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        # Never print an excerpt from a potentially copyrighted source,
        # including XMLSyntaxError's original line text.
        raise PilotError("Original XML could not be safely parsed; source format needs manual review") from None
    document = root.getroottree()
    tags = Counter()
    attrs = Counter()
    text_nodes = 0
    nonempty_text_nodes = 0
    direct_children = Counter()
    commentary_parent_paths = Counter()
    commentary_children = Counter()
    commentary_attribute_names = Counter()
    source_commentary_ref_classes = Counter()
    source_commentary_ref_shapes = Counter()
    source_commentary_books = Counter()
    source_ref_digest = sha256()
    duplicate_ref_count = 0
    observed_ref_keys = set()
    commentary_with_nonempty_direct_text = 0
    chapter_child_tags = Counter()
    entities = 0
    comments = 0
    max_depth = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if sum(tags.values()) + entities + comments > MAX_ELEMENTS or depth > 128:
            raise PilotError("Source XML exceeds inspected structural bounds")
        max_depth = max(max_depth, depth)
        if isinstance(node, etree._Entity):
            entities += 1
            continue
        if isinstance(node, etree._Comment):
            comments += 1
            continue
        if not isinstance(node.tag, str):
            raise PilotError("Unsupported source XML construct")
        tag = safe_name(node.tag)
        tags[tag] += 1
        if tag == "scripCom":
            ancestors = list(node.iterancestors())
            parent_path = "/".join(safe_name(x.tag) for x in reversed(ancestors[:5])
                                   if isinstance(x.tag, str))
            commentary_parent_paths[parent_path] += 1
            commentary_attribute_names.update(safe_name(k) for k in node.attrib)
            ref = node.get("osisRef", "")
            source_ref_digest.update(ref.encode("utf-8"))
            source_ref_digest.update(b"\0")
            category = _ref_category(ref)
            source_commentary_ref_classes[category] += 1
            source_commentary_ref_shapes[_safe_reference_shape(ref)] += 1
            if category in ("one_fully_qualified_verse", "same_book_verse_range"):
                source_commentary_books[ref.split(".")[0]] += 1
            if ref in observed_ref_keys:
                duplicate_ref_count += 1
            observed_ref_keys.add(ref)
            commentary_children.update(safe_name(x.tag) for x in node
                                       if isinstance(x.tag, str))
            if node.text and node.text.strip():
                commentary_with_nonempty_direct_text += 1
        if tag == "div2":
            chapter_child_tags.update(safe_name(x.tag) for x in node
                                      if isinstance(x.tag, str))
        for name in node.attrib:
            attrs[safe_name(name)] += 1
        for value in (node.text, node.tail):
            if value is not None:
                text_nodes += 1
                if value.strip():
                    nonempty_text_nodes += 1
        children = list(node)
        if depth == 1:
            direct_children.update(safe_name(child.tag) for child in children
                                   if isinstance(child.tag, str))
        stack.extend((child, depth + 1) for child in reversed(children))
    if len(tags) > MAX_TAG_TYPES or not tags:
        raise PilotError("Too many distinct original XML element types")
    # XML could be ThML with DTD/unknown entities; always flag instead of
    # silently interpreting its sections as authoritative SWORD mappings.
    return {
        "status": "structure_observed_not_source_to_sword_parity",
        "xml_sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "root_element_name": safe_name(root.tag),
        "root_namespace_uri_disclosed": False,
        "element_counts": dict(sorted(tags.items())),
        "attribute_name_counts": dict(sorted(attrs.items())),
        "direct_root_child_counts": dict(sorted(direct_children.items())),
        "candidate_commentary_parent_path_counts": dict(sorted(commentary_parent_paths.items())),
        "candidate_commentary_direct_child_tags": dict(sorted(commentary_children.items())),
        "candidate_commentary_attribute_name_counts": dict(sorted(commentary_attribute_names.items())),
        "candidate_commentary_reference_classes": dict(sorted(source_commentary_ref_classes.items())),
        "candidate_commentary_reference_shapes": dict(source_commentary_ref_shapes.most_common(15)),
        "candidate_commentary_reference_books": dict(sorted(source_commentary_books.items())),
        "candidate_commentary_reference_ordered_sha256": source_ref_digest.hexdigest(),
        "candidate_commentary_duplicate_identical_reference_count": duplicate_ref_count,
        "candidate_commentary_distinct_reference_count": len(observed_ref_keys),
        "candidate_commentary_nonempty_direct_text_count": commentary_with_nonempty_direct_text,
        "chapter_direct_child_tag_counts": dict(sorted(chapter_child_tags.items())),
        "candidate_sections_are_verified_annotations": False,
        "text_node_count": text_nodes,
        "nonempty_text_node_count": nonempty_text_nodes,
        "unresolved_entity_node_count": entities,
        "comment_node_count": comments,
        "max_depth": max_depth,
        "doctype_declared": bool(document.docinfo.doctype),
        "source_format_validated": False,
        "authored_ranges_verified": False,
        "source_plaintext_to_xml_fidelity_verified": False,
        "source_to_stock_sword_fidelity_verified": False,
        "no_source_text_disclosed": True,
        "content_modified": False,
    }


def inspect_xml(resource_id: str, *, directory: Path | None = None) -> dict:
    manifest = load_manifest(resource_id, directory)
    config = manifest.get("commentary_source", {})
    url = config.get("xml_witness_url")
    if not isinstance(url, str) or not url:
        raise PilotError("Exact independent XML witness URL missing in reviewed manifest")
    parsed = urlsplit(url)
    if (parsed.hostname not in {"ccel.org", "www.ccel.org"}
            or not parsed.path.endswith(".xml") or parsed.query):
        raise PilotError("Unapproved commentary XML provenance URL")
    validate_url(url, "ccel")
    expected = config.get("xml_witness_sha256")
    if expected is not None and not (isinstance(expected, str) and SHA.fullmatch(expected)):
        raise PilotError("Unknown XML witness pin; do not guess a SHA-256")
    with tempfile.TemporaryDirectory(prefix="commentary-xml-witness-") as temp:
        original = Path(temp) / "witness.xml"
        receipt = fetch(url, original, "ccel")
        if receipt["bytes"] > MAX_XML:
            raise PilotError("Original XML exceeds 32 MiB limit")
        if expected is not None and expected != receipt["sha256"]:
            raise PilotError("Original XML changed since the reviewed SHA-256 pin")
        signals = xml_structure(original.read_bytes())
        if receipt["sha256"] != signals["xml_sha256"]:
            raise PilotError("XML source mutated while reading")
    return {
        "schema_version": 1,
        "resource_id": resource_id,
        "observed_witness_url": url,
        "source_sha256_pin_verified": expected is not None,
        **signals,
        "rights_approved": False,
        "original_source_edition_matched_to_sword": False,
        "published": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = inspect_xml(args.resource_id)
        code = 0
    except (OSError, RuntimeError, ValueError) as exc:
        result = {
            "status": "blocked", "resource_id": args.resource_id,
            "diagnostic": str(exc), "published": False,
            "source_to_stock_sword_fidelity_verified": False
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("Original commentary XML structure: " + result["status"] + " (no text logged)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
