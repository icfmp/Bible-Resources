#!/usr/bin/env python3
"""Bounded original-source vs compiled SWORD Unicode word evidence.

This read-only appendix runs only on original CCEL source-unit identities
already independently accepted as SAME-BOOK comparisons. Cross-book source
heading-versus-scripCom contradictions are quarantined elsewhere and are
NEVER normalized/reassigned here.

Original words, source quotations, stock markup and reference targets stay
private. Unicode casefold/NFKC subsequence compatibility is *not* proof of
identical wording, editorial parity or licence clearance.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from lxml import etree
import re
import unicodedata

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_unresolved_lexical_triage import WORD, marked_word_token_indices
from pilot_preflight import PilotError

SHA = re.compile(r"[a-f0-9]{64}\Z")
REVIEW_CLASS = "meaningful_separate_editions_lexical_review_still_required"
MAX_CASES = 256


def _plain_words(source_item: dict, stock_raw: bytes, stock_text_parser) -> tuple[list[str], list[str]]:
    original = source_item.get("original_text")
    original_indices = source_item.get("private_original_scripRef_word_indices")
    if (not isinstance(original, str) or len(original) > 2_000_000
            or not isinstance(original_indices, list)
            or any(type(k) is not int or k < 0 for k in original_indices)
            or not isinstance(stock_raw, bytes) or len(stock_raw) > 2_000_000):
        raise PilotError("Original authored/compiled prose input is not bounded or source authenticated")
    compiled = stock_text_parser(stock_raw)
    if not isinstance(compiled, str):
        raise PilotError("Actual compiled stock XML cannot be strictly read")
    try:
        xml = etree.fromstring(
            b"<stock>" + stock_raw + b"</stock>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False,
            ),
        )
        if any(isinstance(n, etree._Entity) for n in xml.iter()):
            raise PilotError("Original stock entity cannot be read for independent plain words")
    except (ValueError, etree.XMLSyntaxError):
        raise PilotError("Original compiled commentary XML has invalid source markup") from None
    source_all = WORD.findall(original)
    stock_all = WORD.findall(compiled)
    if (not source_all or not stock_all
            or len(set(original_indices)) != len(original_indices)
            or any(k >= len(source_all) for k in original_indices)):
        raise PilotError("Original link-word offsets are invalid")
    stock_indices = marked_word_token_indices(xml, "reference", compiled)
    return (
        [w for i, w in enumerate(source_all) if i not in set(original_indices)],
        [w for i, w in enumerate(stock_all) if i not in set(stock_indices)],
    )


def classify_same_book_unicode_variants(
    source: dict[str, list[dict]], stocked: dict[str, bytes],
    original_identity_report: dict, *, stock_text_parser
) -> dict:
    """Independently rejoin source text and original compiled raw by hash.

    The canonical source-reference marker is evidence only. A difference in
    separate digital editions does NOT authorize editing the original MHCC.
    """
    if (not isinstance(source, dict) or not isinstance(stocked, dict)
            or not callable(stock_text_parser)
            or not isinstance(original_identity_report, dict)):
        raise PilotError("Unreviewed commentary near-match source inventory")
    rows = original_identity_report.get("source_identity_gated_original_line_hash_cases")
    if not isinstance(rows, list) or len(rows) > MAX_CASES:
        raise PilotError("Missing bounded source identity review")
    selected = [r for r in rows if r.get("source_div1_vs_stock_book_comparison_gate") == REVIEW_CLASS]
    lookup = {}
    for start, units in source.items():
        if not isinstance(start, str) or not isinstance(units, list):
            raise PilotError("Malformed original commentary source identity")
        for unit in units:
            ident = (
                unit.get("original_source_line"),
                unit.get("original_full_reference_sha256"),
                unit.get("original_text_sha256"),
            )
            if ident in lookup:
                raise PilotError("Duplicate authentic source line+reference+body identity")
            lookup[ident] = (start, unit)
    stats = Counter()
    results = []
    seen = set()
    for row in selected:
        ident = (
            row.get("original_source_line"),
            row.get("original_full_reference_sha256"),
            row.get("original_body_sha256"),
        )
        if (ident in seen or ident not in lookup
                or not all(isinstance(k, str) and SHA.fullmatch(k) for k in ident[1:])
                or not isinstance(row.get("stock_raw_sha256"), str)
                or not SHA.fullmatch(row["stock_raw_sha256"])):
            raise PilotError("Cannot rejoin the exact authentic near-match source identity")
        seen.add(ident)
        start, source_item = lookup[ident]
        stock_raw = stocked.get(start)
        if (not isinstance(stock_raw, bytes)
                or sha256(stock_raw).hexdigest() != row["stock_raw_sha256"]):
            raise PilotError("Original native key payload is not exactly authenticated")
        exact_unmatched = row.get("source_nonlink_word_tokens_not_found_in_stock_order")
        if type(exact_unmatched) is not int or exact_unmatched <= 0:
            raise PilotError("Actual source near-match class must have a positive word disagreement")
        if exact_unmatched > 2:
            klass = "more_than_two_original_nonlink_word_order_gaps_review_manually"
            casefold_unmatched = None
            nfkc_casefold_unmatched = None
        else:
            source_words, stock_words = _plain_words(source_item, stock_raw, stock_text_parser)
            exact = plain_word_alignment(source_words, stock_words)
            if exact["original_plain_words_not_matched_in_exact_order"] != exact_unmatched:
                raise PilotError("Earlier original exact Unicode alignment no longer reproducible")
            ci = plain_word_alignment(
                [w.casefold() for w in source_words],
                [w.casefold() for w in stock_words],
            )
            nfkc = lambda w: unicodedata.normalize("NFKC", w).casefold()
            nk = plain_word_alignment(
                [nfkc(w) for w in source_words],
                [nfkc(w) for w in stock_words],
            )
            casefold_unmatched = ci["original_plain_words_not_matched_in_exact_order"]
            nfkc_casefold_unmatched = nk["original_plain_words_not_matched_in_exact_order"]
            if casefold_unmatched is None or nfkc_casefold_unmatched is None:
                klass = "unicode_near_match_alignment_safely_skipped_under_budget"
            elif casefold_unmatched == 0:
                klass = "original_plain_word_order_compatible_after_unicode_casefold"
            elif nfkc_casefold_unmatched == 0:
                klass = "original_plain_word_order_compatible_after_nfkc_casefold"
            else:
                klass = "original_plain_word_order_still_differs_after_casefold_and_nfkc"
        stats[klass] += 1
        results.append({
            "original_source_line": ident[0],
            "original_full_reference_sha256": ident[1],
            "original_body_sha256": ident[2],
            "stock_raw_sha256": row["stock_raw_sha256"],
            "exact_unicode_original_nonlink_words_unmatched_in_stock_order": exact_unmatched,
            "after_unicode_casefold_unmatched_original_nonlink_words": casefold_unmatched,
            "after_nfkc_casefold_unmatched_original_nonlink_words": nfkc_casefold_unmatched,
            "original_nonlink_unicode_witness_class": klass,
            "casefold_compatible_order_does_not_certify_exact_wording_or_markup": True,
            "original_source_and_stock_bytes_unchanged": True,
        })
    if sum(stats.values()) != len(selected) or len(results) != len(selected):
        raise PilotError("Near-match Unicode audit omitted a source-valid review case")
    return {
        "schema_version": 1,
        "authentic_same_book_original_digital_edition_cases_evaluated": len(selected),
        "source_book_conflicts_quarantined_elsewhere_not_claimed_as_missing_text": True,
        "source_nonlink_unicode_witness_classes": dict(sorted(stats.items())),
        "bounded_source_line_hash_only_unicode_review_cases": sorted(
            results, key=lambda r: r["original_source_line"]
        ),
        "no_original_authorial_text_words_replacements_or_bible_references_emitted": True,
        "unicode_compatibility_is_not_authored_edition_fidelity_approval": True,
        "original_stock_content_or_source_text_modified": False,
        "editorial_approved": False,
        "published": False,
    }
