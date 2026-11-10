#!/usr/bin/env python3
"""Private original-USFX vs actual stock-SWORD whole-corpus main-text diagnostic.

The publisher's original USFX and SWORD ZIPs are read independently.
Text/notes are processed ONLY inside Python memory; JSON contains hashes,
counts and key IDs, never Scripture. This is NOT a notes/layout, conversion,
source-edition identity, rights, or publication certificate.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
import unicodedata

from lxml import etree

from lsg_source_compare import read_source_xml, scan_usfx
from real_second_bible_probe import _safe_single_module
from source_native_scope import read_crosswalk
from stable_sword_refs import module_payload_digest
from sword_native_raw_corpus_inventory import (
    inspect_native_raw_corpus, write_new_metadata_report,
)

MAX_XML = 128 * 1024 * 1024
MAX_VERSE = 2 * 1024 * 1024
MAX_MISMATCHES = 25
USFX_NOTE = {"f", "fe", "x", "note"}
USFX_HEAD = {"s", "s1", "s2", "s3", "s4", "ms", "ms1", "ms2",
             "mt", "mt1", "mt2", "mr", "d", "cl", "r", "rem"}
NATIVE_SKIP = {"note", "title"}
WORD = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)
USFM_ID = re.compile(r"^[1-4]?[A-Z][A-Z0-9]{1,4}$")


class MainTextParityError(ValueError):
    """Authored or native text could not be independently audited."""


def _tree(data: bytes, root_name: str):
    if not 0 < len(data) <= MAX_XML:
        raise MainTextParityError("Empty or oversized original XML")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        tree = etree.ElementTree(etree.fromstring(data, parser))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise MainTextParityError("Unparseable original source XML") from exc
    if (tree.docinfo.doctype or tree.docinfo.internalDTD
            or tree.docinfo.externalDTD or tree.getroot().tag != root_name):
        raise MainTextParityError("Unexpected source XML root or DTD")
    return tree.getroot()


def authored_usfx_main_text(xml: bytes, mapping: list[tuple[str, str]]):
    """Collect all mapped source verse characters, retaining punctuation/case.

    Heading and note bodies are separately counted but NOT mixed into main
    Scripture. The complete authored source may include unmapped books.
    """
    try:
        metadata, authored_keys = scan_usfx(xml)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise MainTextParityError("Malformed or unsupported original USFX XML") from exc
    if metadata["duplicate_verse_ids"] or metadata["nonstandard_verse_identifiers"]:
        raise MainTextParityError("Ambiguous authored USFX keys")
    root = _tree(xml, "usfx")
    pairs = dict(mapping)
    if not pairs or len(pairs) != len(mapping) or len(set(pairs.values())) != len(mapping):
        raise MainTextParityError("Ambiguous explicit book crosswalk")
    books = [x for x in root.iter() if isinstance(x.tag, str)
             and etree.QName(x).localname == "book"]
    if len(books) != len(metadata["original_books"]):
        raise MainTextParityError("Nested or ambiguous source book structure")
    observed: dict[str, list[str]] = {}
    skipped = Counter()
    visited = set()
    visited_order = []
    for book in books:
        src = book.get("id")
        if (not src or not USFM_ID.fullmatch(src) or src in visited):
            raise MainTextParityError("Unsafe or repeated authorial source book ID")
        visited.add(src)
        visited_order.append(src)
        if src not in pairs:
            continue
        dest = pairs[src]
        chapter = None
        active = None

        def append(fragment):
            if fragment and active is not None:
                observed[active].append(fragment)

        def visit(node, depth=0):
            nonlocal chapter, active
            if depth > 256:
                raise MainTextParityError("Source XML nesting exceeds safe bound")
            if not isinstance(node.tag, str):
                return
            kind = etree.QName(node).localname
            if kind in USFX_NOTE or kind in USFX_HEAD:
                skipped[kind] += 1
                return
            if kind == "book" and depth:
                raise MainTextParityError("Nested source books are unsupported")
            if kind == "c":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0:
                    raise MainTextParityError("Invalid authored chapter marker")
                chapter, active = int(value), None
            elif kind == "v":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0 or chapter is None:
                    raise MainTextParityError("Ambiguous authored verse, including ranges")
                active = f"{dest}.{chapter}.{int(value)}"
                if active in observed:
                    raise MainTextParityError("Repeated canonical authored verse")
                observed[active] = []
            append(node.text)
            for child in node:
                visit(child, depth + 1)
                append(child.tail)

        visit(book)
    if visited_order != metadata["original_books"]:
        raise MainTextParityError("Authored book order changed during scan")
    mapped_keys = {
        f"{pairs[code]}.{chapter}.{verse}" for code, chapter, verse in authored_keys
        if code in pairs
    }
    if set(observed) != mapped_keys:
        raise MainTextParityError("Authored source text and verse inventories disagree")
    strings = {ref: "".join(chunks) for ref, chunks in observed.items()}
    if any(len(value.encode("utf-8")) > MAX_VERSE for value in strings.values()):
        raise MainTextParityError("Implausibly long authored verse")
    return strings, {
        "source_original_book_count": len(visited),
        "mapped_numbered_source_keys": len(strings),
        "unmapped_authored_book_count": len(visited - set(pairs)),
        "unmapped_numbered_source_keys": sum(
            1 for code, _ch, _v in authored_keys if code not in pairs),
        "excluded_source_heading_or_note_element_counts": dict(sorted(skipped.items())),
        "source_explicit_usfm_to_native_book_crosswalk_only": True,
    }


def native_raw_main_text(raw: bytes) -> tuple[str, dict]:
    """Strictly parse a complete raw XML fragment; never 'repair' bad tags.

    Note text and headings are not Scripture. XML entity decoding is done
    by a strict parser; exact emitted bytes are tracked separately by the
    independent native raw corpus hash.
    """
    if len(raw) > MAX_VERSE:
        raise MainTextParityError("Oversized raw native verse")
    if b"<!DOCTYPE" in raw.upper() or b"<?xml" in raw.lower():
        raise MainTextParityError("Unexpected declarations inside native XML fragment")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(b"<private_root>" + raw + b"</private_root>", parser)
    except etree.XMLSyntaxError as exc:
        raise MainTextParityError("Stock SWORD raw entry is not a self-contained XML fragment") from exc
    if any(isinstance(x, etree._Entity) for x in root.iter()):
        raise MainTextParityError("Unresolved native XML entity")
    chars = []
    excluded = Counter()

    def walk(node):
        if isinstance(node.tag, str):
            kind = etree.QName(node).localname
            if kind in NATIVE_SKIP:
                excluded[kind] += 1
                return
            if node.text:
                chars.append(node.text)
            for child in node:
                walk(child)
                if child.tail:
                    chars.append(child.tail)

    walk(root)
    return "".join(chars), dict(excluded)


def _fold_whitespace(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def _classify(source: str, native: str) -> str:
    if source == native:
        return "exact_semantic_characters"
    if unicodedata.normalize("NFC", source) == unicodedata.normalize("NFC", native):
        return "unicode_normalization_only"
    if _fold_whitespace(source) == _fold_whitespace(native):
        return "whitespace_only"
    a, b = WORD.findall(source), WORD.findall(native)
    if a == b:
        return "word_sequence_same_punctuation_or_spacing_differs"
    if [t.casefold() for t in a] == [t.casefold() for t in b]:
        return "case_or_punctuation_differs_same_folded_words"
    return "word_sequence_differs"


def compare_private_main_text(
    source: dict[str, str], mapped_source: dict, native_records: list[tuple[str, bytes]],
    *, max_examples: int = MAX_MISMATCHES,
) -> dict:
    """Utility for synthetic tests and final audited raw reader callback."""
    if not 0 < max_examples <= MAX_MISMATCHES:
        raise MainTextParityError("Unsafe mismatch sample bound")
    counts = Counter()
    samples = []
    seen = set()
    native_keys = set()
    skipped_native = Counter()
    for reference, raw in native_records:
        if reference in seen:
            raise MainTextParityError("Duplicate actual native reference")
        seen.add(reference)
        native_keys.add(reference)
        if reference not in source:
            counts["native_verse_without_same_indexed_source_key"] += 1
            continue
        counts["matching_indexed_keys_checked"] += 1
        try:
            native, excluded = native_raw_main_text(raw)
        except MainTextParityError:
            counts["native_raw_not_parseable_as_self_contained_xml"] += 1
            if len(samples) < max_examples:
                samples.append({"native_ref": reference,
                                "classification": "native_raw_fragment_requires_review"})
            continue
        skipped_native.update(excluded)
        src = source[reference]
        classification = _classify(src, native)
        counts[classification] += 1
        if classification != "exact_semantic_characters" and len(samples) < max_examples:
            samples.append({
                "native_ref": reference,
                "classification": classification,
                "source_character_count": len(src),
                "compiled_character_count": len(native),
                "source_word_count": len(WORD.findall(src)),
                "compiled_word_count": len(WORD.findall(native)),
                "source_utf8_sha256": sha256(src.encode("utf-8")).hexdigest(),
                "compiled_utf8_sha256": sha256(native.encode("utf-8")).hexdigest(),
            })
    missing = sorted(set(source) - native_keys)
    counts["source_verses_without_native_indexed_entry"] = len(missing)
    full_exact = bool(source and not missing
                      and counts["matching_indexed_keys_checked"] == len(source)
                      and counts["exact_semantic_characters"] == len(source)
                      and counts["native_verse_without_same_indexed_source_key"] == 0)
    return {
        "status": ("all_mapped_numbered_maintext_characters_match_index_only"
                   if full_exact else "blocked_full_mapped_numbered_maintext_parity"),
        "source_mapped_numbered_verse_count": len(source),
        "native_mapped_numbered_verse_count": len(native_keys),
        "classifications": dict(sorted(counts.items())),
        "first_differences_no_scripture": samples,
        "first_source_only_refs": missing[:max_examples],
        "native_excluded_note_or_title_elements": dict(sorted(skipped_native.items())),
        "excluded_authored_note_and_title_body_parity_verified": False,
        "exact_mapped_numbered_maintext_semantic_characters_verified": full_exact,
        "exact_original_source_bytes_equal_compiled_bytes_verified": False,
        "unmapped_source_books_verified": False,
        "intro_and_verse_zero_verified": False,
        "notes_strong_references_poetry_layout_verified": False,
        "publisher_exact_edition_revision_identity_verified": False,
        "approved_for_publication": False,
    }


def run_real_usfx_sword_text_probe(
    source_usfx_zip: Path, original_sword_zip: Path, crosswalk: Path,
    native_index_binary: Path, native_raw_binary: Path
) -> dict:
    raw, publisher = read_source_xml(source_usfx_zip, source_format="usfx")
    mapping = read_crosswalk(crosswalk)
    source_text, scope = authored_usfx_main_text(raw, mapping)
    with tempfile.TemporaryDirectory(prefix="private-maintext-") as root:
        module = Path(root) / "original"
        conf = _safe_single_module(original_sword_zip, module)
        before = module_payload_digest(module)
        # Read actual stock-SWORD raw entries into this callback only.
        # No Scripture content is returned, printed or written to disk.
        native_keys = set()
        counts = Counter()
        samples = []
        skipped_native = Counter()

        def on_entry(kind, ref, bytes_):
            if kind != "K":
                return
            if ref in native_keys:
                raise MainTextParityError("Duplicate native verse during compiled scan")
            native_keys.add(ref)
            if ref not in source_text:
                counts["native_verse_without_same_indexed_source_key"] += 1
                return
            counts["matching_indexed_keys_checked"] += 1
            try:
                actual, excluded = native_raw_main_text(bytes_)
            except MainTextParityError:
                counts["native_raw_not_parseable_as_self_contained_xml"] += 1
                if len(samples) < MAX_MISMATCHES:
                    samples.append({"native_ref": ref,
                                    "classification": "native_raw_fragment_requires_review"})
                return
            skipped_native.update(excluded)
            authored = source_text[ref]
            category = _classify(authored, actual)
            counts[category] += 1
            if category != "exact_semantic_characters" and len(samples) < MAX_MISMATCHES:
                samples.append({
                    "native_ref": ref, "classification": category,
                    "source_character_count": len(authored),
                    "compiled_character_count": len(actual),
                    "source_word_count": len(WORD.findall(authored)),
                    "compiled_word_count": len(WORD.findall(actual)),
                    "source_utf8_sha256": sha256(authored.encode()).hexdigest(),
                    "compiled_utf8_sha256": sha256(actual.encode()).hexdigest(),
                })

        corpus = inspect_native_raw_corpus(
            module, conf["module_id"], native_raw_binary, native_index_binary,
            on_entry=on_entry)
        if before != module_payload_digest(module) or before != corpus["module_payload_sha256"]:
            raise MainTextParityError("Native module mutated during private content scan")
        # Read original source ZIP again to reject a source replacement mid-audit.
        if sha256(source_usfx_zip.read_bytes()).hexdigest() != publisher["archive_sha256"]:
            raise MainTextParityError("Original publisher archive changed during audit")
        missing = sorted(set(source_text) - native_keys)
        counts["source_verses_without_native_indexed_entry"] = len(missing)
        exact = bool(source_text and len(native_keys) == len(source_text)
                     and not missing and counts["exact_semantic_characters"] == len(source_text)
                     and not counts["native_verse_without_same_indexed_source_key"])
        comparison = {
            "status": ("all_mapped_numbered_maintext_characters_match_index_only"
                       if exact else "blocked_full_mapped_numbered_maintext_parity"),
            "source_mapped_numbered_verse_count": len(source_text),
            "native_numbered_verse_count": len(native_keys),
            "classifications": dict(sorted(counts.items())),
            "first_differences_no_scripture": samples,
            "first_source_only_refs": missing[:MAX_MISMATCHES],
            "native_excluded_note_or_title_elements": dict(sorted(skipped_native.items())),
            "mapped_numbered_maintext_exact_semantic_characters_verified": exact,
        }
        return {
            "schema_version": 1,
            "status": "real_usfx_to_stock_sword_maintext_diagnostic_not_publication",
            "publisher_original_usfx_zip_sha256": publisher["archive_sha256"],
            "publisher_original_usfx_xml_sha256": publisher["sha256"],
            "publisher_compiled_sword_zip_sha256": sha256(original_sword_zip.read_bytes()).hexdigest(),
            "book_crosswalk_sha256": sha256(crosswalk.read_bytes()).hexdigest(),
            "module_id": conf["module_id"],
            "module_native_driver": corpus["module_driver"],
            "module_versification": corpus["module_native_versification"],
            "stock_sword_version": corpus["native_engine_version"],
            "module_payload_sha256": before,
            "independent_whole_native_raw_manifest_sha256":
                corpus["all_native_raw_entries_ordered_sha256"],
            "native_inspector_sha256": corpus["independent_native_key_inspector_sha256"],
            "native_raw_inspector_sha256": corpus["native_raw_inspector_sha256"],
            "independent_native_whole_corpus_scan_completed":
                corpus["exact_all_occupied_native_keys_matched_independent_index"],
            "source_book_scope": scope,
            "mapped_numbered_text_comparison": comparison,
            "source_usfx_to_osis_conversion_verified": False,
            "exact_publisher_revision_identity_verified": False,
            "full_original_source_including_extra_books_and_intros_verified": False,
            "note_callers_bodies_anchors_references_strong_and_layout_verified": False,
            "actual_graphical_reader_rendering_verified": False,
            "publication_rights_and_human_editorial_approval": False,
            "published": False,
        }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-usfx-zip", type=Path, required=True)
    p.add_argument("--original-sword-zip", type=Path, required=True)
    p.add_argument("--crosswalk", type=Path, required=True)
    p.add_argument("--native-index-inspector", type=Path, required=True)
    p.add_argument("--native-raw-inspector", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if (args.report.exists() or args.report.is_symlink()
            or not args.report.parent.is_dir()
            or args.report.parent.is_symlink()
            or args.report.resolve().is_relative_to(Path.cwd() / "modules")):
        p.error("Output report must be new, outside the resource module tree")
    try:
        report = run_real_usfx_sword_text_probe(
            args.source_usfx_zip, args.original_sword_zip, args.crosswalk,
            args.native_index_inspector, args.native_raw_inspector)
        write_new_metadata_report(args.report, args.original_sword_zip, report)
    except (ValueError, OSError, UnicodeError) as exc:
        p.error(str(exc))
    rows = report["mapped_numbered_text_comparison"]
    print("Compared native-indexed source verse bodies:",
          rows["classifications"].get("matching_indexed_keys_checked", 0))
    print("Exact semantic characters:",
          rows["classifications"].get("exact_semantic_characters", 0))
    print("Overall authorial edition, annotations, structure, rights and release NOT approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
