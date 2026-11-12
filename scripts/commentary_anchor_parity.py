#!/usr/bin/env python3
"""Compare every original ThML commentary reference START against stock SWORD keys.

Diagnostic-only: a populated native VerseKey is NOT proof of the same authored
section, and source range coverage is NOT proof of text being present/absent.
This tool never prints original commentary words, rewrites refs or publishes
third-party sources. Both originals are independently SHA-pinned.
"""
from __future__ import annotations

import argparse
from collections import Counter
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
    OSIS_LOC, WORK_REF, _parse_reference, xml_structure,
)
from commentary_native_inventory import MAX_OUTPUT, parse_index
from pilot_fetch import fetch, validate_url
from pilot_preflight import PilotError, inspect_archive

MAX_XML = 32 * 1024 * 1024
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
                    probe_osis_keys: tuple[str, ...] = ()) -> dict:
    # Preflight entire XML, exact unchanged bytes, grammar and all source tags.
    xml_proof = xml_structure(original_xml)
    index_proof, native_verses, native_intros = _load_native_key_rows(native_output, module_id)
    root = _root_for_raw_xml(original_xml)
    counts = Counter()
    hits = Counter()
    misses = Counter()
    samples = []
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
        "source_work_id_counts": dict(sorted(source_work_ids.items())),
        "source_book_count": len(source_books),
        "native_occupied_verse_count": index_proof["occupied_numbered_slots"],
        "native_occupied_intro_count": index_proof["occupied_intro_slots"],
        "native_occupied_key_ordered_sha256": index_proof["ordered_occupied_key_sha256"],
        "matched_exact_start_by_class": dict(sorted(hits.items())),
        "unoccupied_source_start_by_class": dict(sorted(misses.items())),
        "bounded_unoccupied_start_references": samples,
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


def run(resource_id: str, inspector: Path, probes: tuple[str, ...]) -> dict:
    manifest = load_manifest(resource_id)
    record = manifest.get("commentary_source", {})
    xml_url = record.get("xml_witness_url")
    expected_xml = record.get("xml_witness_sha256")
    expected_sword = manifest.get("archive_sha256")
    if not all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x)
               for x in (expected_xml, expected_sword)):
        raise PilotError("Both original XML and stock SWORD archive must be SHA-256 pinned")
    if not isinstance(xml_url, str) or not xml_url.startswith("https://www.ccel.org/ccel/h/"):
        raise PilotError("Unreviewed original XML source URL")
    validate_url(xml_url, "ccel")
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Reviewed native commentary inspector executable unavailable")

    with tempfile.TemporaryDirectory(prefix="commentary-source-native-") as temp:
        root = Path(temp)
        xml_path = root / "source.xml"
        original_path = root / "sword.zip"
        xml_receipt = fetch(xml_url, xml_path, "ccel")
        sword_receipt = fetch(manifest["sword_zip_url"], original_path, manifest["provider"])
        if xml_receipt["sha256"] != expected_xml or sword_receipt["sha256"] != expected_sword:
            raise PilotError("Pinned original XML or stock SWORD archive changed; refuse comparison")
        if xml_receipt["bytes"] > MAX_XML:
            raise PilotError("Original XML exceeds source-audit safety bound")
        stock = inspect_archive(original_path, source_kind="sword",
                                expected_module_id=manifest["module_id"],
                                expected_category="commentary")
        conf = stock["sword_conf"]
        if conf["version"] != manifest["version"] or conf["language"] != manifest["language"]:
            raise PilotError("Original stock SWORD module ID/version/language mismatch")
        installed = root / "installed"
        installed.mkdir()
        with zipfile.ZipFile(original_path) as archive:
            for record in stock["members"]:
                path = installed / PurePosixPath(record["name"])
                if not path.resolve().is_relative_to(installed.resolve()):
                    raise PilotError("Unsafe original SWORD archive member path")
                path.parent.mkdir(parents=True, exist_ok=True)
                if not record["name"].endswith("/"):
                    with archive.open(record["name"]) as src, path.open("xb") as dst:
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
        comparison = compare_anchors(xml_path.read_bytes(), result.stdout,
                                     manifest["module_id"], probe_osis_keys=probes)
        comparison.update({
            "resource_id": resource_id,
            "stock_sword_archive_sha256": sword_receipt["sha256"],
            "original_ccel_xml_sha256": xml_receipt["sha256"],
            "original_sword_conf_sha256": conf["conf_sha256"],
            "source_and_sword_bytes_remain_temporary": True,
            "rights_release_and_derivative_approval": False,
        })
        return comparison


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--native-inspector", type=Path, required=True)
    p.add_argument("--probe-osis-key", action="append", default=[])
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        report = run(args.resource_id, args.native_inspector, tuple(args.probe_osis_key))
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
