#!/usr/bin/env python3
"""Propose safe, source-preserving commentary links; never mutate any module.

Generic to SWORD/OSIS commentary indexing. All inputs must be independently
audited: this accepts a reviewed *section scope*, not a prose citation or a
heuristic first-verse guess. Exact target references are constrained by the
actual module versification supplied by an independent native registry.
"""
from __future__ import annotations

from collections import defaultdict
import re

KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)\.([1-9]\d*)$")
CHAPTER = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class UnsafeCommentaryLinkPlan(ValueError):
    """A proposed scope cannot safely become a non-destructive SWORD link."""


def propose_commentary_links(*, occupied: dict[str, str],
                             valid_verse_keys: set[str],
                             reviewed_sections: list[dict]) -> dict:
    """Create deterministic proposed aliases into unchanged existing raw bodies.

    occupied: exact original occupied native numbered keys -> original raw SHA.
    valid_verse_keys: complete independently enumerated native versification
        registry; do *not* infer from a chapter's highest occupied comment key.
    reviewed_sections: sections with master_key, raw_sha256, source_scope_reviewed,
        evidence_ids and `segments` made of same-chapter
        {"chapter":"Gen.1","from":1,"through":5} objects. Noncontiguous
        segments are legal, but gaps are never expanded.

    Does not compile, create, duplicate, overwrite, publish, or even produce
    original source words. All deltas remain PROPOSED until independent review.
    """
    if not occupied or not valid_verse_keys or not reviewed_sections:
        raise UnsafeCommentaryLinkPlan("Missing stock keys, verse registry, or reviewed scopes")
    if any(KEY.fullmatch(k) is None or SHA256.fullmatch(h) is None
           for k, h in occupied.items()):
        raise UnsafeCommentaryLinkPlan("Invalid original stock key or original raw digest")
    if any(KEY.fullmatch(k) is None for k in valid_verse_keys):
        raise UnsafeCommentaryLinkPlan("Unreviewed canonical native versification key")

    additions: dict[str, dict] = {}
    no_ops = set()
    processed_master_keys = set()
    row_counts = defaultdict(int)
    for section in reviewed_sections:
        master = section.get("master_key")
        digest = section.get("raw_sha256")
        evidence = section.get("evidence_ids")
        segments = section.get("segments")
        if (not isinstance(master, str) or not KEY.fullmatch(master)
                or master in processed_master_keys or occupied.get(master) != digest
                or not isinstance(digest, str) or not SHA256.fullmatch(digest)):
            raise UnsafeCommentaryLinkPlan("Missing/nonunique master or raw-body digest mismatch")
        if section.get("source_scope_reviewed") is not True:
            raise UnsafeCommentaryLinkPlan("Section scope not independently editor-reviewed")
        if (not isinstance(evidence, list) or not evidence or
                any(not isinstance(item, str) or not item.strip() or len(item) > 256
                    for item in evidence)):
            raise UnsafeCommentaryLinkPlan("Missing bounded section-level evidence IDs")
        if not isinstance(segments, list) or not segments:
            raise UnsafeCommentaryLinkPlan("No reviewed passage segments")
        processed_master_keys.add(master)
        targets = set()
        for span in segments:
            if not isinstance(span, dict):
                raise UnsafeCommentaryLinkPlan("Passage segment is not structured")
            chapter, start, end = span.get("chapter"), span.get("from"), span.get("through")
            if (not isinstance(chapter, str) or not CHAPTER.fullmatch(chapter)
                    or type(start) is not int or type(end) is not int
                    or start < 1 or end < start or end > 1000):
                raise UnsafeCommentaryLinkPlan("Invalid same-chapter range")
            for verse in range(start, end + 1):
                key = f"{chapter}.{verse}"
                if key not in valid_verse_keys:
                    raise UnsafeCommentaryLinkPlan("Proposed link escapes actual module versification")
                if key in targets:
                    raise UnsafeCommentaryLinkPlan("Duplicate/overlapping segment")
                targets.add(key)
        if master not in targets:
            raise UnsafeCommentaryLinkPlan("Master key outside reviewed section scope")
        for key in sorted(targets):
            if key in occupied:
                if occupied[key] != digest:
                    raise UnsafeCommentaryLinkPlan("Would overwrite a different original commentary section")
                no_ops.add(key)
                continue
            if key in additions:
                raise UnsafeCommentaryLinkPlan("Two distinct sections claim one missing verse key")
            additions[key] = {"link_to": master, "source_raw_sha256": digest}
            row_counts[master] += 1
    return {
        "status": "PROPOSED_ONLY_NOT_AN_EDITORIAL_APPROVAL",
        "new_native_aliases": dict(sorted(additions.items())),
        "original_occupied_keys_to_preserve": len(occupied),
        "already_occupied_identical_body_keys": sorted(no_ops),
        "added_alias_count": len(additions),
        "source_master_addition_counts": dict(sorted(row_counts.items())),
        "original_text_rewritten": False,
        "original_keys_overwritten": False,
        "original_source_modified": False,
        "candidate_built_or_reader_tested": False,
    }
