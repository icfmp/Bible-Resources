#!/usr/bin/env python3
"""Compare every original ThML commentary reference START against stock SWORD keys.

Diagnostic-only: a populated native VerseKey is NOT proof of the same authored
section, and source range coverage is NOT proof of text being present/absent.
This tool never prints original commentary words, rewrites refs or publishes
third-party sources. Both originals are independently SHA-pinned.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

from commentary_intake import load_manifest
from commentary_xml_witness import (
    OSIS_LOC, WORK_REF, _parse_reference, _xml_witness_locations,
    xml_structure,
)
from commentary_native_inventory import MAX_OUTPUT, parse_index
from commentary_navigation_link_plan import parse_native_commentary_verse_registry, UnsafeCommentaryLinkPlan
from commentary_reference_registry_triage import classify_original_reference_target
from commentary_prose_cross_slot import strict_native_stock_plain_words
from commentary_text_delta import _contiguous_offset, _is_subsequence
from commentary_unresolved_lexical_triage import WORD, marked_word_token_indices
from commentary_native_raw_inventory import private_crosscheck
from sword_native_raw_corpus_inventory import parse_native_raw_corpus
from pilot_fetch import fetch, validate_url
from pilot_preflight import PilotError, inspect_archive

MAX_XML = 32 * 1024 * 1024
MAX_PRIVATE_MISSING_START_PROBES = 8
OSIS_VERSE = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$")


def _root_for_raw_xml(data: bytes):
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
        huge_tree=False, remove_blank_text=False, recover=False,
    )
    try:
        return etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError:
        raise PilotError("Unparseable original XML source; full reference audit blocked") from None


def _load_native_key_rows(output: bytes, module_id: str) -> tuple[dict, set[str], set[str]]:
    proof = parse_index(output, module_id)
    numbered = set()
    intros = set()
    for line in output.decode("ascii").splitlines()[1:-1]:
        kind, key = line.split("\t")
        if kind == "K":
            numbered.add(key)
        elif kind == "I":
            intros.add(key)
    if len(numbered) != proof["occupied_numbered_slots"] or len(intros) != proof["occupied_intro_slots"]:
        raise PilotError("Native occupied-key parser disagrees with independent proof")
    return proof, numbered, intros


def compare_anchors(original_xml: bytes, native_output: bytes, module_id: str,
                    probe_osis_keys: tuple[str, ...] = (),
                    native_registry: dict | None = None) -> dict:
    # Preflight entire XML, exact unchanged bytes, grammar and all source tags.
    xml_proof = xml_structure(original_xml)
    index_proof, native_verses, native_intros = _load_native_key_rows(native_output, module_id)
    if native_registry is not None:
        if (native_registry.get("module_id") != module_id
                or native_registry.get("versification") != index_proof["native_versification"]
                or not native_verses.issubset(native_registry["verse_keys"])):
            raise PilotError("Original stock key and versification registry disagree")
    root = _root_for_raw_xml(original_xml)
    registry_classes = Counter()
    registry_examples = []
    counts = Counter()
    hits = Counter()
    misses = Counter()
    samples = []
    unoccupied_range_end_samples = []
    same_ref_count = Counter()
    ref_hash = sha256()
    text_body_checked = False
    ranges = []
    source_books = set()
    source_work_ids = Counter()
    seen_markers = 0

    for node in root.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        seen_markers += 1
        original_ref = node.get("osisRef", "")
        ref_hash.update(original_ref.encode("utf-8") + b"\x00")
        kind, book = _parse_reference(original_ref)
        counts[kind] += 1
        if native_registry is not None:
            if not original_ref.startswith("Bible:"):
                canonical_class = "NON_BIBLE_WORK_OR_UNQUALIFIED_UNREVIEWED"
            else:
                canonical_class = classify_original_reference_target(
                    original_ref,
                    canonical_verses=native_registry["verse_keys"],
                    canonical_chapters=native_registry["chapter_maximums"],
                )
            registry_classes[canonical_class] += 1
            if (canonical_class in {
                    "SIMPLE_SINGLE_VERSE_NOT_IN_REGISTRY",
                    "SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY",
                    "SIMPLE_CHAPTER_NOT_IN_REGISTRY",
                    "REVERSED_SAME_CHAPTER_VERSE_RANGE",
                } and len(registry_examples) < 40):
                registry_examples.append({
                    "original_source_reference": original_ref[:160],
                    "canonical_class": canonical_class,
                    "not_automatically_an_authorial_text_loss": True,
                })
        if not book:
            misses["unreviewed_reference_syntax"] += 1
            continue
        source_books.add(book)
        work_match = WORK_REF.fullmatch(original_ref)
        if not work_match:
            raise PilotError("Ref accepted without work-qualified original reference")
        work_id, original_body = work_match.groups()
        source_work_ids[work_id] += 1
        start, *end = original_body.split("-")
        start_match = OSIS_LOC.fullmatch(start)
        if not start_match:
            raise PilotError("Previously accepted ThML start key no longer parses")
        if kind == "work_qualified_chapter":
            is_exact = start in native_intros
            # SWORD book/chapter introduction spellings may differ. Report
            # alternative grammar for separate review, NEVER assert parity.
            convention_variant = start + ".0" in native_intros
        else:
            is_exact = start in native_verses
            convention_variant = False
        if is_exact:
            hits[kind] += 1
        else:
            misses[kind] += 1
            if len(samples) < 12:
                samples.append({
                    "original_work_qualified_reference": original_ref[:120],
                    "start_key": start, "chapter_intro_spelling_variant_present": convention_variant,
                    "diagnostic": "stock_native_start_not_occupied_not_automatic_content_loss",
                })
        same_ref_count[original_ref] += 1
        if kind == "work_qualified_same_book_verse_range":
            end_key = end[0]
            end_match = OSIS_LOC.fullmatch(end_key)
            if end_match is None or start_match.group(1) != end_match.group(1):
                raise PilotError("Previously accepted in-book source range lost endpoint")
            if end_key in native_verses:
                hits["range_last_native_slot"] += 1
            else:
                misses["range_last_native_slot"] += 1
                if len(unoccupied_range_end_samples) < 12:
                    unoccupied_range_end_samples.append({
                        "original_work_qualified_reference": original_ref[:120],
                        "start_key": start,
                        "end_key": end_key,
                        "diagnostic":
                            "stock_native_range_end_not_occupied_not_automatic_text_loss",
                    })
            ranges.append((start_match.group(1),
                           (int(start_match.group(2)), int(start_match.group(3))),
                           (int(end_match.group(2)), int(end_match.group(3)))))

    if seen_markers != xml_proof["element_counts"].get("scripCom", 0):
        raise PilotError("Annotation inventory omitted original XML markers")
    if seen_markers != sum(counts.values()):
        raise PilotError("Annotation counts inconsistent with XML marker total")
    if ref_hash.hexdigest() != xml_proof["candidate_commentary_reference_ordered_sha256"]:
        raise PilotError("Independent original reference-order digest differs")
    known_probes = {}
    for probe in probe_osis_keys:
        if not OSIS_VERSE.fullmatch(probe):
            raise PilotError("Invalid or unreviewed explicit OSIS probe reference")
        book, chapter, verse = probe.split(".")
        position = (int(chapter), int(verse))
        known_probes[probe] = {
            "native_occupied_exact_key": probe in native_verses,
            "source_explicit_verse_range_containing_probe": sum(
                candidate_book == book and start <= position <= end
                for candidate_book, start, end in ranges
            ),
            "chapter_or_book_intro_not_assumed_to_cover_probe": True,
            "no_entry_text_content_compared": True,
        }
    return {
        "schema_version": 1,
        "status": "read_only_source_to_native_anchor_diagnostics_not_textual_parity",
        "source_xml_sha256": xml_proof["xml_sha256"],
        "source_marker_count": seen_markers,
        "source_annotation_reference_ordered_sha256": ref_hash.hexdigest(),
        "source_annotation_classes": dict(sorted(counts.items())),
        "original_native_versification_registry_checked": native_registry is not None,
        "original_reference_registry_classes": dict(sorted(registry_classes.items())),
        "bounded_original_out_of_registry_reference_examples": registry_examples,
        "canonical_validity_does_not_prove_semantic_passage_correctness": True,
        "source_work_id_counts": dict(sorted(source_work_ids.items())),
        "source_book_count": len(source_books),
        "source_books_with_explicit_markers": sorted(source_books),
        "native_occupied_verse_count": index_proof["occupied_numbered_slots"],
        "native_occupied_intro_count": index_proof["occupied_intro_slots"],
        "native_occupied_key_ordered_sha256": index_proof["ordered_occupied_key_sha256"],
        "matched_exact_start_by_class": dict(sorted(hits.items())),
        "unoccupied_source_start_by_class": dict(sorted(misses.items())),
        "bounded_unoccupied_start_references": samples,
        "bounded_unoccupied_range_end_references": unoccupied_range_end_samples,
        "distinct_original_anchors": len(same_ref_count),
        "duplicate_exact_ref_appearances": sum(v-1 for v in same_ref_count.values()),
        "source_books_missing_from_stock": sorted(source_books - set(index_proof["occupied_slots_by_book"])),
        "stock_books_without_explicit_source_scripCom_markers": sorted(
            set(index_proof["occupied_slots_by_book"]) - source_books
        ),
        "lack_of_source_marker_is_not_proof_of_missing_book_text": True,
        "explicit_verse_probes": known_probes,
        "section_range_boundaries_verified": False,
        "authored_source_to_compiled_text_parity": text_body_checked,
        "authorial_notes_headings_and_paragraphs_checked": False,
        "independent_authorial_edition_approved": False,
        "source_text_rewritten": False,
        "published": False,
    }


def _original_unoccupied_source_units(
        original_xml: bytes, *, volume: int, missing: list[dict],
        canonical_verses: set[str]) -> list[dict]:
    """Take only real CCEL bodies with *valid* start refs absent in native keys.

    No independently authored word or body leaves the private inspector; each
    case receives a fixed set of source-word windows for location evidence.
    A match cannot establish the full section or reference indexing is correct.
    """
    wanted = {
        item["original_work_qualified_reference"]: item["start_key"]
        for item in missing if item["start_key"] in canonical_verses
    }
    if not wanted:
        return []
    root = _root_for_raw_xml(original_xml)
    cases = []
    for node in root.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        reference = node.get("osisRef", "")
        if reference not in wanted:
            continue
        body = node.getnext()
        if (body is None or not isinstance(body.tag, str)
                or body.tag.rsplit("}", 1)[-1] != "div"
                or (node.tail and node.tail.strip())):
            raise PilotError("Unoccupied original source reference lacks adjacent authored div")
        source_text = "".join(body.itertext())
        if not source_text.strip() or len(source_text) > 2_000_000:
            raise PilotError("Unreviewed original source unit size or content")
        full_words = WORD.findall(source_text)
        linked = set(marked_word_token_indices(body, "scripRef", source_text))
        if any(type(i) is not int or i < 0 or i >= len(full_words) for i in linked):
            raise PilotError("Original source scripture-link word masking is inconsistent")
        words = [word for i, word in enumerate(full_words) if i not in linked]
        size = 12
        windows = []
        if len(words) >= size:
            last = len(words) - size
            for numerator in (0, 1, 2, 3, 4):
                part = words[(last*numerator)//4:(last*numerator)//4 + size]
                if part not in windows:
                    windows.append(part)
        cases.append({
            "reference": reference, "start_key": wanted[reference],
            "volume": volume, "original_source_line": node.sourceline,
            "original_body_sha256": sha256(source_text.encode("utf-8")).hexdigest(),
            "original_plain_word_count": len(words),
            "private_original_plain_words": words, "private_windows": windows,
        })
    if len(cases) != len(wanted):
        raise PilotError("Ambiguous or missing authorial body for unoccupied source start")
    return cases


class UnoccupiedSourceProseLocator:
    """Read-only K/I native candidate locator; only hashed/closed metadata escapes."""

    def __init__(self, units: list[dict]):
        if not 1 <= len(units) <= MAX_PRIVATE_MISSING_START_PROBES:
            raise PilotError("Unbounded original unoccupied-start lexical probe")
        self.units = units
        self.by_book = defaultdict(list)
        self.scanned = Counter()
        self.hits = defaultdict(list)
        for unit in units:
            if not OSIS_VERSE.fullmatch(unit["start_key"]):
                raise PilotError("Unreviewed source missing-start reference")
            self.by_book[unit["start_key"].split(".", 1)[0]].append(unit)

    @staticmethod
    def _scope(kind: str, key: str, original: str) -> str | None:
        book = original.split(".", 1)[0]
        chapter = original.rsplit(".", 1)[0]
        if kind == "K" and key.startswith(chapter + "."):
            return "other_numbered_key_same_chapter"
        if kind == "I" and key in (chapter, chapter + ".0"):
            return "same_chapter_intro"
        if kind == "I" and key in (book, book + ".0.0"):
            return "book_intro"
        return None

    def observe(self, kind: str, key: str, raw: bytes):
        if kind not in ("K", "I"):
            return
        book = key.split(".", 1)[0]
        candidates = []
        for unit in self.by_book.get(book, []):
            scope = self._scope(kind, key, unit["start_key"])
            if scope:
                candidates.append((unit, scope))
        if not candidates:
            return
        words = strict_native_stock_plain_words(raw)
        digest = sha256(raw).hexdigest()
        for unit, scope in candidates:
            self.scanned[(unit["start_key"], scope)] += 1
            if not unit["private_windows"]:
                continue
            found = sum(_contiguous_offset(sample, words) is not None
                        for sample in unit["private_windows"])
            if found:
                all_in_order = _is_subsequence(unit["private_original_plain_words"], words)
                full_span = _contiguous_offset(
                    unit["private_original_plain_words"], words) is not None
                if full_span and not all_in_order:
                    raise PilotError("Original complete contiguous prose contradicts word-order check")
                self.hits[unit["start_key"]].append({
                    "original_stock_native_key": key,
                    "native_slot_kind": kind,
                    "scope": scope,
                    "stock_raw_sha256": digest,
                    "matched_distinct_original_plain_word_windows": found,
                    "all_original_plain_words_found_in_stock_order": all_in_order,
                    "all_original_plain_words_found_as_contiguous_stock_run": full_span,
                    "total_original_windows": len(unit["private_windows"]),
                })

    def report(self) -> dict:
        rows = []
        for unit in self.units:
            original = unit["start_key"]
            scores = self.hits.get(original, [])
            best = sorted(
                scores, key=lambda x: (
                    -int(x["all_original_plain_words_found_in_stock_order"]),
                    -int(x["all_original_plain_words_found_as_contiguous_stock_run"]),
                    -x["matched_distinct_original_plain_word_windows"],
                    {"other_numbered_key_same_chapter": 0,
                     "same_chapter_intro": 1, "book_intro": 2}[x["scope"]],
                    x["original_stock_native_key"]),
            )
            rows.append({
                "original_source_reference": unit["reference"],
                "source_volume": unit["volume"],
                "source_line": unit["original_source_line"],
                "source_original_body_sha256": unit["original_body_sha256"],
                "source_plain_words_excluding_link_labels": unit["original_plain_word_count"],
                "source_probe_window_count": len(unit["private_windows"]),
                "scanned_native_candidate_count": sum(
                    count for (key, scope), count in self.scanned.items()
                    if key == original),
                "native_candidate_slots_with_any_exact_plain_word_window": len(scores),
                "native_candidate_slots_containing_all_original_words_in_order": sum(
                    int(x["all_original_plain_words_found_in_stock_order"]) for x in scores),
                "native_candidate_slots_containing_all_original_words_contiguously": sum(
                    int(x["all_original_plain_words_found_as_contiguous_stock_run"]) for x in scores),
                "bounded_matching_native_candidates": best[:8],
                "no_match_is_not_proof_of_missing_authorial_text": True,
                "matching_windows_are_not_full_text_or_section_parity": True,
            })
        return {
            "status": "bounded_original_source_prose_location_not_text_parity",
            "original_valid_unoccupied_start_units_checked": len(self.units),
            "units": rows,
            "other_chapters_and_other_books_not_searched": True,
            "exact_original_words_and_raw_bytes_never_disclosed": True,
            "source_or_native_bytes_changed": False,
            "published": False,
        }


def summarize_volume_anchor_results(volumes: list[dict]) -> dict:
    """Aggregate reviewed source-volume diagnostics without merging authorial units.

    Each original volume retains its own exact source SHA and anchor evidence.
    Aggregate counts are only source-marker *appearances*, never independent
    commentary entries or proof that the source and native text match.
    """
    if not volumes or len(volumes) > 12:
        raise PilotError("Unreviewed source-volume count")
    seen_volumes = set()
    expected_native = None
    combined_classes = Counter()
    combined_hits = Counter()
    combined_misses = Counter()
    all_source_books = set()
    missing_books = set()
    samples = []
    end_samples = []
    total_markers = 0
    total_duplicate_within_volume = 0
    all_registry_classes = Counter()
    all_registry_examples = []
    native_registry_checked = None
    for volume in volumes:
        number = volume.get("volume")
        report = volume.get("anchor_diagnostic")
        if (type(number) is not int or number < 1 or number > 12
                or number in seen_volumes or not isinstance(report, dict)
                or report.get("status")
                    != "read_only_source_to_native_anchor_diagnostics_not_textual_parity"):
            raise PilotError("Unreviewed CCEL volume anchor diagnostic")
        seen_volumes.add(number)
        identity = (
            report["native_occupied_key_ordered_sha256"],
            report["native_occupied_verse_count"],
            report["native_occupied_intro_count"],
        )
        if expected_native is None:
            expected_native = identity
        elif identity != expected_native:
            raise PilotError("Volume comparisons disagree on stock native keys")
        observed = report["source_marker_count"]
        categories = Counter(report["source_annotation_classes"])
        if observed != sum(categories.values()):
            raise PilotError("Unreconciled source annotation categories")
        total_markers += observed
        combined_classes.update(categories)
        checked = report["original_native_versification_registry_checked"]
        if native_registry_checked is None:
            native_registry_checked = checked
        elif native_registry_checked != checked:
            raise PilotError("Mixed original verse-registry review states across source volumes")
        registry_classes = Counter(report["original_reference_registry_classes"])
        if checked and sum(registry_classes.values()) != observed:
            raise PilotError("Original reference-to-verse registry census is incomplete")
        all_registry_classes.update(registry_classes)
        for example in report["bounded_original_out_of_registry_reference_examples"]:
            if len(all_registry_examples) < 40:
                all_registry_examples.append({"volume": number, **example})
        combined_hits.update(report["matched_exact_start_by_class"])
        combined_misses.update(report["unoccupied_source_start_by_class"])
        all_source_books.update(report["source_books_with_explicit_markers"])
        missing_books.update(report["source_books_missing_from_stock"])
        total_duplicate_within_volume += report["duplicate_exact_ref_appearances"]
        for item in report["bounded_unoccupied_start_references"]:
            if len(samples) >= 24:
                break
            samples.append({"volume": number, **item})
        for item in report["bounded_unoccupied_range_end_references"]:
            if len(end_samples) >= 24:
                break
            end_samples.append({"volume": number, **item})
    if [row["volume"] for row in volumes] != sorted(seen_volumes):
        raise PilotError("CCEL volumes must remain in original declared order")
    return {
        "status": "ordered_original_xml_volume_anchor_diagnostics_not_parity",
        "original_xml_volume_count": len(volumes),
        "source_annotation_markers_across_volumes": total_markers,
        "source_annotation_classes_across_volumes": dict(sorted(combined_classes.items())),
        "original_native_versification_registry_checked": bool(native_registry_checked),
        "original_reference_registry_classes_across_volumes": dict(sorted(all_registry_classes.items())),
        "bounded_original_out_of_registry_reference_examples": all_registry_examples,
        "canonical_validity_does_not_prove_semantic_passage_correctness": True,
        "matched_stock_start_by_class_across_volumes": dict(sorted(combined_hits.items())),
        "unoccupied_stock_start_by_class_across_volumes": dict(sorted(combined_misses.items())),
        "source_books_with_explicit_markers_across_volumes": sorted(all_source_books),
        "source_books_without_any_occupied_stock_native_slots": sorted(missing_books),
        "duplicate_exact_references_within_each_source_volume": total_duplicate_within_volume,
        "cross_volume_identical_reference_identity_not_established": True,
        "bounded_source_start_mismatch_examples": samples,
        "bounded_source_range_end_mismatch_examples": end_samples,
        "stock_native_key_ordered_sha256": expected_native[0],
        "stock_native_occupied_numbered_count": expected_native[1],
        "stock_native_occupied_intro_count": expected_native[2],
        "volume_observations": volumes,
        "no_authorial_section_identity_inferred_from_key_count": True,
        "full_verse_range_link_coverage_not_verified": True,
        "authored_source_to_compiled_text_parity": False,
        "source_paragraph_or_quote_structure_compared": False,
        "source_bytes_changed": False,
        "rights_release_and_derivative_approval": False,
        "published": False,
    }


def run(resource_id: str, inspector: Path, probes: tuple[str, ...],
        *, raw_binary: Path | None = None) -> dict:
    manifest = load_manifest(resource_id)
    locations, is_collection = _xml_witness_locations(
        manifest.get("commentary_source"))
    expected_sword = manifest.get("archive_sha256")
    if (not isinstance(expected_sword, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sword)
            or any(not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{64}", pin)
                   for _, _, pin in locations)):
        raise PilotError("Stock SWORD and each original XML volume must be SHA-256 pinned")
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Reviewed native commentary inspector executable unavailable")
    if raw_binary is not None and (not raw_binary.is_file() or raw_binary.is_symlink()):
        raise PilotError("Reviewed native raw original commentary reader unavailable")

    with tempfile.TemporaryDirectory(prefix="commentary-source-native-") as temp:
        root = Path(temp)
        original_path = root / "sword.zip"
        sword_receipt = fetch(
            manifest["sword_zip_url"], original_path, manifest["provider"])
        if sword_receipt["sha256"] != expected_sword:
            raise PilotError("Pinned original stock SWORD archive changed; refuse comparison")
        stock = inspect_archive(original_path, source_kind="sword",
                                expected_module_id=manifest["module_id"],
                                expected_category="commentary")
        conf = stock["sword_conf"]
        if conf["version"] != manifest["version"] or conf["language"] != manifest["language"]:
            raise PilotError("Original stock SWORD module ID/version/language mismatch")
        installed = root / "installed"
        installed.mkdir()
        with zipfile.ZipFile(original_path) as archive:
            for member in stock["members"]:
                path = installed / PurePosixPath(member["name"])
                if not path.resolve().is_relative_to(installed.resolve()):
                    raise PilotError("Unsafe original SWORD archive member path")
                path.parent.mkdir(parents=True, exist_ok=True)
                if not member["name"].endswith("/"):
                    with archive.open(member["name"]) as src, path.open("xb") as dst:
                        shutil.copyfileobj(src, dst, length=256*1024)
        try:
            result = subprocess.run([str(inspector), manifest["module_id"]],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    timeout=55, env=dict(os.environ, SWORD_PATH=str(installed)),
                                    check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Trusted native commentary scan exceeded time bound") from None
        if result.returncode or len(result.stdout) > MAX_OUTPUT:
            raise PilotError("Trusted native commentary inventory failed or exceeded output bound")

        try:
            registry_output = subprocess.run(
                [str(inspector), manifest["module_id"], "--chapter-registry"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=55, env=dict(os.environ, SWORD_PATH=str(installed)),
                check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Original native KJV verse registry exceeded time bound") from None
        if registry_output.returncode:
            raise PilotError("Original native KJV verse registry unavailable")
        try:
            source_registry = parse_native_commentary_verse_registry(
                registry_output.stdout, manifest["module_id"])
        except UnsafeCommentaryLinkPlan:
            raise PilotError("Original module verse registry framing was invalid") from None
        if (source_registry["versification"] != (conf["versification"] or "KJV")
                or source_registry["driver"] != conf["driver"]):
            raise PilotError("Original stock KJV registry disagrees with pinned .conf")

        source_reports = []
        unoccupied_original_units = []
        for number, xml_url, expected_xml in locations:
            xml_path = root / f"original-volume-{number}.xml"
            xml_receipt = fetch(xml_url, xml_path, "ccel")
            if xml_receipt["sha256"] != expected_xml:
                raise PilotError("Pinned original XML witness changed; refuse comparison")
            if xml_receipt["bytes"] > MAX_XML:
                raise PilotError("Original XML exceeds source-audit safety bound")
            source_xml = xml_path.read_bytes()
            comparison = compare_anchors(source_xml, result.stdout,
                                         manifest["module_id"],
                                         probe_osis_keys=probes,
                                         native_registry=source_registry)
            if comparison["source_xml_sha256"] != xml_receipt["sha256"]:
                raise PilotError("Original source bytes changed during readback")
            if raw_binary is not None:
                unoccupied_original_units.extend(_original_unoccupied_source_units(
                    source_xml, volume=number,
                    missing=comparison["bounded_unoccupied_start_references"],
                    canonical_verses=source_registry["verse_keys"],
                ))
            source_reports.append({
                "volume": number,
                "original_ccel_xml_sha256": xml_receipt["sha256"],
                "anchor_diagnostic": comparison,
            })
        if is_collection:
            observed = summarize_volume_anchor_results(source_reports)
            observed.update({
                "schema_version": 1, "resource_id": resource_id,
                "stock_sword_archive_sha256": sword_receipt["sha256"],
                "original_sword_conf_sha256": conf["conf_sha256"],
                "source_and_sword_bytes_remain_temporary": True,
            })
        else:
            observed = source_reports[0]["anchor_diagnostic"]
            observed.update({
                "resource_id": resource_id,
                "stock_sword_archive_sha256": sword_receipt["sha256"],
                "original_ccel_xml_sha256": source_reports[0]["original_ccel_xml_sha256"],
                "original_sword_conf_sha256": conf["conf_sha256"],
                "source_and_sword_bytes_remain_temporary": True,
                "rights_release_and_derivative_approval": False,
            })
        if raw_binary is not None:
            if len(unoccupied_original_units) > MAX_PRIVATE_MISSING_START_PROBES:
                observed["original_unoccupied_start_prose_location"] = {
                    "status": "more_than_reviewed_probe_budget_not_scanned",
                    "valid_source_start_units": len(unoccupied_original_units),
                    "not_proof_of_missing_authorial_text": True,
                }
            elif not unoccupied_original_units:
                observed["original_unoccupied_start_prose_location"] = {
                    "status": "no_canonically_valid_unoccupied_source_starts_to_scan",
                    "original_source_or_sword_bytes_modified": False,
                }
            else:
                locator = UnoccupiedSourceProseLocator(unoccupied_original_units)
                env = dict(os.environ, SWORD_PATH=str(installed))
                process = None
                rows = []
                try:
                    process = subprocess.Popen(
                        ["timeout", "360s", str(raw_binary), manifest["module_id"]],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
                    if process.stdout is None:
                        raise PilotError("Private original stock raw stream not available")
                    def inspect_one(kind, key, raw):
                        rows.append((kind, key))
                        locator.observe(kind, key, raw)
                    raw_stats, _, _, _ = parse_native_raw_corpus(
                        process.stdout, on_entry=inspect_one)
                    process.stdout.close()
                    if process.wait(timeout=15):
                        raise PilotError("Original raw SWORD reader stopped before complete scan")
                except BaseException:
                    if process is not None and process.poll() is None:
                        process.kill()
                        process.wait()
                    raise
                crosscheck = private_crosscheck(
                    result.stdout, manifest["module_id"], rows, raw_stats)
                if crosscheck["native_versification"] != source_registry["versification"]:
                    raise PilotError("Original raw SWORD verse registry changed")
                if (manifest.get("native_raw_corpus_sha256")
                        and raw_stats["all_native_raw_entries_ordered_sha256"]
                           != manifest["native_raw_corpus_sha256"]):
                    raise PilotError("Original pinned complete stock raw corpus changed")
                observed["original_unoccupied_start_prose_location"] = {
                    **locator.report(),
                    "pinned_original_stock_raw_corpus_sha256":
                        raw_stats["all_native_raw_entries_ordered_sha256"],
                    "fully_crosschecked_original_native_corpus": True,
                }
        else:
            observed["original_unoccupied_start_prose_location"] = {
                "status": "raw_text_location_not_attempted",
                "not_proof_of_missing_authorial_text": True,
            }
        return observed


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--native-inspector", type=Path, required=True)
    p.add_argument("--native-raw-binary", type=Path)
    p.add_argument("--probe-osis-key", action="append", default=[])
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        report = run(args.resource_id, args.native_inspector, tuple(args.probe_osis_key),
                     raw_binary=args.native_raw_binary)
        code = 0
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        report = {
            "status": "blocked", "resource_id": args.resource_id, "reason": str(exc),
            "authored_source_to_compiled_text_parity": False, "published": False,
        }
        code = 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Source / stock SWORD anchor diagnostic: " + report["status"] + " (no commentary text logged)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
