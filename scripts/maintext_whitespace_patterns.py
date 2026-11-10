#!/usr/bin/env python3
"""Text-free full-corpus statistics for source/native main-text whitespace.

This never classifies whitespace loss as publication/editorial approval.
All authored words, note bodies and raw spacing remain in private memory.
"""
from __future__ import annotations

from collections import Counter

from note_whitespace_diagnostics import classify_note_whitespace

MAX_SAMPLES = 12
NUMERIC_FIELDS = (
    "changed_whitespace_runs",
    "changed_internal_runs",
    "changed_boundary_runs",
    "source_newline_runs_changed",
    "compiled_newline_runs_changed",
    "source_tab_runs_changed",
    "compiled_tab_runs_changed",
    "source_unicode_space_runs_changed",
    "compiled_unicode_space_runs_changed",
    "changed_runs_entirely_ascii_spaces",
    "changed_runs_increased_length",
    "changed_runs_decreased_length",
    "changed_runs_same_length",
)


class MainTextWhitespacePatterns:
    """Stream metadata from each securely matched source→native verse."""

    def __init__(self):
        self._count = 0
        self._categories = Counter()
        self._totals = Counter()
        self._refs = {}

    def observe(self, ref: str, authored: str, native: str) -> None:
        observation = classify_note_whitespace(authored, native)
        if (observation.get("content_equivalent") is not True
                or observation.get("exact") is not False):
            raise ValueError("Whitespace observation requires nonexact equivalent text")
        self._count += 1
        category = observation["class"]
        if category not in {
            "boundary_whitespace_only",
            "internal_whitespace_only",
            "internal_and_boundary_whitespace_only",
        }:
            raise ValueError("Unexpected whitespace observation classification")
        self._categories[category] += 1
        for name in NUMERIC_FIELDS:
            amount = observation[name]
            if type(amount) is not int or amount < 0:
                raise ValueError("Invalid whitespace observation count")
            self._totals[name] += amount
        # Only reference IDs, never original/compiled words or spacing strings.
        if len(self._refs.setdefault(category, [])) < 4:
            self._refs[category].append(ref)

    def finish(self) -> dict:
        return {
            "schema_version": 1,
            "whitespace_only_verses_inspected": self._count,
            "whitespace_change_types": dict(sorted(self._categories.items())),
            "changed_whitespace_totals": dict(sorted(self._totals.items())),
            "first_reference_ids_without_scripture": dict(sorted(self._refs.items())),
            "source_whitespace_preserved_in_original_archive": True,
            "no_scripture_or_raw_whitespace_in_report": True,
            "compiled_paragraph_poetry_or_layout_fidelity_verified": False,
            "publication_approved": False,
        }
