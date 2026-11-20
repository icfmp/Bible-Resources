#!/usr/bin/env python3
"""Private SWORD OSIS transport preview for explicitly reviewed I-only source chapters.

This is NOT a general whole-chapter fallback or a release builder. It accepts
only explicitly manifest-listed chapters with a verified published I body and
no original numbered K entries, and links ONE modern body to the chapter's
numbered verse span. Source text is never exported via the receipt/report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from commentary_modern_draft_osis_preview import NS, XML, _inline

_HEX = re.compile(r"^[0-9a-f]{64}$")
_CHAPTER = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]{0,2})$")
_HEADING = re.compile(r"(?m)^## (.+?)\s*$")


def _read_candidate(path: Path, case: dict, pins: dict) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("Modern manuscript missing source-pinned frontmatter")
    header, remainder = text[4:].split("\n---\n", 1)
    fields = {}
    for line in header.splitlines():
        if ": " not in line:
            raise ValueError("Invalid modern manuscript metadata")
        key, raw = line.split(": ", 1)
        if key in fields:
            raise ValueError("Duplicate manuscript metadata field")
        fields[key] = raw.strip('"')
    if (fields.get("chapter_osis") != case["chapter_osis"]
            or fields.get("source_module") != pins["source_module"]
            or fields.get("source_zip_sha256") != pins["source_zip_sha256"]
            or fields.get("source_native_corpus_sha256") != pins["source_native_corpus_sha256"]
            or not fields.get("publication_status", "").startswith("NOT RELEASED")):
        raise ValueError("Modern manuscript does not match pinned unshipped source")
    if "\n---\n" not in remainder:
        raise ValueError("No separation from editorial review notes")
    prose, reviews = remainder.split("\n---\n", 1)
    if not reviews.lstrip().startswith("## Editorial review"):
        raise ValueError("Unrecognized manuscript editorial review boundary")
    heads = list(_HEADING.finditer(prose))
    if len(heads) != 2 or not heads[0][1].lower().startswith("original"):
        raise ValueError("Expected original-heading metadata and one full-chapter exposition")
    original_meta = prose[heads[0].end():heads[1].start()].strip()
    source_title = case.get("original_source_heading")
    if source_title is None:
        if not original_meta.startswith("*No independent topical heading"):
            raise ValueError("Source heading status requires editorial verification")
    elif original_meta != "**" + source_title + "**":
        raise ValueError("Source heading draft differs from the declared original-heading witness")
    heading = heads[1][1].strip()
    if not heading or heading.lower().startswith("original"):
        raise ValueError("Missing modern exposition section")
    paragraphs = [p.strip().replace("\n", " ") for p in
                  re.split(r"\n\s*\n", prose[heads[1].end():]) if p.strip()]
    if not paragraphs or any(p.startswith("#") for p in paragraphs):
        raise ValueError("Missing/unsupported modern chapter prose")
    if sum(len(re.findall(r"\b\w+\b", p)) for p in paragraphs) < 45:
        raise ValueError("Modern chapter exposition is unexpectedly short")
    return heading, paragraphs


def generate(manifest: dict, receipt: dict, root: Path, work_id: str) -> tuple[bytes, dict]:
    if not re.fullmatch(r"MHCC[A-Z0-9]{2,20}", work_id):
        raise ValueError("Only isolated MHCC technical module IDs are allowed")
    if (manifest.get("status") != "PRIVATE_TECHNICAL_PREVIEW_ONLY_NOT_EDITORIAL_APPROVAL"
            or manifest.get("semantic_translation_independently_approved") is not False
            or manifest.get("publication_authorized") is not False):
        raise ValueError("Preview manifest is not marked unvalidated/unpublished")
    if (receipt.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL"
            or receipt.get("source_prose_or_original_markup_exported") is not False
            or receipt.get("original_compiled_corpus_sha256") != manifest.get("source_native_corpus_sha256")):
        raise ValueError("Source-native full-corpus receipt is absent or unpinned")
    if (manifest.get("source_module") != "MHCC 0.1.1"
            or manifest.get("source_zip_sha256") != "a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746"
            or manifest.get("source_native_corpus_sha256") != "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"):
        raise ValueError("Unexpected original source version")
    cases = manifest.get("chapters")
    if not isinstance(cases, list) or not (1 <= len(cases) <= 10):
        raise ValueError("Only explicitly named I-only chapters are permitted")
    if {c.get("chapter_osis") for c in cases} != set(receipt.get("intro_only_chapters_needing_editorial_review", [])):
        raise ValueError("I-only chapter set does not match the native source")
    doc = ET.Element(f"{{{NS}}}osis")
    osis_text = ET.SubElement(doc, f"{{{NS}}}osisText", {
        "osisIDWork": work_id, "osisRefWork": "Bible",
        f"{{{XML}}}lang": "en", "canonical": "false"
    })
    header = ET.SubElement(osis_text, f"{{{NS}}}header")
    work = ET.SubElement(header, f"{{{NS}}}work", {"osisWork": work_id})
    ET.SubElement(work, f"{{{NS}}}title").text = "Private unvalidated MHCC chapter-I transport test"
    ET.SubElement(work, f"{{{NS}}}identifier", {"type": "OSIS"}).text = work_id
    ET.SubElement(work, f"{{{NS}}}language", {"type": "IETF"}).text = "en"
    group = ET.SubElement(osis_text, f"{{{NS}}}div", {"type": "bookGroup"})
    seen = set()
    reports = []
    total_paragraphs = 0
    for case in cases:
        chapter = case["chapter_osis"]
        match = _CHAPTER.fullmatch(chapter)
        if not match or chapter in seen:
            raise ValueError("Invalid/duplicate explicitly named I-only chapter")
        seen.add(chapter)
        count = case.get("verse_count")
        if type(count) is not int or not (1 <= count <= 200):
            raise ValueError("Invalid chapter verse registry bound")
        native = receipt["chapters"].get(chapter)
        if (not isinstance(native, dict)
                or native.get("source_placement") != "INTRO_ONLY_NEEDS_INDEPENDENT_REVIEW"
                or native.get("original_native_numbered_keys") != 0
                or native.get("distinct_original_raw_units") != 0
                or native.get("original_units") != []):
            raise ValueError("Refusing to overwrite chapter with any original verse commentary")
        intros = native.get("native_introductions_not_assumed_to_be_exposition")
        if (not isinstance(intros, list) or len(intros) != 1
                or intros[0].get("key") != chapter
                or not _HEX.fullmatch(case.get("intro_raw_sha256", ""))
                or intros[0].get("raw_sha256") != case["intro_raw_sha256"]
                or intros[0].get("visible_word_tokens", 0) < 40
                or intros[0].get("markup", {}).get("strict_xml_fragment") is not True):
            raise ValueError("Original chapter I source ownership/content was not proved")
        tags = intros[0]["markup"].get("tag_counts", {})
        if tags.get("reference", 0) or tags.get("note", 0):
            raise ValueError("Original I has linked references/notes requiring a separate fidelity gate")
        manuscript = root / case.get("manuscript", "")
        if not manuscript.is_file() or not manuscript.resolve().is_relative_to(root.resolve()):
            raise ValueError("Manuscript path is missing/outside the repository")
        modern_title, paragraphs = _read_candidate(manuscript, case, manifest)
        book = ET.SubElement(group, f"{{{NS}}}div", {"type": "book", "osisID": match[1]})
        chapter_node = ET.SubElement(book, f"{{{NS}}}chapter", {"osisID": chapter})
        first = chapter + ".1"
        last = chapter + "." + str(count)
        unit = ET.SubElement(chapter_node, f"{{{NS}}}div", {
            "type": "section", "annotateType": "commentary",
            "annotateRef": first + "-" + last
        })
        if case.get("original_source_heading") is not None:
            ET.SubElement(unit, f"{{{NS}}}title", {
                "type": "sub", "resp": "BibleResourcesSecondaryWitnessNotNativeTitleVerified"
            }).text = case["original_source_heading"]
        ET.SubElement(unit, f"{{{NS}}}title", {
            "type": "sub", "resp": "BibleResourcesModernEditorial"
        }).text = modern_title
        for text in paragraphs:
            para = ET.SubElement(unit, f"{{{NS}}}p")
            _inline(para, text)
        total_paragraphs += len(paragraphs)
        reports.append({
            "chapter": chapter,
            "source_placement": "ORIGINAL_CHAPTER_I_ONLY",
            "source_intro_raw_sha256": case["intro_raw_sha256"],
            "native_source_numbered_entries": 0,
            "expected_compiled_linked_verse_keys": count,
            "one_authorial_exposition_section": True,
            "modern_paragraphs": len(paragraphs),
            "original_native_title_words_independently_collated": False,
            "original_source_prose_meaning_independently_collated": False
        })
    output = ET.tostring(doc, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)
    return output, {
        "status": "PRIVATE_UNVALIDATED_IONLY_SWORD_TRANSPORT_PREVIEW",
        "temporary_module_id": work_id,
        "chapters": reports,
        "original_source_module_modified": False,
        "semantic_translation_independently_approved": False,
        "original_osis_markup_exactly_reconstructed": False,
        "original_native_title_words_independently_collated": False,
        "structured_derivative_readback_tested": False,
        "sword_publication_authorized": False,
        "modern_paragraphs": total_paragraphs
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source-receipt", type=Path, required=True)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--osis", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--temp-module-id", default="MHCCIONLY")
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    receipt = json.loads(args.source_receipt.read_text(encoding="utf-8"))
    result, report = generate(manifest, receipt, args.root, args.temp_module_id)
    args.osis.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.osis.write_bytes(result)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Private I-only OSIS preview prepared: " +
          str(len(report["chapters"])) + " chapters, " +
          str(sum(x["expected_compiled_linked_verse_keys"] for x in report["chapters"])) +
          " requested linked verse keys. No publication or editorial approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
