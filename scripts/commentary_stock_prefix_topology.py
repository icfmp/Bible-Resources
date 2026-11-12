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


def stock_prefix_context_correspondence(
    source_text: str, stock_raw: bytes, candidate_source_strings: list[tuple[str,str]]
) -> dict:
    """Compare actual earlier stock title/table/reference text to source neighbors.

    Only an exact Unicode string match, whitespace-only match, or identical
    Unicode word-token sequence is observed. None identifies the stock prefix
    as authorial, licensable, or accurate; source context may belong to a
    surrounding book/chapter and not to the particular annotated body.
    """
    if len(candidate_source_strings)>8 or any(
        not isinstance(kind,str) or not isinstance(value,str) or len(value)>2048
        for kind,value in candidate_source_strings
    ):
        raise ValueError("Unreviewed original neighboring context candidate")
    allowed_types={
        "source_marker_passage_attribute",
        "source_div2_title_attribute",
        "source_div1_title_attribute",
        "source_immediate_previous_heading_element",
    }
    if any(kind not in allowed_types for kind,_value in candidate_source_strings):
        raise ValueError("Unknown original source neighbor candidate type")
    root = _parse_original_stock_fragment(stock_raw)
    compiled="".join(root.itertext())
    original_words=WORD.findall(source_text)
    stock_matches=list(WORD.finditer(compiled))
    stock_words=[m.group(0) for m in stock_matches]
    start=_contiguous_offset(original_words,stock_words)
    if start is None or start<=0 or start+len(original_words)!=len(stock_words):
        raise ValueError("Stock entry is not a source-word-aligned prefixed body")
    source_word_start_char=stock_matches[start].start()
    matches=Counter()
    preceding_counts=Counter()
    candidate_types=Counter(kind for kind,value in candidate_source_strings if value.strip())
    any_exact=False
    any_word_only=False
    cursor=len(root.text or "")
    for child in root:
        if isinstance(child.tag,str):
            label=safe_name(child.tag)
            raw_text="".join(child.itertext())
            end=cursor+len(raw_text)
            if end<=source_word_start_char and raw_text.strip():
                if label in {"title","table","reference"}:
                    preceding_counts[label]+=1
                    for kind,original in candidate_source_strings:
                        if not original.strip():
                            continue
                        if raw_text==original:
                            matches[f"exact_unicode:{label}:{kind}"]+=1
                            any_exact=True
                        elif raw_text.strip()==original.strip():
                            matches[f"only_outer_whitespace:{label}:{kind}"]+=1
                        elif WORD.findall(raw_text)==WORD.findall(original):
                            matches[f"same_unicode_word_tokens_not_exact:{label}:{kind}"]+=1
                            any_word_only=True
            cursor=end
        cursor+=len(child.tail or "")
    if cursor!=len(compiled):
        raise ValueError("Stock source-title context byte traversal does not cover complete original text")
    return {
        "authenticated_source_neighbor_candidate_type_counts":dict(sorted(candidate_types.items())),
        "preceding_stock_metadata_element_count_by_tag":dict(sorted(preceding_counts.items())),
        "source_neighbor_to_stock_element_correspondence_classes":dict(sorted(matches.items())),
        "any_exact_source_neighbor_text_in_stock_metadata":any_exact,
        "any_only_word_token_source_neighbor_in_stock_metadata":any_word_only,
        "actual_source_candidate_is_not_approved_compiled_heading":True,
        "source_or_stock_text_or_attribute_values_disclosed":False,
    }


def stock_prefixed_source_body_concordance(source_text: str, original_stock_raw: bytes) -> dict:
    """Compare the author's source body to the real stock suffix *without changing bytes*.

    This is a second diagnostic view of a stock entry whose original source
    WORD tokens exactly occupy the *ending* stock word sequence. The entire
    original stock entry remains retained; nothing is stripped/recompiled.
    Exact lexical suffix equality does NOT approve extra stock prefix content.
    """
    root = _parse_original_stock_fragment(original_stock_raw)
    stock_text = "".join(root.itertext())
    original_words = WORD.findall(source_text)
    stock_word_matches = list(WORD.finditer(stock_text))
    stock_words = [match.group(0) for match in stock_word_matches]
    if not original_words or len(original_words) >= len(stock_words):
        raise ValueError("No additional stock words before source original")
    offset = _contiguous_offset(original_words, stock_words)
    if offset is None or not offset or offset + len(original_words) != len(stock_words):
        raise ValueError("Original does not occupy complete stock ending word sequence")
    stock_suffix = stock_text[stock_word_matches[offset].start():]
    if WORD.findall(stock_suffix) != original_words:
        raise ValueError("Stock source-word suffix no longer aligns exactly")
    if source_text == stock_suffix:
        match_class = "exact_source_body_unicode_equals_stock_text_suffix"
    elif source_text.lstrip() == stock_suffix:
        match_class = "only_source_leading_whitespace_before_first_word"
    elif source_text.strip() == stock_suffix.strip():
        match_class = "only_edge_whitespace_differences"
    elif " ".join(source_text.split()) == " ".join(stock_suffix.split()):
        match_class = "only_interior_whitespace_differences"
    else:
        match_class = "same_original_word_sequence_with_other_punctuation_or_markup_text_difference"
    punctuation = aligned_punctuation_gap_diagnostics(source_text, stock_suffix)
    return {
        "stock_extra_prefix_word_tokens": offset,
        "suffix_original_word_tokens_consistent": len(original_words),
        "original_source_body_to_stock_suffix_class": match_class,
        "aligned_suffix_changed_nonword_gaps": punctuation["punctuation_gap_changes"],
        "aligned_suffix_gap_class_counts": punctuation["punctuation_gap_classes"],
        "aligned_suffix_one_to_one_numeric_glyph_substitutions":
            punctuation["one_to_one_unicode_numeric_glyph_replacements"],
        "source_leading_nonspace_punctuation_before_first_word": bool(
            source_text and any(not char.isspace() for char in source_text[:WORD.search(source_text).start()])
        ),
        "stock_raw_full_prefix_retained": True,
        "stock_prefix_proven_authorial_or_legal": False,
        "complete_authorial_text_and_structure_parity_proven": False,
        "original_text_or_markup_disclosed": False,
    }


def unexplained_word_boundary_census(source_text: str, stock_text: str) -> dict:
    """Numeric differences in two diverging Unicode word sequences.

    Measures shared boundaries to distinguish isolated substitutions from
    different section selection; **does not** infer text corruption or choose
    an edition. In particular, an unusually long common suffix is a clue,
    not evidence of legitimate stock additions.
    """
    left, right = WORD.findall(source_text), WORD.findall(stock_text)
    if not left or not right or left == right:
        raise ValueError("Expected two nonempty distinct word sequences")
    limit = min(len(left), len(right))
    prefix = 0
    while prefix < limit and left[prefix] == right[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < limit - prefix
           and left[len(left) - suffix - 1] == right[len(right) - suffix - 1]):
        suffix += 1
    original_middle = len(left) - prefix - suffix
    stock_middle = len(right) - prefix - suffix
    if original_middle == 0 and stock_middle == 0:
        raise ValueError("No explanatory changed-word segment detected")
    # Count common suffix proportion of *shorter* sequence, with no source data.
    pct = suffix * 100 // limit
    if pct == 0:
        bucket = "no_exact_common_word_suffix"
    elif pct < 25:
        bucket = "common_suffix_under_25_percent"
    elif pct < 50:
        bucket = "common_suffix_25_to_49_percent"
    elif pct < 75:
        bucket = "common_suffix_50_to_74_percent"
    elif pct < 100:
        bucket = "common_suffix_75_to_99_percent"
    else:
        bucket = "whole_shorter_sequence_matches_at_end_but_not_start"
    return {
        "common_start_word_tokens": prefix,
        "common_end_word_tokens": suffix,
        "source_middle_different_word_tokens": original_middle,
        "stock_middle_different_word_tokens": stock_middle,
        "common_suffix_fraction_bucket": bucket,
        "changed_only_at_start_of_word_sequence": prefix == 0 and suffix > 0,
        "changed_only_at_end_of_word_sequence": prefix > 0 and suffix == 0,
        "changed_in_middle_with_both_matching_boundaries": prefix > 0 and suffix > 0,
        "original_body_words_or_stock_words_disclosed": False,
        "source_loss_or_editorial_equivalence_proven": False,
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
