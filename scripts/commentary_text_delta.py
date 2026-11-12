#!/usr/bin/env python3
"""PRIVATE, source-neutral lexical difference diagnostics for commentary audits.

Never repairs sources or treats normalized matches as fidelity. Pure helpers
return ONLY closed-set category labels and numeric token statistics. Original
words, punctuation, headings, excerpts and revised strings are never emitted.
"""
from __future__ import annotations

from collections import Counter
import re
import unicodedata

WORD = re.compile(r"\w+", flags=re.UNICODE)
RATIO_BOUNDS = (40, 70, 90, 98)


def _is_contiguous(needle: list[str], haystack: list[str]) -> bool:
    """KMP sublist check; bounded O(n + m), including repeated words."""
    if not needle:
        return False
    table = [0] * len(needle)
    matched = 0
    for i in range(1, len(needle)):
        while matched and needle[i] != needle[matched]:
            matched = table[matched - 1]
        if needle[i] == needle[matched]:
            matched += 1
        table[i] = matched
    matched = 0
    for token in haystack:
        while matched and token != needle[matched]:
            matched = table[matched - 1]
        if token == needle[matched]:
            matched += 1
        if matched == len(needle):
            return True
    return False


def _is_subsequence(needle: list[str], haystack: list[str]) -> bool:
    """Order-preserving but not necessarily contiguous."""
    if not needle:
        return False
    i = 0
    for token in haystack:
        if token == needle[i]:
            i += 1
            if i == len(needle):
                return True
    return False


def punctuation_relationship(source: str, stock: str) -> str:
    """Classify ONLY when case-sensitive Unicode word-token lists match.

    Punctuation symbols and source words are examined in-memory, never
    returned. Whitespace is excluded from this *diagnostic* classification.
    """
    a_tokens, b_tokens = WORD.findall(source), WORD.findall(stock)
    if a_tokens != b_tokens:
        raise ValueError("Punctuation analysis requires identical source/stock word tokens")
    a = "".join(char for segment in WORD.split(source)
                for char in segment if not char.isspace())
    b = "".join(char for segment in WORD.split(stock)
                for char in segment if not char.isspace())
    if a == b:
        return "same_nonword_symbols_but_positions_or_whitespace_differ"
    if not a:
        return "nonword_symbols_only_in_stock"
    if not b:
        return "nonword_symbols_only_in_source"
    if a in b:
        return "stock_nonword_symbols_contain_source_sequence"
    if b in a:
        return "source_nonword_symbols_contain_stock_sequence"
    if Counter(a) == Counter(b):
        return "same_nonword_symbol_counts_different_order"
    return "nonword_symbol_identity_or_counts_differ"


def word_relationship(source: str, stock: str) -> dict:
    """Closed-label diagnostics for two *unequal* Unicode word sequences.

    A perfect casefold, NFKC, subsequence, or token-overlap relationship is
    NOT an editorially approved source/stock match.
    """
    a, b = WORD.findall(source), WORD.findall(stock)
    if a == b:
        raise ValueError("Word difference diagnosis requires different word token sequences")
    if not a or not b:
        category = "source_or_stock_has_no_unicode_word_tokens"
    elif [x.casefold() for x in a] == [x.casefold() for x in b]:
        category = "only_unicode_casefold_differences"
    elif ([unicodedata.normalize("NFKC", x) for x in a]
          == [unicodedata.normalize("NFKC", x) for x in b]):
        category = "only_unicode_compatibility_word_differences"
    elif len(a) == len(b) and Counter(a) == Counter(b):
        category = "same_word_multiset_but_order_differs"
    elif len(a) < len(b) and _is_contiguous(a, b):
        category = "source_words_contiguous_inside_longer_stock"
    elif len(b) < len(a) and _is_contiguous(b, a):
        category = "stock_words_contiguous_inside_longer_source"
    elif len(a) < len(b) and _is_subsequence(a, b):
        category = "source_words_in_order_with_extra_stock_words"
    elif len(b) < len(a) and _is_subsequence(b, a):
        category = "stock_words_in_order_with_extra_source_words"
    else:
        category = "different_word_order_or_selection_requires_review"
    intersection = sum((Counter(a) & Counter(b)).values())
    max_tokens = max(len(a), len(b))
    percent = (intersection * 100 // max_tokens) if max_tokens else 100
    if percent < 40:
        bucket = "word_multiset_overlap_under_40pct"
    elif percent < 70:
        bucket = "word_multiset_overlap_40_to_69pct"
    elif percent < 90:
        bucket = "word_multiset_overlap_70_to_89pct"
    elif percent < 98:
        bucket = "word_multiset_overlap_90_to_97pct"
    else:
        bucket = "word_multiset_overlap_98_to_100pct"
    return {
        "relationship": category,
        "overlap_bucket": bucket,
        "original_word_token_count": len(a),
        "stock_word_token_count": len(b),
        "shared_word_token_multiset_occurrences": intersection,
        "exact_text_equivalence_established": False,
        "word_sequences_or_original_content_returned": False,
    }
