#!/usr/bin/env python3
"""Private source-native first-K book-preface cross-reference recovery.

A distinct, unpublished post-preface derivative. Never changes original
MHCC 0.1.1 or accepted modern manuscripts. Uses original source K/ordinal,
target/label SHA, source-first-K introductory proof and uniquely printed
modern book-introduction verse numbers; undecidable links remain in their
original-K provenance notes. Do NOT export source-context text.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from commentary_modern_draft_osis_preview import NS
from commentary_modern_reference_gate import (
    _AUTO_ALIASES,
    _ENGLISH_NAME_BY_OSIS,
    canonical_only_for_comparison,
)

SOURCE_CORPUS = "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"
NOTE_RESP = "BibleResourcesPrivateSourceOnlyLinkSupplement"
INTRO_RESP = "BibleResourcesModernRelocatedFirstNativeKBookPreface"
LINK_RESP = "BibleResourcesOriginalFirstKSourcePrefaceCrossReference"

def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def authored_text(node):
    """Exclude *only* the already-labelled source-only link notes."""
    out = []
    def walk(n):
        if n.tag == f"{{{NS}}}note" and n.get("resp") == NOTE_RESP:
            if n.tail:
                out.append(n.tail)
            return
        if n.text:
            out.append(n.text)
        for child in n:
            walk(child)
            if child.tail and not (
                child.tag == f"{{{NS}}}note" and child.get("resp") == NOTE_RESP):
                out.append(child.tail)
    walk(node)
    return "".join(out)

def paragraph_slots(p):
    items, pieces = [], []
    cur = 0
    def push(node, attr, protected):
        nonlocal cur
        value = getattr(node, attr)
        if value:
            items.append((cur, cur + len(value), node, attr, protected, value))
            pieces.append(value)
            cur += len(value)
    def walk(node, linked=False):
        if node.tag == f"{{{NS}}}note":
            return
        linked_now = linked or node.tag == f"{{{NS}}}reference"
        push(node, "text", linked_now)
        for child in node:
            walk(child, linked_now)
            push(child, "tail", linked)
    walk(p)
    return "".join(pieces), items

def visible_candidates(intro, literal):
    try:
        target = canonical_only_for_comparison(literal)
        book, chapter, verse = target.rsplit(".", 2)
    except (ValueError, KeyError):
        return []
    aliases = set(_AUTO_ALIASES.get(book, ()))
    full = _ENGLISH_NAME_BY_OSIS.get(book)
    if full:
        aliases.add(full)
    if not aliases:
        return []
    alias_re = "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
    # All tokens must be present in the modern intro, even when emphasis
    # separates book labels and numeric verse tokens into XML nodes.
    main = re.compile(
        r"(?<![A-Za-z0-9])(?:" + alias_re + r")\s+" +
        r"\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*"
        r"(?:\s*;\s*\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*)*",
        flags=re.IGNORECASE,
    )
    sub = re.compile(
        r"(?<!\d)(\d+)\s*:\s*(\d+)"
        r"((?:\s*[,\u2013\u2014-]\s*\d+)*)"
    )
    found = []
    for p in intro.findall(f".//{{{NS}}}p"):
        plain, slots = paragraph_slots(p)
        for m in main.finditer(plain):
            display = m.group()
            for pair in sub.finditer(display):
                if pair[1] != chapter:
                    continue
                values = [(pair[2], pair.start(2), pair.end(2))]
                values += [
                    (x.group(), pair.start(3) + x.start(), pair.start(3) + x.end())
                    for x in re.finditer(r"\d+", pair[3])
                ]
                for number, start, end in values:
                    if number != verse:
                        continue
                    a, b = m.start() + start, m.start() + end
                    for slot_start, slot_end, node, attr, protected, old in slots:
                        if not protected and slot_start <= a and b <= slot_end:
                            found.append((node, attr, old, a-slot_start, b-slot_start))
    return found

def build(*, source_osis: bytes, review: dict, notes_receipt: dict,
          preface_receipt: dict, suspected_errors: dict) -> tuple[bytes,dict]:
    if (review.get("status") != "EPHEMERAL_EXCERPTS_PRIVATE_EDITORIAL_REVIEW_ONLY"
            or review.get("source_pinned_corpus_sha256") != SOURCE_CORPUS
            or review.get("original_source_changed") is not False
            or review.get("original_link_placement_approved") is not False
            or review.get("citation_count") != 176
            or notes_receipt.get("original_native_corpus_sha256") != SOURCE_CORPUS
            or notes_receipt.get("status") !=
               "PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY"
            or notes_receipt.get("published_or_distributed") is not False
            or preface_receipt.get("original_native_corpus_sha256") != SOURCE_CORPUS
            or preface_receipt.get("status") !=
               "PRIVATE_SOURCE_K_BOOK_PREFACE_RESTORATION_NOT_EDIT_OR_RELEASE"
            or preface_receipt.get("publication_authorized") is not False
            or suspected_errors.get("status") !=
               "ORIGINAL_DIGITAL_SOURCE_LINK_DISCREPANCIES_REVIEW_ONLY_NOT_APPLIED"
            or suspected_errors.get("original_corpus_sha256") != SOURCE_CORPUS
            or suspected_errors.get("proposed_navigation_approved") is not False):
        raise ValueError("Source pinned and unapproved preface reference review receipts required")
    cases = preface_receipt["cases"]
    vetted = {
        c["original_source_first_K"]: c["book"]
        for c in cases if c["source_K_intro_disposition"] ==
        "INSERTED_SEPARATE_MODERN_INTRO_FROM_VERIFIED_ORIGINAL_K"
    }
    if (len(vetted) != preface_receipt["new_book_intros_inserted_as_separate_introduction_OSIS"]
            or len(set(vetted.values())) != len(vetted)):
        raise ValueError("Missing source-authenticated original first-K preface case")

    prohibited = set()
    for case in suspected_errors["cases"]:
        if case.get("approval") is not False:
            raise ValueError("Unapproved original source hyperlink discrepancy changed")
        prohibited.add((case["source_first_key"], case["source_reference_ordinal"]))
    if len(prohibited) != len(suspected_errors["cases"]):
        raise ValueError("Repeated source hyperlink anomaly")

    source_rows = {
        (x["source_first_key"], x["source_reference_ordinal"]): x
        for x in review["references"]
    }
    if len(source_rows) != 176:
        raise ValueError("Incomplete original source hyperlink contextual review")

    pending = {}
    note_by_K = {}
    for entry in notes_receipt["note_source_K_reference_hashes_for_private_native_readback"]:
        first = entry["source_first_key"]
        if first in note_by_K:
            raise ValueError("Duplicate source K with unresolved original references")
        note_by_K[first] = entry["original_source_reference_hashes"]
        for r in entry["original_source_reference_hashes"]:
            key = (first, r["source_reference_ordinal"])
            if key in pending:
                raise ValueError("Duplicate source K/ordinal")
            row = source_rows.get(key)
            if row is None or (
                sha(row["original_literal_osisRef"]) !=
                r["source_original_literal_target_sha256"]
            ) or (
                row["original_visible_label_sha256"] !=
                r["supplement_display_sha256"]
                and r["supplement_display_sha256"] !=
                    sha(row["original_printed_link_label"])
            ):
                # Supplement *display* is a derived normalized label, not
                # the original printed label; verify the original printed
                # label separately against the packet's pinned hash below.
                if row is None or sha(row["original_literal_osisRef"]) != (
                        r["source_original_literal_target_sha256"]):
                    raise ValueError("Original source K/ordinal or target SHA mismatch")
            if sha(row["original_printed_link_label"]) != (
                    row["original_visible_label_sha256"]):
                raise ValueError("Original source linked-print label SHA mismatch")
            pending[key] = r
    if len(pending) != notes_receipt[
            "original_link_occurrences_preserved_only_in_separate_source_notes"]:
        raise ValueError("Incomplete K source-note identity inventory")

    root = ET.fromstring(source_osis)
    visible_before = authored_text(root)
    raw_refs_before = Counter((x.get("osisRef"), "".join(x.itertext()))
        for x in root.iter() if x.tag == f"{{{NS}}}reference")
    chapters = {x.get("osisID"): x for x in root.iter()
                if x.tag == f"{{{NS}}}chapter"}
    intro_by_first = {}
    original_sections = {}
    for first, book in vetted.items():
        chapter = chapters.get(f"{book}.1")
        if chapter is None:
            raise ValueError("Vetted original book introduction's chapter absent")
        intros = [x for x in chapter.findall(f"./{{{NS}}}div")
                  if x.get("type") == "introduction" and
                  x.get("resp") == INTRO_RESP]
        if len(intros) != 1:
            raise ValueError("Restored original first-K modern preface not unique")
        sections = chapter.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if not sections or not sections[0].get("annotateRef","").startswith(first):
            raise ValueError("Source first K authorial section ownership drift")
        intro_by_first[first] = intros[0]
        original_sections[first] = sections[0]

    matches = {}
    by_slot = {}
    for key, receipt in pending.items():
        if key in prohibited or key[0] not in intro_by_first:
            continue
        row = source_rows[key]
        original_target = row["original_literal_osisRef"]
        printed = row["original_printed_link_label"]
        try:
            verse = canonical_only_for_comparison(original_target).rsplit(".",1)[1]
        except ValueError:
            continue
        if verse not in re.findall(r"\b\d{1,3}\b",printed):
            continue
        found = visible_candidates(intro_by_first[key[0]], original_target)
        if len(found) != 1:
            continue
        node, field, value, a, b = found[0]
        item = dict(
            source_first_key=key[0], source_reference_ordinal=key[1],
            original_literal_target=original_target,
            original_literal_target_sha256=sha(original_target),
            original_visible_label_sha256=row["original_visible_label_sha256"],
            modern_visible_digit_sha256=sha(value[a:b]), node=node,
            attr=field, value=value, start=a, end=b)
        matches[key] = item
        by_slot.setdefault((id(node),field),[]).append(key)
    # Multiple source links claiming exactly one displayed token stay pending.
    collision = set()
    for keys in by_slot.values():
        counts = Counter((matches[k]["start"],matches[k]["end"]) for k in keys)
        collision.update(k for k in keys
            if counts[(matches[k]["start"],matches[k]["end"])] > 1)
    for k in collision:
        matches.pop(k)
    for slot, keys in by_slot.items():
        items = sorted((matches[k] for k in keys if k in matches),
                       key=lambda x:x["start"])
        if not items:
            continue
        node, attr, original = items[0]["node"], items[0]["attr"], items[0]["value"]
        if attr != "text":
            # Avoid creating a sibling inside an XML parent's tail when
            # source markup provenance is less obvious.
            for k in keys:
                matches.pop(k,None)
            continue
        if any(x["node"] is not node or x["attr"]!=attr or
               x["value"]!=original for x in items):
            raise ValueError("Conflicting source preface modern text slot")
        pos=0
        new=[]
        for x in items:
            if x["start"] < pos:
                raise ValueError("Overlapping original preface Bible references")
            link=ET.Element(f"{{{NS}}}reference",{
                "osisRef":x["original_literal_target"], "resp":LINK_RESP})
            link.text=original[x["start"]:x["end"]]
            new.append((original[pos:x["start"]],link))
            pos=x["end"]
        node.text=new[0][0]
        for i,(unused,link) in enumerate(new):
            link.tail=(new[i+1][0] if i+1<len(new) else original[pos:])
            node.insert(i,link)

    kept = {}
    for first, refs in note_by_K.items():
        chapter=chapters[first.rsplit(".",1)[0]]
        sections=chapter.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        candidates=[x for x in sections if x.get("annotateRef","").startswith(first)]
        if len(candidates)!=1:
            raise ValueError("Original source-owned K cannot be located")
        section=candidates[0]
        notes=[x for x in section if x.tag==f"{{{NS}}}note" and
               x.get("resp")==NOTE_RESP]
        if len(notes)!=1:
            raise ValueError("Source-only original K note missing")
        note=notes[0]
        original_references=[x for x in note if x.tag==f"{{{NS}}}reference"]
        if len(original_references)!=len(refs):
            raise ValueError("Original source-only K note count drift")
        remainder=[]
        for proof,ref in zip(refs,original_references):
            key=first,proof["source_reference_ordinal"]
            if sha(ref.get("osisRef","")) != proof["source_original_literal_target_sha256"] or (
                    sha("".join(ref.itertext())) != proof["supplement_display_sha256"]):
                raise ValueError("Original source note target/display or order changed")
            if key not in matches:
                remainder.append((key,ref))
        for ref in original_references:
            note.remove(ref)
        if not remainder:
            section.remove(note)
        else:
            note.text="Unplaced links from original edition (not translated citations): "
            for i,(key,ref) in enumerate(remainder):
                ref.tail="; " if i+1<len(remainder) else "."
                note.append(ref)
            kept[first] = [x[0][1] for x in remainder]
    if authored_text(root) != visible_before:
        raise ValueError("Source first-K preface link relocation changed visible prose")
    links_after=Counter((x.get("osisRef"), "".join(x.itertext()))
        for x in root.iter() if x.tag == f"{{{NS}}}reference")
    # Existing links are preserved except a normalized original-source
    # note label is replaced by a real printed modern verse-number label.
    for key,item in matches.items():
        pass
    if sum(links_after.values())!=sum(raw_refs_before.values()):
        raise ValueError("Original source crossreference occurrence count changed")

    left = sorted(set(pending)-set(matches))
    if len(left)+len(matches)!=len(pending):
        raise ValueError("Unresolved preface source-link disposition incomplete")
    out=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(out)
    result={
        "status":"PRIVATE_AUTHENTICATED_ORIGINAL_FIRST_K_PREFACE_LINKS_NOT_RELEASE",
        "original_native_corpus_sha256":SOURCE_CORPUS,
        "original_unplaced_link_occurrences_in_input":len(pending),
        "original_links_recovered_inside_verified_preface":len(matches),
        "source_original_link_occurrences_remain_in_K_notes":len(left),
        "source_original_link_destination_rewritten":False,
        "original_text_and_modern_manuscript_prose_changed":False,
        "original_K_section_structure_changed":False,
        "source_context_excerpt_exported":False,
        "preface_links_editorial_transfer_not_original_inline":True,
        "editorial_approval":False,"released_or_distributed":False,
        "placements":[{
            "source_first_key":v["source_first_key"],
            "source_reference_ordinal":v["source_reference_ordinal"],
            "original_literal_target_sha256":v["original_literal_target_sha256"],
            "original_visible_label_sha256":v["original_visible_label_sha256"],
            "modern_visible_verse_token_sha256":v["modern_visible_digit_sha256"],
        } for _,v in sorted(matches.items())],
        "remaining_source_K_notes":[{
            "source_first_key":first,
            "original_reference_ordinals":kept[first],
        } for first in sorted(kept)]
    }
    return out,result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("source-osis","source-review-json","remaining-notes-report",
                "source-preface-proof","source-error-review","out-osis",
                "out-receipt"):
        p.add_argument("--"+arg, type=Path,required=True)
    args=p.parse_args()
    data=lambda p:json.loads(p.read_text(encoding="utf-8"))
    whole=data(args.remaining_notes_report)
    source_osis,proof=build(
        source_osis=args.source_osis.read_bytes(),
        review=data(args.source_review_json),
        notes_receipt=whole["private_first_K_outline_verse_remaining_notes"],
        preface_receipt=data(args.source_preface_proof),
        suspected_errors=data(args.source_error_review))
    args.out_osis.parent.mkdir(parents=True,exist_ok=True)
    args.out_receipt.parent.mkdir(parents=True,exist_ok=True)
    args.out_osis.write_bytes(source_osis)
    args.out_receipt.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n",
                               encoding="utf-8")
    print("PRIVATE ORIGINAL FIRST-K PREFACE LINK RESTORATION: "+
          str(proof["original_links_recovered_inside_verified_preface"]) +
          " original links on exact modern introductory verse digits; "+
          str(proof["source_original_link_occurrences_remain_in_K_notes"]) +
          " remaining source K notes; NOT source-authorial-inline proof")

if __name__=="__main__":
    main()
