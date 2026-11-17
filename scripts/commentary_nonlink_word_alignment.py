#!/usr/bin/env python3
"""Private bounded alignment of original commentary prose OUTSIDE scripture links.

Only numerical counts and closed-set categories may leave temporary runners.
A longest common subsequence is a lexical location witness: it is never
proof of source attribution, edition identity, punctuation or preserved XML.
"""
from __future__ import annotations

from commentary_text_delta import longest_contiguous_token_run
from pilot_preflight import PilotError

MAX_WORDS_PER_SIDE = 4000
MAX_CELLS = 2_000_000
MAX_LINEAR_SUBSEQUENCE_WORDS = 100_000


def exact_unicode_source_ordered_subsequence(source: list[str], stock: list[str]) -> bool | None:
    """Linear exact-case Unicode word-order witness, not an edit-distance or edition check.

    True proves only that every source token occurs in order in the stock.
    False is NOT evidence that original prose was omitted; different order is possible.
    None means even the independent linear input bound was exceeded.
    """
    if max(len(source), len(stock)) > MAX_LINEAR_SUBSEQUENCE_WORDS:
        return None
    matched = 0
    for token in stock:
        if matched < len(source) and token == source[matched]:
            matched += 1
    return matched == len(source)



def plain_word_alignment(source: list[str], stock: list[str]) -> dict:
    """Compute exact Unicode ordered LCS and maximal contiguous word run.

    The LCS retains its bounded two-row dynamic-programming witness;
    the exact contiguous run uses the independently shared, strict-token
    primitive. Neither output exposes original words or proves fidelity.
    """
    if (not isinstance(source, list) or not isinstance(stock, list)
            or not all(isinstance(w, str) and w for w in source)
            or not all(isinstance(w, str) and w for w in stock)):
        raise PilotError("Original commentary plain-word streams are invalid")
    n, m = len(source), len(stock)
    if n > MAX_WORDS_PER_SIDE or m > MAX_WORDS_PER_SIDE or n * m > MAX_CELLS:
        return {
            "exact_unicode_ordered_alignment_class":
                "alignment_skipped_exceeds_reviewed_word_or_cell_bound",
            "original_plain_word_tokens": n,
            "stock_plain_word_tokens": m,
            "original_plain_words_not_matched_in_exact_order": None,
            "stock_plain_words_not_matched_in_exact_order": None,
            "exact_unicode_longest_common_subsequence_word_count": None,
            "exact_unicode_longest_contiguous_shared_word_run_count": None,
            "linear_exact_source_subsequence_in_stock":
                exact_unicode_source_ordered_subsequence(source, stock),
            "linear_source_subsequence_does_not_certify_original_text_or_markup_parity": True,
            "common_start_word_tokens": None,
            "common_end_word_tokens": None,
            "alignment_budget_cells": MAX_CELLS,
            "longest_common_subsequence_is_not_textual_or_edition_parity": True,
            "original_words_never_exposed": True,
        }
    common_prefix = 0
    while common_prefix < min(n, m) and source[common_prefix] == stock[common_prefix]:
        common_prefix += 1
    common_suffix = 0
    # Prefix and suffix word comparisons cannot overlap the shared prefix.
    while (common_suffix < min(n, m) - common_prefix
           and source[n - 1 - common_suffix] == stock[m - 1 - common_suffix]):
        common_suffix += 1
    prev_lcs = [0] * (m + 1)
    for word in source:
        lcs = [0] * (m + 1)
        for j, compiled_word in enumerate(stock, start=1):
            if word == compiled_word:
                lcs[j] = prev_lcs[j-1] + 1
            else:
                lcs[j] = lcs[j-1] if lcs[j-1] >= prev_lcs[j] else prev_lcs[j]
        prev_lcs = lcs
    common_ordered = prev_lcs[m]
    longest_run = longest_contiguous_token_run(source, stock)
    if common_ordered > min(n, m) or longest_run > common_ordered:
        raise PilotError("Original/compiled Unicode word alignment accounting invalid")
    source_unmatched, stock_unmatched = n - common_ordered, m - common_ordered
    if source_unmatched == 0 and stock_unmatched == 0:
        category = "plain_words_exactly_identical_in_original_order"
    elif source_unmatched == 0:
        category = "all_source_plain_words_in_stock_order_with_extra_stock_words"
    elif stock_unmatched == 0:
        category = "all_stock_plain_words_in_source_order_with_extra_source_words"
    elif source_unmatched <= 2:
        category = "one_or_two_original_plain_words_not_found_in_exact_order"
    elif source_unmatched <= 10:
        category = "three_to_ten_original_plain_words_not_found_in_exact_order"
    else:
        category = "more_than_ten_original_plain_words_not_found_in_exact_order"
    return {
        "exact_unicode_ordered_alignment_class": category,
        "original_plain_word_tokens": n,
        "stock_plain_word_tokens": m,
        "original_plain_words_not_matched_in_exact_order": source_unmatched,
        "stock_plain_words_not_matched_in_exact_order": stock_unmatched,
        "exact_unicode_longest_common_subsequence_word_count": common_ordered,
        "exact_unicode_longest_contiguous_shared_word_run_count": longest_run,
        "common_start_word_tokens": common_prefix,
        "common_end_word_tokens": common_suffix,
        "alignment_budget_cells": MAX_CELLS,
        "longest_common_subsequence_is_not_textual_or_edition_parity": True,
        "original_words_never_exposed": True,
    }
