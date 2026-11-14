#!/usr/bin/env python3
"""Read-only editorial section-scope triage for any pinned RawCom/zCom commentary.

Independently inspect every original stock SWORD entry. Compare an explicitly
numbered *prose heading* with the actual verse slots and their unfiltered raw
payload identities. The first numbered heading is only a heuristic candidate:
no correction, authorial extent, verse loss or source parity is inferred.
All original words and XML remain private in the ephemeral runner.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import re
import subprocess
import tempfile
import zipfile

from lxml import etree

from commentary_intake import load_manifest
from commentary_navigation_link_plan import (
    parse_native_commentary_verse_registry, UnsafeCommentaryLinkPlan
)
from commentary_source_english_osis_alias import (
    read_existing_66_book_english_aliases, _canon_name
)
from commentary_xml_witness import _parse_reference, WORK_REF
from commentary_native_raw_inventory import _safe_stock_install, private_crosscheck
from pilot_fetch import ALLOWED_HOSTS, fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import RawCorpusError, parse_native_raw_corpus

HEADING = re.compile(r"\b(Verses?)\s+(\d{1,3}(?:\s*[-–,]\s*\d{1,3}){0,8})(?!\d)")
KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)\.([1-9]\d*)$")
PROBES = ("Song.1.7", "Jer.4.1", "Jer.4.3")


def heading_extent(raw: bytes) -> tuple[tuple[int, ...], str] | None:
    """Return a tentative single-chapter extent, without editing original text.

    A source heading like 'Verse 7 ,8' is an enumerated, not a one-verse,
    section. Ranges/lists are different shapes; malformed or ambiguous
    combinations deliberately produce no verdict.
    """
    try:
        root = etree.fromstring(
            b"<entry>" + raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
        if any(isinstance(el, etree._Entity) for el in root.iter()):
            return None
    except (ValueError, etree.XMLSyntaxError):
        return None
    prose = "".join(root.itertext())
    # Limit attention to a leading heading, not arbitrary verse citations
    # scattered throughout the commentary.
    match = HEADING.search(prose[:3000])
    if match is None:
        return None
    literal = match.group(2)
    numbers = [int(n) for n in re.findall(r"\d+", literal)]
    if not numbers or min(numbers) == 0 or max(numbers) > 176:
        return None
    punctuation = {ch for ch in literal if ch in ",-–"}
    if not punctuation:
        return ((numbers[0],), "single")
    if "," not in punctuation and punctuation <= {"-", "–"}:
        if len(numbers) != 2 or numbers[0] >= numbers[1]:
            return None
        return (tuple(range(numbers[0], numbers[1] + 1)), "dash")
    if "," in punctuation:
        expanded = []
        has_range = False
        for item in literal.split(","):
            item = item.strip()
            match = re.fullmatch(r"(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", item)
            if match is None:
                return None
            start = int(match.group(1))
            end = int(match.group(2) or start)
            if start > end:
                return None
            has_range |= match.group(2) is not None
            expanded.extend(range(start, end + 1))
        if expanded != sorted(set(expanded)):
            return None
        return (tuple(expanded), "discontinuous" if has_range else "comma")
    return None



def describe_unrecognized_heading(raw: bytes) -> dict:
    """Classify an unexplained *native occupied slot*, never infer lost prose.

    Use only fixed classes, XML element names and counts. Do not emit any
    authorial words, original XML, scripture text or free-form snippets.
    """
    if not raw.strip():
        return {"reason": "EMPTY_RAW_PAYLOAD", "has_title": False}
    if len(raw) > 2 * 1024 * 1024 or b"\x00" in raw:
        return {"reason": "UNSAFE_OR_OVERSIZE_RAW", "has_title": False}
    try:
        root = etree.fromstring(
            b"<entry>" + raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
        if any(isinstance(el, etree._Entity) for el in root.iter()):
            return {"reason": "UNRESOLVED_XML_ENTITY", "has_title": False}
    except (ValueError, etree.XMLSyntaxError):
        return {"reason": "INVALID_XML_FRAGMENT", "has_title": False}
    visible = "".join(root.itertext())
    titles = [
        n for n in root.iter()
        if isinstance(n.tag, str)
        and n.tag.rsplit("}", 1)[-1] in {"title", "h1", "h2", "h3", "h4", "h5", "h6"}
    ]
    if not visible.strip():
        reason = "NO_VISIBLE_PROSE"
    elif HEADING.search(visible[:3000]):
        # The heading is legible but rejected for an invalid/ambiguous span.
        reason = "UNSUPPORTED_NUMBERED_SPAN"
    elif HEADING.search(visible[3000:]):
        reason = "NUMBERED_HEADING_AFTER_SCAN_LIMIT"
    elif re.search(r"\bVerses?\b", visible, re.IGNORECASE):
        reason = "UNPARSED_VERSE_LABEL"
    elif titles:
        reason = "NON_NUMERIC_XML_TITLE"
    else:
        reason = "UNLABELLED_VISIBLE_PROSE"
    return {
        "reason": reason,
        "has_title": bool(titles),
        "title_node_count": len(titles),
        "visible_nonempty": bool(visible.strip()),
        "raw_bytes": len(raw),
    }


def audit_unrecognized_slots(records: dict[str, dict]) -> dict:
    """Classify each row once and detect duplicates without guessing ranges."""
    from collections import defaultdict
    hash_refs = defaultdict(list)
    chapter_refs = defaultdict(list)
    for ref, row in records.items():
        hash_refs[row["sha256"]].append(ref)
        match = KEY.fullmatch(ref)
        if match is not None:
            chapter_refs[(match.group(1), int(match.group(2)))].append(
                (int(match.group(3)), ref)
            )
    for chapter in chapter_refs.values():
        chapter.sort()
    categories = Counter()
    books = defaultdict(Counter)
    rows = []
    for ref, item in records.items():
        if item.get("heading") is not None:
            continue
        profile = item.get("unrecognized_profile")
        if profile is None:
            raise PilotError("Original unrecognized stock payload was not profiled")
        linked_refs = hash_refs[item["sha256"]]
        key = KEY.fullmatch(ref)
        if key is None:
            raise PilotError("Unrecognized slot is not a canonical numbered VerseKey")
        chapter = chapter_refs[(key.group(1), int(key.group(2)))]
        chapter_digests = {records[k]["sha256"] for _, k in chapter}
        shared_with_recognized = [
            key for key in linked_refs
            if records[key].get("heading") is not None
        ]
        result = {
            "native_key": ref,
            "category": profile["reason"],
            "raw_payload_sha256": item["sha256"],
            "same_raw_payload_slot_count": len(linked_refs),
            "same_payload_with_recognized_heading": bool(shared_with_recognized),
            "same_payload_with_unrecognized_heading": len(linked_refs) > 1,
            "first_verse_in_chapter": int(key.group(3)) == 1,
            "number_of_occupied_native_slots_in_chapter": len(chapter),
            "number_of_distinct_native_payloads_in_chapter": len(chapter_digests),
            "highest_occupied_native_verse_in_chapter": chapter[-1][0],
            "source_chapter_verse_count_verified": False,
            "xml_title_present": profile["has_title"],
            "visible_nonempty": profile.get("visible_nonempty", False),
        }
        rows.append(result)
        categories[profile["reason"]] += 1
        books[ref.split(".", 1)[0]][profile["reason"]] += 1
    return {
        "total": len(rows),
        "reason_counts": dict(sorted(categories.items())),
        "reason_counts_by_book": {
            book: dict(sorted(classes.items())) for book, classes in sorted(books.items())
        },
        "shares_content_with_recognized_heading": sum(
            row["same_payload_with_recognized_heading"] for row in rows
        ),
        "first_verse_entries": sum(row["first_verse_in_chapter"] for row in rows),
        "single_occupied_slot_chapters_among_unknown": sum(
            row["first_verse_in_chapter"]
            and row["number_of_occupied_native_slots_in_chapter"] == 1
            for row in rows
        ),
        "distinct_native_raw_payload_hashes": len({row["raw_payload_sha256"] for row in rows}),
        "case_rows": rows,
        "unrecognized_means_missing_text_proven": False,
        "all_output_is_original_text_free_metadata": True,
    }


def classify(records: dict[str, dict]) -> dict:
    """Compare declared start-anchored headings with real occupied key payloads.

    Presence is not authoritative correspondence: a missing slot, a linked
    duplicate payload, and a different payload are separate observations.
    """
    counts = Counter()
    by_book = defaultdict(Counter)
    anomalies = []
    probes = {}
    sections = []
    for ref, entry in records.items():
        match = KEY.fullmatch(ref)
        if match is None:
            continue
        book, chapter, verse = match.groups()
        chapter, verse = int(chapter), int(verse)
        scope = entry.get("heading")
        if scope is None:
            counts["no_recognized_heading"] += 1
            by_book[book]["no_recognized_heading"] += 1
            continue
        span, style = scope
        counts["recognized_heading_rows"] += 1
        by_book[book]["recognized_heading_rows"] += 1
        if span[0] != verse:
            counts["non_start_verse_rows"] += 1
            by_book[book]["non_start_verse_rows"] += 1
            continue
        sections.append({"start": ref, "declared_end": span[-1],
                         "heading_kind": style})
        counts["start_anchored_sections"] += 1
        counts["start_sections_" + style] += 1
        by_book[book]["start_anchored_sections"] += 1
        by_book[book]["start_sections_" + style] += 1
        missing, same, different = [], [], []
        for target in span[1:]:
            next_ref = f"{book}.{chapter}.{target}"
            other = records.get(next_ref)
            if other is None:
                missing.append(next_ref)
            elif other["sha256"] == entry["sha256"]:
                same.append(next_ref)
            else:
                different.append(next_ref)
        if missing or different:
            category = (
                "missing_and_distinct_within_declared_section"
                if missing and different else
                "missing_slots_within_declared_section"
                if missing else "distinct_payload_within_declared_section"
            )
            counts[category] += 1
            by_book[book][category] += 1
            anomalies.append({
                "start": ref, "heading_kind": style,
                "declared_end": span[-1], "declared_verse_count": len(span),
                "missing_slots": missing, "same_payload_slots": same,
                "different_payload_slots": different,
                "classification": "SUSPECTED_NOT_EDITORIALLY_CONFIRMED",
                "category": category
            })
        else:
            counts["all_declared_slots_same_raw_payload"] += 1
            by_book[book]["all_declared_slots_same_raw_payload"] += 1
        if ref in PROBES:
            probes[ref] = {
                "heading_kind": style, "declared_verses": list(span),
                "missing_slots": missing, "same_payload_slots": same,
                "different_payload_slots": different,
                "raw_payload_sha256": entry["sha256"],
            }
    return {
        "counts": dict(sorted(counts.items())),
        "by_book": {k: dict(sorted(v.items())) for k, v in sorted(by_book.items())},
        "anomalies": anomalies, "probes": probes,
        "start_anchored_section_map": sections
    }




def independent_chapter_scope_evidence(document, unrecognized_cases: list[dict]) -> dict:
    """Classify genuine chapter-level source anchors in their div2 context.

    A chapter scripCom annotation is NOT by itself proof of an undivided
    chapter comment. The same div2 may contain other verse/range sections;
    report that separately, and never infer absent verse keys or copy prose.
    """
    source_by_chapter = defaultdict(list)
    source_marker_counts = Counter()
    for node in document.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        original_ref = node.get("osisRef", "")
        kind, _ = _parse_reference(original_ref)
        if kind != "work_qualified_chapter":
            continue
        m = WORK_REF.fullmatch(original_ref)
        if m is None or not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", m.group(2)):
            continue
        chapter = m.group(2)
        source_marker_counts["complete_chapter_marker_occurrences"] += 1
        parent = node.getparent()
        while parent is not None and (
            not isinstance(parent.tag, str) or
            parent.tag.rsplit("}", 1)[-1] != "div2"
        ):
            parent = parent.getparent()
        if parent is None:
            source_by_chapter[chapter].append({
                "shape": "CHAPTER_MARKER_OUTSIDE_DIV2",
                "verse_markers": -1,
                "paragraphs": 0,
                "nonempty_div2": False,
                "after_marker_tag": "_NOT_IN_CHAPTER"
            })
            continue
        verse_markers = sum(
            isinstance(child.tag, str)
            and child.tag.rsplit("}", 1)[-1] == "scripCom"
            and _parse_reference(child.get("osisRef", ""))[0] in (
                "work_qualified_verse",
                "work_qualified_same_book_verse_range"
            )
            for child in parent.iter()
        )
        paragraph_nodes = [
            child for child in parent.iter()
            if isinstance(child.tag, str) and child.tag.rsplit("}", 1)[-1] == "p"
        ]
        next_sibling = node.getnext()
        next_tag = (next_sibling.tag.rsplit("}", 1)[-1]
                    if next_sibling is not None and isinstance(next_sibling.tag, str)
                    else "_END")
        source_by_chapter[chapter].append({
            "shape": ("CHAPTER_MARKER_WITH_SEPARATE_VERSE_SECTIONS"
                      if verse_markers else "CHAPTER_MARKER_WITHOUT_VERSE_SECTIONS"),
            "verse_markers": verse_markers,
            "paragraphs": len(paragraph_nodes),
            "nonempty_div2": bool("".join(parent.itertext()).strip()),
            "after_marker_tag": next_tag,
        })
    rows = []
    classes = Counter()
    grouped_by_book = defaultdict(Counter)
    candidates = [
        row for row in (unrecognized_cases or [])
        if row.get("first_verse_in_chapter", False)
        and row.get("number_of_occupied_native_slots_in_chapter") == 1
    ]
    seen = set()
    for row in candidates:
        ref = row["native_key"]
        if ref in seen:
            raise PilotError("Duplicate candidate whole-chapter native key")
        seen.add(ref)
        chapter = ref.rsplit(".", 1)[0]
        annotations = source_by_chapter.get(chapter, [])
        if not annotations:
            cls = "NO_MATCHING_CHAPTER_ANNOTATION_IN_OTHER_EDITION"
        elif len(annotations) != 1:
            cls = "MULTIPLE_CHAPTER_ANNOTATIONS_REQUIRE_EDITORIAL_REVIEW"
        elif annotations[0]["shape"] == "CHAPTER_MARKER_WITHOUT_VERSE_SECTIONS" and (
            annotations[0]["paragraphs"] > 0 and annotations[0]["nonempty_div2"]
        ):
            cls = "INDEPENDENT_UNDIVIDED_CHAPTER_SCOPE_CANDIDATE"
        else:
            cls = "CHAPTER_ANNOTATION_WITH_SECTIONS_OR_UNREVIEWED_SHAPE"
        classes[cls] += 1
        grouped_by_book[chapter.split(".", 1)[0]][cls] += 1
        rows.append({
            "native_start": ref,
            "candidate_chapter": chapter,
            "witness_class": cls,
            "matching_source_chapter_markers": len(annotations),
            "witness_marker_shapes": [i["shape"] for i in annotations],
            "witness_verse_marker_count": sum(max(i["verse_markers"], 0) for i in annotations),
            "witness_nonempty_paragraphs": sum(i["paragraphs"] for i in annotations),
            "source_reference_strings_rewritten": False,
            "authorial_chapter_scope_approved": False,
        })
    return {
        "stock_single_occupied_slot_chapter_candidates": len(candidates),
        "independent_source_chapter_marker_inventory": dict(sorted(source_marker_counts.items())),
        "source_scope_candidate_classes": dict(sorted(classes.items())),
        "source_scope_candidates_by_book": {
            book: dict(sorted(counts.items())) for book, counts in sorted(grouped_by_book.items())
        },
        "case_rows": rows,
        "source_digital_edition_equivalence_unverified": True,
        "per_verse_navigation_approved": False
    }



def independent_div2_chapter_body_evidence(document, native_registry: dict,
                                          unrecognized_cases: list[dict]) -> dict:
    """Collate chapter wrappers in canonical order, verifying book identities.

    Source order alone is never authority: each div1 must be the expected book
    with independently checked chapter count, a non-conflicting source book
    title and/or explicit source section annotations. Unmarked div2 paragraphs
    are evidence for a *chapter-unit candidate*, not automatically approval
    to assign its whole body to each verse in the stock digital edition.
    """
    chapter_maximums = native_registry["chapter_maximums"]
    native_by_book = defaultdict(list)
    for chapter_key in chapter_maximums:
        book, chapter_str = chapter_key.rsplit(".", 1)
        native_by_book[book].append(int(chapter_str))
    if any(chapters != list(range(1, len(chapters) + 1))
           for chapters in native_by_book.values()):
        raise PilotError("Actual native registry has discontinuous chapter enumeration")
    canonical_books = list(native_by_book)
    chapters_div1 = []
    for node in document.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "div1":
            continue
        chapters = [x for x in node if
                    isinstance(x.tag, str) and x.tag.rsplit("}", 1)[-1] == "div2"]
        if chapters:
            chapters_div1.append((node, chapters))
    if len(chapters_div1) != len(canonical_books):
        return {
            "status": "SOURCE_BOOK_LAYOUT_NOT_EXACT_NATIVE_BOOK_COUNT",
            "native_book_count": len(canonical_books),
            "source_book_divisions": len(chapters_div1),
            "case_rows": [], "scope_authorized": False
        }
    aliases, alias_registry_meta = read_existing_66_book_english_aliases()
    if not set(canonical_books).issubset(aliases):
        return {
            "status": "SOURCE_BOOK_ALIASES_NOT_REVIEWED_FOR_NATIVE_MODULE",
            "case_rows": [], "scope_authorized": False
        }
    source_chapters = {}
    book_classes = Counter()
    for (div1, chapters), code in zip(chapters_div1, canonical_books):
        title = _canon_name(div1.get("title", ""))
        candidates = set()
        for book, alias in aliases.items():
            needle = _canon_name(alias)
            if re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", title):
                candidates.add(book)
        annotated_books = set()
        for marker in div1.iter():
            if not isinstance(marker.tag, str) or marker.tag.rsplit("}", 1)[-1] != "scripCom":
                continue
            kind, book = _parse_reference(marker.get("osisRef", ""))
            if book and kind in (
                "work_qualified_chapter", "work_qualified_verse",
                "work_qualified_same_book_verse_range"
            ):
                annotated_books.add(book)
        if len(candidates) > 1 or (candidates and code not in candidates):
            identity = "SOURCE_BOOK_TITLE_CONFLICT_OR_AMBIGUOUS"
        elif annotated_books and annotated_books != {code}:
            identity = "SOURCE_BOOK_ANNOTATION_CONFLICT"
        elif code in candidates and code in annotated_books:
            identity = "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH"
        elif code in candidates:
            identity = "SOURCE_BOOK_TITLE_MATCH"
        elif annotated_books == {code}:
            identity = "SOURCE_BOOK_MARKERS_MATCH"
        else:
            identity = "SOURCE_BOOK_IDENTITY_ORDINAL_ONLY_UNREVIEWED"
        if len(chapters) != len(native_by_book[code]):
            identity = "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
        book_classes[identity] += 1
        for chapter_number, div2 in enumerate(chapters, start=1):
            chapter = f"{code}.{chapter_number}"
            markers = [
                marker for marker in div2.iter()
                if isinstance(marker.tag, str)
                and marker.tag.rsplit("}", 1)[-1] == "scripCom"
            ]
            numbered = [
                marker for marker in markers
                if _parse_reference(marker.get("osisRef", ""))[0] in (
                    "work_qualified_verse", "work_qualified_same_book_verse_range"
                )
            ]
            chapter_markers = [
                marker for marker in markers
                if _parse_reference(marker.get("osisRef", ""))[0]
                == "work_qualified_chapter"
            ]
            nonempty_paragraphs = sum(
                bool("".join(node.itertext()).strip())
                for node in div2.iter()
                if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "p"
            )
            source_chapters[chapter] = {
                "book_identity_class": identity,
                "source_marker_count": len(markers),
                "source_numbered_section_marker_count": len(numbered),
                "source_chapter_marker_count": len(chapter_markers),
                "source_nonempty_paragraph_count": nonempty_paragraphs,
                "source_div2_text_sha256": sha256(
                    "".join(div2.itertext()).encode("utf-8")
                ).hexdigest(),
                "source_div2_original_text_retained": True,
            }
    cases = []
    classes = Counter()
    candidates = [
        row for row in unrecognized_cases
        if row.get("first_verse_in_chapter", False)
        and row.get("number_of_occupied_native_slots_in_chapter") == 1
    ]
    for row in candidates:
        chapter = row["native_key"].rsplit(".", 1)[0]
        source = source_chapters.get(chapter)
        if source is None:
            classification = "NO_CORRESPONDING_SOURCE_DIV2"
        elif source["book_identity_class"] not in {
            "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH",
            "SOURCE_BOOK_TITLE_MATCH",
            "SOURCE_BOOK_MARKERS_MATCH"
        }:
            classification = "SOURCE_BOOK_OR_CHAPTER_ALIGNMENT_NEEDS_REVIEW"
        elif source["source_numbered_section_marker_count"] > 0:
            classification = "SOURCE_DIV2_HAS_INDEPENDENT_VERSE_SECTIONS"
        elif source["source_nonempty_paragraph_count"] == 0:
            classification = "SOURCE_DIV2_NO_NONEMPTY_COMMENTARY_PARAGRAPHS"
        else:
            classification = "SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE"
        classes[classification] += 1
        cases.append({
            "native_start": row["native_key"],
            "source_div2_structure_class": classification,
            "source_chapter_marker_count": source["source_chapter_marker_count"] if source else 0,
            "source_numbered_marker_count": source["source_numbered_section_marker_count"] if source else 0,
            "source_nonempty_paragraph_count": source["source_nonempty_paragraph_count"] if source else 0,
            "source_div2_text_sha256": source["source_div2_text_sha256"] if source else None,
            "stock_raw_sha256": row["raw_payload_sha256"],
            "source_text_to_stock_text_identity_proven": False,
            "approved_for_native_index_expansion": False,
        })
    return {
        "status": "SOURCE_DIV2_STRUCTURE_COLLATED_NO_REINDEX_AUTHORIZATION",
        "source_book_divisions": len(chapters_div1),
        "native_book_count": len(canonical_books),
        "book_alignment_evidence_classes": dict(sorted(book_classes.items())),
        "reviewed_registry_evidence": alias_registry_meta,
        "candidate_classes": dict(sorted(classes.items())),
        "case_rows": cases,
        "derived_authorial_section_scope_proven": False,
        "original_xml_or_stock_modified": False
    }


def compare_independent_thml_witness(manifest: dict, sections: list[dict],
                                     anomalies: list[dict], temp: Path,
                                     unrecognized_cases: list[dict] | None = None,
                                     native_registry: dict | None = None) -> dict:
    """Compare all start/end section locations with a separately pinned ThML.

    Different digital editions are never automatically assumed identical;
    this is corroborating metadata, not an instruction to rewrite stock.
    """
    config = manifest.get("commentary_source", {})
    url = config.get("xml_witness_url")
    expected = config.get("xml_witness_sha256")
    if not url or not re.fullmatch(r"[0-9a-f]{64}", expected or ""):
        return {"status": "NO_PINNED_THML_WITNESS", "proven_stock_faults": 0}
    parts = urlsplit(url)
    approved_providers = sorted(
        provider for provider, hosts in ALLOWED_HOSTS.items()
        if parts.hostname in hosts
    )
    if (parts.scheme != "https" or not url.endswith(".xml")
            or not approved_providers or parts.username or parts.password
            or parts.port not in (None, 443) or parts.fragment):
        raise PilotError("Independent ThML witness URL is not in the approved source registry")
    witness_path = temp / "independent-witness.xml"
    receipt = fetch(url, witness_path, approved_providers[0])
    if receipt["sha256"] != expected or receipt["bytes"] > 32 * 1024 * 1024:
        raise PilotError("Independent ThML witness hash or bound mismatch")
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
        recover=False, huge_tree=False, remove_blank_text=False)
    try:
        document = etree.parse(str(witness_path), parser)
    except (etree.XMLSyntaxError, ValueError):
        raise PilotError("Pinned independent ThML is not safely parseable") from None
    markers = defaultdict(set)
    observed = 0
    unresolved_near_candidates = defaultdict(list)
    suspect_starts = {row["start"] for row in anomalies}
    for node in document.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        original_ref = node.get("osisRef", "")
        kind, _ = _parse_reference(original_ref)
        if kind not in ("work_qualified_verse", "work_qualified_same_book_verse_range"):
            for start in suspect_starts:
                if re.search(re.escape(start) + r"(?![0-9])", original_ref):
                    if len(original_ref) <= 256:
                        unresolved_near_candidates[start].append({
                            "source_reference_attribute": original_ref,
                            "strict_parser_class": kind
                        })
            continue
        match = WORK_REF.fullmatch(original_ref)
        if match is None:
            continue
        body = match.group(2)
        first, last = body.split("-", 1) if "-" in body else (body, body)
        if not KEY.fullmatch(first) or not KEY.fullmatch(last):
            continue
        if first.split(".")[:2] != last.split(".")[:2]:
            continue
        markers[first].add(last)
        observed += 1

    # Source XML can encode a passage in a non-scripCom attribute or as
    # editorial prose. Record only short location attributes for diagnosis.
    nearby_attributes = defaultdict(list)
    independent_reference_ranges = defaultdict(set)
    for node in document.iter():
        if not isinstance(node.tag, str):
            continue
        if node.tag.rsplit("}", 1)[-1] == "scripRef":
            ref = node.get("osisRef", "")
            kind, _ = _parse_reference(ref)
            if kind in ("work_qualified_verse", "work_qualified_same_book_verse_range"):
                parsed = WORK_REF.fullmatch(ref)
                if parsed is not None:
                    body = parsed.group(2)
                    first, last = body.split("-", 1) if "-" in body else (body, body)
                    if KEY.fullmatch(first) and KEY.fullmatch(last):
                        if first.split(".")[:2] == last.split(".")[:2]:
                            independent_reference_ranges[first].add(last)
        for attr, value in node.attrib.items():
            if len(value) > 256:
                continue
            for start in suspect_starts:
                if re.search(re.escape(start) + r"(?![0-9])", value):
                    if len(nearby_attributes[start]) < 8:
                        nearby_attributes[start].append({
                            "xml_tag": node.tag.rsplit("}", 1)[-1],
                            "attribute_name": attr.rsplit("}", 1)[-1],
                            "attribute_value": value
                        })
    def relation(section: dict) -> str:
        first = section["start"]
        last = first.rsplit(".", 1)[0] + "." + str(section["declared_end"])
        endpoints = markers.get(first)
        if not endpoints:
            return "NO_MATCHING_INDEPENDENT_START"
        if last in endpoints:
            return "SAME_DECLARED_RANGE_IN_INDEPENDENT_EDITION"
        return "DIFFERENT_RANGE_IN_INDEPENDENT_EDITION"

    counts = Counter(relation(s) for s in sections)
    reference_counts = Counter()
    independent_evidence_matrix = Counter()
    no_independent_range_evidence = []
    for s in sections:
        last = s["start"].rsplit(".", 1)[0] + "." + str(s["declared_end"])
        has_scripref = last in independent_reference_ranges.get(s["start"], set())
        has_scripcom = relation(s) == "SAME_DECLARED_RANGE_IN_INDEPENDENT_EDITION"
        reference_counts[
            "EXACT_INDEPENDENT_SCRIPREF_RANGE" if has_scripref
            else "NO_EXACT_INDEPENDENT_SCRIPREF_RANGE"
        ] += 1
        independent_evidence_matrix[
            ("scripCom" if has_scripcom else "no_scripCom") + "_and_" +
            ("scripRef" if has_scripref else "no_scripRef")
        ] += 1
        if not has_scripcom and not has_scripref:
            no_independent_range_evidence.append(s)
    # These rows have no machine-recognized verse-range heading in stock.
    # Inspect their independent *source annotation anchors* without deriving
    # any new stock index or treating verse citations as section extents.
    unrecognized_source_rows = []
    unrecognized_source_classes = Counter()
    processed_digests = set()
    for row in (unrecognized_cases or []):
        digest = row["raw_payload_sha256"]
        if digest in processed_digests:
            continue
        processed_digests.add(digest)
        ref = row["native_key"]
        native = KEY.fullmatch(ref)
        if native is None:
            raise PilotError("Noncanonical unknown numbered SWORD slot in source review")
        same_book_chapter = lambda s: (
            KEY.fullmatch(s) is not None
            and s.split(".")[:2] == ref.split(".")[:2]
        )
        com_ends = sorted(
            (end for end in markers.get(ref, set()) if same_book_chapter(end)),
            key=lambda end: int(end.split(".")[-1])
        )
        citation_ends = sorted(
            (end for end in independent_reference_ranges.get(ref, set())
             if same_book_chapter(end)),
            key=lambda end: int(end.split(".")[-1])
        )
        source_multi = any(int(end.split(".")[-1]) > int(native.group(3))
                           for end in com_ends)
        cls = (
            "SOURCE_EXPLICIT_MULTI_VERSE_SECTION" if source_multi
            else "SOURCE_SINGLE_START_OR_NO_EXPLICIT_MULTI_VERSE_SECTION"
        )
        unrecognized_source_classes[cls] += 1
        unrecognized_source_rows.append({
            "native_start": ref,
            "source_section_endpoints": com_ends,
            "source_citation_endpoints_not_sections": citation_ends,
            "source_explicit_multiverse_annotation": source_multi,
            "only_one_native_occupied_verse_in_chapter":
                row["number_of_occupied_native_slots_in_chapter"] == 1,
            "classification": "CROSS_EDITION_METADATA_ONLY_NOT_A_CORRECTION",
        })

    chapter_scopes = independent_chapter_scope_evidence(document, unrecognized_cases or [])
    div2_scopes = (
        independent_div2_chapter_body_evidence(
            document, native_registry, unrecognized_cases or []
        ) if native_registry is not None else {
            "status": "NO_NATIVE_REGISTRY_PROVIDED",
            "case_rows": [], "derived_authorial_section_scope_proven": False
        }
    )
    return {
        "status": "PINNED_DIFFERENT_DIGITAL_EDITION_SCOPE_COMPARISON",
        "independent_whole_chapter_review": chapter_scopes,
        "independent_div2_chapter_body_review": div2_scopes,
        "witness_sha256": expected,
        "source_marker_rows_observed": observed,
        "unrecognized_source_annotation_classes": dict(
            sorted(unrecognized_source_classes.items())
        ),
        "unrecognized_distinct_payload_source_rows": unrecognized_source_rows,
        "source_distinct_starts": len(markers),
        "stock_start_sections_compared": len(sections),
        "source_range_agreement_counts": dict(sorted(counts.items())),
        "independent_scripref_range_agreement_counts": dict(sorted(reference_counts.items())),
        "independent_reference_evidence_matrix": dict(sorted(independent_evidence_matrix.items())),
        "no_exact_independent_reference_evidence_sections": no_independent_range_evidence,
        "independent_scripref_is_not_section_anchor": True,
        "anomaly_source_range_corroboration": [
            {"start": a["start"], "declared_end": a["declared_end"],
             "relation": relation(a),
             "same_end_in_independent_scripref": (
                 a["start"].rsplit(".", 1)[0] + "." + str(a["declared_end"])
                 in independent_reference_ranges.get(a["start"], set())
             )} for a in anomalies
        ],
        "unparsed_source_reference_candidates_near_anomalies": {
            start: values for start, values in sorted(unresolved_near_candidates.items())
        },
        "source_attributes_near_anomalies": {
            start: values for start, values in sorted(nearby_attributes.items())
        },
        "ccel_edition_equivalence_to_stock_proven": False,
        "editorial_correctness_proven": False,
        "text_or_reference_edited": False
    }


def audit(resource_id: str, index_binary: Path, raw_binary: Path) -> dict:
    """Use exact SHA-pinned official stock, existing independently proved readers."""
    manifest = load_manifest(resource_id)
    for p in (index_binary, raw_binary):
        if not p.is_file() or p.is_symlink():
            raise PilotError("Trusted native SWORD inspector binary unavailable")
    with tempfile.TemporaryDirectory(prefix="commentary-section-audit-") as tmp:
        directory = Path(tmp)
        zip_path = directory / "original.zip"
        downloaded = fetch(manifest["sword_zip_url"], zip_path, manifest["provider"])
        if downloaded["sha256"] != manifest["archive_sha256"]:
            raise PilotError("Pinned original commentary ZIP SHA mismatch")
        archive = inspect_archive(
            zip_path, source_kind="sword",
            expected_module_id=manifest["module_id"],
            expected_category="commentary"
        )
        conf = archive["sword_conf"]
        if conf["version"] != manifest["version"]:
            raise PilotError("Unexpected original commentary version")
        installed = directory / "installed"
        _safe_stock_install(zip_path, archive["members"], installed)
        env = dict(os.environ, SWORD_PATH=str(installed))
        independent = subprocess.run(
            [str(index_binary), manifest["module_id"]],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=env, timeout=75, check=False
        )
        if independent.returncode or len(independent.stdout) > 12 * 1024 * 1024:
            raise PilotError("Independent stock SWORD index read failed")
        registry_run = subprocess.run(
            [str(index_binary), manifest["module_id"], "--chapter-registry"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=env, timeout=75, check=False
        )
        if registry_run.returncode or len(registry_run.stdout) > 256 * 1024:
            raise PilotError("Independent native versification chapter registry unavailable")
        try:
            registry = parse_native_commentary_verse_registry(
                registry_run.stdout, manifest["module_id"]
            )
        except UnsafeCommentaryLinkPlan:
            raise PilotError("Native versification registry invalid") from None
        original_header = independent.stdout.splitlines()[0].split(b"\t")
        if (len(original_header) != 5
                or original_header[0] != b"M"
                or original_header[1].decode("ascii") != manifest["module_id"]
                or original_header[2].decode("ascii") != registry["versification"]
                or original_header[3].decode("ascii") != registry["engine_version"]
                or original_header[4].decode("ascii") != registry["driver"]):
            raise PilotError("Independent native index and registry module identity differ")
        rows = []
        records = {}
        unparsed = 0
        process = None
        try:
            process = subprocess.Popen(
                ["timeout", "360s", str(raw_binary), manifest["module_id"]],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env
            )
            if process.stdout is None:
                raise PilotError("No private native raw stream")
            def on_entry(kind: str, ref: str, raw: bytes) -> None:
                nonlocal unparsed
                rows.append((kind, ref))
                if kind != "K":
                    return
                heading = heading_extent(raw)
                if heading is None and raw.strip():
                    unparsed += 1
                records[ref] = {
                    "sha256": sha256(raw).hexdigest(),
                    "heading": heading,
                    "unrecognized_profile": (
                        describe_unrecognized_heading(raw) if heading is None else None
                    ),
                }
            summary, keys, intros, top = parse_native_raw_corpus(
                process.stdout, on_entry=on_entry
            )
            process.stdout.close()
            if process.wait(timeout=15) != 0:
                raise PilotError("Private native SWORD raw scan failed")
        except BaseException:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            raise
        proof = private_crosscheck(
            independent.stdout, manifest["module_id"], rows, summary
        )
        expected_raw = manifest.get("native_raw_corpus_sha256")
        actual_raw = summary["all_native_raw_entries_ordered_sha256"]
        if not expected_raw or expected_raw != actual_raw:
            raise PilotError("Original full native corpus hash drift")
        if set(records) - registry["verse_keys"]:
            raise PilotError("Stock native occupied key escaped independent versification registry")
        result = classify(records)
        unknown = audit_unrecognized_slots(records)
        if unknown["total"] != result["counts"]["no_recognized_heading"]:
            raise PilotError("Unrecognized heading count diverged from complete native inventory")
        witness = compare_independent_thml_witness(
            manifest, result["start_anchored_section_map"],
            result["anomalies"], directory, unknown["case_rows"], registry)
        # A native single-key chapter plus an independently corroborated
        # source division still needs explicit editorial signoff. These are
        # chapter-limit *measurements*, not link insertion instructions.
        chapter_sizing = []
        for row in witness["independent_whole_chapter_review"]["case_rows"]:
            chapter = row["candidate_chapter"]
            maximum = registry["chapter_maximums"].get(chapter)
            if maximum is None or maximum < 1:
                raise PilotError("Source chapter candidate absent from actual SWORD versification")
            chapter_sizing.append({
                "chapter": chapter,
                "native_verse_max": maximum,
                "potential_new_navigation_keys_not_editorially_approved": maximum - 1,
                "independent_source_class": row["witness_class"],
            })
        return {
            "schema_version": 1,
            "status": "COMPLETE_NATIVE_SCAN_EDITORIAL_TRIAGE_NOT_APPROVAL",
            "resource_id": resource_id, "original_zip_sha256": downloaded["sha256"],
            "original_native_raw_sha256": actual_raw,
            "native_versification_registry": {
                "name": registry["versification"],
                "libSWORD_version": registry["engine_version"],
                "canonical_chapters": registry["chapter_count"],
                "canonical_verse_keys": registry["canonical_verse_count"],
                "original_occupied_numbered_keys_within_registry": True,
                "candidate_single_key_chapter_sizing": chapter_sizing,
                "candidate_new_navigation_keys_if_all_chapters_approved": sum(
                    row["potential_new_navigation_keys_not_editorially_approved"]
                    for row in chapter_sizing
                ),
                "navigation_changes_approved": False,
            },
            "native_numbered_rows": len(keys),
            "native_intro_rows": len(intros), "native_top_rows": len(top),
            "native_full_key_crosscheck": proof["exact_all_occupied_stock_keys_read_and_crosschecked"],
            "native_rows_with_unrecognized_heading_or_xml": unparsed,
            **result,
            "unrecognized_native_slot_review": unknown,
            "independent_thml_witness": witness,
            "section_heading_matching_is_heuristic": True,
            "independent_edition_range_comparison_completed": witness["status"].startswith("PINNED"),
            "source_prose_or_bible_text_missing_proven": False,
            "original_text_logged_or_published": False,
            "original_sword_changed": False
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--native-index-binary", type=Path, required=True)
    parser.add_argument("--native-raw-binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.resource_id, args.native_index_binary, args.native_raw_binary)
        code = 0
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, RawCorpusError) as exc:
        result = {
            "status": "BLOCKED", "reason_class": type(exc).__name__,
            "native_scan_completed": False, "original_sword_changed": False
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Commentary editorial section triage:", result["status"],
          "(metadata-only report; original text never logged)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
