#!/usr/bin/env python3
"""Dry-run source-bound USFX/OSIS note separator restoration.

This explicitly simulates (in a deep copy) only spaces that are demonstrably
present immediately before a source note but missing before the paired OSIS
note. No original file or candidate file is rewritten or published. The
recovered draft is useful only for a separate, full-corpus parity diagnostic.

Never infer a separator from a verse reference, book-specific wording, or
token heuristics. Pair every note by source verse, order and approved
text/word anchor first. Do not silently repair unknown editorial structure.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib

from lxml import etree

from lsg_note_parity import audit_notes, _collect_usfx, _collect_osis
from pilot_preflight import PilotError


def _predecessor_text(node) -> str:
    previous=node.getprevious()
    if previous is not None:
        return previous.tail or ""
    parent=node.getparent()
    if parent is None:
        raise PilotError("Unattached note node in spacing audit")
    return parent.text or ""


def _append_before(node, separator: str) -> None:
    if separator!=" ":
        raise PilotError("Only original ASCII spaces are modeled automatically")
    previous=node.getprevious()
    if previous is not None:
        previous.tail=(previous.tail or "")+separator
        return
    parent=node.getparent()
    if parent is None:
        raise PilotError("Unattached target note node")
    parent.text=(parent.text or "")+separator


def simulate_source_note_spaces(source_root, target_root, mapping):
    """Return a modified *copy* plus machine-safe metadata (not a saved OSIS).

    Requires all source note labels, kind, order and word anchors to match.
    Existing source metadata is never changed. Source tabs/newlines may be
    represented by one ASCII space in the cloned *diagnostic* rendering,
    but that does not claim exact preservation of source editorial whitespace.
    Candidate-added spaces remain explicit unreviewed differences.
    """
    initial=audit_notes(source_root,target_root,mapping)
    count=initial["source_note_count"]
    if count!=initial["candidate_note_count"] or initial["unpaired_note_count"]:
        raise PilotError("Cannot model note spaces when note counts differ")
    allowed_differences={"raw_component_text","preceding_separator_presence"}
    unexpected=set(initial["mismatch_counts"])-allowed_differences
    if (unexpected or initial["matching_note_component_text"]!=count
            or initial["matching_note_caller_markers"]!=count
            or initial["matching_note_word_anchors"]!=count
            or initial["matching_note_kinds"]!=count
            or initial["unsupported_note_substructures"]
            or initial["source_notes_outside_verses"]
            or initial["candidate_notes_outside_verses"]):
        raise PilotError("Cannot model note spaces without verified note identity")
    source_notes, _=_collect_usfx(source_root)
    candidate_copy=deepcopy(target_root)
    target_notes, _=_collect_osis(candidate_copy)
    before_bytes=etree.tostring(target_root,encoding="utf-8")
    cases=Counter()
    insertions=[]
    for (book,chapter,verse), notes in sorted(source_notes.items()):
        if book not in mapping:
            raise PilotError("Unknown book mapping in note-space model")
        candidate_key=f"{mapping[book]}.{chapter}.{verse}"
        paired=target_notes.get(candidate_key,[])
        if len(notes)!=len(paired):
            raise PilotError("Lost note alignment during dry run")
        for ordinal,(original,generated) in enumerate(zip(notes,paired),1):
            old_space=original["space_immediately_before_note"]
            new_space=generated["space_immediately_before_note"]
            if old_space and not new_space:
                raw=_predecessor_text(original["_xml_node"])
                if not raw or not raw[-1].isspace():
                    raise PilotError("Source note separator audit does not match the XML")
                kind=(
                    "ascii_space" if raw[-1]==" " else
                    "newline" if raw[-1] in "\r\n" else
                    "tab" if raw[-1]=="\t" else
                    "other_unicode_space"
                )
                # This is a visual normalization *only in the clone*:
                # retain the exact source character in the original USFX.
                _append_before(generated["_xml_node"]," ")
                cases["source_space_modeled_in_memory"]+=1
                cases["source_separator_"+kind]+=1
                if len(insertions)<50:
                    insertions.append({
                        "reference":f"{book}.{chapter}.{verse}",
                        "note_ordinal":ordinal,
                        "word_anchor":original["word_index"],
                        "preceding_source_whitespace_characters":
                            len(raw)-len(raw.rstrip()),
                    })
            elif old_space and new_space:
                cases["source_space_already_preserved"]+=1
            elif not old_space and new_space:
                cases["candidate_only_space_not_removed"]+=1
            else:
                cases["both_without_space"]+=1
    if etree.tostring(target_root,encoding="utf-8")!=before_bytes:
        raise PilotError("Dry run unexpectedly mutated the original candidate tree")
    new_audit=audit_notes(source_root,candidate_copy,mapping)
    if new_audit["source_note_count"]!=count or (
            new_audit["matching_note_component_text"]!=count
            or new_audit["matching_note_word_anchors"]!=count
            or new_audit["matching_note_caller_markers"]!=count):
        raise PilotError("Dry run altered note identity, text or word anchors")
    return candidate_copy,{
        "operation":"in_memory_source_bound_dry_run_only",
        "original_candidate_unchanged":True,
        "candidate_before_sha256":hashlib.sha256(before_bytes).hexdigest(),
        "candidate_draft_sha256":hashlib.sha256(
            etree.tostring(candidate_copy,encoding="utf-8")).hexdigest(),
        "source_note_count":count,
        "by_category":dict(sorted(cases.items())),
        "first_modeled_insertions":insertions,
        "notes_with_missing_preceding_space_after_dryrun":
            new_audit["preceding_note_separator_presence_cases"].get(
                "missing_from_candidate",0),
        "full_note_editorial_metadata_approved":False,
        "limitation":"Source-authored whitespace immediately before notes "
                     "is visualized as one ASCII space in an isolated copy, "
                     "not restored byte-for-byte. XML originals and candidate "
                     "are unchanged; editorial whitespace, note text formatting "
                     "and SWORD indexing remain separate review gates.",
    }
