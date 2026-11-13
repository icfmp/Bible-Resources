#!/usr/bin/env python3
"""Private bounded alignment of original commentary prose OUTSIDE scripture links.

Only numerical counts and closed-set categories may leave temporary runners.
A longest common subsequence is a lexical location witness: it is never
proof of source attribution, edition identity, punctuation or preserved XML.
"""
from __future__ import annotations

from pilot_preflight import PilotError

MAX_WORDS_PER_SIDE = 4000
MAX_CELLS = 2_000_000


def plain_word_alignment(source: list[str], stock: list[str]) -> dict:
    """Compute exact Unicode ordered LCS and maximal contiguous word run.

    Two rows of dynamic programming are used for each metric (O(stock words)
    memory), with a reviewed cell cap; no original word is copied to output.
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
    prev_run = [0] * (m + 1)
    longest_run = 0
    for word in source:
        lcs = [0] * (m + 1)
        run = [0] * (m + 1)
        for j, compiled_word in enumerate(stock, start=1):
            if word == compiled_word:
                lcs[j] = prev_lcs[j-1] + 1
                run[j] = prev_run[j-1] + 1
                if run[j] > longest_run:
                    longest_run = run[j]
            else:
                lcs[j] = lcs[j-1] if lcs[j-1] >= prev_lcs[j] else prev_lcs[j]
        prev_lcs, prev_run = lcs, run
    common_ordered = prev_lcs[m]
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
