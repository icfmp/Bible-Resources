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
    shared=sum((Counter(original)&Counter(compiled)).values())
    if shared>min(len(original),len(compiled)):
        raise PilotError("Original/compiled plain word overlap exceeds available tokens")
    return {
        "outside_link_word_relation":category,
        "original_plain_word_tokens":len(original),
        "stock_plain_word_tokens":len(compiled),
        "original_scripture_link_word_tokens_removed":len(marked_source),
        "stock_reference_word_tokens_removed":len(marked_stock),
        "shared_plain_word_multiset_occurrences":shared,
        "plain_word_containment_or_sequence_match_is_not_edition_or_markup_parity":True,
        "unmarked_compiled_citation_labels_may_be_counted_as_stock_plain_words":True,
        "actual_original_words_or_compiled_content_exposed":False,
    }
