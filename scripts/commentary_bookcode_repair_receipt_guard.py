#!/usr/bin/env python3
"""Fail-closed, source-independent validation of a PRIVATE ThML repair receipt.

A book-marker defect is not required to exist. A zero-change source must
produce zero proposals, an identical private candidate hash and empty
cross-book comparison rows. No source reading or authorial text is emitted.
"""
from __future__ import annotations

import re

from commentary_original_bookcode_repair import MAX_REPAIRS
from pilot_preflight import PilotError

SHA = re.compile(r"[a-f0-9]{64}\Z")
KINDS = {
    "proposed_book_key_not_occupied_in_original_stock",
    "original_stock_correct_book_alignment_exceeds_safe_budget",
    "all_source_prose_words_found_in_order_at_correct_book_stock_key",
    "some_source_prose_words_still_differ_at_correct_book_stock_key",
}


def _sha(value: object) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def validate_private_bookcode_repair_receipt(report: dict) -> dict:
    """Check every proposed source-only change against exact-source receipt totals.

    Returns only counts/classes; never original references, words or notes.
    A passed check is NOT an editorial licence or publication approval.
    """
    if not isinstance(report, dict):
        raise PilotError("Missing original/stock commentary audit report")
    receipt = report.get("original_source_book_marker_private_repair_proposal_stock_review")
    if not isinstance(receipt, dict):
        raise PilotError("Missing independently generated private source repair receipt")

    original = receipt.get("original_source_sha256")
    candidate = receipt.get("private_corrected_source_sha256")
    if (not _sha(original) or not _sha(candidate)
            or original != report.get("source_original_sha256")):
        raise PilotError("Original source and candidate hashes are not authenticated")
    stock = report.get("stock_full_raw_content_sha256")
    if (not _sha(stock)
            or receipt.get("actual_original_stock_full_native_corpus_sha256") != stock):
        raise PilotError("Original full SWORD stock raw content was not authenticated")

    proposed = receipt.get("reviewed_private_original_bookcode_replacements")
    all_markers = receipt.get("all_original_scripCom_elements_preserved")
    if (type(proposed) is not int or not 0 <= proposed <= MAX_REPAIRS
            or type(all_markers) is not int or not proposed <= all_markers <= 50000
            or type(receipt.get("corrected_book_source_marker_count_compared")) is not int
            or receipt["corrected_book_source_marker_count_compared"] != proposed):
        raise PilotError("Source repair proposal and original marker counts disagree")
    if (candidate != original) != (proposed > 0):
        raise PilotError("Private source candidate hash is inconsistent with changes")

    ops = receipt.get("original_scripCom_replacement_operations_without_authorial_text")
    rows = receipt.get("original_repaired_book_line_SHA_only_stock_comparison_cases")
    classes = receipt.get("original_repaired_book_source_text_match_classes")
    if (not isinstance(ops, list) or len(ops) != proposed
            or not isinstance(rows, list) or len(rows) != proposed
            or not isinstance(classes, dict) or not set(classes) <= KINDS
            or any(type(n) is not int or n < 0 for n in classes.values())
            or sum(classes.values()) != proposed):
        raise PilotError("Private source repair operations and original-stock comparisons disagree")
    op_lines = set()
    for op in ops:
        if (not isinstance(op, dict)
                or type(op.get("source_line")) is not int or op["source_line"] <= 0
                or not _sha(op.get("original_source_osisRef_sha256"))
                or not _sha(op.get("proposed_private_osisRef_sha256"))
                or op["original_source_osisRef_sha256"] == op["proposed_private_osisRef_sha256"]
                or op.get("only_inferred_book_code_changed_in_scripCom") is not True):
            raise PilotError("Private source book replacement operation is not auditable")
        if op["source_line"] in op_lines:
            raise PilotError("Duplicate original source book-marker line in repair receipt")
        op_lines.add(op["source_line"])
    row_lines = set()
    row_counts = {}
    for row in rows:
        if (not isinstance(row, dict)
                or type(row.get("original_source_line")) is not int
                or row["original_source_line"] <= 0
                or not all(_sha(row.get(name)) for name in (
                    "original_authorial_body_sha256",
                    "original_wrong_book_start_sha256", "proposed_book_start_sha256"))
                or row["original_wrong_book_start_sha256"] == row["proposed_book_start_sha256"]
                or row.get("private_original_repaired_book_text_witness_class") not in KINDS
                or row.get("not_authorized_to_reassign_crosswire_original_reference") is not True):
            raise PilotError("Private corrected-book comparison case lacks authenticated identity")
        number = row.get("source_plain_words_not_aligned_at_proposed_book_key")
        if number is not None and (type(number) is not int or number < 0):
            raise PilotError("Private source word count is invalid")
        if row["original_source_line"] in row_lines:
            raise PilotError("Duplicate original source unit in corrected-book stock comparisons")
        row_lines.add(row["original_source_line"])
        kind = row["private_original_repaired_book_text_witness_class"]
        row_counts[kind] = row_counts.get(kind, 0) + 1
    if op_lines != row_lines or row_counts != classes:
        raise PilotError("Original book-marker repairs do not match their stock comparisons")

    fixed = {
        "schema_version": 1,
        "status": "private_exact_scripCom_book_token_repair_proposal_not_approved",
        "only_unique_original_exact_english_div1_title_conflicts_proposed": True,
        "original_source_byte_for_byte_restorable": True,
        "every_original_other_XML_text_title_note_reference_and_structure_unmodified": True,
        "original_crosswire_sword_data_or_versification_changed": False,
        "source_book_repair_is_not_crosswire_text_or_verse_repair": True,
        "original_XML_or_stock_SWORD_mutated": False,
        "independent_authorial_edition_identity_established": False,
        "source_owner_or_editor_approved": False,
        "public_release_authorized": False,
    }
    for key, expected in fixed.items():
        if receipt.get(key) != expected or type(receipt.get(key)) is not type(expected):
            raise PilotError("Private source repair receipt violates unchanged-source/release guard: " + key)
    return {
        "original_book_marker_repairs_proposed_privately": proposed,
        "repaired_markers_compared_to_pinned_original_stock": len(rows),
        "original_corrected_book_source_word_comparison_classes": dict(sorted(classes.items())),
        "zero_change_original_source_candidate_allowed": proposed == 0,
        "original_authorial_text_and_stock_payload_changed": False,
        "editorial_and_publication_approved": False,
    }
