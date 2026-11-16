#!/usr/bin/env python3
"""Generic, byte-preserving proposed SWORD commentary erratum preflights.

Never changes original stock modules or repository data. In a PRIVATE in-memory
preview only, change a strictly identified original reference/@osisRef endpoint AND
its matching direct-text numeric label, or one reviewed plain-text typo. Reject ambiguous source
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


def _original_literal_text_spans(raw: bytes) -> list[tuple[int, int]]:
    """Locate genuine literal XML text/tail bytes; exclude comments and CDATA.

    Expat reports original UTF-8 byte offsets at CharacterData events. Entity
    expansions or CRLF normalization do not necessarily occupy the same raw
    byte span: those segments are intentionally ineligible for surgery.
    No XML serializer or regex-only element inference is involved.
    """
    prefix = b"<entry>"
    parser = expat.ParserCreate("UTF-8")
    depth = 0
    in_cdata = False
    spans: list[tuple[int, int]] = []

    def opening(name, attrs):
        nonlocal depth
        depth += 1

    def closing(name):
        nonlocal depth
        depth -= 1

    def cdata_start():
        nonlocal in_cdata
        in_cdata = True

    def cdata_end():
        nonlocal in_cdata
        in_cdata = False

    def chars(value):
        if in_cdata or depth < 1 or not value:
            return
        index = parser.CurrentByteIndex - len(prefix)
        literal = value.encode("utf-8")
        # Never mistake entity syntax or a normalized fragment for a raw
        # literal span that can be patched at these byte coordinates.
        if index >= 0 and raw[index:index + len(literal)] == literal:
            spans.append((index, index + len(literal)))

    parser.StartElementHandler = opening
    parser.EndElementHandler = closing
    parser.StartCdataSectionHandler = cdata_start
    parser.EndCdataSectionHandler = cdata_end
    parser.CharacterDataHandler = chars
    try:
        parser.Parse(prefix + raw + b"</entry>", True)
    except expat.ExpatError:
        raise ValueError("Original commentary XML text events unavailable") from None
    if depth or in_cdata or len(spans) > 100000:
        raise ValueError("Unbounded original commentary XML text events")
    return spans


def _surgical_literal_prose_change(
        raw: bytes, *, original_phrase: str, corrected_phrase: str) -> bytes:
    """Change one uniquely identified real XML text/tail phrase, never markup."""
    # Only bounded literal printable snippets are supported here. A further
    # generic adapter would be needed for non-ASCII/escaped source wording.
    form = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .,;:'()/-]{2,158}")
    if (not isinstance(original_phrase, str)
            or not isinstance(corrected_phrase, str)
            or not form.fullmatch(original_phrase)
            or not form.fullmatch(corrected_phrase)
            or original_phrase == corrected_phrase):
        raise ValueError("Unreviewed source-text erratum phrases")
    _strict_original_fragment(raw)
    before = original_phrase.encode("ascii")
    after = corrected_phrase.encode("ascii")
    # Context words/letters must remain whole lexical units. These boundaries
    # also reject replacing 'Dn' inside a longer proper name by accident.
    candidate = re.compile(rb"(?<![A-Za-z0-9_])"
                           + re.escape(before) + rb"(?![A-Za-z0-9_])")
    matches = []
    for start, end in _original_literal_text_spans(raw):
        matches.extend(
            (start + match.start(), start + match.end())
            for match in candidate.finditer(raw[start:end])
        )
    if len(matches) != 1:
        raise ValueError("Exactly one original XML literal-text phrase must match")
    start, end = matches[0]
    patched = raw[:start] + after + raw[end:]
    _strict_original_fragment(patched)
    return patched


def preview_exact_reversible_commentary_prose_erratum(
        original_raw: bytes, *, original_phrase: str,
        corrected_phrase: str) -> tuple[bytes, dict]:
    """Only a private, source-exact, text-free and byte-reversible proposal.

    A single literal correction is not an automatic editorial or publishing
    decision. The separately pinned source/edition and human explanation
    must independently justify the replacement.
    """
    revised = _surgical_literal_prose_change(
        original_raw, original_phrase=original_phrase,
        corrected_phrase=corrected_phrase,
    )
    restored = _surgical_literal_prose_change(
        revised, original_phrase=corrected_phrase,
        corrected_phrase=original_phrase,
    )
    if restored != original_raw:
        raise ValueError("Original commentary prose edit is not exactly reversible")
    return revised, {
        "status": "PRIVATE_SINGLE_ORIGINAL_PROSE_PHRASE_BYTE_REVERSIBLE_PREVIEW",
        "exactly_one_parsed_original_text_span_edited": True,
        "original_raw_sha256": sha256(original_raw).hexdigest(),
        "proposed_raw_sha256": sha256(revised).hexdigest(),
        "exact_original_byte_length_delta": len(revised) - len(original_raw),
        "reverse_restores_exact_original_raw_bytes": True,
        "all_other_original_xml_words_references_and_structure_preserved": True,
        "source_text_or_xml_exported": False,
        "original_or_published_module_modified": False,
        "release_authorized": False,
    }
