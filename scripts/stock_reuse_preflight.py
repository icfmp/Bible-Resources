#!/usr/bin/env python3
"""Source-safe, edition-neutral stock-SWORD material loss preflight.

Consumes the real source/native audit's numeric metadata, never Bible text.
A clean result is not editorial acceptance or stock-module reuse approval.
"""
from __future__ import annotations

MAX_COUNT = 300_000
MATERIAL_NOTE = (
    "note_count_differs", "ordered_note_bodies_differ",
    "native_fragment_unparseable_notes_unverified",
    "source_note_bearing_verses_without_native_slot",
)
MATERIAL_ATTRIBUTES = (
    "literal_source_caller_no_native_n", "literal_caller_string_differs",
    "cross_reference_class_differs", "authored_explicit_target_absent_in_native",
    "explicit_target_raw_strings_differ", "note_count_alignment_unavailable",
)
REVIEW_ATTRIBUTES = (
    "source_note_type_unknown",
    "source_caller_automatic_absent_or_unverifiable",
    "native_target_without_authorial_machine_target",
)


def _count(values: dict, name: str) -> int:
    v = values.get(name, 0)
    if type(v) is not int or not 0 <= v <= MAX_COUNT:
        raise ValueError("Untrusted stock-reuse diagnostic count")
    return v


def preflight_stock_reuse(*, native_scan_complete: bool, main_text_preserved: bool,
                          notes: dict, note_positions: dict,
                          original_note_scope: dict) -> dict:
    """Detect known material losses before choosing to reuse stock SWORD."""
    if (type(native_scan_complete) is not bool
            or type(main_text_preserved) is not bool
            or not all(isinstance(v, dict) for v in
                       (notes, note_positions, original_note_scope))):
        raise ValueError("Incomplete stock-reuse evidence input")
    note_classes = notes.get("classifications")
    annotation = notes.get("note_annotation_structure_diagnostic")
    note_classes = note_classes if isinstance(note_classes, dict) else {}
    annotation = annotation if isinstance(annotation, dict) else {}
    attrs = annotation.get("classifications")
    attrs = attrs if isinstance(attrs, dict) else {}
    losses, review = {}, {}
    if not main_text_preserved:
        losses["numbered_main_text_not_preserved"] = 1
    for name in MATERIAL_NOTE:
        n = _count(note_classes, name)
        if n:
            losses[name] = n
    for name in MATERIAL_ATTRIBUTES:
        n = _count(attrs, name)
        if n:
            losses[name] = n
    source_total = notes.get("source_numbered_note_count")
    native_total = notes.get("native_parseable_numbered_note_count")
    for count in (source_total, native_total):
        if type(count) is int and not 0 <= count <= MAX_COUNT:
            raise ValueError("Invalid source/native numbered note total")
    if type(source_total) is int and type(native_total) is int:
        if source_total != native_total:
            losses["source_native_note_total_difference"] = abs(source_total-native_total)
        if source_total and (_count(attrs,"native_note_n_present") +
                             _count(attrs,"native_note_n_absent") != source_total):
            review["note_annotation_attribute_coverage_unverified"] = 1
    else:
        review["numbered_note_total_coverage_unverified"] = 1
    if _count(note_classes, "ordered_note_bodies_equal_after_whitespace_folding"):
        review["note_body_whitespace_requires_editorial_review"] = _count(
            note_classes, "ordered_note_bodies_equal_after_whitespace_folding")
    for name in REVIEW_ATTRIBUTES:
        n = _count(attrs, name)
        if n:
            review[name] = n
    for name in ("notes_outside_numbered_verses", "unmapped_source_book_count"):
        n = _count(original_note_scope, name)
        if n:
            review["original_" + name] = n
    if not native_scan_complete:
        review["independent_native_scan_incomplete"] = 1
    if note_positions.get("all_numbered_note_nonspace_anchor_positions_match") is not True:
        review["note_anchor_parity_unverified"] = 1
    if notes.get("status") != (
            "numbered_source_to_native_note_body_diagnostic_not_editorial_approval"):
        review["unrecognized_source_native_note_receipt"] = 1
    return {
        "schema_version": 1,
        "status": "BLOCKED" if losses else "REVIEW_REQUIRED",
        "proven_material_stock_loss": bool(losses),
        "material_loss_categories": losses,
        "other_unverified_categories": review,
        "stock_reuse_approved": False,
        "editorial_or_publication_approved": False,
        "scripture_notes_and_original_targets_exposed": False,
    }
