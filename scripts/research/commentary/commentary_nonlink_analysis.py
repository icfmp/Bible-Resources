"""Private read-only commentary word comparisons outside Scripture references.

Groups two complementary, source-neutral analyses into one bounded, non-CLI
module: unlinked-word accounting and ordered Unicode word alignment.
Original function bodies are retained verbatim. Word matching is not proof
of edition identity, verse placement, link permission or textual fidelity.
"""
from __future__ import annotations

from collections import Counter
import unicodedata

from commentary_text_delta import (
    _contiguous_offset, _is_subsequence, longest_contiguous_token_run,
)
from pilot_preflight import PilotError


# A. Original source vs compiled words outside marked Scripture references.

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


def _private_unique_original_gap_windows(
    original: list[str], compiled: list[str],
) -> list[tuple[int,int]] | None:
    """Exact unique extra-word [start,end) windows in *unlinked* source tokens.

    Windows are private lexical coordinates, never authorized section/paragraph
    corrections. A repeated-token alignment returns None rather than guessing.
    """
    layout = _source_extra_word_layout(original,compiled)
    if layout["alignment_topology"] == (
            "multiple_exact_subsequence_alignments_no_fixed_gap_ownership"):
        return None
    cursor=0
    windows=[]
    for word in compiled:
        start=cursor
        while cursor<len(original) and original[cursor]!=word:
            cursor+=1
        if cursor>=len(original):
            raise PilotError("Original extra-word windows lost exact compiled alignment")
        if cursor>start:
            windows.append((start,cursor))
        cursor+=1
    if cursor<len(original):
        windows.append((cursor,len(original)))
    if (len(windows)!=layout["fixed_extra_word_spans"]
            or sum(b-a for a,b in windows)!=layout["source_extra_nonlink_word_count"]):
        raise PilotError("Original source-only lexical gap window counts do not reconcile")
    return windows


def _private_unique_original_gap_spans(
    original: list[str], compiled: list[str],
) -> list[list[str]] | None:
    """Preserve actual words only in private memory, never any metadata receipt."""
    windows=_private_unique_original_gap_windows(original,compiled)
    return None if windows is None else [original[a:b] for a,b in windows]


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

# B. Independent exact-case Unicode word order and classification.

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



def classify_original_link_label_effect_on_source_longer_words(
        original_words: list[str], native_words: list[str],
        source_link_word_positions: list[int]) -> dict:
    """Research source-extra words after excluding only authentic link-label text.

    Only originally marked *scripture reference label* word positions are
    removed from the source-side observation. Do not remove notes, quotations,
    verse text, book headings or any surrounding original authorial prose.
    This procedure never edits a source or asserts digital-edition parity.
    """
    if (not isinstance(original_words, list) or not isinstance(native_words, list)
            or not isinstance(source_link_word_positions, list)
            or not original_words or not native_words
            or any(not isinstance(w, str) or not w for w in original_words+native_words)
            or len(original_words) <= len(native_words)):
        raise PilotError("Original source-longer link-label review requires actual word streams")
    if any(type(i) is not int or i < 0 or i >= len(original_words)
           for i in source_link_word_positions):
        raise PilotError("Unreviewed original scripture link-label word offsets")
    if source_link_word_positions != sorted(set(source_link_word_positions)):
        raise PilotError("Original source linked words must have unique ordered positions")
    if (max(len(original_words), len(native_words)) >
            MAX_LINEAR_SUBSEQUENCE_WORDS):
        return {
            "source_original_link_label_exclusion_class":
                "source_or_native_words_exceed_exact_linear_review_budget",
            "original_all_words": len(original_words),
            "native_all_words": len(native_words),
            "original_marked_scripRef_label_words": len(source_link_word_positions),
            "original_unlinked_words": len(original_words)-len(source_link_word_positions),
            "source_original_extra_total_words_vs_native":len(original_words)-len(native_words),
            "full_original_source_or_native_text_modified":False,
            "source_link_label_exclusion_proves_authorial_omission":False,
        }
    if exact_unicode_source_ordered_subsequence(native_words,original_words) is not True:
        raise PilotError("Original stock words are not an ordered subsequence of source case")
    linked=set(source_link_word_positions)
    unlinked=[word for index,word in enumerate(original_words) if index not in linked]
    if unlinked == native_words:
        category="only_original_scripRef_label_words_account_for_full_source_extra"
    elif not unlinked:
        category="source_has_no_nonlinked_words_after_link_label_exclusion"
    elif exact_unicode_source_ordered_subsequence(unlinked,native_words):
        category="all_original_nonlinked_words_found_in_native_order"
    elif exact_unicode_source_ordered_subsequence(native_words,unlinked):
        category="native_words_in_order_with_extra_original_nonlink_words"
    else:
        category="source_nonlink_and_native_no_complete_ordered_containment"
    return {
        "source_original_link_label_exclusion_class":category,
        "original_all_words":len(original_words),
        "native_all_words":len(native_words),
        "original_marked_scripRef_label_words":len(source_link_word_positions),
        "original_unlinked_words":len(unlinked),
        "source_original_extra_total_words_vs_native":len(original_words)-len(native_words),
        "source_nonlink_word_surplus_vs_native":len(unlinked)-len(native_words),
        "comparison_uses_exact_case_sensitive_unicode_word_order":True,
        "excluded_only_original_XML_marked_reference_label_words":True,
        "full_original_source_or_native_text_modified":False,
        "source_link_label_exclusion_proves_authorial_omission":False,
        "full_original_edition_or_markup_parity_proven":False,
    }


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
