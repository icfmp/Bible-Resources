#!/usr/bin/env python3
"""Read-only original eBible USFX -> compiled SWORD footnote body comparison.

This adds an independent publisher-source leg to the existing OSIS->SWORD
diagnostic, so loss of whitespace in both conversion stages is visible.
The temporary SWORD note contents are passed in memory, NEVER serialized.
Only book-level counts, reference IDs and hashes may reach CI artifacts.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re
import unicodedata

from lxml import etree

from lsg_note_parity import _collect_usfx
from lsg_stock_lemma_parity import _books
from lsg_note_whitespace_diagnostics import classify_note_whitespace
from pilot_preflight import PilotError


def _space(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC",value).split())


def _raw(value: str) -> str:
    return unicodedata.normalize("NFC",value)


def _parsed_compiled_body(xml_fragment: str) -> str:
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    root=etree.fromstring(("<root>"+xml_fragment+"</root>").encode("utf-8"),parser)
    return _raw("".join(root.itertext()))


def compare_publisher_usfx_to_compiled_notes(
    publisher_usfx: bytes, candidate, aliases: list[tuple[str,str]],
    decisions: list[dict], compiled: dict
) -> dict:
    if re.search(rb"<!DOCTYPE\b", publisher_usfx, re.IGNORECASE):
        raise PilotError("Untrusted publisher USFX has forbidden DOCTYPE")
    root=etree.fromstring(publisher_usfx,parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,
        recover=False,huge_tree=False))
    book_codes=[book.get("id") for book in root.iter("book")]
    book_ids=[book.get("osisID") for book in _books(candidate)]
    if (len(book_codes)!=len(book_ids)
            or len(set(book_codes))!=len(book_codes)
            or any(not code for code in book_codes)):
        raise PilotError("Cannot align publisher USFX and candidate OSIS books")
    mapping=dict(zip(book_codes,book_ids))
    source_notes,outside=_collect_usfx(root)
    if outside:
        raise PilotError("Publisher notes outside verse scope need review")
    aliases_by_key=dict(aliases)
    remap={}
    for decision in decisions:
        src=decision["osis_source_key"]
        dst=decision["osis_reader_key"]
        if src in remap or src==dst or dst not in aliases_by_key:
            raise PilotError("Unexpected publisher-to-reader reference merge")
        remap[src]=dst
    expected=defaultdict(list)
    for (code,chapter,verse),notes in source_notes.items():
        if code not in mapping:
            raise PilotError("Unmapped publisher note book")
        original_key=f"{mapping[code]}.{chapter}.{verse}"
        reader_key=remap.get(original_key,original_key)
        if reader_key not in aliases_by_key:
            raise PilotError("Publisher note reference has no stock reader key")
        expected[(reader_key.split(".",1)[0],aliases_by_key[reader_key])].extend(notes)
    unmatched_counts=[]
    source_count=sum(len(v) for v in expected.values())
    compiled_count=sum(len(v) for v in compiled.values())
    raw_equal=normalized_equal=0
    classifications=Counter()
    whitespace_features=Counter()
    mismatches=[]
    for location in sorted(set(expected)|set(compiled)):
        source_group=expected.get(location,[])
        target_group=compiled.get(location,{})
        if len(source_group)!=len(target_group):
            if len(unmatched_counts)<60:
                unmatched_counts.append({
                    "book":location[0],"reader_reference":location[1],
                    "publisher_notes":len(source_group),
                    "compiled_notes":len(target_group)})
        if not all(note_id.isascii() and note_id.isdecimal()
                   for note_id in target_group):
            raise PilotError("Unordered compiled publisher-source note references")
        note_ids=sorted(target_group,key=int)
        for index,(source_note,note_id) in enumerate(
                zip(source_group,note_ids),1):
            body=target_group[note_id].get("body")
            if not body:
                raise PilotError("Compiled SWORD note body missing in publisher review")
            try:
                compiled_raw=_parsed_compiled_body(body)
            except (etree.XMLSyntaxError,UnicodeError,ValueError) as exc:
                raise PilotError("Unparseable compiled note in publisher review") from exc
            original_raw=_raw("".join(source_note["_xml_node"].itertext()))
            same=original_raw==compiled_raw
            raw_equal+=same
            normalized_equal+=_space(original_raw)==_space(compiled_raw)
            detail=classify_note_whitespace(original_raw,compiled_raw)
            classifications[detail["class"]]+=1
            if not same:
                whitespace_features.update({
                    k:v for k,v in detail.items()
                    if k in ("source_newline_runs_changed",
                             "compiled_newline_runs_changed",
                             "source_unicode_space_runs_changed",
                             "compiled_unicode_space_runs_changed",
                             "changed_whitespace_runs","changed_boundary_runs",
                             "changed_internal_runs",
                             "changed_runs_increased_length",
                             "changed_runs_decreased_length",
                             "changed_runs_same_length")
                })
                if len(mismatches)<70:
                    mismatches.append({
                        "book":location[0],
                        "reader_reference":location[1],
                        "note_ordinal":index,
                        "category":detail["class"],
                        "publisher_body_sha256":sha256(original_raw.encode()).hexdigest(),
                        "compiled_body_sha256":sha256(compiled_raw.encode()).hexdigest(),
                        "tokens_match_exactly":detail["content_equivalent"],
                    })
    matched=(source_count==compiled_count==normalized_equal
             and not unmatched_counts)
    return {
        "status":("publisher_usfx_to_compiled_sword_notes_normalized_match"
                  if matched else "publisher_to_compiled_sword_note_text_mismatch"),
        "source_stage":"immutable_original_eBible_USFX_not_generated_OSIS",
        "publisher_source_note_count":source_count,
        "compiled_note_count":compiled_count,
        "publisher_raw_note_bodies_exact_in_compiled_sword":raw_equal,
        "publisher_normalized_note_bodies_equal":normalized_equal,
        "publisher_vs_compiled_note_whitespace_classes":dict(sorted(classifications.items())),
        "publisher_vs_compiled_changed_whitespace_features":dict(
            sorted(whitespace_features.items())),
        "note_count_mismatches":unmatched_counts,
        "first_source_to_binary_note_body_differences":mismatches,
        "exact_publisher_editorial_whitespace_preserved":raw_equal==source_count,
        "publisher_note_spelling_and_punctuation_verified":matched,
        "original_source_modified":False,
        "full_editorial_whitespace_approved":False,
        "published":False,
    }
