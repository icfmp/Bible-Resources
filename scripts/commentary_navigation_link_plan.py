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


def triage_missing_native_section_links(*, occupied: dict[str, str],
                                        valid_verse_keys: set[str],
                                        source_heading_anomalies: list[dict]) -> dict:
    """Safely inventory original indexed-section gaps before editorial approval.

    A source heading parsed from the compiled module is not equivalent to a
    reviewed authorial section scope. This produces **no** build-ready link
    plan: unlike propose_commentary_links, every candidate is pending
    independent source review and subsequent explicit editorial acceptance.
    """
    if (not occupied or not valid_verse_keys
            or not isinstance(source_heading_anomalies, list)
            or len(source_heading_anomalies) > 10000):
        raise UnsafeCommentaryLinkPlan("Empty or unbounded original index-gap audit")
    if any(KEY.fullmatch(key) is None or SHA256.fullmatch(digest) is None
           for key, digest in occupied.items()):
        raise UnsafeCommentaryLinkPlan("Original native index keys/digests are unverified")
    if any(KEY.fullmatch(key) is None for key in valid_verse_keys):
        raise UnsafeCommentaryLinkPlan("Original native versification is unverified")
    candidates = []
    claimed = set()
    blocked = []
    for row in source_heading_anomalies:
        if not isinstance(row, dict):
            raise UnsafeCommentaryLinkPlan("Unstructured native section anomaly")
        master = row.get("start")
        missing = row.get("missing_slots")
        other_payload = row.get("different_payload_slots")
        if (not isinstance(master, str) or KEY.fullmatch(master) is None
                or master not in occupied or master not in valid_verse_keys
                or not isinstance(missing, list) or not isinstance(other_payload, list)
                or not all(isinstance(k, str) and KEY.fullmatch(k) for k in missing+other_payload)):
            raise UnsafeCommentaryLinkPlan("Index gap does not authenticate a native master/target")
        if not missing and not other_payload:
            raise UnsafeCommentaryLinkPlan("Claimed anomaly has no missing or different original native target")
        if len(set(missing)) != len(missing):
            raise UnsafeCommentaryLinkPlan("A purported original gap appears more than once")
        if any(k in claimed for k in missing):
            raise UnsafeCommentaryLinkPlan("A missing target belongs to multiple candidate sections")
        for key in missing:
            if key in occupied or key not in valid_verse_keys:
                raise UnsafeCommentaryLinkPlan("Original missing slot is occupied or outside native versification")
        claimed.update(missing)
        if other_payload:
            blocked.append({
                "original_master_key": master,
                "status": "BLOCKED_DIFFERENT_EXISTING_COMMENTARY",
                "occupied_different_original_keys": sorted(set(other_payload)),
                "no_content_or_index_mutated": True,
            })
            continue
        candidates.append({
            "original_master_key": master,
            "original_master_raw_sha256": occupied[master],
            "unoccupied_native_target_keys": sorted(
                missing,
                key=lambda ref: (
                    ref.rsplit(".", 1)[0], int(ref.rsplit(".", 1)[1])
                )
            ),
            "origin": "PARSED_COMPILED_NATIVE_HEADING_NOT_AUTHORIAL_APPROVAL",
            "source_scope_editorially_reviewed": False,
            "standards_based_sword_links_built": False,
        })
    return {
        "status": "PRELIMINARY_NATIVE_INDEX_GAPS_REVIEW_REQUIRED",
        "candidate_section_count": len(candidates),
        "candidate_additional_native_target_keys": sum(
            len(row["unoccupied_native_target_keys"]) for row in candidates
        ),
        "blocked_sections_with_different_existing_original_payload": blocked,
        "candidate_sections": sorted(candidates, key=lambda x: x["original_master_key"]),
        "original_occupied_keys_preserved": len(occupied),
        "source_prose_modified": False,
        "compiled_binary_modified": False,
        "editorial_approval": False,
        "release_authorized": False,
    }


def parse_native_commentary_verse_registry(raw: bytes, expected_module: str) -> dict:
    """Parse read-only released-libSWORD chapter bounds, never manuscript data.

    Expected framing from sword_native_commentary_index --chapter-registry:
    M<TAB>module<TAB>v11n<TAB>engine<TAB>driver
    R<TAB>book.chapter<TAB>native_verse_max
    S<TAB>chapter_count<TAB>total_verse_count
    """
    if (not isinstance(raw, bytes) or len(raw) > 256 * 1024
            or b"\x00" in raw):
        raise UnsafeCommentaryLinkPlan("Oversize or invalid native registry stream")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise UnsafeCommentaryLinkPlan("Non-ASCII native registry") from exc
    if len(lines) < 3:
        raise UnsafeCommentaryLinkPlan("Missing native registry framing")
    header = lines[0].split("\t")
    if (len(header) != 5 or header[0] != "M"
            or header[1] != expected_module
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", expected_module)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,31}", header[2])
            or not re.fullmatch(r"\d+\.\d+\.\d+", header[3])
            or header[4] not in {"RawCom", "RawCom4", "zCom", "zCom4"}):
        raise UnsafeCommentaryLinkPlan("Unknown native registry module/version/driver")
    chapters = {}
    verse_keys = set()
    for line in lines[1:-1]:
        parts = line.split("\t")
        if (len(parts) != 3 or parts[0] != "R"
                or CHAPTER.fullmatch(parts[1]) is None
                or not re.fullmatch(r"[1-9]\d{0,3}", parts[2])):
            raise UnsafeCommentaryLinkPlan("Unreviewed native chapter registry row")
        chapter = parts[1]
        limit = int(parts[2])
        if limit > 1000 or chapter in chapters or len(chapters) >= 2500:
            raise UnsafeCommentaryLinkPlan("Duplicated/unsupported native chapter bounds")
        chapters[chapter] = limit
        verse_keys.update(f"{chapter}.{verse}" for verse in range(1, limit + 1))
        if len(verse_keys) > 300000:
            raise UnsafeCommentaryLinkPlan("Oversize native verse registry")
    footer = lines[-1].split("\t")
    if (len(footer) != 3 or footer[0] != "S"
            or not all(re.fullmatch(r"[1-9]\d{0,8}", x) for x in footer[1:])
            or int(footer[1]) != len(chapters)
            or int(footer[2]) != len(verse_keys)):
        raise UnsafeCommentaryLinkPlan("Incomplete native chapter/verse registry")
    if not chapters:
        raise UnsafeCommentaryLinkPlan("Empty native chapter registry")
    return {
        "module_id": expected_module, "versification": header[2],
        "engine_version": header[3], "driver": header[4],
        "chapter_maximums": chapters,
        "verse_keys": verse_keys,
        "chapter_count": len(chapters), "canonical_verse_count": len(verse_keys),
        "registry_is_original_sword_engine_not_source_text": True
    }
