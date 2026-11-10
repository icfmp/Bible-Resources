#!/usr/bin/env python3
"""Check source/native p/q structure relative to punctuation-bearing text.

This comparison is stronger than book-wide *word* ordinals but remains
strictly narrower than original whitespace, source-newline, poetry-stanza,
verse-zero typography or visual reader equivalence. Both private original
USFX and native SWORD scanners already independently verified each main-text
word and constructed safe structural events. No Scripture is returned.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json

MAX_SAMPLES = 24
FIELDS = ("nonwhitespace_codepoint_ordinal", "private_book_nonwhitespace_sha256")


class NonspaceBoundaryError(ValueError):
    """Original/native full-text source prerequisite is not met."""


def _anchors(event):
    if not isinstance(event, dict) or event.get("kind") not in {"p", "q"}:
        raise NonspaceBoundaryError("Invalid structure kind")
    pair = []
    for part in ("open", "close"):
        value = event.get(part)
        if not isinstance(value, dict) or not all(k in value for k in FIELDS):
            raise NonspaceBoundaryError("Incomplete private structural boundary")
        number = value["nonwhitespace_codepoint_ordinal"]
        if not isinstance(number, int) or number < 0:
            raise NonspaceBoundaryError("Unsafe character codepoint ordinal")
        digest = value["private_book_nonwhitespace_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(
                c not in "0123456789abcdef" for c in digest):
            raise NonspaceBoundaryError("Invalid private normalized book hash")
        if (value.get("inside_word") or not isinstance(value.get("word_ordinal"), int)
                or value.get("word_ordinal") < 0):
            raise NonspaceBoundaryError("Invalid original/native lexical word position")
        pair.append(value)
    return pair


def compare_punctuation_sensitive_boundaries(source, native):
    """Return a *metadata-only* receipt from independently scanned events."""
    if not source or set(source) != set(native):
        raise NonspaceBoundaryError("Incomplete book scope")
    counts = Counter()
    samples = []
    src_hash = sha256()
    nat_hash = sha256()
    for book in sorted(source):
        source_words, se = source[book]
        native_words, ne = native[book]
        if source_words != native_words or len(se) != len(ne):
            raise NonspaceBoundaryError("Original/native lexical event prerequisite not met")
        counts["books_checked"] += 1
        if not se:
            counts["books_without_addressable_body_boundaries"] += 1
            continue
        source_digests = set()
        native_digests = set()
        src_signatures, nat_signatures = [], []
        for index,(a,b) in enumerate(zip(se,ne),1):
            if a.get("kind") != b.get("kind"):
                raise NonspaceBoundaryError("Original/native kind sequence differs")
            left = _anchors(a)
            right = _anchors(b)
            counts["p_q_events_compared"] += 1
            src_signatures.append((a["kind"],left[0][FIELDS[0]],left[1][FIELDS[0]]))
            nat_signatures.append((b["kind"],right[0][FIELDS[0]],right[1][FIELDS[0]]))
            different = False
            for endpoint,original,compiled in zip(("open","close"),left,right):
                if original["word_ordinal"] != compiled["word_ordinal"]:
                    raise NonspaceBoundaryError("Original/native word boundary positions differ")
                source_digests.add(original[FIELDS[1]])
                native_digests.add(compiled[FIELDS[1]])
                counts["source_event_endpoints_checked"] += 1
                if original[FIELDS[0]] == compiled[FIELDS[0]]:
                    counts[f"{endpoint}_same_nonwhitespace_codepoint_ordinal"] += 1
                else:
                    different=True
                    counts[f"{endpoint}_nonwhitespace_codepoint_ordinal_differs"] += 1
                    if len(samples) < MAX_SAMPLES:
                        samples.append({
                            "book":book,"one_based_event_index":index,
                            "structure_kind":a["kind"],"endpoint":endpoint,
                            "source_reference":original.get("reference"),
                            "native_reference":compiled.get("reference"),
                            "source_nonspace_codepoint_ordinal":original[FIELDS[0]],
                            "native_nonspace_codepoint_ordinal":compiled[FIELDS[0]],
                            "category":"punctuation_or_other_nonspace_boundary_shift",
                        })
            if different:
                counts["events_with_any_nonspace_boundary_shift"] += 1
        if len(source_digests) != 1 or len(native_digests) != 1:
            raise NonspaceBoundaryError("Conflicting private book main-text fingerprints")
        source_digest = next(iter(source_digests))
        native_digest = next(iter(native_digests))
        if source_digest != native_digest:
            counts["books_with_nonwhitespace_maintext_character_difference"] += 1
            if len(samples) < MAX_SAMPLES:
                samples.append({"book":book,
                                "category":"original_and_compiled_nonspace_book_text_differs"})
        else:
            counts["books_with_exact_private_nonwhitespace_text_match"] += 1
        for digest,events in ((src_hash,src_signatures),(nat_hash,nat_signatures)):
            payload=json.dumps([book,events],separators=(",",":"),ensure_ascii=True).encode()
            digest.update(len(payload).to_bytes(4,"big")+payload)

    for field in ("books_without_addressable_body_boundaries",
                  "books_with_nonwhitespace_maintext_character_difference",
                  "open_nonwhitespace_codepoint_ordinal_differs",
                  "close_nonwhitespace_codepoint_ordinal_differs",
                  "events_with_any_nonspace_boundary_shift"):
        counts.setdefault(field,0)

    pass_codepoint_proof=bool(
        source and counts["books_checked"] == len(source)
        and not counts["books_without_addressable_body_boundaries"]
        and not counts["books_with_nonwhitespace_maintext_character_difference"]
        and not counts["events_with_any_nonspace_boundary_shift"]
    )
    return {
        "schema_version":1,
        "status": ("all_p_q_nonwhitespace_codepoint_boundaries_match_diagnostic_only"
                   if pass_codepoint_proof else "nonwhitespace_text_or_event_boundary_differs"),
        "character_sensitive_source_native_counts":dict(sorted(counts.items())),
        "first_character_boundary_anomalies_references_only":samples,
        "source_p_q_nonspace_codepoint_event_hash_sha256":src_hash.hexdigest(),
        "native_p_q_nonspace_codepoint_event_hash_sha256":nat_hash.hexdigest(),
        "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match":pass_codepoint_proof,
        "original_book_main_text_codepoints_compared_after_removing_only_whitespace":True,
        "source_original_whitespace_and_newlines_not_compared_or_approved":True,
        "book_intro_and_punctuation_encoding_editorial_approval_not_given":True,
        "no_original_text_notes_native_markup_or_sids_in_receipt":True,
        "source_module_unchanged_no_publication":True,
    }
