#!/usr/bin/env python3
"""Metadata-only census of structural tags in original SWORD raw XML entries.

Never equate aggregate markup counts to authorial editorial fidelity.
This observer receives already-parsed, private per-verse XML; it only returns
bounded counters and reference IDs, never words, attributes values or XML.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re

from lxml import etree

KNOWN_TAGS = frozenset({
    "abbr", "chapter", "catchWord", "div", "foreign", "hi", "inscription",
    "l", "lb", "lg", "list", "milestone", "name", "note", "p", "q",
    "reference", "seg", "speech", "title", "transChange", "verse", "w",
    "words", "item", "speaker", "rdg", "table", "row", "cell",
})
KNOWN_ATTRIBUTES = frozenset({
    "type", "subType", "sID", "eID", "osisID", "osisRef", "n",
    "lemma", "morph", "marker", "level", "canonical", "who",
    "resp", "xml:lang",
})
REF = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$")
MAX_SAMPLE_REFS = 4
# Approved OSIS/SWORD structural style identifiers only. Unknown values are
# counted as "other" rather than copied into public GitHub reports.
SAFE_STRUCTURE_STYLES = frozenset({
    "", "book", "chapter", "section", "paragraph", "poetry", "preverse",
    "x-p", "x-m", "x-mi", "x-pi", "x-pm", "x-pc", "x-pr",
    "x-q", "x-q1", "x-q2", "x-q3", "x-q4",
    "x-qm", "x-qm1", "x-qm2", "x-qr", "x-qc",
    "x-s", "x-s1", "x-s2", "x-s3", "x-ms", "x-mt",
    "x-intro", "x-title", "x-verse", "x-chapter",
})
STRUCTURAL_TAGS = frozenset({"div", "p", "milestone", "l", "lg", "lb", "q"})
_WORDS = re.compile(r"[^\\W_]+(?:['\\u2019][^\\W_]+)*", re.UNICODE)


def _style(value):
    return value if value in SAFE_STRUCTURE_STYLES else "other_unreviewed_style"


def _endpoint(element):
    opening, closing = "sID" in element.attrib, "eID" in element.attrib
    if opening and closing:
        raise ValueError("Ambiguous native structural milestone with both sID and eID")
    return "open_sID" if opening else "close_eID" if closing else "container_or_standalone"


def _relative_word_positions(root):
    """Recognize starts/end milestones relative to independently parsed text.

    Word ordinals are a diagnostic, not a claim of source layout equivalence.
    Original text is transient and never returned.
    """
    text = []
    marks = []

    def walk(node):
        if not isinstance(node.tag, str):
            return
        tag = etree.QName(node).localname
        if node is not root and tag in STRUCTURAL_TAGS:
            marks.append((node, len(_WORDS.findall("".join(text)))))
        if node is not root and tag in {"note", "title"}:
            return
        if node.text:
            text.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                text.append(child.tail)

    walk(root)
    n = len(_WORDS.findall("".join(text)))
    for element, words_before in marks:
        pos = ("before_first_word" if words_before == 0
               else "after_last_word" if words_before >= n
               else "inside_verse")
        yield element, pos


class NativeMarkupCensus:
    def __init__(self):
        self._verses = 0
        self._tags = Counter()
        self._attributes = Counter()
        self._categories = Counter()
        self._verses_with = Counter()
        self._samples = defaultdict(list)
        self._native_styles = Counter()
        self._native_structural_positions = Counter()
        self._native_endpoint_types = Counter()
        self._unknown_styles = 0

    def observe(self, ref: str, parsed_root: etree._Element):
        if not REF.fullmatch(ref):
            raise ValueError("Invalid native reference for structural scan")
        if etree.QName(parsed_root).localname != "private_root":
            raise ValueError("Unexpected private XML fragment wrapper")
        self._verses += 1
        seen = set()
        for element in parsed_root.iterdescendants():
            if not isinstance(element.tag, str):
                continue
            tag = etree.QName(element).localname
            safe_tag = tag if tag in KNOWN_TAGS else "other_unrecognized_xml_tag"
            self._tags[safe_tag] += 1
            for key in element.attrib:
                attr = etree.QName(key).localname
                self._attributes[attr if attr in KNOWN_ATTRIBUTES
                                 else "other_unrecognized_attribute_name"] += 1
            categories = set()
            if tag == "p":
                categories.add("explicit_paragraph_element")
            if tag in {"l", "lg", "lb"}:
                categories.add("explicit_poetry_or_linebreak_element")
            if tag == "title":
                categories.add("explicit_title_element")
            if tag == "note":
                categories.add("note_element")
            if tag in {"reference", "seg"}:
                categories.add("reference_or_segment_element")
            if tag == "milestone":
                raw_type = element.get("type", "")
                if raw_type in {"x-p", "x-m", "x-pi", "x-pm", "x-mi", "x-pc"}:
                    categories.add("paragraph_like_milestone")
                elif raw_type.startswith(("x-q", "x-qr", "x-qa", "x-qm")):
                    categories.add("poetry_like_milestone")
                else:
                    categories.add("other_milestone")
            if tag == "div" and element.get("type") in {"section", "paragraph"}:
                categories.add("explicit_section_or_paragraph_div")
            for category in categories:
                self._categories[category] += 1
                seen.add(category)
        for category in seen:
            self._verses_with[category] += 1
            if len(self._samples[category]) < MAX_SAMPLE_REFS:
                self._samples[category].append(ref)
        for element, position in _relative_word_positions(parsed_root):
            tag = etree.QName(element).localname
            endpoint = _endpoint(element)
            style = _style(element.get("type", ""))
            subtype = _style(element.get("subType", ""))
            self._native_styles[f"{tag}:{style}"] += 1
            if subtype not in ("", "other_unreviewed_style"):
                self._native_styles[f"{tag}:subType:{subtype}"] += 1
            if style == "other_unreviewed_style" or subtype == "other_unreviewed_style":
                self._unknown_styles += 1
            self._native_endpoint_types[f"{tag}:{endpoint}"] += 1
            self._native_structural_positions[
                f"{tag}:{endpoint}:{position}"] += 1

    def finish(self):
        return {
            "schema_version": 1,
            "native_numbered_verse_fragments_inspected": self._verses,
            "native_raw_element_counts": dict(sorted(self._tags.items())),
            "native_raw_attribute_name_counts": dict(sorted(self._attributes.items())),
            "native_structural_category_element_counts": dict(sorted(self._categories.items())),
            "native_numbered_verses_with_structural_category": dict(sorted(self._verses_with.items())),
            "first_reference_ids_without_scripture": dict(sorted(self._samples.items())),
            "native_structure_style_counts_allowlisted": dict(sorted(self._native_styles.items())),
            "native_structure_endpoint_counts": dict(sorted(self._native_endpoint_types.items())),
            "native_structure_relative_word_position_counts":
                dict(sorted(self._native_structural_positions.items())),
            "unrecognized_native_structural_style_occurrences": self._unknown_styles,
            "relative_positions_are_diagnostic_not_source_parity": True,
            "raw_markup_content_or_attribute_values_exposed": False,
            "aggregate_counts_are_not_original_layout_parity": True,
            "cross_verse_markers_and_verse_zero_positions_verified": False,
            "source_to_compiled_structure_fidelity_verified": False,
            "editorial_or_publication_approved": False,
        }
