#!/usr/bin/env python3
"""Read-only OSIS reference target addressability against native SWORD keys.

Recognize documented full endpoint book/chapter/verse ranges and space-delimited
references. Never silently infer abbreviated references or invent omitted
verses. This proves only native key addressability, not actual GUI navigation.
Keep all raw targets, notes and Scripture inside the private audit runner.
"""
from __future__ import annotations

from collections import Counter
import re

from stable_sword_refs import KEY

ENDPOINT = re.compile(
    r"([1-4]?[A-Za-z][A-Za-z0-9]{0,39})"
    r"(?:\.([1-9][0-9]{0,4})(?:\.([1-9][0-9]{0,4}))?)?\Z"
)
MAX_LINKS = 200_000
MAX_SAMPLES = 15


class OSISTargetAuditError(ValueError):
    """Unverifiable original OSIS reference target structure."""


def _scope(key: str, rank: dict[str, int], chapters: dict,
           books: dict):
    """Return (classification, first, last) without inventing any key."""
    if not isinstance(key, str) or len(key)>150:
        return "unsupported_syntax", None, None
    match=ENDPOINT.fullmatch(key)
    if not match:
        if ":" in key:
            return "unsupported_work_prefix_or_colon", None, None
        if "!" in key or "@" in key:
            return "unsupported_osis_grain_or_subidentifier", None, None
        return "unsupported_syntax", None, None
    book, chapter, verse=match.groups()
    if verse:
        if key in rank:
            return "indexed_verse", rank[key], rank[key]
        return ("unindexed_verse_existing_book" if book in books
                else "unindexed_verse_unknown_book"), None, None
    if chapter:
        value=chapters.get(f"{book}.{chapter}")
        return ("indexed_chapter", *value) if value else (
            "unindexed_chapter_existing_book" if book in books
            else "unindexed_chapter_unknown_book", None, None)
    value=books.get(book)
    return ("indexed_book", *value) if value else ("unindexed_book", None, None)


def _resolve_endpoint(key: str, keys: set[str], chapters: set[str],
                      books: set[str]):
    """Backward-compatible bounded simple endpoint diagnostic."""
    rank={x:i for i,x in enumerate(sorted(keys))}
    c={x:(0,0) for x in chapters}
    b={x:(0,0) for x in books}
    kind,_,_=_scope(key,rank,c,b)
    if kind.startswith("indexed_"):
        return kind
    if kind.startswith("unindexed_"):
        return kind.split("_existing_book")[0].split("_unknown_book")[0]
    return "unsupported_syntax"


def _classify_one(token: str, rank: dict, chapters: dict, books: dict):
    """Use OSIS full range endpoints; do not guess shortened displayed refs."""
    if token.count("-")>1:
        return "unsupported_compound_range", 0, False
    if "-" not in token:
        kind,_,_=_scope(token,rank,chapters,books)
        return (kind,1,False) if kind.startswith("indexed_") else (kind,0,False)
    first,last=token.split("-",1)
    left,left_start,left_end=_scope(first,rank,chapters,books)
    right,right_start,right_end=_scope(last,rank,chapters,books)
    if left.startswith("unsupported_") or right.startswith("unsupported_"):
        return "unsupported_range_endpoint_syntax",0,True
    if not left.startswith("indexed_") or not right.startswith("indexed_"):
        return "unindexed_range_endpoint",0,True
    if left_start is None or right_end is None or left_start>right_end:
        return "reversed_or_invalid_range",0,True
    return "indexed_ordered_full_range",2,True


def audit_explicit_targets(source_notes: dict, source_keys: set[str],
                           native_keys: set[str]) -> dict:
    """Classify every authored target against the exact real native verse index.

    Insertion order of source_notes is the independently checked original
    OSIS canonical verse order. No target strings or values leave this report.
    """
    if (not isinstance(source_notes,dict) or not source_keys
            or source_keys!=native_keys or set(source_notes)!=source_keys
            or not all(isinstance(x,str) and KEY.fullmatch(x)
                       for x in source_keys)):
        raise OSISTargetAuditError("Original/native verse reference scope is unverified")
    rank={}
    chapter_bounds={}
    book_bounds={}
    for key in source_notes:
        position=len(rank)
        rank[key]=position
        book,chapter,_verse=key.split(".")
        for item,collection in ((book,book_bounds),
                                (book+"."+chapter,chapter_bounds)):
            if item not in collection:
                collection[item]=(position,position)
            else:
                start,_old=collection[item]
                collection[item]=(start,position)
    counts=Counter()
    samples=[]
    total=0
    for host in source_notes:
        for note_index,note in enumerate(source_notes[host],1):
            if not isinstance(note,dict) or not isinstance(note.get("targets"),tuple):
                raise OSISTargetAuditError("Untrusted authored note/target scope")
            counts["notes_checked"]+=1
            for target in note["targets"]:
                total+=1
                if total>MAX_LINKS:
                    raise OSISTargetAuditError("Reference audit exceeded bounded work")
                counts["explicit_target_attributes_checked"]+=1
                if not isinstance(target,str) or not target or len(target)>1024:
                    outcome="empty_or_oversized_target"
                else:
                    parts=target.split()
                    if not parts or len(parts)>100:
                        outcome="empty_or_oversized_target"
                    else:
                        if len(parts)>1:
                            counts["multi_reference_target_attributes"]+=1
                        classes=[]
                        for item in parts:
                            shape,components,is_range=_classify_one(
                                item,rank,chapter_bounds,book_bounds)
                            classes.append(shape)
                            counts["target_component_"+shape]+=1
                            counts["addressable_endpoint_components"]+=components
                            if is_range:
                                counts["range_components_checked"]+=1
                        if all(x in {"indexed_verse","indexed_chapter","indexed_book",
                                     "indexed_ordered_full_range"} for x in classes):
                            outcome="all_target_components_index_addressable"
                        elif any(x.startswith("unsupported_") for x in classes):
                            outcome="target_with_unsupported_grammar"
                        elif any(x.startswith("unindexed_") for x in classes):
                            outcome="target_with_unindexed_endpoint"
                        else:
                            outcome="target_with_reversed_range_or_other"
                counts[outcome]+=1
                if outcome!="all_target_components_index_addressable" and len(samples)<MAX_SAMPLES:
                    samples.append({"note_host_reference":host,
                                    "one_based_note_index":note_index,
                                    "category":outcome,"target_raw_exposed":False})
    verified=(counts["all_target_components_index_addressable"]==
              counts["explicit_target_attributes_checked"])
    return {
        "status":("all_explicit_targets_index_addressable_including_full_ranges"
                  if verified else "unindexed_or_unreviewed_osis_targets_require_review"),
        "counts":dict(sorted(counts.items())),
        "bounded_note_host_reference_samples":samples,
        "source_and_native_verse_indices_equal":True,
        "all_original_explicit_targets_index_addressable":verified,
        "actual_reader_link_click_navigation_verified":False,
        "original_target_literals_or_note_text_exposed":False,
        "publication_approved":False,
    }
