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
from commentary_osis_rebuild_preflight import (
    NativeOSISRebuildPreflight, compare_opaque_top_with_standard_compiler_fixture,
)
from commentary_osis_transport_probe import (
    isolated_osis2mod_original_sample_roundtrip, _source_visible_text,
)
from commentary_osis_mixed_transport_probe import (
    probe_original_mixed_transport, probe_complete_original_transport,
    privately_stage_versioned_zcom_zip,
)
from commentary_osis_intro_transport_probe import probe_original_intro_transport
from commentary_intro_chapter_text_review import (
    review_original_intro_against_numbered_chapter,
    independent_thml_chapter_intro_witness,
)
from commentary_navigation_link_plan import (
    parse_native_commentary_verse_registry, UnsafeCommentaryLinkPlan,
    triage_missing_native_section_links,
    triage_single_key_chapter_navigation,
    verify_original_native_adjacent_section_boundaries,
    corroborate_reviewed_commentary_link_plan,
)
from commentary_source_english_osis_alias import (
    read_existing_66_book_english_aliases, _canon_name
)
from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_stock_prefix_topology import (
    source_word_prefix_topology, stock_prefixed_source_body_concordance,
    single_word_stock_markup_diagnostic, stock_prefix_context_correspondence,
)
from commentary_chapter_ref_labels import link_label_location
from commentary_editorial_topology import NativeCommentaryEditorialTopology
from commentary_layout_census import NativeCommentaryLayoutCensus
from commentary_paragraph_witness_probe import compare_paragraph_witness
from commentary_reference_registry_triage import OriginalCommentaryReferenceRegistryTriage
from commentary_literal_erratum_preflight import (
    preview_exact_reversible_commentary_reference_erratum,
    preview_exact_reversible_commentary_prose_erratum,
)
from commentary_source_erratum_compiled_probe import probe_private_compiled_source_erratum
from commentary_unresolved_lexical_triage import marked_word_token_indices
from commentary_xml_witness import _parse_reference, WORK_REF
from commentary_native_raw_inventory import _safe_stock_install, private_crosscheck
from pilot_fetch import ALLOWED_HOSTS, fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import RawCorpusError, parse_native_raw_corpus

HEADING = re.compile(r"\b(Verses?)\s+(\d{1,3}(?:\s*[-–,]\s*\d{1,3}){0,8})(?!\d)")
KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)\.([1-9]\d*)$")
PROBES = ("Song.1.7", "Jer.4.1", "Jer.4.3")


def independent_lexical_overlap(source_text: str, stock_raw: bytes,
                                source_neighbor_candidates: list[tuple[str, str]] | None = None) -> dict:
    """Compare word-multiset overlap in memory, emitting NO original words.

    This is diagnostic cross-edition evidence, not exact text parity:
    punctuation, sequence, markup, source edition and omitted prose must be
    audited independently before authorising a derivative.
    """
    if (not isinstance(source_text, str) or not isinstance(stock_raw, bytes)
            or len(source_text) > 2 * 1024 * 1024
            or len(stock_raw) > 2 * 1024 * 1024 or b"\x00" in stock_raw):
        return {"status": "UNREVIEWED_OR_OVERSIZE", "source_text_equal": False}
    try:
        fragment = etree.fromstring(
            b"<entry>" + stock_raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
        if any(isinstance(n, etree._Entity) for n in fragment.iter()):
            return {"status": "UNRESOLVED_XML_ENTITY", "source_text_equal": False}
        stock_text = "".join(fragment.itertext())
    except (ValueError, etree.XMLSyntaxError):
        return {"status": "UNPARSEABLE_ORIGINAL_RAW", "source_text_equal": False}
    original = re.findall(r"\w+", source_text.casefold())
    compiled = re.findall(r"\w+", stock_text.casefold())
    if not original or not compiled or len(original) > 100000 or len(compiled) > 100000:
        return {"status": "EMPTY_OR_OVERSIZE_LEXICAL_UNITS", "source_text_equal": False}
    # Reuse the independently reviewed bounded LCS helper. Multiset
    # overlap by itself would hide reordering/omission of original prose.
    ordered = plain_word_alignment(original, compiled)
    common = sum((Counter(original) & Counter(compiled)).values())
    source_pct = round(common * 100 / len(original))
    stock_pct = round(common * 100 / len(compiled))
    least = min(source_pct, stock_pct)
    classification = (
        "HIGH_95_PLUS" if least >= 95 else
        "HIGH_80_PLUS" if least >= 80 else
        "MODERATE_50_PLUS" if least >= 50 else "LOW_OVERLAP"
    )
    prefix = None
    suffix = None
    if (ordered["original_plain_words_not_matched_in_exact_order"] == 0
            and ordered["stock_plain_words_not_matched_in_exact_order"] > 0
            and ordered["common_end_word_tokens"] == len(original)):
        try:
            prefix = source_word_prefix_topology(source_text, stock_raw)
            suffix = stock_prefixed_source_body_concordance(source_text, stock_raw)
        except (ValueError, PilotError):
            prefix = {
                "status": "NOT_A_STRICT_CASE_SENSITIVE_STOCK_PREFIX",
                "extra_stock_words_are_not_approved": True,
            }
    neighbor_concordance = None
    if (prefix is not None and prefix.get("full_original_source_word_sequence_inside_stock")
            and source_neighbor_candidates is not None):
        try:
            neighbor_concordance = stock_prefix_context_correspondence(
                source_text, stock_raw, source_neighbor_candidates
            )
        except (ValueError, PilotError):
            neighbor_concordance = {
                "status": "SOURCE_CONTEXT_NOT_SAFE_FOR_CORRESPONDENCE",
                "original_text_or_xml_disclosed": False,
            }
    single_word = None
    if (ordered["original_plain_words_not_matched_in_exact_order"] == 1
            and ordered["stock_plain_words_not_matched_in_exact_order"] == 1
            and len(original) == len(compiled)):
        # Existing cross-edition counts identify a small number of isolated
        # mismatches. Locate their stock XML owner without logging any words.
        single_word = single_word_stock_markup_diagnostic(source_text, stock_raw)
    return {
        "status": "INDEPENDENT_DIGITAL_EDITION_DIAGNOSTIC_ONLY",
        "source_word_count": len(original),
        "stock_word_count": len(compiled),
        "matched_word_multiset_count": common,
        "source_word_overlap_percent": source_pct,
        "stock_word_overlap_percent": stock_pct,
        "overlap_class": classification,
        "exact_ordered_word_equality": original == compiled,
        "ordered_word_alignment": ordered,
        "stock_extra_prefix_xml_topology": prefix,
        "stock_prefix_independent_source_neighbor_correspondence": neighbor_concordance,
        "isolated_one_word_xml_location": single_word,
        "stock_source_suffix_punctuation_topology": suffix,
        "source_text_equal": source_text == stock_text,
        "historical_or_editorial_equivalence_proven": False,
        "authorial_prose_modified": False,
    }




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
                                          unrecognized_cases: list[dict],
                                          stock_unknown_raw: dict[str, bytes] | None = None,
                                          original_visible_chapter_intro_raw: dict[str, bytes] | None = None) -> dict:
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
    aliases, alias_registry_meta = read_existing_66_book_english_aliases()
    if not set(canonical_books).issubset(aliases):
        return {
            "status": "SOURCE_BOOK_ALIASES_NOT_REVIEWED_FOR_NATIVE_MODULE",
            "case_rows": [], "scope_authorized": False
        }
    chapters_div1 = []
    excluded_unattributed_div1 = 0
    for node in document.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "div1":
            continue
        chapters = [x for x in node if
                    isinstance(x.tag, str) and x.tag.rsplit("}", 1)[-1] == "div2"]
        if not chapters:
            continue
        title = _canon_name(node.get("title", ""))
        title_names = [
            code for code, alias in aliases.items()
            if re.search(r"(?<!\w)" + re.escape(_canon_name(alias)) + r"(?!\w)", title)
        ]
        has_scripcom = any(
            isinstance(child.tag, str)
            and child.tag.rsplit("}", 1)[-1] == "scripCom"
            for child in node.iter()
        )
        if not title_names and not has_scripcom:
            excluded_unattributed_div1 += 1
            continue
        chapters_div1.append((node, chapters))
    if len(chapters_div1) != len(canonical_books):
        return {
            "status": "SOURCE_BOOK_LAYOUT_NOT_EXACT_NATIVE_BOOK_COUNT",
            "native_book_count": len(canonical_books),
            "source_book_divisions": len(chapters_div1),
            "case_rows": [], "scope_authorized": False
        }
    source_chapters = {}
    private_book_prefix_text = {}
    private_book_prefix_neighbors = {}
    private_book_prefix_ref_links = {}
    private_book_prefix_structure = {}
    explicit_source_chapters = {}
    ambiguous_source_heading_chapters = set()
    book_classes = Counter()
    book_evidence_rows = []
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
        source_prefix_nodes = []
        for direct_child in div1:
            if isinstance(direct_child.tag, str) and direct_child.tag.rsplit("}", 1)[-1] == "div2":
                break
            source_prefix_nodes.append(direct_child)
        prefix_tag_counts = Counter(
            node.tag.rsplit("}", 1)[-1]
            for node in source_prefix_nodes if isinstance(node.tag, str)
        )
        prefix_chapter_markers = []
        prefix_heading_numbers = set()
        prefix_nonempty_paragraphs = 0
        for prefix_node in source_prefix_nodes:
            for element in prefix_node.iter():
                if not isinstance(element.tag, str):
                    continue
                kind = element.tag.rsplit("}", 1)[-1]
                if kind == "scripCom":
                    ref = element.get("osisRef", "")
                    typ, _ = _parse_reference(ref)
                    matched = WORK_REF.fullmatch(ref)
                    if typ == "work_qualified_chapter" and matched:
                        prefix_chapter_markers.append(matched.group(2))
                if kind in ("h2", "title"):
                    heading = "".join(element.itertext())
                    for number in re.findall(r"\bchapter\s+([1-9]\d*)\b", heading, re.I):
                        prefix_heading_numbers.add(int(number))
                if kind == "p":
                    prefix_nonempty_paragraphs += bool("".join(element.itertext()).strip())
        private_book_prefix_text[code] = " ".join(
            "".join(node.itertext())
            for element in source_prefix_nodes
            for node in element.iter()
            if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "p"
        )
        private_book_prefix_ref_links[code] = [
            {
                "text": "".join(node.itertext()),
                "attribute_name_types": list(node.attrib),
                "private_original_osisRef_target": node.get("osisRef", ""),
            }
            for element in source_prefix_nodes for node in element.iter()
            if isinstance(node.tag, str)
            and node.tag.rsplit("}", 1)[-1] == "scripRef"
        ]
        private_book_prefix_neighbors[code] = [
            ("source_div1_title_attribute", div1.get("title", "")),
            *(
                ("source_immediate_previous_heading_element",
                 "".join(element.itertext()))
                for element in source_prefix_nodes
                if isinstance(element.tag, str)
                and element.tag.rsplit("}", 1)[-1] in {"h1", "h2", "title"}
            ),
        ][:8]
        # Extra caution: several CCEL ThML editions put the first
        # chapter prose directly under the BOOK div1, before the first div2.
        # Only a complete one-chapter deficit + explicit nonconflicting
        # chapter numbering from chapter 2 onward can support that scope.
        # This remains an *independent digital witness*, not a publication
        # or text normalization permit.
        first_expected_chapter = 2
        numbered_source_div2_evidence = 0
        source_div2_heading_conflicts = 0
        source_first_div2_declares_chapter_two = False
        for offset, child in enumerate(chapters, start=first_expected_chapter):
            declared_numbers = set()
            for heading in child:
                if (isinstance(heading.tag, str)
                        and heading.tag.rsplit("}", 1)[-1] in ("h2", "title")):
                    declared_numbers.update(int(n) for n in re.findall(
                        r"\bchapter\s+([1-9]\d*)\b",
                        "".join(heading.itertext()), re.I
                    ))
            if declared_numbers:
                numbered_source_div2_evidence += 1
                if declared_numbers != {offset}:
                    source_div2_heading_conflicts += 1
            if offset == first_expected_chapter:
                source_first_div2_declares_chapter_two = (
                    declared_numbers == {first_expected_chapter}
                )
        first_prefix_compatible = (
            len(chapters) == len(native_by_book[code]) - 1
            and candidates == {code} and annotated_books == {code}
            and len(native_by_book[code]) >= 3
            and prefix_nonempty_paragraphs >= 1
            and source_first_div2_declares_chapter_two
            and numbered_source_div2_evidence >= 2
            and source_div2_heading_conflicts == 0
            and set(prefix_chapter_markers) <= {f"{code}.1"}
            and set(prefix_heading_numbers) <= {1}
        )
        private_book_prefix_structure[code] = {
            "missing_exactly_one_div2_with_book_prefix_prose":
                len(chapters) == len(native_by_book[code]) - 1
                and prefix_nonempty_paragraphs > 0,
            "first_div2_explicitly_declares_second_chapter":
                source_first_div2_declares_chapter_two,
            "nonconflicting_later_numeric_chapter_headings":
                numbered_source_div2_evidence,
            "conflicting_later_numeric_chapter_headings":
                source_div2_heading_conflicts,
            "all_source_book_identity_and_chapter_order_guards_pass":
                first_prefix_compatible,
            "original_book_prefix_text_not_reassigned": True,
        }
        book_evidence_rows.append({
            "native_book": code,
            "title_alias_candidate_books": sorted(candidates),
            "explicit_source_annotation_books": sorted(annotated_books),
            "source_direct_div2_count": len(chapters),
            "native_registry_chapter_count": len(native_by_book[code]),
            "identity_class": identity,
            "source_direct_nodes_before_first_div2": dict(sorted(prefix_tag_counts.items())),
            "source_prefix_chapter_scripCom_refs": sorted(set(prefix_chapter_markers)),
            "source_prefix_numeric_h2_chapters": sorted(prefix_heading_numbers),
            "source_prefix_nonempty_paragraphs": prefix_nonempty_paragraphs,
        })
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
            marker_chapter_references = set()
            for marker in markers:
                kind, _ = _parse_reference(marker.get("osisRef", ""))
                if kind not in (
                    "work_qualified_chapter", "work_qualified_verse",
                    "work_qualified_same_book_verse_range"
                ):
                    continue
                match = WORK_REF.fullmatch(marker.get("osisRef", ""))
                if match:
                    for part in match.group(2).split("-"):
                        parts = part.split(".")
                        if len(parts) >= 2 and parts[1].isdigit():
                            marker_chapter_references.add(parts[0] + "." + parts[1])
            # Title text is inspected privately for *numerical* chapter
            # indicators only; it is not emitted in the report.
            heading_chapter_numbers = set()
            for head in div2:
                if not isinstance(head.tag, str) or head.tag.rsplit("}", 1)[-1] not in ("h2", "title"):
                    continue
                text = "".join(head.itertext())
                for number in re.findall(r"\bchapter\s+([1-9]\d*)\b", text, re.I):
                    heading_chapter_numbers.add(int(number))
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
                "source_annotated_chapter_references": sorted(marker_chapter_references),
                "source_h2_explicit_numeric_chapters": sorted(heading_chapter_numbers),
                "source_div2_text_sha256": sha256(
                    "".join(div2.itertext()).encode("utf-8")
                ).hexdigest(),
                "source_div2_original_text_retained": True,
                "source_div2_ordinal": chapter_number,
                "_private_source_visible_text": "".join(div2.itertext()),
                "_private_source_xml_div2_element": div2,
                "_private_original_scripref_links": [
                    {
                        "text": "".join(node.itertext()),
                        "attribute_name_types": list(node.attrib),
                        "private_original_osisRef_target": node.get("osisRef", ""),
                    }
                    for node in div2.iter()
                    if isinstance(node.tag, str)
                    and node.tag.rsplit("}", 1)[-1] == "scripRef"
                ],
                "_private_source_neighbor_candidates": [
                    ("source_div2_title_attribute", div2.get("title", "")),
                    ("source_div1_title_attribute", div1.get("title", "")),
                    *(
                        ("source_immediate_previous_heading_element",
                         "".join(head.itertext()))
                        for head in div2
                        if isinstance(head.tag, str)
                        and head.tag.rsplit("}", 1)[-1] in {"h2", "h1", "title"}
                    ),
                ][:8],
            }
            if (identity == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
                    and candidates == {code} and annotated_books == {code}
                    and len(heading_chapter_numbers) == 1):
                declared = next(iter(heading_chapter_numbers))
                target = f"{code}.{declared}"
                if (target in chapter_maximums
                        and marker_chapter_references <= {target}):
                    if target in explicit_source_chapters:
                        ambiguous_source_heading_chapters.add(target)
                    else:
                        explicit_source_chapters[target] = source_chapters[chapter]
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
        alignment_method = "SOURCE_NATIVE_DIV2_ORDINAL_AND_BOOK"
        if chapter in explicit_source_chapters or chapter in ambiguous_source_heading_chapters:
            source = (
                explicit_source_chapters.get(chapter)
                if chapter not in ambiguous_source_heading_chapters else None
            )
            alignment_method = "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        elif (source is not None and
              source["book_identity_class"] == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"):
            # The unverified div2 ordinal must never stand in for a chapter
            # omitted from this digital witness's division sequence.
            source = None
            alignment_method = "NO_SAFE_EXPLICIT_SOURCE_CHAPTER_MAPPING"
        if source is None:
            classification = "NO_SAFE_SOURCE_DIV2_FOR_NATIVE_CHAPTER"
        elif source["book_identity_class"] not in {
            "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH",
            "SOURCE_BOOK_TITLE_MATCH",
            "SOURCE_BOOK_MARKERS_MATCH",
            "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
        }:
            classification = "SOURCE_BOOK_OR_CHAPTER_ALIGNMENT_NEEDS_REVIEW"
        elif source["book_identity_class"] == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY" and (
            alignment_method != "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        ):
            classification = "SOURCE_CHAPTER_COUNT_UNREVIEWED"
        elif source["source_h2_explicit_numeric_chapters"] and (
            int(chapter.rsplit(".", 1)[1])
            not in source["source_h2_explicit_numeric_chapters"]
        ):
            classification = "SOURCE_HEADING_CHAPTER_CONFLICT"
        elif source["source_numbered_section_marker_count"] > 0:
            classification = "SOURCE_DIV2_HAS_INDEPENDENT_VERSE_SECTIONS"
        elif source["source_nonempty_paragraph_count"] == 0:
            classification = "SOURCE_DIV2_NO_NONEMPTY_COMMENTARY_PARAGRAPHS"
        elif alignment_method == "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING":
            classification = "SOURCE_DIV2_UNDIVIDED_EXPLICIT_HEADING_CANDIDATE"
        else:
            classification = "SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE"
        lexical = None
        reference_targets = None
        if stock_unknown_raw and row["native_key"] in stock_unknown_raw:
            # For a source div2, compare that chapter's actual private source
            # unit; for a missing first div2, compare the prefix *as a probe*
            # and never silently call it the authored first chapter.
            source_text = (
                source["_private_source_visible_text"] if source is not None
                else private_book_prefix_text.get(chapter.split(".", 1)[0])
                if chapter.endswith(".1") else None
            )
            if source_text is not None:
                neighboring = (
                    source["_private_source_neighbor_candidates"] if source is not None
                    else private_book_prefix_neighbors.get(chapter.split(".", 1)[0], [])
                )
                # Keep all private source strings bounded before passing them to
                # a metadata-only XML source-context comparison.
                neighboring = [
                    (name, value) for name, value in neighboring
                    if isinstance(value, str) and len(value) <= 2048
                ]
                lexical = independent_lexical_overlap(
                    source_text, stock_unknown_raw[row["native_key"]],
                    source_neighbor_candidates=neighboring
                )
                source_links = (
                    source["_private_original_scripref_links"] if source is not None
                    else private_book_prefix_ref_links.get(chapter.split(".", 1)[0], [])
                )
                # The existing strict original-reference/stock-reference
                # comparator verifies literal source target pairing without
                # treating label resemblance as destination identity.
                reference_targets = link_label_location(
                    source_links, stock_unknown_raw[row["native_key"]]
                )
                one_word = lexical.get("isolated_one_word_xml_location")
                if one_word is not None:
                    if source is None:
                        source_position = "NO_SAFE_INDEPENDENT_SOURCE_UNIT"
                    else:
                        source_link_word_positions = set(marked_word_token_indices(
                            source["_private_source_xml_div2_element"], "scripRef",
                            source_text
                        ))
                        source_position = (
                            "SOURCE_SCRIPREF_LINK_LABEL"
                            if one_word["original_word_index_from_zero"]
                            in source_link_word_positions
                            else "SOURCE_COMMENTARY_TEXT_OUTSIDE_SCRIPREF"
                        )
                    one_word["original_source_word_markup_location"] = source_position
                    one_word["source_link_annotation_is_not_authorial_prose_parity"] = True
        prefix_proof = None
        if source is None and chapter.endswith(".1"):
            candidate_proof = private_book_prefix_structure.get(
                chapter.rsplit(".", 1)[0], {}
            )
            source_alignment = (
                lexical.get("ordered_word_alignment",{})
                if isinstance(lexical, dict) else {}
            )
            full_original_prose_retained = (
                source_alignment.get(
                    "original_plain_words_not_matched_in_exact_order"
                ) == 0
                and source_alignment.get(
                    "exact_unicode_longest_common_subsequence_word_count"
                ) == source_alignment.get("original_plain_word_tokens")
                and isinstance(lexical,dict)
                and lexical.get("overlap_class") == "HIGH_95_PLUS"
            )
            prefix_proof = {
                **candidate_proof,
                "source_book_prefix_prose_is_complete_in_original_K":
                    full_original_prose_retained,
                "source_book_prefix_first_chapter_attribution_approved":False,
            }
            if (candidate_proof.get(
                    "all_source_book_identity_and_chapter_order_guards_pass")
                    and full_original_prose_retained):
                classification = (
                    "SOURCE_BOOK_PREFIX_FIRST_CHAPTER_UNDIVIDED_CANDIDATE"
                )
        classes[classification] += 1
        cases.append({
            "independent_lexical_comparison": lexical,
            "independent_reference_target_comparison": reference_targets,
            "native_start": row["native_key"],
            "source_div2_structure_class": classification,
            "source_book_prefix_first_chapter_structural_witness": prefix_proof,
            "source_chapter_alignment_method": alignment_method,
            "source_div2_original_ordinal": source["source_div2_ordinal"] if source else None,
            "source_chapter_marker_count": source["source_chapter_marker_count"] if source else 0,
            "source_numbered_marker_count": source["source_numbered_section_marker_count"] if source else 0,
            "source_nonempty_paragraph_count": source["source_nonempty_paragraph_count"] if source else 0,
            "source_div2_text_sha256": source["source_div2_text_sha256"] if source else None,
            "source_annotated_chapters": source["source_annotated_chapter_references"] if source else [],
            "source_h2_numeric_chapters": source["source_h2_explicit_numeric_chapters"] if source else [],
            "stock_raw_sha256": row["raw_payload_sha256"],
            "source_text_to_stock_text_identity_proven": False,
            "approved_for_native_index_expansion": False,
        })
    # Compare inline scripture-link *targets* separately from displayed
    # words: an exact spelling match must never substitute for real OSIS
    # destination preservation. These are different pinned digital editions.
    reference_classes = Counter()
    reference_totals = Counter()
    reference_exception_rows = []
    missing_stock_link_label_locations = Counter()
    unmatched_source_target_label_locations = Counter()
    unpaired_literal_unique_anchor_candidates = 0
    for row in cases:
        refs = row.get("independent_reference_target_comparison")
        if refs is None:
            reference_classes["NOT_COMPARABLE"] += 1
            continue
        orig = refs["original_scripRef_with_nonempty_osisRef_target_count"]
        stock = refs["selected_stock_reference_elements_with_osisRef_attribute"]
        paired = (
            refs["original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"]
            + refs["original_scripRef_osisRef_work_qualifier_only_matches_in_stock"]
        )
        if paired > min(orig, stock):
            raise PilotError("Original/stock reference target pairing exceeds actual markup")
        unpaired_source = orig - paired
        unpaired_stock = stock - paired
        if refs["unpaired_original_source_target_occurrences"] != unpaired_source:
            raise PilotError("Independent original source target remainder misclassified")
        unmatched_source_target_label_locations.update(
            refs["unpaired_original_source_target_label_location_classes"]
        )
        unpaired_literal_unique_anchor_candidates += refs[
            "unpaired_unique_literal_unlinked_citation_label_candidate_count"
        ]
        reference_totals["original_source_nonempty_target_occurrences"] += orig
        reference_totals["stock_nonempty_target_occurrences"] += stock
        reference_totals["paired_target_occurrences_exact_or_literal_work_prefix"] += paired
        reference_totals["source_target_occurrences_not_paired_in_selected_stock"] += unpaired_source
        reference_totals["stock_target_occurrences_not_paired_in_selected_source"] += unpaired_stock
        if orig == stock == 0:
            classification = "BOTH_HAVE_NO_LINK_MARKUP"
        elif orig and not stock:
            classification = "SOURCE_LINK_MARKUP_NOT_PRESENT_IN_SELECTED_STOCK"
        elif not orig and stock:
            classification = "STOCK_ONLY_LINK_MARKUP"
        elif orig == stock == paired:
            classification = "ALL_LINK_TARGETS_MATCH_EXACT_OR_LITERAL_WORK_PREFIX"
        elif unpaired_source and not unpaired_stock:
            classification = "SOURCE_HAS_EXTRA_UNPAIRED_LINK_TARGETS"
        elif unpaired_stock and not unpaired_source:
            classification = "STOCK_HAS_EXTRA_UNPAIRED_LINK_TARGETS"
        else:
            classification = "BOTH_EDITIONS_HAVE_UNPAIRED_LINK_TARGETS"
        reference_classes[classification] += 1
        if classification == "SOURCE_LINK_MARKUP_NOT_PRESENT_IN_SELECTED_STOCK":
            # Every source citation in this precise class is target-unpaired:
            # its displayed label may remain visible as ordinary stock prose,
            # or be absent from the selected stock text. Never infer the
            # underlying destination from label resemblance alone.
            missing_stock_link_label_locations.update(
                refs["original_scripRef_to_stock_text_location_classes"]
            )
        if unpaired_source or unpaired_stock:
            reference_exception_rows.append({
                "native_start": row["native_start"],
                "source_target_occurrences_not_paired": unpaired_source,
                "stock_target_occurrences_not_paired": unpaired_stock,
                "selected_stock_reference_element_count":
                    refs["selected_stock_reference_element_count"],
                "classification": classification,
                "source_link_label_location_classes":
                    refs["original_scripRef_to_stock_text_location_classes"],
                "unpaired_source_link_label_location_classes":
                    refs["unpaired_original_source_target_label_location_classes"],
                "unique_literal_unlinked_original_source_label_candidates":
                    refs["unpaired_unique_literal_unlinked_citation_label_candidate_count"],
                "source_to_stock_reference_markup_parity_proven": False,
            })
    single_word_source_markup = Counter(
        row["independent_lexical_comparison"]["isolated_one_word_xml_location"].get(
            "original_source_word_markup_location", "NOT_LOCATED"
        )
        for row in cases
        if row["independent_lexical_comparison"] is not None
        and row["independent_lexical_comparison"].get("isolated_one_word_xml_location")
    )
    word_classes = Counter(
        row["independent_lexical_comparison"].get("overlap_class", "UNREVIEWED")
        for row in cases if row["independent_lexical_comparison"] is not None
    )
    ordered_word_classes = Counter(
        row["independent_lexical_comparison"]["ordered_word_alignment"][
            "exact_unicode_ordered_alignment_class"
        ]
        for row in cases if row["independent_lexical_comparison"] is not None
        and "ordered_word_alignment" in row["independent_lexical_comparison"]
    )
    # Reuse the *same* already verified book-title/chapter-ordinal
    # source mapping for original native I text, rather than guessing a
    # section scope from another edition's stray verse citation.
    introduction_witnesses = []
    for intro_chapter, raw in sorted((original_visible_chapter_intro_raw or {}).items()):
        source = source_chapters.get(intro_chapter)
        alignment = "SOURCE_NATIVE_DIV2_ORDINAL_AND_BOOK"
        if (intro_chapter in explicit_source_chapters
                or intro_chapter in ambiguous_source_heading_chapters):
            source = (
                explicit_source_chapters.get(intro_chapter)
                if intro_chapter not in ambiguous_source_heading_chapters else None
            )
            alignment = "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        if (source is not None
                and source["book_identity_class"] ==
                   "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
                and alignment != "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"):
            source = None
        if source is None:
            classification = "NO_SAFE_WITNESS_DIV2_CHAPTER_MAPPING"
        elif source["book_identity_class"] not in {
                "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH",
                "SOURCE_BOOK_TITLE_MATCH",
                "SOURCE_BOOK_MARKERS_MATCH",
                "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY",
        }:
            classification = "SOURCE_BOOK_IDENTITY_UNVERIFIED"
        elif (source["source_h2_explicit_numeric_chapters"]
              and int(intro_chapter.rsplit(".", 1)[1])
              not in source["source_h2_explicit_numeric_chapters"]):
            classification = "SOURCE_CHAPTER_HEADING_DISAGREES_WITH_NATIVE_KEY"
        else:
            classification = "INDEPENDENT_DIGITAL_EDITION_CHAPTER_LOCATION_CORROBORATED"
        lex = (
            independent_lexical_overlap(source["_private_source_visible_text"], raw)
            if classification ==
               "INDEPENDENT_DIGITAL_EDITION_CHAPTER_LOCATION_CORROBORATED"
            else None
        )
        introduction_witnesses.append({
            "original_native_intro_chapter": intro_chapter,
            "classification": classification,
            "source_book_alignment_class": (
                source["book_identity_class"] if source is not None else None
            ),
            "source_chapter_alignment_method": alignment,
            "source_numbered_comment_section_markers": (
                source["source_numbered_section_marker_count"]
                if source is not None else None
            ),
            "source_chapter_comment_section_markers": (
                source["source_chapter_marker_count"]
                if source is not None else None
            ),
            "original_intro_vs_witness_word_overlap": lex,
            "is_not_source_edition_or_authorial_chapter_approval": True,
        })
    return {
        "status": "SOURCE_DIV2_STRUCTURE_COLLATED_NO_REINDEX_AUTHORIZATION",
        "independent_source_div2_text_bearing_native_intro_reviews":
            introduction_witnesses,
        "independent_stock_vs_source_reference_target_classes":
            dict(sorted(reference_classes.items())),
        "independent_stock_vs_source_reference_target_totals":
            dict(sorted(reference_totals.items())),
        "independent_stock_vs_source_reference_target_exception_rows":
            reference_exception_rows,
        "source_reference_labels_when_stock_has_no_link_markup":
            dict(sorted(missing_stock_link_label_locations.items())),
        "unpaired_original_source_reference_target_label_location_classes":
            dict(sorted(unmatched_source_target_label_locations.items())),
        "unpaired_unique_literal_reference_label_candidate_count":
            unpaired_literal_unique_anchor_candidates,
        "all_cross_edition_unpaired_source_targets_require_review":True,
        "source_reference_label_location_is_not_a_target_or_text_parity_check": True,
        "isolated_one_word_original_source_markup_location_classes":
            dict(sorted(single_word_source_markup.items())),
        "source_reference_target_completeness_not_proven": True,
        "independent_stock_vs_source_lexical_diagnostic_classes":
            dict(sorted(word_classes.items())),
        "independent_stock_vs_source_ordered_word_diagnostic_classes":
            dict(sorted(ordered_word_classes.items())),
        "source_book_divisions": len(chapters_div1),
        "unattributed_noncanonical_div1_with_div2_excluded": excluded_unattributed_div1,
        "native_book_count": len(canonical_books),
        "book_alignment_evidence_classes": dict(sorted(book_classes.items())),
        "book_alignment_evidence_rows": book_evidence_rows,
        "ambiguous_original_numeric_chapter_headings": sorted(ambiguous_source_heading_chapters),
        "reviewed_registry_evidence": alias_registry_meta,
        "candidate_classes": dict(sorted(classes.items())),
        "case_rows": cases,
        "derived_authorial_section_scope_proven": False,
        "original_xml_or_stock_modified": False
    }



def inspect_independent_leading_range_citations(document, anomalies: list[dict],
                                                original_stock_raw: dict[str, bytes]) -> dict:
    """Read-only, source-neutral attribution of claimed ranges to source prose.

    A scripRef in a chapter outline is a citation, NOT a commentary-section
    anchor. Compare source scripRef placement and the exact original stock
    passage's plain-word overlap; disclose only counts and closed-set classes.
    This never grants independent editorial approval or modifies the source.
    """
    wanted = {}
    for row in anomalies:
        key = row["start"]
        end = row["declared_end"]
        if (KEY.fullmatch(key) is None or not isinstance(end, int)
                or end < int(key.rsplit(".", 1)[1])
                or key not in original_stock_raw):
            raise PilotError("Unverified source range candidate in independent review")
        wanted[key] = key.rsplit(".", 1)[0] + "." + str(end)
    if len(wanted) > 100:
        raise PilotError("Excessive independent citation range candidates")
    entries = defaultdict(list)
    for node in document.iter():
        if (not isinstance(node.tag, str)
                or node.tag.rsplit("}", 1)[-1] != "scripRef"):
            continue
        ref = node.get("osisRef", "")
        parsed = WORK_REF.fullmatch(ref)
        if parsed is None or _parse_reference(ref)[0] not in (
                "work_qualified_verse", "work_qualified_same_book_verse_range"):
            continue
        body = parsed.group(2)
        first, last = body.split("-", 1) if "-" in body else (body, body)
        if wanted.get(first) != last:
            continue
        direct_parent = node.getparent()
        direct_parent_type = (
            direct_parent.tag.rsplit("}", 1)[-1]
            if direct_parent is not None and isinstance(direct_parent.tag, str)
            else "_NONE"
        )
        # CCEL ThML often nests the citation inside formatting markup.
        # A direct p-only rule would wrongly reject a genuine lead reference.
        paragraph = direct_parent
        while paragraph is not None and (
                not isinstance(paragraph.tag, str)
                or paragraph.tag.rsplit("}", 1)[-1] != "p"):
            paragraph = paragraph.getparent()
        reference_words = "".join(node.itertext(with_tail=False)).strip()
        source_text = "".join(paragraph.itertext()) if paragraph is not None else ""
        visible = source_text.lstrip()
        leading_in_paragraph = (
            bool(reference_words) and bool(paragraph is not None)
            and visible.startswith(reference_words)
        )
        after_ref = visible[len(reference_words):] if leading_in_paragraph else ""
        tail_words = re.findall(r"\w+", after_ref.casefold())
        original_root = etree.fromstring(
            b"<entry>" + original_stock_raw[first] + b"</entry>",
            parser=etree.XMLParser(resolve_entities=False, no_network=True,
                                   load_dtd=False, recover=False,
                                   huge_tree=False, remove_blank_text=False)
        )
        stock_words = re.findall(
            r"\w+", "".join(original_root.itertext()).casefold()
        )
        source_words = re.findall(
            r"\w+", source_text.casefold()
        ) if paragraph is not None else []
        aligned = plain_word_alignment(source_words, stock_words) if source_words else None
        passage_body_correspondence = (
            leading_in_paragraph and len(tail_words) >= 20
            and aligned is not None
            and aligned["exact_unicode_longest_contiguous_shared_word_run_count"] is not None
            and aligned["exact_unicode_longest_contiguous_shared_word_run_count"] >= 20
        )
        entries[first].append({
            "source_scripRef_is_leading_paragraph_element": leading_in_paragraph,
            "reference_has_substantial_following_prose": len(tail_words) >= 20,
            "source_and_stock_share_at_least_twenty_contiguous_words":
                passage_body_correspondence,
            "source_paragraph_word_count": len(source_words),
            "source_following_direct_tail_word_count": len(tail_words),
            "aligned_consecutive_word_count":
                (aligned["exact_unicode_longest_contiguous_shared_word_run_count"]
                 if aligned else None),
            "source_markup_parent": direct_parent_type,
            "source_reference_inside_paragraph": paragraph is not None,
            "scripRef_is_not_scripCom": True,
        })
    cases = []
    for start, end in wanted.items():
        observations = entries.get(start, [])
        cases.append({
            "original_section_start": start,
            "stock_declared_end": end,
            "independent_exact_range_citation_count": len(observations),
            "independent_leading_reference_with_substantial_following_prose":
                sum(o["source_scripRef_is_leading_paragraph_element"]
                    and o["reference_has_substantial_following_prose"]
                    for o in observations),
            "independent_leading_reference_and_matching_original_stock_exposition":
                sum(o["source_and_stock_share_at_least_twenty_contiguous_words"]
                    for o in observations),
            "independent_reference_observations": observations[:6],
            "scope_authorially_reviewed": False,
            "claim_is_only_corroborating_digital_witness": True,
        })
    return {
        "status": "INDEPENDENT_DIGITAL_SECTION_LEAD_TO_STOCK_PROSE_TRIAGE_NOT_APPROVAL",
        "case_count": len(cases),
        "cases_with_independent_exact_range_citation": sum(
            row["independent_exact_range_citation_count"] > 0 for row in cases
        ),
        "cases_with_source_lead_prose_and_matching_stock_exposition": sum(
            row["independent_leading_reference_and_matching_original_stock_exposition"] > 0
            for row in cases
        ),
        "case_rows": cases,
        "original_or_independent_source_text_logged": False,
        "original_source_changed": False,
        "publication_authorized": False,
    }


def compare_independent_thml_witness(manifest: dict, sections: list[dict],
                                     anomalies: list[dict], temp: Path,
                                     unrecognized_cases: list[dict] | None = None,
                                     native_registry: dict | None = None,
                                     stock_unknown_raw: dict[str, bytes] | None = None,
                                     original_chapter_intro_raw: dict[str, bytes] | None = None,
                                     original_range_stock_raw: dict[str, bytes] | None = None,
                                     original_reference_triage: OriginalCommentaryReferenceRegistryTriage | None = None,
                                     original_native_section_spans: dict[str, tuple[int, ...]] | None = None,
                                     paragraph_pilot_samples: list[tuple[str, str, bytes]] | None = None) -> dict:
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

    source_intro_chapter_comparison = independent_thml_chapter_intro_witness(
        document, original_chapter_intro_raw or {}
    )
    chapter_scopes = independent_chapter_scope_evidence(document, unrecognized_cases or [])
    div2_scopes = (
        independent_div2_chapter_body_evidence(
            document, native_registry, unrecognized_cases or [], stock_unknown_raw,
            original_chapter_intro_raw
        ) if native_registry is not None else {
            "status": "NO_NATIVE_REGISTRY_PROVIDED",
            "case_rows": [], "derived_authorial_section_scope_proven": False
        }
    )
    independent_lead_citations = inspect_independent_leading_range_citations(
        document, anomalies, original_range_stock_raw or {}
    ) if original_range_stock_raw is not None else None
    reversed_reference_witness = (
        original_reference_triage.triangulate_reversed_ranges_against_independent_witness(
            document, canonical_verses=native_registry["verse_keys"],
            native_section_spans=original_native_section_spans or {})
        if original_reference_triage is not None and native_registry is not None else None
    )
    paragraph_pilot = compare_paragraph_witness(
        document, paragraph_pilot_samples
    ) if paragraph_pilot_samples is not None else None
    return {
        "independent_original_paragraph_witness_pilot": paragraph_pilot,
        "independent_original_reversed_reference_witness": reversed_reference_witness,
        "independent_leading_range_citations": independent_lead_citations,
        "status": "PINNED_DIFFERENT_DIGITAL_EDITION_SCOPE_COMPARISON",
        "independent_whole_chapter_review": chapter_scopes,
        "independent_div2_chapter_body_review": div2_scopes,
        "independent_chapter_intro_text_witness": source_intro_chapter_comparison,
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


def audit(resource_id: str, index_binary: Path, raw_binary: Path,
          *, transport_sample_chapters: tuple[str, ...] = (),
          synthetic_intro_native_stream: Path | None = None,
          intro_sample_chapters: tuple[str, ...] = (),
          mixed_sample_chapters: tuple[str, ...] = (),
          full_transport: bool = False,
          paragraph_pilot_keys: tuple[str, ...] = (),
          provisional_range_preview: bool = False,
          preview_real_xiphos: bool = False) -> dict:
    """Use exact SHA-pinned official stock, existing independently proved readers."""
    manifest = load_manifest(resource_id)
    if provisional_range_preview and not full_transport:
        raise PilotError("Provisional range preview requires original complete transport")
    if preview_real_xiphos and not provisional_range_preview:
        raise PilotError("Real-reader preview requires source-constrained index preview")
    if ((paragraph_pilot_keys and not full_transport)
            or len(paragraph_pilot_keys) > 8
            or len(set(paragraph_pilot_keys)) != len(paragraph_pilot_keys)
            or any(re.fullmatch(
                r"(?:I:[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*|"
                r"K:[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*\.[1-9]\d*)",
                val) is None for val in paragraph_pilot_keys)):
        raise PilotError("Unbounded or unsafe original paragraph pilot selection")
    if (len(mixed_sample_chapters) > 3
            or len(set(mixed_sample_chapters)) != len(mixed_sample_chapters)
            or any(re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", ref) is None
                   for ref in mixed_sample_chapters)):
        raise PilotError("Unreviewed or excessive original mixed I+K sample chapters")
    if (len(intro_sample_chapters) > 4
            or len(set(intro_sample_chapters)) != len(intro_sample_chapters)
            or any(re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", ref) is None
                   for ref in intro_sample_chapters)):
        raise PilotError("Unreviewed or excessive original introduction transport chapters")
    if (len(transport_sample_chapters) > 6
            or len(set(transport_sample_chapters)) != len(transport_sample_chapters)
            or any(re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*",
                                chapter) is None
                   for chapter in transport_sample_chapters)):
        raise PilotError("Unreviewed or excessive original chapter transport samples")
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
        private_unrecognized_raw = {}
        private_range_heading_raw = {}
        temporary_original_sample_raw = []
        original_sample_chapter_set = set(transport_sample_chapters)
        original_mixed_sample_set = set(mixed_sample_chapters)
        private_mixed_I = {}
        private_mixed_K = defaultdict(list)
        private_full_I = {}
        private_full_K = defaultdict(list)
        osis_rebuild_preflight = NativeOSISRebuildPreflight()
        editorial_topology = NativeCommentaryEditorialTopology()
        layout_census = NativeCommentaryLayoutCensus()
        original_reference_triage = OriginalCommentaryReferenceRegistryTriage()
        original_opaque_top_records = []
        private_intro_text_raw_by_chapter = {}
        private_numbered_bodies_for_intro_chapter = defaultdict(dict)
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
                osis_rebuild_preflight.observe(kind, ref, raw)
                editorial_topology.observe(kind, ref, raw)
                try:
                    layout_census.observe(kind, ref, raw)
                except ValueError as exc:
                    # A bounded diagnostic on the ephemeral audit runner:
                    # the original native key and an allowlisted fixed error
                    # class only; never output original XML, text or attrs.
                    allowed = {
                        "Unsafe original commentary source fragment",
                        "Original commentary layout XML is unparseable",
                        "Unresolved original commentary XML entity",
                        "Unbounded original layout element count",
                        "Malformed commentary native layout key",
                        "Unbounded original native commentary entries",
                        "Unbounded distinct original commentary layout bodies",
                    }
                    print("Original layout census gate rejected key", ref,
                          "class", str(exc) if str(exc) in allowed else "UNKNOWN")
                    raise
                original_reference_triage.observe(kind, ref, raw)
                if kind == "U":
                    original_opaque_top_records.append(raw)
                if kind == "I":
                    if full_transport:
                        private_full_I[ref] = raw
                    if (ref in original_mixed_sample_set
                            or ref in {ch.rsplit(".",1)[0] for ch in original_mixed_sample_set}):
                        private_mixed_I[ref] = raw
                    if (osis_rebuild_preflight.intro_visible_cases
                            and osis_rebuild_preflight.intro_visible_cases[-1][
                                "original_native_intro_key"] == ref
                            and "." in ref):
                        private_intro_text_raw_by_chapter[ref] = raw
                    return
                if kind != "K":
                    return
                chapter = ref.rsplit(".", 1)[0]
                if chapter in original_mixed_sample_set:
                    private_mixed_K[chapter].append((ref, raw))
                if full_transport:
                    private_full_K[chapter].append((ref, raw))
                if chapter in private_intro_text_raw_by_chapter:
                    digest = sha256(raw).hexdigest()
                    private_numbered_bodies_for_intro_chapter[chapter].setdefault(
                        digest, (ref, raw)
                    )
                if ref.rsplit(".", 1)[0] in original_sample_chapter_set:
                    temporary_original_sample_raw.append((ref, raw))
                heading = heading_extent(raw)
                if (heading is not None
                        and heading[1] in ("comma", "discontinuous")
                        and heading[0][0] == int(ref.rsplit(".",1)[1])):
                    private_range_heading_raw[ref] = raw
                if heading is None and raw.strip():
                    unparsed += 1
                    private_unrecognized_raw[ref] = raw
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
        original_osis_rebuild_feasibility = osis_rebuild_preflight.report(
            expected_count=summary["all_actual_raw_entries_scanned"]
        )
        synthetic_opaque_top_comparison = None
        if synthetic_intro_native_stream is not None:
            if (not synthetic_intro_native_stream.is_file()
                    or synthetic_intro_native_stream.is_symlink()
                    or synthetic_intro_native_stream.stat().st_size > 16 * 1024 * 1024):
                raise PilotError("Unverified private synthetic introduction raw stream")
            synthetic_opaque = []
            def collect_synthetic(kind, key, raw):
                if kind == "U":
                    synthetic_opaque.append(raw)
            with synthetic_intro_native_stream.open("rb") as stream:
                parse_native_raw_corpus(stream, on_entry=collect_synthetic)
            synthetic_opaque_top_comparison = (
                compare_opaque_top_with_standard_compiler_fixture(
                    original_opaque_top_records, synthetic_opaque
                )
            )
        expected_raw = manifest.get("native_raw_corpus_sha256")
        actual_raw = summary["all_native_raw_entries_ordered_sha256"]
        if not expected_raw or expected_raw != actual_raw:
            raise PilotError("Original full native corpus hash drift")
        if set(records) - registry["verse_keys"]:
            raise PilotError("Stock native occupied key escaped independent versification registry")
        topology_review = editorial_topology.report(registry["chapter_maximums"])
        layout_review = layout_census.report()
        if (layout_review["original_native_K_seen"] != len(keys)
                or layout_review["original_native_I_seen"] != len(intros)
                or layout_review["original_native_TOP_seen"] != len(top)
                or layout_review["source_word_text_xml_and_targets_disclosed"]
                or layout_review["original_module_modified"]
                or layout_review["publication_authorized"]):
            raise PilotError("Full original layout census did not reconcile with native source")
        original_reference_review = original_reference_triage.report(
            canonical_verses=registry["verse_keys"],
            canonical_chapters=registry["chapter_maximums"],
        )
        if (original_reference_review["original_native_K_seen"] != len(keys)
                or original_reference_review["original_native_I_seen"] != len(intros)
                or original_reference_review["original_native_TOP_seen"] != len(top)
                or original_reference_review["publication_authorized"]
                or original_reference_review["original_reference_targets_or_prose_exported"]):
            raise PilotError("Original source reference registry census incomplete")
        if (topology_review["original_native_K_rows_seen"] != len(keys)
                or topology_review["original_native_I_rows_seen"] != len(intros)
                or topology_review["original_native_TOP_rows_seen"] != len(top)
                or not topology_review["all_original_native_K_rows_examined"]
                or topology_review["release_authorized"]):
            raise PilotError("Original editorial topology census does not match native source")
        intro_transport_probes = []
        for i, chapter in enumerate(intro_sample_chapters):
            original_intro_raw = private_intro_text_raw_by_chapter.get(chapter)
            if original_intro_raw is None:
                raise PilotError("Original text-bearing I entry is absent from chapter intro")
            subdir = directory / f"sample-original-intro-{i}"
            subdir.mkdir()
            intro_transport_probes.append(
                probe_original_intro_transport(
                    chapter, original_intro_raw,
                    scratch=subdir, native_raw_binary=raw_binary
                )
            )
        mixed_probes = []
        for i, chapter in enumerate(mixed_sample_chapters):
            book = chapter.rsplit(".", 1)[0]
            if (book not in private_mixed_I or chapter not in private_mixed_I
                    or not private_mixed_K[chapter]):
                raise PilotError("Mixed original chapter lacks verified book I, chapter I or occupied K")
            scratch = directory / f"sample-mixed-original-{i}"
            scratch.mkdir()
            mixed_probes.append(probe_original_mixed_transport(
                chapter, private_mixed_I[book], private_mixed_I[chapter],
                private_mixed_K[chapter],
                scratch=scratch, native_raw_binary=raw_binary
            ))
        full_probe = None
        if full_transport:
            full_dir = directory / "whole-original-private-transport"
            full_dir.mkdir()
            full_probe = probe_complete_original_transport(
                private_full_I, private_full_K, original_opaque_top_records,
                scratch=full_dir, native_raw_binary=raw_binary
            )
        sample_probe = None
        if original_sample_chapter_set:
            observed_sample_chapters = {
                ref.rsplit(".", 1)[0] for ref, _ in temporary_original_sample_raw
            }
            if observed_sample_chapters != original_sample_chapter_set:
                raise PilotError("Some requested real original commentary sample chapters have no native keys")
            sample_probe = isolated_osis2mod_original_sample_roundtrip(
                temporary_original_sample_raw, scratch=directory,
                native_raw_binary=raw_binary,
            )
        source_intro_chapter_text_reviews = [
            review_original_intro_against_numbered_chapter(
                chapter, raw,
                list(private_numbered_bodies_for_intro_chapter[chapter].values())
            )
            for chapter, raw in sorted(private_intro_text_raw_by_chapter.items())
        ]
        for row in source_intro_chapter_text_reviews:
            limit = registry["chapter_maximums"].get(row["original_native_intro_key"])
            if not isinstance(limit, int) or limit < 1:
                raise PilotError("Original intro chapter is outside native versification registry")
            row["registered_native_chapter_verse_limit"] = limit
            row["navigation_keys_not_originally_occupied_if_intro_is_approved_as_whole_chapter"] = (
                limit if row["numbered_keys_present_in_original_chapter"] == 0 else None
            )
            row["whole_chapter_authorial_scope_is_not_yet_approved"] = True
        # Check original SWORD's ACTUAL native link identity for every
        # adjacent occupied K pair. Raw XML equality is not independently
        # sufficient evidence that two authors' entries are one section.
        adjacency_run = subprocess.run(
            [str(index_binary), manifest["module_id"], "--adjacent-links"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=150, check=False
        )
        if adjacency_run.returncode or len(adjacency_run.stdout) > 12*1024*1024:
            raise PilotError("Original complete native section-link identity unavailable")
        native_section_boundaries = verify_original_native_adjacent_section_boundaries(
            adjacency_run.stdout,
            expected_module=manifest["module_id"],
            original_occupied_sha256={
                ref: row["sha256"] for ref,row in records.items()
            }
        )
        result = classify(records)
        index_preflight = triage_missing_native_section_links(
            occupied={key: entry["sha256"] for key, entry in records.items()},
            valid_verse_keys=registry["verse_keys"],
            source_heading_anomalies=result["anomalies"],
        )
        # Source corroboration must precede any proposed production-like build.
        provisional_preview = None
        reviewed_scope_plan = None
        unknown = audit_unrecognized_slots(records)
        if unknown["total"] != result["counts"]["no_recognized_heading"]:
            raise PilotError("Unrecognized heading count diverged from complete native inventory")
        paragraph_pilot_samples = []
        for requested in paragraph_pilot_keys:
            kind, key = requested.split(":", 1)
            raw = (private_full_I.get(key) if kind == "I"
                   else dict(private_full_K.get(key.rsplit(".", 1)[0], [])).get(key))
            if raw is None:
                raise PilotError("Requested exact original native paragraph pilot key missing")
            paragraph_pilot_samples.append((kind, key, raw))
        witness = compare_independent_thml_witness(
            manifest, result["start_anchored_section_map"],
            result["anomalies"], directory, unknown["case_rows"],
            registry, private_unrecognized_raw,
            original_chapter_intro_raw=private_intro_text_raw_by_chapter,
            original_range_stock_raw=private_range_heading_raw,
            original_reference_triage=original_reference_triage,
            paragraph_pilot_samples=paragraph_pilot_samples if paragraph_pilot_keys else None,
            original_native_section_spans={
                key: row["heading"][0]
                for key, row in records.items()
                if row["heading"] is not None
                and row["heading"][0][0] == int(key.rsplit(".", 1)[1])
            })
        # Review a proposed literal source erratum ONLY as a private in-memory
        # exact-byte reversible preview. The separately staged 0.1.1 package
        # below still uses all ORIGINAL stock entries, never these bytes.
        unapproved_literal_erratum_preflight = None
        unapproved_prose_erratum_preflight = None
        errata_path = (Path(__file__).resolve().parents[1] /
                       "config" / "commentary-intake" /
                       f"{resource_id}-proposed-literal-errata.json")
        if errata_path.is_file() and full_transport:
            if errata_path.is_symlink() or errata_path.stat().st_size > 128 * 1024:
                raise PilotError("Untrusted original commentary erratum review plan")
            proposed_errata = json.loads(errata_path.read_text(encoding="utf-8"))
            if (proposed_errata.get("schema_version") != 1
                    or proposed_errata.get("resource_id") != resource_id
                    or proposed_errata.get("source_module_id") != manifest["module_id"]
                    or proposed_errata.get("source_archive_sha256") != downloaded["sha256"]
                    or proposed_errata.get("independent_digital_witness_sha256")
                       != witness["witness_sha256"]
                    or proposed_errata.get("status")
                       != "PRIVATE_EDIT_COMPILATION_APPROVED_PUBLIC_RELEASE_NOT_AUTHORIZED"
                    or proposed_errata.get("release_authorized") is not False
                    or proposed_errata.get("source_text_changes_for_public_release_authorized") is not False
                    or proposed_errata.get("original_source_published_or_overwritten") is not False):
                raise PilotError("Source erratum review was not explicitly unapproved/pinned")
            proposals = proposed_errata.get("proposed_single_reference_changes")
            if not isinstance(proposals, list) or not 1 <= len(proposals) <= 16:
                raise PilotError("Unreviewed number of original commentary errata")
            source_cases = witness["independent_original_reversed_reference_witness"][
                "case_rows"]
            receipts = []
            used_original_keys = set()
            for row in proposals:
                key = row.get("original_native_entry")
                first = row.get("first_verse")
                old_end = row.get("original_end_verse")
                new_end = row.get("proposed_end_verse")
                if (not isinstance(key, str) or key in used_original_keys
                        or not isinstance(row.get("external_review_url"), str)
                        or not row["external_review_url"].startswith(
                            "https://github.com/icfmp/Bible-Resources/issues/")
                        or row.get("editorial_decision")
                           != "PRIVATE_COMPILATION_AND_TESTS_APPROVED_PUBLICATION_REQUIRES_SEPARATE_SIGNOFF"
                        or row.get("corroboration_class")
                           != "SAME_MALFORMED_CCEL_SCRIPREF_PLUS_VALID_CCEL_SCRIPREF_AND_ORIGINAL_NATIVE_SECTION_HEADING"):
                    raise PilotError("Original commentary source erratum plan is not source-reviewed")
                used_original_keys.add(key)
                support = [
                    case for case in source_cases
                    if case["original_native_entry"] == key
                    and case["candidate_end_verse_if_both_witnesses_agree"]
                        == int(new_end.rsplit(".", 1)[1])
                    and case["original_link_display_text_contains_reversed_numeric_span"]
                    and case["independent_source_same_reversed_numeric_label_present"]
                    and case["independent_source_same_bad_range_scripref_count"] >= 1
                    and case["independent_source_valid_range_scripref_matching_native_count"] >= 1
                    and case["original_native_numbered_heading_at_range_start_exists"]
                    and not case["editorial_approval"]
                ]
                if len(support) != 1:
                    raise PilotError("Source erratum proposed endpoint not independently corroborated")
                chapter = key.rsplit(".", 1)[0]
                original_raw = dict(private_full_K[chapter]).get(key)
                if (original_raw is None or sha256(original_raw).hexdigest() != records[key]["sha256"]
                        or row.get("original_raw_sha256") != records[key]["sha256"]):
                    raise PilotError("Exact pinned original native erratum record missing")
                _, receipt = preview_exact_reversible_commentary_reference_erratum(
                    original_raw, first_verse=first,
                    original_end_verse=old_end,
                    proposed_end_verse=new_end)
                if (not receipt["reverse_restores_exact_original_raw_bytes"]
                        or receipt["editorial_change_authorized"]
                        or receipt["release_authorized"]):
                    raise PilotError("Source erratum candidate does not preserve original bytes")
                linked_count=sum(entry["sha256"] == records[key]["sha256"]
                                 for entry in records.values())
                if linked_count != row.get("expected_original_linked_native_K_count"):
                    raise PilotError("Original linked source erratum group changed unexpectedly")
                receipts.append({
                    "original_native_entry": key,
                    "proposed_endpoint_corroborated_by_source_and_native": True,
                    "source_witness_is_citation_not_authorial_scope": True,
                    "native_existing_aliases_sharing_original_raw": linked_count,
                    **receipt,
                })

            # Independently reviewed *prose typo* candidates are a distinct
            # correction class from malformed scripture target endpoints.
            # This scope-neutral private receipt never changes compiled data.
            prose_proposals = proposed_errata.get("proposed_single_prose_changes", [])
            if (not isinstance(prose_proposals, list)
                    or len(prose_proposals) > 16):
                raise PilotError("Unbounded original source prose erratum proposals")
            prose_receipts = []
            seen_prose = set()
            for prose_case in prose_proposals:
                if not isinstance(prose_case, dict):
                    raise PilotError("Malformed original commentary prose erratum proposal")
                key = prose_case.get("original_native_entry")
                issue_url = prose_case.get("external_review_url")
                corroboration = prose_case.get("independent_edition_corrob_url")
                if (not isinstance(key, str) or not KEY.fullmatch(key)
                        or key in seen_prose
                        or key in used_original_keys
                        or not isinstance(issue_url, str)
                        or not issue_url.startswith(
                            "https://github.com/icfmp/Bible-Resources/issues/")
                        or not isinstance(corroboration, str)
                        or not corroboration.startswith("https://")
                        or prose_case.get("source_error_class")
                           != "MISSPELLED_PROPER_NAME_IN_AUTHORIAL_PROSE"
                        or prose_case.get("editorial_decision")
                           != "PRIVATE_REVERSIBLE_PREFLIGHT_ONLY_NOT_COMPILED"
                        or prose_case.get("public_release_authorized") is not False):
                    raise PilotError("Unreviewed original source prose correction request")
                seen_prose.add(key)
                source_fragment = dict(private_full_K.get(
                    key.rsplit(".", 1)[0], [])).get(key)
                if (source_fragment is None or key not in records
                        or sha256(source_fragment).hexdigest() != records[key]["sha256"]):
                    raise PilotError("Source prose erratum master not found in pinned native corpus")
                expected_hash = prose_case.get("original_raw_sha256")
                if expected_hash is not None and expected_hash != records[key]["sha256"]:
                    raise PilotError("Prose source correction has stale original SHA-256")
                _, text_receipt = preview_exact_reversible_commentary_prose_erratum(
                    source_fragment,
                    original_phrase=prose_case.get("original_phrase"),
                    corrected_phrase=prose_case.get("corrected_phrase"),
                )
                aliases = sum(
                    entry["sha256"] == records[key]["sha256"]
                    for entry in records.values()
                )
                expected_aliases = prose_case.get("expected_original_linked_native_K_count")
                if expected_aliases is not None and expected_aliases != aliases:
                    raise PilotError("Original prose master native linked occupancy changed")
                if (not text_receipt["reverse_restores_exact_original_raw_bytes"]
                        or text_receipt["release_authorized"]
                        or text_receipt["original_or_published_module_modified"]):
                    raise PilotError("Unapproved prose preview did not preserve original")
                prose_receipts.append({
                    "original_native_entry": key,
                    "original_linked_native_K_count": aliases,
                    "source_original_hash_pinned_in_plan": expected_hash is not None,
                    "source_native_alias_count_pinned_in_plan": expected_aliases is not None,
                    **text_receipt
                })
            if prose_receipts:
                unapproved_prose_erratum_preflight = {
                    "status": "PRIVATE_PROSE_ERRATUMS_REVERSIBLE_NOT_COMPILED",
                    "case_count": len(prose_receipts),
                    "case_rows": prose_receipts,
                    "exact_original_witness_zip_and_native_source_authenticated": True,
                    "candidate_is_only_an_unpublished_in_memory_preview": True,
                    "all_original_source_or_compiled_content_unchanged": True,
                    "source_words_xml_or_reference_targets_exported": False,
                    "public_release_authorized": False,
                }
            unapproved_literal_erratum_preflight = {
                "status": "PRIVATE_ORIGINAL_SOURCE_ERRATUM_PREVIEW_NOT_APPROVED_OR_COMPILED",
                "case_count": len(receipts),
                "case_rows": receipts,
                "all_original_K_I_TOP_entries_untouched": True,
                "public_or_private_staged_zcom_package_content_unchanged": True,
                "text_or_reference_values_exported": False,
                "publication_authorized": False,
            }
        review_path = (Path(__file__).resolve().parents[1] /
                       "config" / "commentary-intake" /
                       f"{resource_id}-reviewed-links.json")
        if review_path.is_file():
            if review_path.is_symlink() or review_path.stat().st_size > 128*1024:
                raise PilotError("Unbounded or unsafe original source-scope decision file")
            decisions = json.loads(review_path.read_text(encoding="utf-8"))
            reviewed_scope_plan = corroborate_reviewed_commentary_link_plan(
                review=decisions, resource_id=resource_id,
                original_archive_sha256=downloaded["sha256"],
                witness_sha256=witness["witness_sha256"],
                occupied={key:row["sha256"] for key,row in records.items()},
                valid_verse_keys=registry["verse_keys"],
                original_candidate_preflight=index_preflight,
                independent_leading_range_citations=
                    witness["independent_leading_range_citations"]
            )
        if provisional_range_preview:
            if reviewed_scope_plan is None:
                raise PilotError(
                    "Private index preview requires independently corroborated"
                    " editorial section-scope decision data")
            preview_dir = directory / "range-index-reviewed-private-not-release"
            preview_dir.mkdir()
            provisional_preview = probe_complete_original_transport(
                private_full_I, private_full_K, original_opaque_top_records,
                scratch=preview_dir, native_raw_binary=raw_binary,
                provisional_index_aliases=reviewed_scope_plan[
                    "new_native_aliases"],
                test_preview_in_xiphos=preview_real_xiphos,
                original_stock_sword_root=installed,
                original_stock_module_id=manifest["module_id"],
                native_index_binary=index_binary,
            )
            if not provisional_preview.get(
                    "full_original_K_I_U_native_entry_parity_proven"):
                raise PilotError("Cannot stage unverified source-preserving SWORD preview")
            meta_file=(Path(__file__).resolve().parents[1] /
                       "modules" / resource_id / "metadata.json")
            if not meta_file.is_file() or meta_file.is_symlink():
                raise PilotError("Curated versioned commentary metadata not found")
            if meta_file.stat().st_size>128*1024:
                raise PilotError("Oversize curated commentary source metadata")
            curated=json.loads(meta_file.read_text(encoding="utf-8"))
            if (curated.get("id")!=resource_id
                    or not isinstance(curated.get("sword_id"),str)
                    or not isinstance(curated.get("version"),str)
                    or not isinstance(curated.get("origin"), dict)
                    or not isinstance(curated["origin"].get("publisher"), str)
                    or not curated["origin"]["publisher"].strip()
                    or curated["origin"].get("url") != manifest["source_page_url"]
                    or downloaded["sha256"] not in
                       str(curated["origin"].get("source_revision", ""))
                    or not isinstance(curated.get("upstreams"), list)
                    or not any(isinstance(item, dict)
                               and item.get("module_id") == manifest["module_id"]
                               and item.get("last_integrated_version") == manifest["version"]
                               for item in curated["upstreams"])
                    or not isinstance(decisions.get("proposed_next_version"),str)
                    or decisions.get("package_staging_only") is not True):
                raise PilotError("Unreviewed original curated commentary version identity")
            original_conf=(meta_file.parent / "payload" / "mods.d" /
                           (curated["sword_id"].lower()+".conf"))
            if not original_conf.is_file() or original_conf.is_symlink():
                raise PilotError("Original curated module configuration is missing")
            package_staging=privately_stage_versioned_zcom_zip(
                compiler_root=preview_dir/"complete-original-private-candidate",
                compiled_module_id="BRIndexProbe",
                package_module_id=curated["sword_id"],
                previous_version=curated["version"],
                proposed_version=decisions["proposed_next_version"],
                published_conf_template=original_conf.read_bytes(),
                scratch=preview_dir,
                native_raw_binary=raw_binary,
                provisional_index_aliases=reviewed_scope_plan["new_native_aliases"],
                test_with_real_xiphos=preview_real_xiphos,
            )
            provisional_preview["private_versioned_package_install_not_released"]=package_staging
            if proposed_errata.get("private_revised_candidate_build_authorized") is True:
                if (proposed_errata.get("source_text_changes_for_public_release_authorized") is not False
                        or proposed_errata.get("release_authorized") is not False
                        or not isinstance(proposed_errata.get("private_revised_candidate_build_authorization"),dict)
                        or proposed_errata["private_revised_candidate_build_authorization"].get("scope")
                           != "private_compile_and_validate_only"
                        or proposed_errata["private_revised_candidate_build_authorization"].get("source")
                           != "project_owner_instruction"
                        or not isinstance(proposed_errata["private_revised_candidate_build_authorization"].get("decision_text"),str)
                        or not 2 <= len(proposed_errata["private_revised_candidate_build_authorization"]["decision_text"]) <= 200
                        or not isinstance(proposed_errata["private_revised_candidate_build_authorization"].get("recorded_date"),str)
                        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                            proposed_errata["private_revised_candidate_build_authorization"]["recorded_date"])
                        or proposed_errata["private_revised_candidate_build_authorization"].get("review_issue_url")
                           != proposals[0]["external_review_url"]
                        or any(proposed_errata["private_revised_candidate_build_authorization"].get(name) is not False
                               for name in ("merge_authorized", "public_release_authorized",
                                            "catalogue_update_authorized"))
                        or not isinstance(proposed_errata.get("private_revised_candidate_history_note"),str)
                        or len(proposals)!=1 or len(receipts)!=1
                        or receipts[0]["native_existing_aliases_sharing_original_raw"]
                           != proposals[0]["expected_original_linked_native_K_count"]):
                    raise PilotError("Owner did not separately authorize a bounded private text-change build")
                correction=proposals[0]
                revised_dir=directory/"single-source-erratum-revised-private"
                revised_dir.mkdir()
                private_corrected=probe_private_compiled_source_erratum(
                    original_intros=private_full_I,
                    original_numbered=private_full_K,
                    original_TOP=original_opaque_top_records,
                    original_master_key=correction["original_native_entry"],
                    first_verse=correction["first_verse"],
                    original_end_verse=correction["original_end_verse"],
                    proposed_end_verse=correction["proposed_end_verse"],
                    original_index_only_compiled_root=(
                        preview_dir/"complete-original-private-candidate"),
                    reviewed_aliases=reviewed_scope_plan["new_native_aliases"],
                    curated_module_id=curated["sword_id"],
                    curated_previous_version=curated["version"],
                    curated_proposed_version=decisions["proposed_next_version"],
                    original_curated_conf=original_conf.read_bytes(),
                    scratch=revised_dir,
                    native_raw_binary=raw_binary,
                    native_index_binary=index_binary,
                    history_note=proposed_errata["private_revised_candidate_history_note"],
                    source_provider=curated["origin"]["publisher"],
                )
                if (private_corrected["source_linked_original_verse_keys_changed"]
                        != correction["expected_original_linked_native_K_count"]
                        or private_corrected["original_raw_source_checksum"]
                           != correction["original_raw_sha256"]
                        or private_corrected["corrected_package_uploaded_or_distributed"]
                        or private_corrected["owner_publication_authorized"]):
                    raise PilotError("Source-corrected private package violated reviewed source boundaries")
                provisional_preview["private_source_edited_versioned_candidate_not_released"]=private_corrected
            provisional_preview["source_scope_corroborated_in_draft_only"] = True
            provisional_preview["source_scope_editorially_approved"] = False
            provisional_preview["preflight_candidate_section_count"] = (
                index_preflight["candidate_section_count"]
            )
            # The index-only *control* must not be confused with the
            # separately recompiled private source-corrected candidate.
            provisional_preview["index_only_control_source_content_edited"] = False
            provisional_preview["private_source_corrected_candidate_compiled"] = (
                "private_source_edited_versioned_candidate_not_released"
                in provisional_preview
            )
            provisional_preview["release_authorized"] = False
        chapter_source_cases = witness["independent_div2_chapter_body_review"]["case_rows"]
        chapter_intros = (
            {
                case["native_start"].rsplit(".",1)[0]:
                bool(_source_visible_text(
                    private_full_I[case["native_start"].rsplit(".",1)[0]]
                ).strip())
                for case in chapter_source_cases
                if case["native_start"].rsplit(".",1)[0] in private_full_I
            } if full_transport else None
        )
        chapter_navigation_review = triage_single_key_chapter_navigation(
            occupied={key: value["sha256"] for key,value in records.items()},
            chapter_verse_maximums=registry["chapter_maximums"],
            independent_chapter_cases=chapter_source_cases,
            original_chapter_intro_has_visible_prose=chapter_intros,
        )
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
            "original_osis_rebuild_structure_preflight": original_osis_rebuild_feasibility,
            "original_intro_visible_text_slot_concordance":
                source_intro_chapter_text_reviews,
            "synthetic_compiler_opaque_top_original_exact_byte_comparison":
                synthetic_opaque_top_comparison,
            "private_numbered_only_osis2mod_sample_roundtrip": sample_probe,
            "private_original_intro_only_osis2mod_sample_roundtrips":
                intro_transport_probes,
            "private_original_mixed_intro_and_numbered_osis2mod_roundtrips":
                mixed_probes,
            "private_complete_original_I_K_U_osis2mod_roundtrip":
                full_probe,
            "private_provisional_range_index_preview_not_approved":
                provisional_preview,
            "source_corroborated_reviewed_section_alias_plan_not_release_approved":
                reviewed_scope_plan,
            "native_rows_with_unrecognized_heading_or_xml": unparsed,
            **result,
            "explicit_heading_native_link_candidate_preflight": index_preflight,
            "complete_original_native_linked_section_boundary_review":
                native_section_boundaries,
            "single_key_chapter_navigation_source_review_not_approved":
                chapter_navigation_review,
            "unrecognized_native_slot_review": unknown,
            "independent_original_native_editorial_topology_triage": topology_review,
            "independent_original_native_layout_census": layout_review,
            "independent_original_native_reference_registry_triage": original_reference_review,
            "private_unapproved_original_literal_erratum_byte_preflight":
                unapproved_literal_erratum_preflight,
            "private_unapproved_original_prose_erratum_byte_preflight":
                unapproved_prose_erratum_preflight,
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
    parser.add_argument("--temporary-numbered-sample-chapters", nargs="*", default=[],
                        help="Read-only selected original chapters, temporary private OSIS conversion")
    parser.add_argument("--temporary-original-intro-sample-chapters", nargs="*", default=[],
                        help="Original I-only chapter tests in private isolated zCom candidates")
    parser.add_argument("--temporary-original-mixed-chapters", nargs="*", default=[],
                        help="Strict private mixed original book I, chapter I and K native OSIS roundtrips")
    parser.add_argument("--temporary-original-full-transport", action="store_true",
                        help="Attempt isolated whole-original I/K OSIS compile and independent TOP reconciliation")
    parser.add_argument("--temporary-source-paragraph-witness", nargs="*", default=[],
                        help="Bounded private independent ThML paragraph observations at original I:/K: native keys")
    parser.add_argument("--temporary-provisional-range-index-preview", action="store_true",
                        help="Experimentally compile heading-derived missing links; editorial approval explicitly absent")
    parser.add_argument("--temporary-preview-real-xiphos", action="store_true",
                        help="One bounded authentic Xiphos test of provisional alias samples, not edition approval")
    parser.add_argument("--synthetic-intro-native-stream", type=Path,
                        help="Optional invented standalone OSIS compilation raw stream, compare TOP bytes only")
    parser.add_argument("--native-index-binary", type=Path, required=True)
    parser.add_argument("--native-raw-binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(
            args.resource_id, args.native_index_binary, args.native_raw_binary,
            transport_sample_chapters=tuple(args.temporary_numbered_sample_chapters),
            synthetic_intro_native_stream=args.synthetic_intro_native_stream,
            intro_sample_chapters=tuple(args.temporary_original_intro_sample_chapters),
            mixed_sample_chapters=tuple(args.temporary_original_mixed_chapters),
            full_transport=args.temporary_original_full_transport,
            paragraph_pilot_keys=tuple(args.temporary_source_paragraph_witness),
            provisional_range_preview=args.temporary_provisional_range_index_preview,
            preview_real_xiphos=args.temporary_preview_real_xiphos
        )
        code = 0
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, RawCorpusError) as exc:
        # Only predeclared, source-neutral failure phrases may leave the
        # ephemeral runner; raw exception messages can include source text.
        public_safe = {
            "Original commentary block-ownership census incomplete",
            "Full original layout census did not reconcile with native source",
            "Original source visible word ownership mismatch",
            "Original commentary layout XML is unparseable",
            "Unbounded original layout element count",
            "Unbounded distinct original commentary layout bodies",
            "Unbounded original native commentary entries",
        }
        reason = str(exc) if str(exc) in public_safe else "OTHER_OR_PRIVATE_ERROR"
        result = {
            "status": "BLOCKED", "reason_class": type(exc).__name__,
            "reason_fixed_code": reason,
            "native_scan_completed": False, "original_sword_changed": False
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Commentary editorial section triage:", result["status"],
          "fixed-code", result.get("reason_fixed_code", "NONE"),
          "(metadata-only report; original text never logged)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
