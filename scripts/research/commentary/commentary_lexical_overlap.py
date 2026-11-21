"""Read-only source/stock lexical-overlap diagnostics, without prose export.

Matching words across distinct witnesses cannot prove authorial equivalence,
verse ownership, text preservation or editorial approval.
"""
from __future__ import annotations

from collections import Counter
import re

from lxml import etree

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_stock_prefix_topology import (
    source_word_prefix_topology, stock_prefixed_source_body_concordance,
    single_word_stock_markup_diagnostic, stock_prefix_context_correspondence,
)
from pilot_preflight import PilotError


def independent_lexical_overlap(source_text: str, stock_raw: bytes,
                                source_neighbor_candidates: list[tuple[str, str]] | None = None) -> dict:
    """Compare word-multiset overlap in memory, emitting NO original words.

    This is diagnostic cross-edition evidence, not exact text parity:
    punctuation, sequence, markup, source edition and omitted prose must be
    audited independently before authorising a derivative.
    """
    if (not isinstance(source_text, str) or not isinstance(stock_raw, bytes)
            or len(source_text) > 2 * 1024 * 1024
            or len(stock_raw) > 2 * 1024 * 1024 or b"\x00" in stock_raw):
        return {"status": "UNREVIEWED_OR_OVERSIZE", "source_text_equal": False}
    try:
        fragment = etree.fromstring(
            b"<entry>" + stock_raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
        if any(isinstance(n, etree._Entity) for n in fragment.iter()):
            return {"status": "UNRESOLVED_XML_ENTITY", "source_text_equal": False}
        stock_text = "".join(fragment.itertext())
    except (ValueError, etree.XMLSyntaxError):
        return {"status": "UNPARSEABLE_ORIGINAL_RAW", "source_text_equal": False}
    original = re.findall(r"\w+", source_text.casefold())
    compiled = re.findall(r"\w+", stock_text.casefold())
    if not original or not compiled or len(original) > 100000 or len(compiled) > 100000:
        return {"status": "EMPTY_OR_OVERSIZE_LEXICAL_UNITS", "source_text_equal": False}
    # Reuse the independently reviewed bounded LCS helper. Multiset
    # overlap by itself would hide reordering/omission of original prose.
    ordered = plain_word_alignment(original, compiled)
    common = sum((Counter(original) & Counter(compiled)).values())
    source_pct = round(common * 100 / len(original))
    stock_pct = round(common * 100 / len(compiled))
    least = min(source_pct, stock_pct)
    classification = (
        "HIGH_95_PLUS" if least >= 95 else
        "HIGH_80_PLUS" if least >= 80 else
        "MODERATE_50_PLUS" if least >= 50 else "LOW_OVERLAP"
    )
    prefix = None
    suffix = None
    if (ordered["original_plain_words_not_matched_in_exact_order"] == 0
            and ordered["stock_plain_words_not_matched_in_exact_order"] > 0
            and ordered["common_end_word_tokens"] == len(original)):
        try:
            prefix = source_word_prefix_topology(source_text, stock_raw)
            suffix = stock_prefixed_source_body_concordance(source_text, stock_raw)
        except (ValueError, PilotError):
            prefix = {
                "status": "NOT_A_STRICT_CASE_SENSITIVE_STOCK_PREFIX",
                "extra_stock_words_are_not_approved": True,
            }
    neighbor_concordance = None
    if (prefix is not None and prefix.get("full_original_source_word_sequence_inside_stock")
            and source_neighbor_candidates is not None):
        try:
            neighbor_concordance = stock_prefix_context_correspondence(
                source_text, stock_raw, source_neighbor_candidates
            )
        except (ValueError, PilotError):
            neighbor_concordance = {
                "status": "SOURCE_CONTEXT_NOT_SAFE_FOR_CORRESPONDENCE",
                "original_text_or_xml_disclosed": False,
            }
    single_word = None
    if (ordered["original_plain_words_not_matched_in_exact_order"] == 1
            and ordered["stock_plain_words_not_matched_in_exact_order"] == 1
            and len(original) == len(compiled)):
        # Existing cross-edition counts identify a small number of isolated
        # mismatches. Locate their stock XML owner without logging any words.
        single_word = single_word_stock_markup_diagnostic(source_text, stock_raw)
    return {
        "status": "INDEPENDENT_DIGITAL_EDITION_DIAGNOSTIC_ONLY",
        "source_word_count": len(original),
        "stock_word_count": len(compiled),
        "matched_word_multiset_count": common,
        "source_word_overlap_percent": source_pct,
        "stock_word_overlap_percent": stock_pct,
        "overlap_class": classification,
        "exact_ordered_word_equality": original == compiled,
        "ordered_word_alignment": ordered,
        "stock_extra_prefix_xml_topology": prefix,
        "stock_prefix_independent_source_neighbor_correspondence": neighbor_concordance,
        "isolated_one_word_xml_location": single_word,
        "stock_source_suffix_punctuation_topology": suffix,
        "source_text_equal": source_text == stock_text,
        "historical_or_editorial_equivalence_proven": False,
        "authorial_prose_modified": False,
    }
