#!/usr/bin/env python3
"""Separate incompatible source-book joins from real cross-edition lexical review.

The authorial CCEL ThML div1 heading and its claimed scripCom OSIS book
are independent ORIGINAL fields. Comparing its body to an original stock
SWORD slot selected solely from a contradictory marker is unsafe: do not
treat that cross-book collision as evidence of SWORD authorial text loss.

All decisions are read-only. No actual heading, word, reference, proposed
replacement, scripture target or book code is returned or logged. Generic
for any SWORD commentary with the supported reviewed 66-book crosswalk.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re

from commentary_source_english_osis_alias import (
    _classify, read_existing_66_book_english_aliases,
)
from pilot_preflight import PilotError

SHA = re.compile(r"[0-9a-f]{64}\Z")
CONFLICTS = frozenset({
    "original_title_exact_english_alias_points_to_different_book_code",
    "original_title_contains_english_alias_for_different_book_code",
})
CONSISTENT = frozenset({
    "original_title_exact_english_alias_matches_claimed_book_code",
    "original_title_contains_english_alias_matching_claimed_book_code",
})


def classify_lexical_source_identity(source: dict, cases: list[dict]) -> dict:
    """Join exact source line+reference+body hashes, not a guessed SWORD verse.

    An independently authored heading that contradicts a source OSIS marker
    QUARANTINES that witness pair: it does not allow silent book-code repair.
    An ambiguous title also cannot be auto-cleared. Even matching metadata
    only makes comparison meaningful, never proves print/edition equivalence.
    """
    if (not isinstance(source, dict) or not isinstance(cases, list)
            or len(cases) > 256):
        raise PilotError("Unreviewed original commentary lexical identity inputs")
    if not cases:
        return {
            "schema_version": 1,
            "original_source_compiled_lexical_attention_cases_checked": 0,
            "original_div1_book_identity_gate_classes": {},
            "source_identity_gated_original_line_hash_cases": [],
            "no_unresolved_nonlink_lexical_cases_to_classify": True,
            "source_book_heading_alias_is_not_authorial_book_reassignment": True,
            "cross_book_join_is_not_evidence_of_missing_stock_prose": True,
            "same_book_comparison_is_not_proof_of_digital_edition_parity": True,
            "original_source_stock_binary_and_scripture_references_unmodified": True,
            "editorial_decisions_approved": False,
            "published": False,
        }
    aliases, registry = read_existing_66_book_english_aliases()
    identities = {}
    for start, units in source.items():
        if (not isinstance(start, str) or not isinstance(units, list)
                or "." not in start):
            raise PilotError("Unreviewed original ThML source identity mapping")
        claimed_book = start.split(".", 1)[0]
        for unit in units:
            ident = (
                unit.get("original_source_line"),
                unit.get("original_full_reference_sha256"),
                unit.get("original_text_sha256"),
            )
            if (type(ident[0]) is not int or ident[0] <= 0
                    or not all(isinstance(x, str) and SHA.fullmatch(x)
                               for x in ident[1:])):
                raise PilotError("Unverified actual source annotation identity")
            if ident in identities:
                raise PilotError("Two source comments share one attested original identity")
            ordinal = unit.get("private_original_enclosing_div1_document_ordinal")
            total = unit.get("private_original_total_div1_in_document")
            heading = unit.get("private_original_div1_heading_text")
            heading_sha = unit.get("private_original_div1_heading_sha256")
            if (type(ordinal) is not int or type(total) is not int
                    or not 1 <= ordinal <= total <= 500 or
                    not isinstance(heading, str) or len(heading) > 4096 or
                    (sha256(heading.encode("utf-8")).hexdigest()
                     if heading.strip() else None) != heading_sha):
                raise PilotError("Original source division heading is not SHA-attested")
            identities[ident] = (claimed_book, ordinal, heading, heading_sha)
    counts = Counter()
    rows = []
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise PilotError("Unreviewed original-source lexical case")
        ident = (
            case.get("original_source_line"),
            case.get("original_full_reference_sha256"),
            case.get("original_body_sha256"),
        )
        if ident in seen or ident not in identities:
            raise PilotError("Lexical case does not join unique original source line/hashes")
        seen.add(ident)
        stock_hash = case.get("stock_raw_sha256")
        if not isinstance(stock_hash, str) or not SHA.fullmatch(stock_hash):
            raise PilotError("Lexical case lacks pinned actual stock raw identity")
        alignment = case.get("exact_plain_word_alignment")
        if not isinstance(alignment, dict):
            raise PilotError("Independent nonlink word alignment evidence absent")
        unmatched = alignment.get("original_plain_words_not_matched_in_exact_order")
        if type(unmatched) is not int or unmatched <= 0:
            raise PilotError("Cannot classify an already exact-matching source/body pair")
        claimed, ordinal, heading, heading_sha = identities[ident]
        klass, candidate_code, matched = _classify(heading, claimed, aliases)
        if klass in CONFLICTS:
            decision = "quarantine_original_book_title_vs_osis_marker_conflict"
        elif klass in CONSISTENT:
            decision = "meaningful_separate_editions_lexical_review_still_required"
        else:
            decision = "ambiguous_original_source_book_identity_manual_review"
        counts[decision] += 1
        rows.append({
            "original_source_line": ident[0],
            "original_full_reference_sha256": ident[1],
            "original_body_sha256": ident[2],
            "stock_raw_sha256": stock_hash,
            "original_source_div1_document_ordinal": ordinal,
            "original_div1_heading_sha256": heading_sha,
            "original_div1_title_vs_marker_class": klass,
            "unambiguous_original_heading_alias_count": matched,
            "source_nonlink_word_tokens_not_found_in_stock_order": unmatched,
            "source_div1_vs_stock_book_comparison_gate": decision,
            "original_source_marker_or_heading_edited": False,
            "source_canonical_alias_is_diagnostic_not_a_reference_correction": True,
        })
    if sum(counts.values()) != len(cases) or len(rows) != len(cases):
        raise PilotError("Incomplete original source-book gate accounting")
    rows.sort(key=lambda r:(
        r["source_div1_vs_stock_book_comparison_gate"],
        -r["source_nonlink_word_tokens_not_found_in_stock_order"],
        r["original_source_line"],
    ))
    return {
        "schema_version": 1,
        "original_source_compiled_lexical_attention_cases_checked": len(cases),
        "original_div1_book_identity_gate_classes": dict(sorted(counts.items())),
        "source_identity_gated_original_line_hash_cases": rows,
        **registry,
        "source_book_heading_alias_is_not_authorial_book_reassignment": True,
        "cross_book_join_is_not_evidence_of_missing_stock_prose": True,
        "same_book_comparison_is_not_proof_of_digital_edition_parity": True,
        "original_source_stock_binary_and_scripture_references_unmodified": True,
        "editorial_decisions_approved": False,
        "published": False,
    }
