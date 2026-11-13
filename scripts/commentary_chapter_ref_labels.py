#!/usr/bin/env python3
"""Read-only original ThML scripRef text ↔ stock raw XML reference witness.

No generated text, original reference attribute or stock XML is published.
A matching displayed label never validates an OSIS target, authorial edition,
citation scope or original annotation-range assignment.
"""
from __future__ import annotations

from collections import Counter
import re

from lxml import etree

from commentary_text_delta import _contiguous_offset
from pilot_preflight import PilotError

MAX_RAW_BYTES = 2 * 1024 * 1024
MAX_SOURCE_LINKS = 250
MAX_LINK_TEXT_CHARS = 10000
XML_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{0,127}")


def link_label_location(source_links: list[dict], raw: bytes) -> dict:
    """Compare source link display text against actual strictly parsed stock XML."""
    if len(raw) > MAX_RAW_BYTES or b"\x00" in raw:
        raise PilotError("Original stock raw XML too large or malformed for link audit")
    if len(source_links) > MAX_SOURCE_LINKS:
        raise PilotError("Original source link count exceeds safe bound")
    try:
        node = etree.fromstring(
            b"<stock>" + raw + b"</stock>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                huge_tree=False, recover=False, remove_blank_text=False,
            ),
        )
    except (ValueError, etree.XMLSyntaxError):
        raise PilotError("Cannot strictly parse original stock XML link structure") from None
    if any(isinstance(x, etree._Entity) for x in node.iter()):
        raise PilotError("Original stock XML link contains unresolved XML entity")
    all_text = "".join(node.itertext())
    references = [
        child for child in node.iter()
        if isinstance(child.tag, str)
        and child.tag.rsplit("}", 1)[-1] == "reference"
    ]
    reference_texts = ["".join(child.itertext()) for child in references]
    label_categories = Counter()
    attribute_types = Counter()
    for source_link in source_links:
        label = source_link.get("text")
        attr_names = source_link.get("attribute_name_types")
        if not isinstance(label, str) or len(label) > MAX_LINK_TEXT_CHARS:
            raise PilotError("Unreviewed original scripRef label text")
        if not isinstance(attr_names, list) or not all(
            isinstance(name, str) and XML_NAME.fullmatch(name) for name in attr_names
        ):
            raise PilotError("Unreviewed original scripRef attribute names")
        attribute_types.update(attr_names)
        words = re.findall(r"\w+", label)
        if not label.strip():
            status = "empty_original_label_unreviewed"
        elif any(label in ref_text for ref_text in reference_texts):
            status = "literal_label_inside_stock_reference_element"
        elif label in all_text:
            status = "literal_label_in_stock_text_outside_confirmed_reference_element"
        elif words and any(
            _contiguous_offset(words, re.findall(r"\w+", ref_text)) is not None
            for ref_text in reference_texts
        ):
            status = "word_tokens_in_stock_reference_element_different_punctuation"
        elif words and _contiguous_offset(words, re.findall(r"\w+", all_text)) is not None:
            status = "word_tokens_in_stock_text_different_punctuation_or_markup"
        else:
            status = "original_label_text_not_located_in_selected_stock_entry"
        label_categories[status] += 1
    if sum(label_categories.values()) != len(source_links):
        raise PilotError("Original source scripture-reference label count incomplete")
    return {
        "original_scripRef_label_count": len(source_links),
        "original_scripRef_attribute_name_occurrences": dict(sorted(attribute_types.items())),
        "original_scripRef_to_stock_text_location_classes": dict(sorted(label_categories.items())),
        "selected_stock_reference_element_count": len(references),
        "selected_stock_reference_elements_with_osisRef_attribute": sum(
            "osisRef" in child.attrib for child in references
        ),
        "matched_label_does_not_validate_reference_target_or_edition": True,
        "original_words_and_stock_XML_never_reported": True,
    }
