#!/usr/bin/env python3
"""Source-only triage of original OSIS note-link navigation limitations.

Read the publisher's already pinned original OSIS, NOT stock SWORD. Never
alter Scripture, targets, notes, or source verse keys. Returns only metadata,
validated source-note host coordinates, and fixed diagnostic class labels.
It does not claim real reader navigation or authorial editorial approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from publisher_osis_observation import read_pinned_publisher_osis
from publisher_osis_usfx_parity import original_osis_verses_and_notes
from source_native_osis_target_addressability import (
    _classify_one, ENDPOINT, MAX_LINKS,
)
from stable_sword_refs import KEY

MAX_SAMPLES = 40
INDEXABLE = frozenset({
    "indexed_verse", "indexed_chapter", "indexed_book",
    "indexed_ordered_full_range",
})


class SourceLinkTriageError(ValueError):
    """The original note reference scope is inconsistent or untrustworthy."""


def _shape_hint(value: str, outcome: str) -> str:
    """Only fixed broad shapes; never expose or decode unreviewed literal URLs."""
    if outcome == "target_with_unindexed_endpoint":
        return "source_key_not_present_in_authorial_index"
    if ":" in value:
        return "authorial_work_prefix_or_colon_requires_review"
    if "!" in value or "@" in value:
        return "authorial_grain_or_subidentifier_requires_review"
    if value.count("-") > 1:
        return "authorial_compound_range_requires_review"
    if "-" in value and any(x.isdigit() for x in value.split("-", 1)[1])             and "." not in value.split("-", 1)[1]:
        return "authorial_abbreviated_range_endpoint_requires_review"
    return "authorial_target_grammar_requires_review"


def _navigation_review_detail(value: str, outcome: str,
                              host: str, source_keys: set[str],
                              rank: dict, chapters: dict, books: dict) -> dict:
    """Return only bounded classifications, never the author's target text.

    Interpret punctuation alternatives only as research hypotheses. OSIS
    references are NOT corrected or resolved by this function.
    """
    if not isinstance(value, str) or len(value) > 1024:
        return {"analysis": "unreviewed_nonstandard_value"}
    if outcome == "target_with_unindexed_endpoint":
        tokens = value.split()
        if len(tokens) != 1:
            return {"analysis": "multiple_components_need_editorial_review"}
        match = ENDPOINT.fullmatch(tokens[0])
        if not match or match.group(2) is None or match.group(3) is None:
            return {"analysis": "unindexed_non_simple_reference"}
        book, chapter, verse_text = match.groups()
        verse = int(verse_text)
        same_book = book == host.split(".")[0]
        same_chapter = f"{book}.{chapter}" == host.rsplit(".", 1)[0]
        before = f"{book}.{chapter}.{verse-1}" in source_keys if verse > 1 else False
        after = f"{book}.{chapter}.{verse+1}" in source_keys
        return {
            "analysis": "simple_missing_publisher_verse_key",
            "target_same_book_as_note": same_book,
            "target_same_chapter_as_note": same_chapter,
            "preceding_verse_indexed": before,
            "following_verse_indexed": after,
            "chapter_exists_in_source": f"{book}.{chapter}" in chapters,
            "missing_target_created": False,
        }

    if outcome != "target_with_unsupported_grammar":
        return {"analysis": "other_original_reference_limitation"}

    # A source might encode multiple OSIS references using punctuation other
    # than mandated whitespace. Only classify the shape: never normalize it
    # for compilation, nor silently accept the proposed alternate grammar.
    cleaned = value.strip()
    has_separator = ";" in cleaned or "," in cleaned
    if has_separator:
        parts = [p for p in re.split(r"[;,\s]+", cleaned) if p]
        if 1 < len(parts) <= 100 and all(
            _classify_one(p, rank, chapters, books)[0] in INDEXABLE
            for p in parts
        ):
            return {
                "analysis": "punctuation_delimited_indexed_targets_candidate",
                "candidate_component_count": len(parts),
                "original_grammar_still_unsupported": True,
            }
    if cleaned and cleaned[0] in "([{":
        matching = {"(": ")", "[": "]", "{": "}"}
        if cleaned.endswith(matching[cleaned[0]]):
            middle = cleaned[1:-1].strip()
            if _classify_one(middle, rank, chapters, books)[0] in INDEXABLE:
                return {
                    "analysis": "bracket_wrapped_indexed_target_candidate",
                    "original_grammar_still_unsupported": True,
                }
    if re.search(r"\.[1-9][0-9]*[a-zA-Z](?:\s|$)", cleaned):
        return {
            "analysis": "letter_suffixed_verse_reference_candidate",
            "original_grammar_still_unsupported": True,
        }
    if any(c in cleaned for c in ("–", "—", "‑")):
        return {
            "analysis": "unicode_dash_reference_candidate",
            "original_grammar_still_unsupported": True,
        }
    if "-" in cleaned:
        return {
            "analysis": "other_hyphenated_reference_requires_review",
            "original_grammar_still_unsupported": True,
        }
    if any(c in cleaned for c in (",", ";")):
        return {
            "analysis": "punctuation_reference_requires_review",
            "original_grammar_still_unsupported": True,
        }
    if any(not (c.isascii() and (c.isalnum() or c in ". \t\r\n")) for c in cleaned):
        return {
            "analysis": "nonstandard_character_reference_requires_review",
            "original_grammar_still_unsupported": True,
        }
    return {
        "analysis": "unknown_source_reference_grammar",
        "original_grammar_still_unsupported": True,
    }


def triage_source_notes(notes: dict, source_keys: set[str],
                        *, source_sha256: str) -> dict:
    """Analyze source authorial targets against **source** index only.

    source_keys is not a native SWORD index, therefore no statement about
    runtime link clicks, compiled parity, or external works is inferred.
    """
    if (not isinstance(notes, dict) or not source_keys
            or set(notes) != source_keys or len(source_sha256) != 64
            or any(c not in "0123456789abcdef" for c in source_sha256)
            or not all(isinstance(k, str) and KEY.fullmatch(k)
                       for k in source_keys)):
        raise SourceLinkTriageError("Unverified original source-note/key scope")
    rank, chapters, books = {}, {}, {}
    for ref in notes:
        index = len(rank)
        rank[ref] = index
        book, chapter, _verse = ref.split(".")
        for label, mapping in ((book, books),
                               (f"{book}.{chapter}", chapters)):
            start, _old_end = mapping.get(label, (index, index))
            mapping[label] = start, index

    counts = Counter()
    findings = []
    for host, authored_notes in notes.items():
        if not isinstance(authored_notes, list):
            raise SourceLinkTriageError("Unknown original note inventory form")
        for index, note in enumerate(authored_notes, 1):
            if not isinstance(note, dict) or not isinstance(note.get("targets"), tuple):
                raise SourceLinkTriageError("Unverified original note target attributes")
            counts["numbered_source_notes_examined"] += 1
            for raw_target in note["targets"]:
                counts["explicit_original_target_attributes"] += 1
                if counts["explicit_original_target_attributes"] > MAX_LINKS:
                    raise SourceLinkTriageError("Unbounded original reference count")
                if not isinstance(raw_target, str) or not raw_target or len(raw_target) > 1024:
                    outcome = "target_unreviewed_invalid_or_oversized"
                    pieces = []
                else:
                    pieces = raw_target.split()
                    if not pieces or len(pieces) > 100:
                        outcome = "target_unreviewed_invalid_or_oversized"
                    else:
                        shapes = []
                        for part in pieces:
                            shape, _components, is_range = _classify_one(
                                part, rank, chapters, books)
                            shapes.append(shape)
                            counts["original_target_component_" + shape] += 1
                            if is_range:
                                counts["original_range_components"] += 1
                        if all(shape in INDEXABLE for shape in shapes):
                            outcome = "source_index_addressable"
                        elif any(shape.startswith("unsupported_") for shape in shapes):
                            outcome = "target_with_unsupported_grammar"
                        elif any(shape.startswith("unindexed_") for shape in shapes):
                            outcome = "target_with_unindexed_endpoint"
                        else:
                            outcome = "target_with_unreviewed_range_or_other"
                counts[outcome] += 1
                if outcome != "source_index_addressable" and len(findings) < MAX_SAMPLES:
                    findings.append({
                        "authorial_note_host_reference": host,
                        "one_based_note_ordinal": index,
                        "category": outcome,
                        "shape_hint": _shape_hint(
                            raw_target if isinstance(raw_target, str) else "", outcome),
                        "literal_target_exposed": False,
                        "source_navigation_review_detail":
                            _navigation_review_detail(
                                raw_target, outcome, host, source_keys,
                                rank, chapters, books),
                    })
    unresolved = sum(value for k, value in counts.items()
                     if k.startswith("target_"))
    return {
        "schema_version": 1,
        "status": ("original_targets_source_addressable_only"
                   if not unresolved else "original_note_links_need_editorial_navigation_review"),
        "official_source_sha256": source_sha256,
        "numbered_authorial_source_keys": len(source_keys),
        "metadata_counts": dict(sorted(counts.items())),
        "unresolved_original_target_attributes": unresolved,
        "bounded_note_host_findings": findings,
        "source_verse_index_only": True,
        "source_note_target_literals_or_bodies_exposed": False,
        "actual_compiled_navigation_verified": False,
        "no_missing_verses_invented": True,
        "original_text_notes_and_links_unchanged": True,
        "publication_or_editorial_approval": False,
    }


def run(resource_id: str) -> dict:
    source = read_pinned_publisher_osis(resource_id)
    _verses, notes, _scope = original_osis_verses_and_notes(source)
    return triage_source_notes(
        notes, set(notes), source_sha256=sha256(source).hexdigest())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if (args.report.exists() or args.report.is_symlink()
            or not args.report.parent.is_dir()):
        parser.error("Refusing to overwrite original evidence or write outside prepared directory")
    try:
        report = run(args.resource_id)
        args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    except Exception as exc:
        # Third-party exception values can contain authorial XML and are never
        # printed to the public runner. Only stable local exception type.
        parser.error("Original-source link audit failed: " + type(exc).__name__)
    print("Source-only note link review:", report["status"])
    print("Original SHA-256:", report["official_source_sha256"])
    print("Authorial targets:", report["metadata_counts"].get(
          "explicit_original_target_attributes", 0))
    print("Editorial/navigation review count:",
          report["unresolved_original_target_attributes"])
    print("No source target strings, notes or Scripture printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
