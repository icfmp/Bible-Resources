#!/usr/bin/env python3
"""Private, source-identity-checked zCom link preview for underindexed K groups.

A single genuine authored original numbered-K group may be reachable over a
larger original *editorial* chapter scope in an experimental modern derivative.
Only proof-attested empty native keys are eligible for extension. Source prose,
notes and Bible references are not copied, modified or approved; no original
module or catalogue file is changed. This is reusable for manifest-selected
chapters, never a global fallback for partially annotated chapters.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from commentary_modern_draft_osis_preview import NS, XML, _inline

_CHAPTER = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]{0,2})$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_HEAD = re.compile(r"(?m)^## ([^\n]+)$")
_WORD = re.compile(r"\b[\w’'-]+\b", re.UNICODE)


def modern_exposition(manuscript: Path, *, root: Path, case: dict,
                      source_zip: str, corpus: str) -> list[str]:
    if not manuscript.is_file() or not manuscript.resolve().is_relative_to(root.resolve()):
        raise ValueError("Modern manuscript missing or outside trusted root")
    raw = manuscript.read_text(encoding="utf-8")
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise ValueError("Manuscript missing frontmatter")
    front, remainder = raw[4:].split("\n---\n", 1)
    fields = {}
    for row in front.splitlines():
        if not row.strip():
            continue
        if ": " not in row:
            raise ValueError("Malformed modern manuscript field")
        key, value = row.split(": ", 1)
        if key in fields:
            raise ValueError("Duplicate modern manuscript field")
        fields[key] = value.strip('"')
    if (fields.get("chapter_osis") != case["chapter_osis"] or
        fields.get("source_zip_sha256") != source_zip or
        fields.get("source_native_corpus_sha256") != corpus or
        fields.get("source_module") != "MHCC 0.1.1" or
        not fields.get("publication_status", "").startswith("NOT RELEASED")):
        raise ValueError("Untrusted draft identity, provenance or publication status")
    if "\n---\n" not in remainder:
        raise ValueError("Manuscript lacks separate editorial review")
    main = remainder.split("\n---\n", 1)[0]
    headings = list(_HEAD.finditer(main))
    matching = [i for i, m in enumerate(headings)
                if m[1].strip() == case["modern_heading"]]
    if len(matching) != 1:
        raise ValueError("Source-corresponding chapter section title absent/ambiguous")
    i = matching[0]
    section = main[headings[i].end():headings[i + 1].start()
                   if i + 1 < len(headings) else len(main)]
    if re.search(r"(?m)^#{1,6} ", section):
        raise ValueError("Nested section hierarchy needs source mapping first")
    paragraphs = [p.strip().replace("\n", " ") for p in
                  re.split(r"\n\s*\n", section) if p.strip()]
    if len(paragraphs) < 3 or sum(len(_WORD.findall(p)) for p in paragraphs) < 60:
        raise ValueError("Modern exposition too short for bounded linked preview")
    return paragraphs


def generate(manifest: dict, receipt: dict, root: Path, module_id: str) -> tuple[bytes, dict]:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,32}", module_id):
        raise ValueError("Invalid temporary SWORD preview module ID")
    if manifest.get("status") != (
        "PRIVATE_PROVISIONAL_EXISTING_K_SOURCE_RANGE_LINK_PREVIEW_NOT_EDITORIAL_APPROVAL"):
        raise ValueError("Unknown or nonprivate link-preview manifest")
    if (manifest.get("source_native_corpus_sha256") !=
        receipt.get("original_compiled_corpus_sha256") or
        manifest.get("source_zip_sha256") !=
        "a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746" or
        receipt.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL" or
        receipt.get("source_prose_or_original_markup_exported") is not False or
        receipt.get("semantic_translation_independently_approved") is not False):
        raise ValueError("Original source/rights status not independently authenticated")
    if not _SHA.fullmatch(manifest["source_native_corpus_sha256"]):
        raise ValueError("Invalid complete native source SHA")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 12:
        raise ValueError("Preview must name bounded candidate original K chapters")
    doc = ET.Element(f"{{{NS}}}osis")
    text = ET.SubElement(doc, f"{{{NS}}}osisText", {
        "osisIDWork": module_id, "osisRefWork": "Bible",
        f"{{{XML}}}lang": "en", "canonical": "false"})
    header = ET.SubElement(text, f"{{{NS}}}header")
    work = ET.SubElement(header, f"{{{NS}}}work", {"osisWork": module_id})
    ET.SubElement(work, f"{{{NS}}}title").text = "Private, unapproved native-K scope extension preview"
    ET.SubElement(work, f"{{{NS}}}identifier", {"type": "OSIS"}).text = module_id
    ET.SubElement(work, f"{{{NS}}}language", {"type": "IETF"}).text = "en"
    group = ET.SubElement(text, f"{{{NS}}}div", {"type": "bookGroup"})
    seen = set()
    rows = []
    for case in cases:
        chapter = case.get("chapter_osis", "")
        match = _CHAPTER.fullmatch(chapter)
        if not match or chapter in seen:
            raise ValueError("Duplicate, foreign or invalid original chapter identity")
        seen.add(chapter)
        native = receipt["chapters"].get(chapter)
        if not native or native.get("source_placement") != "NUMBERED_KEYS_WITH_SEPARATE_INTRO":
            raise ValueError("Refuse implicit chapter-wide fallback or I-only source here")
        units = native["original_units"]
        source_first = case.get("source_original_first_key")
        source_last = case.get("source_original_last_key")
        source_sha = case.get("source_original_raw_sha256", "")
        matches = [u for u in units if u["first_key"] == source_first and
                   u["keys"][-1] == source_last and
                   u["source_unit_sha256"] == source_sha]
        if len(matches) != 1 or not _SHA.fullmatch(source_sha):
            raise ValueError("Original numbered-K body hash/bounds are unproven")
        first = case.get("modern_declared_first_verse")
        last = case.get("modern_declared_last_verse")
        cap = case.get("chapter_kjv_verse_count")
        if (type(first) is not int or type(last) is not int or
            type(cap) is not int or not 1 <= first < last <= cap <= 200 or
            source_first != chapter + "." + str(first) or
            int(source_last.rsplit(".", 1)[1]) >= last):
            raise ValueError("Original editorial wider verse range is not bounded")
        original_keys = matches[0]["keys"]
        actual_verse_keys = [int(k.rsplit(".", 1)[1]) for k in original_keys]
        if actual_verse_keys != list(range(first, max(actual_verse_keys) + 1)):
            raise ValueError("Original raw K body does not start as a contiguous index")
        if max(actual_verse_keys) >= last:
            raise ValueError("No genuinely unoccupied end-of-range keys to test")
        all_occupied = {k for u in units for k in u["keys"]}
        added = {f"{chapter}.{n}" for n in
                 range(max(actual_verse_keys) + 1, last + 1)}
        if added & all_occupied:
            raise ValueError("Range extension would overwrite another authorial K body")
        manuscript = root / "work/mhcc-modern/production" / case.get("manuscript", "")
        paragraphs = modern_exposition(manuscript, root=root, case=case,
                                       source_zip=manifest["source_zip_sha256"],
                                       corpus=manifest["source_native_corpus_sha256"])
        book_node = ET.SubElement(group, f"{{{NS}}}div", {
            "type": "book", "osisID": match[1]})
        chapter_node = ET.SubElement(book_node, f"{{{NS}}}chapter", {"osisID": chapter})
        unit = ET.SubElement(chapter_node, f"{{{NS}}}div", {
            "type": "section", "annotateType": "commentary",
            "annotateRef": source_first + "-" + chapter + "." + str(last)})
        ET.SubElement(unit, f"{{{NS}}}title", {
            "type": "sub", "resp": "BibleResourcesModernEditorialNotSourceNative"
        }).text = case["modern_heading"]
        for p in paragraphs:
            paragraph = ET.SubElement(unit, f"{{{NS}}}p")
            _inline(paragraph, p)
        rows.append({
            "chapter": chapter,
            "source_original_first_key": source_first,
            "source_original_last_occupied_key": source_last,
            "original_K_raw_sha256": source_sha,
            "source_authorial_K_groups_in_chapter": len(units),
            "exact_original_K_native_numbered_addresses":native["original_native_numbered_keys"],
            "linked_modern_verse_count":last - first + 1,
            "additional_originally_unoccupied_verse_keys":len(added),
            "authorial_source_K_bodies_added_or_split":0,
            "modern_paragraphs":len(paragraphs),
            "original_notes_references_markups_preservation_approved":False
        })
    output=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(output)
    return output,{
        "status":"PRIVATE_UNVALIDATED_SINGLE_ORIGINAL_K_BODY_EXTENDED_RANGE_PREVIEW",
        "temporary_module_id":module_id,
        "source_zip_sha256":manifest["source_zip_sha256"],
        "source_native_corpus_sha256":manifest["source_native_corpus_sha256"],
        "cases":rows,
        "source_original_module_modified":False,
        "source_versification_modified":False,
        "independent_source_prose_meaning_approved":False,
        "original_source_paragraphs_footnotes_references_preserved":False,
        "original_source_wording_exported":False,
        "sword_published":False
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--source-receipt",type=Path,required=True)
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--osis",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--temp-module-id",default="MHCCKRANGE")
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    receipt=json.loads(args.source_receipt.read_text(encoding="utf-8"))
    out,report=generate(manifest,receipt,args.root,args.temp_module_id)
    args.osis.parent.mkdir(parents=True,exist_ok=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.osis.write_bytes(out)
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("PRIVATE_K_SCOPE_PREVIEW prepared "+str(len(report["cases"]))+
          " original K body link transport cases; original semantics and reader compatibility NOT approved")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
