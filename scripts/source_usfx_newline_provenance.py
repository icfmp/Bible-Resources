#!/usr/bin/env python3
"""Independent source-USFX XML fragment provenance for *captured* verse newlines.

Every source-newline position is identified by numbered verse and preceding
non-whitespace Unicode codepoint ordinal, then classified by the actual
lxml text-node or element-tail where it originated. This does NOT decide
whether XML line wrapping is authorial formatting. Source characters and
unknown XML labels never enter the public receipt.
"""
from __future__ import annotations

from collections import defaultdict

from lxml import etree

from source_native_word_boundaries import (
    BoundaryAuditError, SOURCE_NOT_MAIN, _parsed_original,
)
from source_native_paragraph_counts import classify_prefatory_p_sfm
from stable_sword_refs import KEY

MAX_SOURCE_VERSE = 2 * 1024 * 1024
SOURCE_NEWLINE_ORIGIN_LABELS = frozenset({
    "tail_after_numbering_milestone",
    "tail_after_poetry_element",
    "tail_after_paragraph_element",
    "tail_after_annotation_element",
    "tail_after_inline_element",
    "tail_after_other_or_unreviewed_element",
    "text_within_poetry_element",
    "text_within_paragraph_element",
    "text_within_inline_element",
    "text_within_other_or_unreviewed_element",
})



class SourceNewlineProvenanceError(ValueError):
    """Original authorial verse fragment provenance is ambiguous."""


def _local_name(node):
    if not isinstance(node.tag, str):
        return ""
    return etree.QName(node).localname


def _source_segment_category(owner, is_tail):
    tag = _local_name(owner)
    if is_tail:
        if tag in {"v", "ve", "c"}:
            return "tail_after_numbering_milestone"
        if tag == "q":
            return "tail_after_poetry_element"
        if tag == "p":
            return "tail_after_paragraph_element"
        if tag in {"f", "fe", "x", "note", "ef", "ex"}:
            return "tail_after_annotation_element"
        if tag in {"hi", "it", "sc", "nd", "w", "char", "seg", "reference", "ref"}:
            return "tail_after_inline_element"
        return "tail_after_other_or_unreviewed_element"
    if tag == "q":
        return "text_within_poetry_element"
    if tag == "p":
        return "text_within_paragraph_element"
    if tag in {"hi", "it", "sc", "nd", "w", "char", "seg", "reference", "ref"}:
        return "text_within_inline_element"
    return "text_within_other_or_unreviewed_element"


def newline_gaps_from_text(text: str) -> set[int]:
    """Private gap positions, excluding non-authorial verse/book separators."""
    gap = 0
    positions = set()
    for char in text:
        if char in "\r\n\u2028\u2029":
            positions.add(gap)
        if not char.isspace():
            gap += 1
    return positions


def classify_source_newline_gaps(xml: bytes, mapping, source_verses: dict):
    """Read exact original source text/tails independently of stock SWORD.

    Result contains only private per-verse positions and *allowlisted*
    origin labels. The caller must NOT upload its raw mapping; aggregate it
    through the metadata-only whitespace classifier first.
    """
    crosswalk = dict(mapping)
    if (not crosswalk or len(mapping) != len(crosswalk)
            or len(set(crosswalk.values())) != len(mapping)):
        raise SourceNewlineProvenanceError("Invalid or ambiguous source book mapping")
    try:
        root = _parsed_original(xml)
    except BoundaryAuditError as exc:
        raise SourceNewlineProvenanceError("Original USFX cannot be parsed safely") from exc

    observed_parts = defaultdict(list)
    newline_origins = defaultdict(lambda: defaultdict(set))
    seen_books = set()
    for book in root.iter("book"):
        authorial = book.get("id")
        if authorial not in crosswalk or authorial in seen_books:
            raise SourceNewlineProvenanceError("Unmapped or duplicated source book")
        seen_books.add(authorial)
        native_book = crosswalk[authorial]
        chapter = None
        current = None
        nonspace_index = 0

        def append(fragment, owner, is_tail=False):
            nonlocal nonspace_index
            if current is None or not fragment:
                return
            observed_parts[current].append(fragment)
            category = _source_segment_category(owner, is_tail)
            for char in fragment:
                if char in "\r\n\u2028\u2029":
                    newline_origins[current][nonspace_index].add(category)
                if not char.isspace():
                    nonspace_index += 1

        def visit(node, depth=0):
            nonlocal chapter, current, nonspace_index
            if depth > 256:
                raise SourceNewlineProvenanceError("Excessive source XML nesting")
            tag = _local_name(node)
            if not tag:
                return
            style = node.get("sfm", "")
            excluded = (tag in SOURCE_NOT_MAIN
                        or (tag == "p" and style == "sp")
                        or (tag == "p" and chapter is None
                            and classify_prefatory_p_sfm(style)[0] == "book_title_style"))
            if excluded:
                if any(_local_name(child) in {"c", "v"}
                       for child in node.iterdescendants()):
                    raise SourceNewlineProvenanceError(
                        "Excluded source structure contains numbered verse markers")
                return
            if tag == "c":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0:
                    raise SourceNewlineProvenanceError("Invalid authorial chapter marker")
                chapter, current = int(value), None
            elif tag == "v":
                value = node.get("id", "")
                if chapter is None or not value.isdecimal() or int(value) <= 0:
                    raise SourceNewlineProvenanceError("Invalid authorial verse marker")
                current = f"{native_book}.{chapter}.{int(value)}"
                if current in observed_parts:
                    raise SourceNewlineProvenanceError("Duplicate source numbered verse")
                observed_parts[current] = []
                nonspace_index = 0
            elif tag == "ve":
                current = None
                return
            if tag not in {"c", "v"}:
                append(node.text, node)
            for child in node:
                visit(child, depth + 1)
                append(child.tail, child, is_tail=True)

        visit(book)
    if seen_books != set(crosswalk):
        raise SourceNewlineProvenanceError("Incomplete authorial book coverage")
    if set(observed_parts) != set(source_verses):
        raise SourceNewlineProvenanceError("Source newline scanner verse inventory differs")
    result = {}
    for ref, chunks in observed_parts.items():
        if not KEY.fullmatch(ref):
            raise SourceNewlineProvenanceError("Unsafe authorial mapped reference")
        reconstructed = "".join(chunks)
        if (reconstructed != source_verses[ref]
                or len(reconstructed.encode("utf-8")) > MAX_SOURCE_VERSE):
            raise SourceNewlineProvenanceError(
                "Source newline scanner disagrees with independent main-text reader")
        origins = newline_origins[ref]
        if set(origins) != newline_gaps_from_text(reconstructed):
            raise SourceNewlineProvenanceError(
                "XML fragment provenance failed complete original newline-gap coverage")
        result[ref] = {
            int(offset): frozenset(labels) for offset, labels in origins.items()
        }
    return result
