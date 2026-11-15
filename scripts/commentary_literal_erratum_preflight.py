#!/usr/bin/env python3
"""Generic, byte-preserving proposed SWORD commentary reference erratum preflight.

Never changes original stock modules or repository data. In a PRIVATE in-memory
preview only, change exactly one original XML reference/@osisRef endpoint AND
the matching direct-text numeric label. Reject nested labels, ambiguous source
matches, unexpected XML and any change that cannot be undone byte-for-byte.
Do not confuse a technically reversible proposal with editorial approval.
"""
from __future__ import annotations

from hashlib import sha256
import re
from xml.parsers import expat

from lxml import etree

from commentary_reference_registry_triage import (
    SINGLE_VERSE, _unambiguous_verse_range_endpoints
)

MAX_ORIGINAL_BYTES = 2 * 1024 * 1024
# The byte-local replacement is deliberate: serializing with an XML library
# would silently change original whitespace, attribute order or entities.
REFERENCE_ELEMENT = re.compile(
    rb"<reference(?P<attrs>\s[^<>]*?)>(?P<label>[^<>]*)</reference>",
    flags=re.DOTALL
)
REF_ATTRIBUTE = re.compile(
    rb"(?<!\S)osisRef=(?P<quote>['\"])(?P<value>[^'\"<>]{1,2048})(?P=quote)"
)


def _strict_original_fragment(raw: bytes) -> None:
    if (not isinstance(raw, bytes) or not raw
            or len(raw) > MAX_ORIGINAL_BYTES or b"\x00" in raw):
        raise ValueError("Untrusted original commentary XML fragment")
    try:
        root = etree.fromstring(
            b"<entry>" + raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
    except (etree.XMLSyntaxError, ValueError):
        raise ValueError("Original commentary XML fragment is not strictly parseable") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError("Unsafe unresolved entity in source commentary XML")



def _parsed_reference_spans(raw: bytes) -> list[tuple[int, int, str]]:
    """Bind editable byte offsets to *actual* XML reference parser events.

    The expat offsets point into the original UTF-8 source. A regex alone can
    mistake comment or CDATA bytes for real elements. Parsing first also
    rules out reference-like attributes on unrelated tags. The wrapper and
    offsets are never written to the source.
    """
    prefix = b"<entry>"
    parser = expat.ParserCreate("UTF-8")
    stack = []
    references = []

    def start(name, attrs):
        stack.append((name, parser.CurrentByteIndex - len(prefix), attrs))

    def end(name):
        if not stack:
            raise ValueError("Unbalanced original commentary reference nodes")
        opened, start_byte, attrs = stack.pop()
        if opened != name:
            raise ValueError("Unexpected original commentary nesting")
        if name == "reference" and "osisRef" in attrs:
            references.append((start_byte, parser.CurrentByteIndex - len(prefix),
                               attrs["osisRef"]))

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    try:
        parser.Parse(prefix + raw + b"</entry>", True)
    except expat.ExpatError:
        raise ValueError("Original commentary cannot be parsed for exact XML spans") from None
    if stack or len(references) > 10000:
        raise ValueError("Unbounded or unbalanced commentary reference parsing")
    return references


def _apply_exact_original_link_change(
        raw: bytes, *, first_verse: str,
        original_end_verse: str, proposed_end_verse: str) -> bytes:
    """Surgical single-node patch; no reusable arbitrary-text replace."""
    if (not all(SINGLE_VERSE.fullmatch(s) for s in
                (first_verse, original_end_verse, proposed_end_verse))
            or first_verse.rsplit(".", 1)[0] != original_end_verse.rsplit(".", 1)[0]
            or first_verse.rsplit(".", 1)[0] != proposed_end_verse.rsplit(".", 1)[0]
            or original_end_verse == proposed_end_verse):
        raise ValueError("Invalid original/proposed scripture range identities")
    _strict_original_fragment(raw)
    matches = []
    first_n = first_verse.rsplit(".", 1)[-1].encode("ascii")
    old_n = original_end_verse.rsplit(".", 1)[-1].encode("ascii")
    new_n = proposed_end_verse.rsplit(".", 1)[-1].encode("ascii")
    label_form = re.compile(
        rb"(?<!\d)" + re.escape(first_n) + rb"\s*(?:-|\xe2\x80\x93)\s*"
        + rb"(?P<end>" + re.escape(old_n) + rb")(?!\d)"
    )
    for start_byte, close_byte, parsed_target in _parsed_reference_spans(raw):
        if _unambiguous_verse_range_endpoints(parsed_target) != (
                first_verse, original_end_verse):
            continue
        # Both boundaries belong to an actual parsed element. Any XML comment,
        # CDATA or nested-markup lookalike lacks these exact parser offsets.
        element = REFERENCE_ELEMENT.match(raw, start_byte)
        if (element is None or element.end("label") != close_byte
                or not raw[close_byte:].startswith(b"</reference>")):
            raise ValueError("Original reference does not have a direct-text XML label")
        attributes = element.group("attrs")
        attr = REF_ATTRIBUTE.search(attributes)
        if attr is None:
            raise ValueError("Parsed original reference has no exact osisRef attribute")
        try:
            existing = attr.group("value").decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Invalid original encoded scripture target") from None
        if existing != parsed_target:
            raise ValueError("Lexical source reference does not match parsed XML attribute")
        label = element.group("label")
        numeric = list(label_form.finditer(label))
        if len(numeric) != 1:
            raise ValueError("Original source link does not have one unambiguous numeric label")
        split = existing.rsplit("-", 1)
        if len(split) != 2:
            raise ValueError("Unrecognized original range delimiter")
        if split[1] == old_n.decode("ascii"):
            next_target = split[0] + "-" + new_n.decode("ascii")
        elif split[1] == original_end_verse:
            next_target = split[0] + "-" + proposed_end_verse
        else:
            raise ValueError("Original range endpoint has unsupported grammar")
        matches.append((
            element.start("attrs") + attr.start("value"),
            element.start("attrs") + attr.end("value"),
            next_target.encode("utf-8"),
            element.start("label") + numeric[0].start("end"),
            element.start("label") + numeric[0].end("end"),
            new_n,
        ))
    if len(matches) != 1:
        raise ValueError("Exactly one strict original reference node must match")
    left, right, target, label_start, label_end, label = matches[0]
    if (left >= right or label_start >= label_end
            or right >= label_start):
        raise ValueError("Original XML reference edit spans are not independent")
    # Replace from the right to keep offsets stable and every other byte exact.
    result = raw[:label_start] + label + raw[label_end:]
    result = result[:left] + target + result[right:]
    _strict_original_fragment(result)
    if result == raw:
        raise ValueError("Original and proposed source references are identical")
    return result


def preview_exact_reversible_commentary_reference_erratum(
        original_raw: bytes, *, first_verse: str,
        original_end_verse: str, proposed_end_verse: str) -> tuple[bytes, dict]:
    """Private only: return a proposed fragment and a text-free proof receipt."""
    if (int(original_end_verse.rsplit(".", 1)[-1]) >=
            int(first_verse.rsplit(".", 1)[-1])
            or int(proposed_end_verse.rsplit(".", 1)[-1]) <
            int(first_verse.rsplit(".", 1)[-1])):
        raise ValueError("Original range is not reversed or proposal remains reversed")
    patched = _apply_exact_original_link_change(
        original_raw, first_verse=first_verse,
        original_end_verse=original_end_verse,
        proposed_end_verse=proposed_end_verse)
    restored = _apply_exact_original_link_change(
        patched, first_verse=first_verse,
        original_end_verse=proposed_end_verse,
        proposed_end_verse=original_end_verse)
    if restored != original_raw:
        raise ValueError("Surgical commentary source correction is not byte-reversible")
    return patched, {
        "status": "PRIVATE_SINGLE_ORIGINAL_LINK_AND_LABEL_BYTE_REVERSIBLE_PREVIEW",
        "exactly_one_original_reference_and_label_changed": True,
        "original_raw_sha256": sha256(original_raw).hexdigest(),
        "proposed_raw_sha256": sha256(patched).hexdigest(),
        "reverse_restores_exact_original_raw_bytes": True,
        "no_other_original_xml_text_annotation_or_punctuation_changed": True,
        "source_text_edited_in_published_module": False,
        "editorial_change_authorized": False,
        "release_authorized": False,
        "original_prose_and_reference_values_disclosed": False,
    }
