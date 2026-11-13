#!/usr/bin/env python3
"""Draft *reversible* repairs for demonstrably inconsistent original ThML book markers.

The original is never modified or redistributed. Only source <scripCom>
osisRef book tokens may change in an in-memory review candidate, and only
when the enclosing original div1 title is EXACTLY one verified canonical
book alias and all original markers in that division claim one contradictory
canonical book. Every other source byte is preserved.

This is a proposal for the original source maintainer, NOT permission to
rewrite a different CrossWire digital edition, publish a corrected CCEL
transcription, or silently edit authorial content.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

from commentary_source_english_osis_alias import (
    _classify, read_existing_66_book_english_aliases,
)
from pilot_preflight import PilotError

SHA = re.compile(r"[a-f0-9]{64}\Z")
MARKER_OPEN = re.compile(
    rb"<(?:[A-Za-z_][A-Za-z0-9_.-]*:)?scripCom\b[^>]{0,4000}>",
    re.S,
)
REF_ATTRIBUTE = re.compile(rb"(?<![A-Za-z0-9_.:-])osisRef\s*=\s*(['\"])(.*?)\1", re.S)
REF_START = re.compile(r"^Bible:([1-4]?[A-Za-z][A-Za-z0-9]{0,15})\.")
LOC = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]{0,15})(\.[1-9][0-9]{0,2}(?:\.[1-9][0-9]{0,2})?)$")
MAX_ORIGINAL_XML = 20_000_000
MAX_MARKERS = 50_000
MAX_REPAIRS = 100


def _parse(raw: bytes):
    try:
        return etree.fromstring(
            raw,
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False,
            ),
        )
    except (ValueError, etree.XMLSyntaxError) as exc:
        raise PilotError("Original source XML cannot be parsed strictly") from exc


def _replace_book_only(ref: str, old: str, proposed: str) -> str:
    if not ref.startswith("Bible:"):
        raise PilotError("Original reference is not the exact reviewed Bible work")
    parts = ref[len("Bible:"):].split("-")
    if not 1 <= len(parts) <= 2:
        raise PilotError("Original source range shape is not safely reviewable")
    changed = []
    for part in parts:
        m = LOC.fullmatch(part)
        if not m or m.group(1) != old:
            raise PilotError("Source cross-book or unknown endpoint cannot be repaired")
        changed.append(proposed + m.group(2))
    return "Bible:" + "-".join(changed)


def _heading(source_div1):
    title = source_div1.get("title")
    if title is not None:
        return title
    for node in source_div1:
        if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] in {"h1", "title"}:
            return "".join(node.itertext())
    return ""


def propose_private_source_bookcode_repair(
    original_xml: bytes, *, expected_source_sha256: str,
) -> tuple[bytes, dict]:
    """Return a private candidate and *text-free* exact-byte patch receipt.

    The proposed candidate must remain private until editorial approval and
    the upstream owner/maintainer has been consulted. This never touches the
    CrossWire zCom or its passage mappings.
    """
    if (not isinstance(original_xml, bytes)
            or not 1 <= len(original_xml) <= MAX_ORIGINAL_XML
            or not isinstance(expected_source_sha256, str)
            or not SHA.fullmatch(expected_source_sha256)
            or sha256(original_xml).hexdigest() != expected_source_sha256):
        raise PilotError("Original ThML bytes do not match independently pinned SHA-256")

    original_root = _parse(original_xml)
    marker_nodes = [
        n for n in original_root.iter()
        if isinstance(n.tag, str) and n.tag.rsplit("}", 1)[-1] == "scripCom"
    ]
    physical_tags = list(MARKER_OPEN.finditer(original_xml))
    if (not 1 <= len(marker_nodes) <= MAX_MARKERS
            or len(physical_tags) != len(marker_nodes)):
        raise PilotError("Original source XML scripCom byte positions are not provable")

    aliases, registry = read_existing_66_book_english_aliases()
    divisions = defaultdict(list)
    marker_rows = []
    for i, (node, tag) in enumerate(zip(marker_nodes, physical_tags)):
        attrs = list(REF_ATTRIBUTE.finditer(tag.group(0)))
        if len(attrs) != 1:
            raise PilotError("Original source marker has ambiguous/missing osisRef attribute")
        observed = attrs[0].group(2)
        try:
            original_ref = observed.decode("utf-8")
        except UnicodeError as exc:
            raise PilotError("Source original verse token is not UTF-8") from exc
        if original_ref != node.get("osisRef"):
            raise PilotError("Original source lexical attribute/entity differs from parsed value")
        div = next((
            ancestor for ancestor in node.iterancestors()
            if isinstance(ancestor.tag, str)
            and ancestor.tag.rsplit("}", 1)[-1] == "div1"
        ), None)
        if div is None:
            raise PilotError("Original reference has no enclosing authorial book division")
        claimed = REF_START.match(original_ref)
        if claimed is not None:
            divisions[id(div)].append((i, div, claimed.group(1)))
        marker_rows.append((node, tag, attrs[0], original_ref))

    planned = {}
    considered = set()
    for items in divisions.values():
        codes = {code for _, _, code in items}
        # Mixed source marker codes in a single div1 are ambiguous. Do not
        # infer a correction by replacing all markers in such a division.
        if len(codes) != 1:
            continue
        claimed = next(iter(codes))
        heading = _heading(items[0][1])
        cls, proposed_code, matched = _classify(heading, claimed, aliases)
        if cls != "original_title_exact_english_alias_points_to_different_book_code":
            continue
        if (matched != 1 or proposed_code is None or
                proposed_code == claimed or proposed_code not in aliases):
            raise PilotError("No unique source book identity for proposed correction")
        for index, _div, old in items:
            if index in considered:
                raise PilotError("Original source marker assigned to multiple divisions")
            considered.add(index)
            original_ref = marker_rows[index][3]
            proposed_ref = _replace_book_only(original_ref, old, proposed_code)
            if proposed_ref == original_ref:
                raise PilotError("Original contradictory book token was not changed")
            planned[index] = proposed_ref
    if len(planned) > MAX_REPAIRS:
        raise PilotError("Too many inferred source marker changes for a review proposal")

    patches = []
    operations = []
    for index, replacement in sorted(planned.items()):
        node, tag, attr, source_ref = marker_rows[index]
        start = tag.start() + attr.start(2)
        end = tag.start() + attr.end(2)
        expected = source_ref.encode("utf-8")
        rewritten = replacement.encode("utf-8")
        if original_xml[start:end] != expected:
            raise PilotError("Original source byte span is not identical to its source annotation")
        patches.append((start, end, expected, rewritten))
        operations.append({
            "source_line": node.sourceline,
            "original_source_osisRef_sha256": sha256(expected).hexdigest(),
            "proposed_private_osisRef_sha256": sha256(rewritten).hexdigest(),
            "original_source_annotation_byte_span_length": len(expected),
            "proposed_annotation_byte_span_length": len(rewritten),
            "only_inferred_book_code_changed_in_scripCom": True,
        })

    candidate = original_xml
    for start, end, old, new in reversed(patches):
        if candidate[start:end] != old:
            raise PilotError("Source-original span moved or was mutated before repair")
        candidate = candidate[:start] + new + candidate[end:]

    # Reverse the exact byte operations with shifted positions. No
    # normalization, XML serialization or whitespace rewriting is allowed.
    forward_shift = 0
    reverse_spans = []
    for start, end, old, new in patches:
        reverse_spans.append((start + forward_shift, new, old))
        forward_shift += len(new) - len(old)
    restored = candidate
    for start, new, old in reversed(reverse_spans):
        if restored[start:start+len(new)] != new:
            raise PilotError("Original source metadata patch is not reversible")
        restored = restored[:start] + old + restored[start+len(new):]
    if restored != original_xml:
        raise PilotError("Original source cannot be restored byte-for-byte")

    candidate_root = _parse(candidate)
    candidate_nodes = [
        n for n in candidate_root.iter()
        if isinstance(n.tag, str) and n.tag.rsplit("}", 1)[-1] == "scripCom"
    ]
    if len(candidate_nodes) != len(marker_nodes):
        raise PilotError("Proposed source marker change altered source element count")
    edited_marker_indices = set(planned)
    for index, (before, after) in enumerate(zip(original_root.iter(), candidate_root.iter())):
        if before.tag != after.tag or before.text != after.text or before.tail != after.tail:
            raise PilotError("Private source repair changed authorial XML text or structure")
        left = dict(before.attrib)
        right = dict(after.attrib)
        if before in marker_nodes and marker_nodes.index(before) in edited_marker_indices:
            marker_index = marker_nodes.index(before)
            if right.pop("osisRef", None) != planned[marker_index]:
                raise PilotError("Proposed scripCom OSIS target differs from reviewed patch")
            left.pop("osisRef", None)
        if left != right:
            raise PilotError("Private repair changed unrelated source attributes")

    receipt = {
        "schema_version": 1,
        "status": "private_exact_scripCom_book_token_repair_proposal_not_approved",
        "original_source_sha256": expected_source_sha256,
        "private_corrected_source_sha256": sha256(candidate).hexdigest(),
        "all_original_scripCom_elements_preserved": len(marker_nodes),
        "reviewed_private_original_bookcode_replacements": len(planned),
        "only_unique_original_exact_english_div1_title_conflicts_proposed": True,
        "original_source_byte_for_byte_restorable": True,
        "every_original_other_XML_text_title_note_reference_and_structure_unmodified": True,
        "original_crosswire_sword_data_or_versification_changed": False,
        "original_scripCom_replacement_operations_without_authorial_text": operations,
        "source_owner_or_editor_approved": False,
        "public_release_authorized": False,
        **registry,
    }
    return candidate, receipt
