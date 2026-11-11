#!/usr/bin/env python3
"""Metadata-only OSIS note target addressability against exact native SWORD keys.

This is a conservative syntactic and index-presence screen, NEVER a claim
that a GUI follows note links or that abbreviated/custom targets are invalid.
Do not emit original target literals, notes or source text.
"""
from __future__ import annotations

from collections import Counter
import re

from stable_sword_refs import KEY

ENDPOINT = re.compile(r"([1-4]?[A-Za-z][A-Za-z0-9]{0,39})(?:\.([1-9][0-9]{0,4})(?:\.([1-9][0-9]{0,4}))?)?\Z")
MAX_LINKS = 200_000
MAX_SAMPLES = 15


class OSISTargetAuditError(ValueError):
    """Cannot trust original OSIS target comparison."""


def _resolve_endpoint(token: str, keys: set[str], chapters: set[str], books: set[str]):
    if not isinstance(token, str) or len(token)>150:
        return "unsupported_syntax"
    match=ENDPOINT.fullmatch(token)
    if not match:
        return "unsupported_syntax"
    book,ch,verse=match.groups()
    if verse:
        return "indexed_verse" if token in keys else "unindexed_verse"
    if ch:
        return "indexed_chapter" if token in chapters else "unindexed_chapter"
    return "indexed_book" if book in books else "unindexed_book"


def audit_explicit_targets(source_notes: dict, source_keys: set[str],
                           native_keys: set[str]) -> dict:
    """Inspect *every* explicit osisRef privately, without coercing a target.

    Native index equality is a prerequisite: an upstream missing verse must not
    be misreported as a local rendering failure.
    """
    if (not source_keys or source_keys != native_keys
            or not all(isinstance(x,str) and KEY.fullmatch(x) for x in source_keys)
            or not isinstance(source_notes,dict)
            or set(source_notes)!=source_keys):
        raise OSISTargetAuditError("Native and publisher indexed source scope is unverified")
    chapters={ref.rsplit(".",1)[0] for ref in native_keys}
    books={ref.split(".",1)[0] for ref in native_keys}
    counts=Counter()
    samples=[]
    total=0
    for ref in sorted(source_notes):
        for index,note in enumerate(source_notes[ref],1):
            if not isinstance(note,dict) or not isinstance(note.get("targets"),tuple):
                raise OSISTargetAuditError("Untrusted original note annotation scope")
            counts["notes_checked"]+=1
            for target in note["targets"]:
                total+=1
                if total>MAX_LINKS:
                    raise OSISTargetAuditError("Target audit exceeds bounded work")
                counts["explicit_target_attributes_checked"]+=1
                if not isinstance(target,str) or not target or len(target)>1024:
                    category="empty_or_oversized"
                    parts=[]
                else:
                    parts=target.split()
                    if len(parts)>100:
                        category="unsupported_multi_target_size"
                    elif not parts:
                        category="empty_or_oversized"
                    elif any("-" in p for p in parts):
                        category="range_or_compound_reference_requires_review"
                    else:
                        categories=[_resolve_endpoint(p,native_keys,chapters,books) for p in parts]
                        if all(c.startswith("indexed_") for c in categories):
                            category="all_endpoints_index_addressable"
                            counts["addressable_endpoint_components"]+=len(categories)
                        elif any(c=="unsupported_syntax" for c in categories):
                            category="unsupported_endpoint_syntax"
                        else:
                            category="nonindexed_endpoint_requires_review"
                        if len(parts)>1:
                            counts["multi_reference_target_attributes"]+=1
                counts[category]+=1
                if category!="all_endpoints_index_addressable" and len(samples)<MAX_SAMPLES:
                    samples.append({"note_host_reference":ref,"one_based_note_index":index,
                                    "category":category,"target_raw_exposed":False})
    return {
        "status":"all_explicit_targets_index_addressable_simple_syntax"
                 if not sum(v for k,v in counts.items() if k in {
                    "empty_or_oversized","unsupported_multi_target_size",
                    "range_or_compound_reference_requires_review",
                    "unsupported_endpoint_syntax","nonindexed_endpoint_requires_review"
                 }) else "some_explicit_targets_need_grammar_or_editorial_review",
        "counts":dict(sorted(counts.items())),
        "bounded_note_host_reference_samples":samples,
        "source_and_native_verse_indices_equal":True,
        "actual_reader_link_click_navigation_verified":False,
        "original_target_literals_or_note_text_exposed":False,
        "publication_approved":False,
    }
