#!/usr/bin/env python3
"""Derive an experimental SWORD XML v11n delta from verified authorial keys.

This file MUST NOT be used to publish by itself. The v11n is a compatibility
experiment until the *same exact* compiled module is validated with target
SWORD/Xiphos runtime, and all content/formatting/editorial checks succeed.

It never creates Bible verses, rewrites USFM/USFX, or hardcodes specific books.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET

from pilot_preflight import PilotError


def build_v11n_delta(
    keys: list[tuple[str, int, int]],
    names: dict[str, str],
    baseline: dict[tuple[str, int], int],
    *,
    base_name: str,
    edition_id: str,
    book_order: list[str],
    new_testament_first: str = "Matt",
) -> tuple[bytes, dict]:
    """Return UTF-8 XML delta and text-free proof of its origin and coverage.

    The input verse keys MUST be a faithful source inventory. A skipped
    *internal* number cannot be represented as a missing slot in this grid:
    fail, rather than silently fabricate or add an unannotated empty verse.
    """
    if not keys or len(keys) != len(set(keys)):
        raise PilotError("Missing or duplicate source verse keys for XML v11n")
    if not base_name.isalnum() or not edition_id.isalnum():
        raise PilotError("Invalid v11n base or edition system name")
    if len(book_order) != len(names) or set(book_order) != set(names):
        raise PilotError("Unverified or incomplete book order for XML v11n")
    if new_testament_first not in names.values():
        raise PilotError("No known original New Testament boundary")
    if len(set(names.values())) != len(names):
        raise PilotError("Duplicate OSIS book identities in XML v11n derivation")
    if not baseline:
        raise PilotError("Empty SWORD built-in versification inventory")

    by_chapter = defaultdict(set)
    for code, chapter, verse in keys:
        if (code not in names or not isinstance(chapter,int)
                or not isinstance(verse,int) or chapter<1 or verse<1):
            raise PilotError("Unreviewed source verse identity in XML v11n")
        by_chapter[(names[code],chapter)].add(verse)

    # Every original chapter must be a known part of the chosen standard
    # SWORD registry. Never use this function to add or reorder a Bible book.
    if any(chapter not in baseline for chapter in by_chapter):
        raise PilotError("Edition has chapters outside base v11n; human review required")
    changes = {}
    for key, verses in by_chapter.items():
        maximum = max(verses)
        if set(range(1, maximum + 1)) != verses:
            raise PilotError("Source has internal verse omissions requiring editorial review")
        if maximum != baseline[key]:
            changes[key] = maximum

    # The baseline may contain additional full chapters absent from the
    # edition: this is NOT a safe derivation of an exact slot set.
    if set(baseline) != set(by_chapter):
        raise PilotError("Base and source chapter sets differ")

    root=ET.Element("v11n", {"v11nID": edition_id,"base":base_name})
    grouping={"1":[],"2":[]}
    seen_nt=False
    for code in book_order:
        osis=names[code]
        if osis==new_testament_first:
            seen_nt=True
        group="2" if seen_nt else "1"
        changed=[(ch,maximum) for (book,ch),maximum in changes.items()
                 if book==osis]
        if changed:
            grouping[group].append((osis,sorted(changed)))
    for group,records in grouping.items():
        if not records:
            continue
        col=ET.SubElement(root,"collection",{"collectionID":group})
        for book,chapters in records:
            entry=ET.SubElement(col,"book",{"osisID":book})
            for ch,maximum in chapters:
                ET.SubElement(entry,"chapter",{
                    "osisID":f"{book}.{ch}","verseMax":str(maximum),
                })
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n"
    # Reconstruct effective registry entirely independently of markup
    # formatting before claiming a complete reference-index definition.
    effective=dict(baseline)
    effective.update(changes)
    effective_slots={(book,ch,v) for (book,ch),max_v in effective.items()
                     for v in range(1,max_v+1)}
    source_slots={(names[code],ch,v) for code,ch,v in keys}
    if effective_slots!=source_slots:
        raise PilotError("Derived XML v11n still differs from original source slots")
    return xml,{
        "status":"experiment_only_not_approved",
        "base_name":base_name,
        "derived_edition_system_name":edition_id,
        "source_book_count":len(book_order),
        "source_chapter_count":len(by_chapter),
        "source_verse_key_count":len(keys),
        "maxima_adjustments":[
            {"osis_book":book,"chapter":ch,
             "baseline_verse_max":baseline[(book,ch)],
             "source_verse_max":new}
            for (book,ch),new in sorted(changes.items())
        ],
        "changed_chapter_count":len(changes),
        "effective_reference_slot_set_exactly_matches_source":True,
        "xml_sha256":sha256(xml).hexdigest(),
        "original_text_modified":False,
        "editorial_approval":False,
        "can_install_into_unmodified_stable_sword":False,
        "published":False,
    }
