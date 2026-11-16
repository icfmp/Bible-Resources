#!/usr/bin/env python3
"""Read-only paragraph structure comparison across two digital commentary witnesses.

Original manuscript/abridged edition authority is not established by matching
digital anchors. No original words, XML, markup, source attributes or rendered
paragraph text leave the private reader. This returns only canonical native
key IDs, structure counts and word-anchor offsets for manual review.

An independently digitized source's <p> nodes are *candidates* for faithful
restoration, never instructions to change CrossWire/SWORD content.
"""
from __future__ import annotations

from collections import Counter
import re

from lxml import etree

from commentary_layout_census import layout_profile, _strict_fragment
from commentary_xml_witness import WORK_REF, _parse_reference

WORD = re.compile(r"\w+", re.UNICODE)
MAX_SAMPLES = 8
MAX_SOURCE_MARKERS = 12
MAX_P = 250
MAX_ANCHOR_WORDS = 8


def _name(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _tokens(source: str) -> list[str]:
    return WORD.findall(source.casefold())


def _unique_offset(tokens: list[str], anchor: list[str]):
    """Report a token offset only for one exact unique anchor in the native text."""
    if len(anchor) < MAX_ANCHOR_WORDS or len(tokens) < len(anchor):
        return None
    size = len(anchor)
    positions = [i for i in range(len(tokens) - size + 1)
                 if tokens[i:i + size] == anchor]
    return positions[0] if len(positions) == 1 else None


def _first_reference(osis: str) -> str | None:
    if _parse_reference(osis)[0] not in (
            "work_qualified_chapter", "work_qualified_verse",
            "work_qualified_same_book_verse_range"):
        return None
    m = WORK_REF.fullmatch(osis)
    if m is None:
        return None
    return m.group(2).split("-", 1)[0]


def _source_sections(document) -> dict[str, list]:
    sections = {}
    for node in document.iter():
        if not isinstance(node.tag, str) or _name(node) != "scripCom":
            continue
        first = _first_reference(node.get("osisRef", ""))
        if first:
            sections.setdefault(first, []).append(node)
    return sections


def _source_chapter_and_section(marker):
    chapter = marker
    while chapter is not None and (
            not isinstance(chapter.tag, str) or _name(chapter) != "div2"):
        chapter = chapter.getparent()
    if chapter is None:
        return {"status": "SOURCE_MARKER_OUTSIDE_CHAPTER_DIV2"}
    numbered = [n for n in chapter.iter()
                if isinstance(n.tag, str) and _name(n) == "scripCom"]
    if marker not in numbered:
        raise ValueError("Independent source marker not found in own chapter")
    nodes = [n for n in chapter.iter() if isinstance(n.tag, str)]
    index = {n: i for i, n in enumerate(nodes)}
    start = index[marker]
    next_marker_node = next((n for n in numbered if index[n] > start), None)
    next_marker = index[next_marker_node] if next_marker_node is not None else len(nodes)
    paragraphs = [n for n in nodes if _name(n) == "p"]
    if len(paragraphs) > MAX_P:
        return {"status": "SOURCE_CHAPTER_HAS_TOO_MANY_PARAGRAPHS"}
    active = []
    for p in paragraphs:
        position = index[p]
        contains_marker = marker in p.iterdescendants()
        contains_next_marker = (
            next_marker_node is not None
            and next_marker_node in p.iterdescendants()
        )
        # Parent <p> may precede the marker in element preorder. Exclude
        # the paragraph wrapping a *subsequent* commentary section marker.
        if contains_marker or (start < position < next_marker
                               and not contains_next_marker):
            active.append(p)
    return {
        "status": "SOURCE_CHAPTER_SECTION_MARKER_LOCATED",
        "source_chapter_p_count": len(paragraphs),
        "source_chapter_scripcom_count": len(numbered),
        "candidate_section_p_nodes": active,
        "marker_inside_p": any(marker in p.iterdescendants() for p in paragraphs),
        "marker_parent_element_type": _name(marker.getparent())
                                      if marker.getparent() is not None else "ROOT",
    }


def compare_paragraph_witness(document, samples: list[tuple[str, str, bytes]]) -> dict:
    """Inspect independently pinned ThML with exact original native I/K samples.

    The caller has already authenticated both original inputs against their
    pinned source checksums; this does not establish print-edition equivalence.
    """
    if (len(samples) > MAX_SAMPLES
            or len({(kind, key) for kind, key, _ in samples}) != len(samples)):
        raise ValueError("Invalid bounded original commentary paragraph samples")
    sections = _source_sections(document)
    rows = []
    for kind, key, raw in samples:
        if kind not in ("I", "K"):
            raise ValueError("Only original native commentary I/K are eligible")
        own = _strict_fragment(raw)
        original_words = _tokens("".join(own.itertext()))
        profile = layout_profile(raw)
        match = sections.get(key, [])
        row = {
            "original_native_kind": kind,
            "original_native_key": key,
            "original_native_word_tokens": len(original_words),
            "original_existing_p_count": profile["p_count"],
            "original_unowned_prose_words": profile["words_outside_any_recognized_block"],
            "source_scripcom_markers_with_exact_start": len(match),
            "original_text_or_reference_changed": False,
            "source_words_or_xml_in_report": False,
            "candidate_para_boundaries_authorized": False,
            "source_digital_edition_equivalence_proven": False,
        }
        if len(match) != 1:
            row["status"] = (
                "NO_UNIQUE_INDEPENDENT_MARKER"
                if len(match) <= MAX_SOURCE_MARKERS else "EXCESS_SOURCE_MARKERS"
            )
            rows.append(row)
            continue
        scope = _source_chapter_and_section(match[0])
        row["status"] = scope["status"]
        if scope["status"] != "SOURCE_CHAPTER_SECTION_MARKER_LOCATED":
            rows.append(row)
            continue
        pnodes = scope.pop("candidate_section_p_nodes")
        row.update(scope)
        row["candidate_source_section_p_count"] = len(pnodes)
        anchors = []
        for p in pnodes:
            pwords = _tokens("".join(p.itertext()))
            # Eight-word lexical anchoring is only a *location clue*; it is
            # NOT proof of editorial/print identity or punctuation parity.
            begin = _unique_offset(original_words, pwords[:MAX_ANCHOR_WORDS])
            tail = _unique_offset(original_words, pwords[-MAX_ANCHOR_WORDS:])
            # A matched beginning AND end can still conceal changed middle
            # prose. Check every Unicode word token, in exact original order.
            # A differently punctuated digital edition may pass this token
            # test: it is NOT punctuation or original-edition parity proof.
            end = begin + len(pwords) if begin is not None else None
            aligned = original_words[begin:end] if begin is not None and (
                end <= len(original_words)) else None
            mismatches = (
                [i for i, (source_word, original_word)
                 in enumerate(zip(pwords, aligned))
                 if source_word != original_word]
                if aligned is not None else None
            )
            whole = (
                aligned is not None
                and not mismatches
                and (tail is None or tail == end - MAX_ANCHOR_WORDS)
            )
            anchors.append({
                "source_p_word_tokens": len(pwords),
                "unique_native_start_token_offset": begin,
                "unique_native_end_anchor_token_offset": tail,
                "both_8_word_anchors_uniquely_present":
                    begin is not None and tail is not None and begin <= tail,
                "all_source_p_words_exact_contiguous_original_order": whole,
                "original_digital_witness_same_position_word_difference_count": (
                    len(mismatches) if mismatches is not None else None
                ),
                "original_digital_witness_first_difference_token_offset": (
                    mismatches[0] if mismatches else None
                ),
                "all_differences_require_independent_editorial_review": True,
                "original_prefix_word_tokens_before_exact_source_p": (
                    begin if whole else None
                ),
                "original_suffix_word_tokens_after_exact_source_p": (
                    len(original_words) - end if whole else None
                ),
            })
        row["source_paragraph_lexical_anchors"] = anchors
        row["paragraphs_with_both_unique_8_word_anchors"] = sum(
            a["both_8_word_anchors_uniquely_present"] for a in anchors
        )
        row["source_paragraphs_with_all_words_in_exact_original_order"] = sum(
            a["all_source_p_words_exact_contiguous_original_order"]
            for a in anchors
        )
        rows.append(row)
    return {
        "status": "PRIVATE_DIGITAL_SOURCE_PARAGRAPH_PILOT_NOT_EDITORIAL_APPROVAL",
        "selected_original_native_I_K_entries": len(rows),
        "results": rows,
        "source_text_xml_annotation_attributes_exported": False,
        "original_stock_or_source_modified": False,
        "public_release_authorized": False,
    }
