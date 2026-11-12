#!/usr/bin/env python3
"""Read-only, PRIVATE diagnostics of commentary stock XML prefix topology.

A source body's Unicode word sequence may appear after extra stock words.
This tool shows where that prefix sits in the *existing stock raw markup*.
It NEVER treats the prefix as a legitimate heading, edits text, or emits words,
punctuation strings, XML attributes, or original source/stock bytes.
"""
from __future__ import annotations

from collections import Counter
import re

from lxml import etree

from commentary_text_delta import WORD, _contiguous_offset
from commentary_xml_witness import safe_name

MAX_RAW = 2 * 1024 * 1024


def _parse_original_stock_fragment(raw: bytes):
    if not isinstance(raw, bytes) or len(raw) > MAX_RAW or b"\x00" in raw:
        raise ValueError("Unreviewed original stock XML fragment bounds")
    try:
        root = etree.fromstring(
            b"<stock_original>" + raw + b"</stock_original>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False))
    except (ValueError, etree.XMLSyntaxError, UnicodeError):
        raise ValueError("Original stock raw fragment is not strict XML") from None
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise ValueError("Unexpanded original stock XML entity")
    return root


def _text_segments(node, owner: str):
    if node.text:
        yield node.text, owner
    for child in node:
        if isinstance(child.tag, str):
            yield from _text_segments(child, owner)
        # Ignore comment / PI content, but account for its trailing text.
        if child.tail:
            yield child.tail, owner


def _top_level_segments(root):
    if root.text:
        yield root.text, "_ROOT_TEXT"
    for child in root:
        if isinstance(child.tag, str):
            label = safe_name(child.tag)
            # Excludes the direct child's own tail; tails of descendants are
            # retained by the recursive walker in original document order.
            if child.text:
                yield child.text, label
            for nested in child:
                if isinstance(nested.tag, str):
                    yield from _text_segments(nested, label)
                if nested.tail:
                    yield nested.tail, label
        if child.tail:
            yield child.tail, "_ROOT_TAIL"


def source_word_prefix_topology(source_text: str, original_stock_raw: bytes) -> dict:
    """Classify a real source-token match in the stock raw XML text stream.

    Source and compiled *word tokens* must match contiguously; punctuation and
    spacing remain *unverified*. A complete matched word sequence can still
    reflect a different digital edition, a different entry boundary, or
    unapproved additions. Only counts and XML tag names leave this function.
    """
    root = _parse_original_stock_fragment(original_stock_raw)
    compiled = "".join(root.itertext())
    segments = list(_top_level_segments(root))
    if "".join(text for text, _tag in segments) != compiled:
        raise ValueError("Source-neutral stock XML segment topology differs from native text")
    source_words = WORD.findall(source_text)
    stock_words = WORD.findall(compiled)
    if not source_words or len(source_words) >= len(stock_words):
        raise ValueError("No source body with strictly longer stock word sequence")
    start_token = _contiguous_offset(source_words, stock_words)
    if start_token is None or start_token == 0 or start_token + len(source_words) != len(stock_words):
        raise ValueError("Original source is not a pure stock-prefixed word sequence")
    matches = list(WORD.finditer(compiled))
    start_char = matches[start_token].start()
    preceding_markup_elements = Counter()
    before_text_top_tags = set()
    start_owner = None
    cursor = 0
    for text, top_owner in segments:
        end = cursor + len(text)
        if cursor <= start_char < end:
            start_owner = top_owner
        if cursor < start_char and any(ch.isalnum() for ch in text[:max(0, start_char-cursor)]):
            before_text_top_tags.add(top_owner)
        cursor = end
    if cursor != len(compiled) or start_owner is None:
        raise ValueError("Stock prefix/source boundary cannot be located in original XML")
    # Full top-level sibling subtree text offsets, computed with the same
    # exact traversal (not hypothetical publisher heading conversions).
    cursor = len(root.text or "")
    for child in root:
        if isinstance(child.tag, str):
            child_text = "".join(_text for _text, _owner in _text_segments(child, "unused"))
            end = cursor + len(child_text)
            if end <= start_char and child_text.strip():
                preceding_markup_elements[safe_name(child.tag)] += 1
            cursor = end
        cursor += len(child.tail or "")
    if cursor != len(compiled):
        raise ValueError("Top-level original stock markup offsets do not reconcile")
    return {
        "full_original_source_word_sequence_inside_stock": True,
        "unapproved_stock_extra_word_prefix_count": start_token,
        "source_word_boundary_stock_top_level_owner": start_owner,
        "top_level_element_types_wholly_before_original_source_words":
            dict(sorted(preceding_markup_elements.items())),
        "prefix_text_top_level_owner_types": sorted(before_text_top_tags),
        "source_boundary_is_at_start_of_stock_text": False,
        "source_and_stock_punctuation_or_markup_parity_verified": False,
        "additional_stock_words_approved_as_heading": False,
        "content_or_attributes_disclosed": False,
    }


def aligned_punctuation_gap_diagnostics(source_text: str, stock_text: str) -> dict:
    """Compare nonword symbols *between corresponding identical word tokens*.

    This proves only correspondence of punctuation *locations and codepoints*,
    not permission to replace original punctuation or approve a whole edition.
    """
    if WORD.findall(source_text) != WORD.findall(stock_text):
        raise ValueError("Punctuation gap comparison requires identical Unicode word tokens")
    source_gaps = WORD.split(source_text)
    stock_gaps = WORD.split(stock_text)
    if len(source_gaps) != len(stock_gaps):
        raise ValueError("Aligned word boundaries lost")
    mapped = Counter()
    gap_classes = Counter()
    gaps_changed = 0
    for a, b in zip(source_gaps, stock_gaps):
        ac = [c for c in a if not c.isspace()]
        bc = [c for c in b if not c.isspace()]
        if ac == bc:
            continue
        gaps_changed += 1
        if len(ac) == len(bc) == 1:
            mapped[f"U+{ord(ac[0]):04X}>U+{ord(bc[0]):04X}"] += 1
            gap_classes["one_to_one_glyph_substitution"] += 1
        elif len(ac) == 1 and not bc:
            gap_classes["one_source_glyph_removed_in_stock"] += 1
        elif len(bc) == 1 and not ac:
            gap_classes["one_stock_glyph_added"] += 1
        else:
            gap_classes["multi_glyph_or_reordered_gap_requires_review"] += 1
    if gaps_changed != sum(gap_classes.values()):
        raise ValueError("Punctuation gap classification incomplete")
    return {
        "punctuation_gap_changes": gaps_changed,
        "punctuation_gap_classes": dict(sorted(gap_classes.items())),
        "one_to_one_unicode_numeric_glyph_replacements": dict(sorted(mapped.items())),
        "all_nonword_glyph_differences_consistently_mapped":
            gaps_changed == gap_classes["one_to_one_glyph_substitution"],
        "editorial_punctuation_approval": False,
        "original_punctuation_modified": False,
        "text_or_punctuation_excerpts_exported": False,
    }
