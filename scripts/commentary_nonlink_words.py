#!/usr/bin/env python3
"""Source-neutral private comparison of actual words OUTSIDE scripture links.

A compiled reference display label without a <reference> wrapper appears as
stock plain text. Extra stock words may also be headings/tables or range text.
These categories NEVER establish authorial text, punctuation or edition parity.
"""
from __future__ import annotations

from collections import Counter
import unicodedata

from commentary_text_delta import _contiguous_offset, _is_subsequence
from pilot_preflight import PilotError

MAX_WORDS = 100000

def _validate_indices(indices: list[int], total: int) -> set[int]:
    if not isinstance(indices, list) or any(type(x) is not int for x in indices):
        raise PilotError("Unreviewed private original link index type")
    unique = set(indices)
    if len(indices) != len(unique) or any(x < 0 or x >= total for x in unique):
        raise PilotError("Original link/stock reference word offsets are not source-bound")
    return unique


def _source_extra_word_layout(original: list[str], compiled: list[str]) -> dict:
    """Bounded exact subsequence positions; never infer authored section ownership.

    Repeated words can permit several valid alignments. In that case no
    particular omitted-word span is treated as an authenticated source unit.
    """
    if (not original or not compiled or len(original) <= len(compiled)
            or len(original) > MAX_WORDS):
        raise PilotError("Source-extra word topology requires bounded longer original")
    earliest = []
    cursor = 0
    for word in compiled:
        while cursor < len(original) and original[cursor] != word:
            cursor += 1
        if cursor == len(original):
            raise PilotError("Selected compiled words are not ordered original tokens")
        earliest.append(cursor)
        cursor += 1
    latest = [0] * len(compiled)
    cursor = len(original) - 1
    for index in range(len(compiled) - 1, -1, -1):
        while cursor >= 0 and original[cursor] != compiled[index]:
            cursor -= 1
        if cursor < 0:
            raise PilotError("Reverse original word alignment disagrees with forward")
        latest[index] = cursor
        cursor -= 1
    excess = len(original) - len(compiled)
    if earliest != latest:
        return {
            "alignment_topology": "multiple_exact_subsequence_alignments_no_fixed_gap_ownership",
            "source_extra_nonlink_word_count": excess,
            "fixed_extra_word_spans": None,
            "fixed_prefix_extra_words": None,
            "fixed_interior_extra_words": None,
            "fixed_suffix_extra_words": None,
            "longest_fixed_extra_word_span": None,
            "textual_section_or_editional_ownership_established": False,
        }
    prefix = earliest[0]
    suffix = len(original) - 1 - earliest[-1]
    interior = excess - prefix - suffix
    if interior < 0:
        raise PilotError("Source word subsequence span accounting disagreement")
    if interior and (prefix or suffix):
        category = "unique_alignment_interior_and_edge_extra_words"
    elif interior:
        category = "unique_alignment_interior_extra_words_only"
    elif prefix and suffix:
        category = "unique_alignment_both_edges_extra_words_only"
    elif prefix:
        category = "unique_alignment_prefix_extra_words_only"
    else:
        category = "unique_alignment_suffix_extra_words_only"
    matched = set(earliest)
    runs = []
    run = 0
    for position in range(len(original)):
        if position not in matched:
            run += 1
        elif run:
            runs.append(run)
            run = 0
    if run:
        runs.append(run)
    if sum(runs) != excess:
        raise PilotError("Exact source extra word spans fail source/stock reconciliation")
    return {
        "alignment_topology": category,
        "source_extra_nonlink_word_count": excess,
        "fixed_extra_word_spans": len(runs),
        "fixed_prefix_extra_words": prefix,
        "fixed_interior_extra_words": interior,
        "fixed_suffix_extra_words": suffix,
        "longest_fixed_extra_word_span": max(runs),
        "textual_section_or_editional_ownership_established": False,
    }


def compare_words_outside_links(
    source_word_tokens: list[str],
    stock_word_tokens: list[str],
    source_link_word_indices: list[int],
    stock_reference_word_indices: list[int],
) -> dict:
    """Return only numeric counts and closed labels, never any original words."""
    if (not isinstance(source_word_tokens,list) or
            not isinstance(stock_word_tokens,list) or
            not all(isinstance(w,str) for w in source_word_tokens+stock_word_tokens) or
            max(len(source_word_tokens),len(stock_word_tokens)) > MAX_WORDS):
        raise PilotError("Original/compiled lexical stream outside safe review bounds")
    marked_source = _validate_indices(source_link_word_indices,len(source_word_tokens))
    marked_stock = _validate_indices(stock_reference_word_indices,len(stock_word_tokens))
    original = [w for n,w in enumerate(source_word_tokens) if n not in marked_source]
    compiled = [w for n,w in enumerate(stock_word_tokens) if n not in marked_stock]
    if not original and not compiled:
        category="no_plain_words_outside_citations_either_side"
    elif not original:
        category="stock_plain_words_only_after_removing_source_scripture_labels"
    elif not compiled:
        category="source_plain_words_only_after_removing_stock_scripture_labels"
    elif original==compiled:
        category="same_ordered_case_sensitive_unicode_plain_words"
    elif [x.casefold() for x in original]==[x.casefold() for x in compiled]:
        category="same_ordered_plain_words_only_casefold_differs"
    elif ([unicodedata.normalize("NFKC",x) for x in original]
          ==[unicodedata.normalize("NFKC",x) for x in compiled]):
        category="same_ordered_plain_words_only_nfkc_differs"
    elif len(original)<len(compiled) and _contiguous_offset(original,compiled) is not None:
        category="original_plain_words_contiguous_inside_longer_stock_plain_text"
    elif len(compiled)<len(original) and _contiguous_offset(compiled,original) is not None:
        category="stock_plain_words_contiguous_inside_longer_original_plain_text"
    elif len(original)<len(compiled) and _is_subsequence(original,compiled):
        category="original_plain_words_in_order_with_extra_unmarked_stock_words"
    elif len(compiled)<len(original) and _is_subsequence(compiled,original):
        category="stock_plain_words_in_order_with_extra_original_words"
    elif len(original)==len(compiled) and Counter(original)==Counter(compiled):
        category="same_plain_word_multiset_but_different_order"
    else:
        category="plain_word_order_or_selection_requires_editorial_review"
    extra_layout = (
        _source_extra_word_layout(original, compiled)
        if category in (
            "stock_plain_words_contiguous_inside_longer_original_plain_text",
            "stock_plain_words_in_order_with_extra_original_words",
        ) else None
    )
    shared=sum((Counter(original)&Counter(compiled)).values())
    if shared>min(len(original),len(compiled)):
        raise PilotError("Original/compiled plain word overlap exceeds available tokens")
    return {
        "outside_link_word_relation":category,
        "source_extra_unlinked_word_gap_layout":extra_layout,
        "original_plain_word_tokens":len(original),
        "stock_plain_word_tokens":len(compiled),
        "original_scripture_link_word_tokens_removed":len(marked_source),
        "stock_reference_word_tokens_removed":len(marked_stock),
        "shared_plain_word_multiset_occurrences":shared,
        "plain_word_containment_or_sequence_match_is_not_edition_or_markup_parity":True,
        "unmarked_compiled_citation_labels_may_be_counted_as_stock_plain_words":True,
        "actual_original_words_or_compiled_content_exposed":False,
    }
