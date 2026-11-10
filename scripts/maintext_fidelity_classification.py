#!/usr/bin/env python3
"""Classify full-corpus original→native text evidence without waiving layout.

Only consumes metadata from the independent, read-only native SWORD scanner.
No Scripture, strings or note bodies are logged, rewritten or returned.
"""
from __future__ import annotations

ALLOWED_CHAR_EQUIVALENCE = frozenset({
    "exact_semantic_characters",
    "unicode_normalization_only",
    "whitespace_only",
})


def classify_compiled_numbered_maintext(
    maintext: dict, source_scope: dict, absorbed: dict, *,
    full_native_scan_verified: bool, exact_entry_spotcheck_verified: bool,
) -> dict:
    """A whitespace-only outcome is never an exact/full-editorial approval."""
    counts = maintext.get("classifications", {})
    n = maintext.get("source_mapped_numbered_verse_count", 0)
    native = maintext.get("native_numbered_verse_count")
    def integer(value):
        return type(value) is int and value >= 0

    credible = bool(
        integer(n) and n > 0 and integer(native) and native == n
        and full_native_scan_verified is True
        and exact_entry_spotcheck_verified is True
        and integer(counts.get("matching_indexed_keys_checked", 0))
        and counts.get("matching_indexed_keys_checked") == n
        and integer(counts.get("source_verses_without_native_indexed_entry", 0))
        and counts.get("source_verses_without_native_indexed_entry", 0) == 0
        and counts.get("native_verse_without_same_indexed_source_key", 0) == 0
        and source_scope.get("mapped_numbered_source_keys") == n
        and source_scope.get("unmapped_authored_book_count") == 0
        and source_scope.get("unmapped_numbered_source_keys") == 0
        and absorbed.get("source_only_reference_count") == 0
        and absorbed.get("native_occupied_refs_without_authored_counterpart_count") == 0
        and not maintext.get("material_differences_metadata_truncated", True)
        and not maintext.get("first_source_only_refs")
    )
    complete = all(
        integer(counts.get(key, 0)) for key in ALLOWED_CHAR_EQUIVALENCE
    ) and sum(counts.get(key, 0) for key in ALLOWED_CHAR_EQUIVALENCE) == n
    other = {
        name: value for name, value in counts.items()
        if name not in ALLOWED_CHAR_EQUIVALENCE
        and name not in {"matching_indexed_keys_checked",
                         "source_verses_without_native_indexed_entry"}
        and value
    }
    if any(not integer(v) for v in counts.values()):
        credible = False
    equal_after_whitespace = bool(credible and complete and not other)
    whitespace_count = counts.get("whitespace_only", 0)
    unicode_count = counts.get("unicode_normalization_only", 0)
    exact_characters = bool(equal_after_whitespace
                            and whitespace_count == 0
                            and unicode_count == 0
                            and counts.get("exact_semantic_characters", 0) == n)
    return {
        "status": (
            "exact_numbered_maintext_at_matching_keys_only" if exact_characters
            else "all_mapped_numbered_text_equal_after_whitespace_folding_only"
            if equal_after_whitespace
            else "blocked_non_whitespace_or_index_discrepancy"
        ),
        "source_mapped_numbered_reference_count": n if integer(n) else 0,
        "all_source_and_native_numbered_reference_keys_match": credible,
        "all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding": equal_after_whitespace,
        "numbered_maintext_exact_characters_verified": exact_characters,
        "source_verses_with_whitespace_only_changes": whitespace_count if integer(whitespace_count) else 0,
        "source_verses_with_unicode_normalization_only_changes": unicode_count if integer(unicode_count) else 0,
        "unresolved_material_classifications": dict(sorted(other.items())),
        "original_whitespace_layout_headings_and_poetry_verified": False,
        "book_intro_verse_zero_and_original_book_order_verified": False,
        "original_note_callers_anchors_references_verified": False,
        "exact_publisher_revision_identity_verified": False,
        "publication_approved": False,
    }
