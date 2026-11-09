#!/usr/bin/env python3
"""Private read-only second REAL Bible evidence, independent source and SWORD.

A real source and reader smoke for issue #28, NOT a full source→SWORD
content/word/notes parity certificate, conversion approval, or publication.
Inputs must be independently obtained from the actual rights-cleared publisher.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
import zipfile

from check_updates import parse_conf
from diff_sword_snapshots import _read_snapshot, SnapshotError
from lsg_source_compare import read_source_xml, scan_usfx
from sword_native_inventory import collect_native_inventory, NativeIndexError
from stable_sword_refs import parse_keys, parse_registry, module_payload_digest


class SecondBibleError(ValueError):
    pass


def _safe_single_module(zip_path: Path, root: Path) -> str:
    """Copy an already safety-vetted ZIP into a private isolated SWORD root."""
    if not zip_path.is_file() or zip_path.is_symlink():
        raise SecondBibleError("Missing or symlinked original SWORD ZIP")
    indexed, conf_bytes = _read_snapshot(zip_path)
    conf = parse_conf(conf_bytes)
    name = conf["module_id"]
    conf_path = f"mods.d/{name.lower()}.conf"
    if conf_path not in indexed:
        raise SecondBibleError("No exact, single native module .conf")
    if conf["driver"] not in {"RawText", "zText"}:
        raise SecondBibleError("Original source is not a supported Bible SWORD driver")
    root.mkdir(parents=True, exist_ok=False)
    payload = root / "payload"
    payload.mkdir()
    with zipfile.ZipFile(zip_path) as archive:
        for member in sorted(indexed):
            target = payload / member
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.read(member)
            proof = indexed[member]
            if len(raw) != proof["size"] or sha256(raw).hexdigest() != proof["sha256"]:
                raise SecondBibleError("Source archive changed between checks")
            target.write_bytes(raw)
    if module_payload_digest(root) == "":
        raise SecondBibleError("Empty installed SWORD module digest")
    return {"module_id": name, "original_version": conf.get("version"),
            "original_driver": conf["driver"],
            "original_versification": conf.get("versification") or "KJV"}


def _source_counts_by_order(usfx_raw: bytes) -> tuple[dict, list[dict]]:
    metadata, keys = scan_usfx(usfx_raw)
    if metadata["duplicate_verse_ids"] or metadata["nonstandard_verse_identifiers"]:
        raise SecondBibleError("Ambiguous or duplicate source-authored USFX verse IDs")
    books = metadata["original_books"]
    if not books or len(set(books)) != len(books):
        raise SecondBibleError("Ambiguous original source book identities")
    groups = {}
    for code, chapter, verse in keys:
        if chapter < 1 or verse < 1:
            raise SecondBibleError("Nonpositive original source reference")
        groups.setdefault(code, set()).add((chapter, verse))
    if not set(groups).issubset(set(books)):
        raise SecondBibleError("Original source verse IDs outside declared books")
    # An authorial USFX document may include introduction/front-matter
    # sections with no numbered verse. Never fabricate verse IDs, nor
    # erase those source elements as if they lacked content.
    summary = [
        {"usfx_book_id": name, "authored_verse_count": len(groups.get(name, set())),
         "authored_chapter_count": len(set(c for c, _ in groups.get(name, set()))),
         "requires_unnumbered_intro_content_audit": name not in groups}
        for name in books
    ]
    return metadata, summary


def _reader_counts_by_order(keys_text: str) -> list[dict]:
    counts: dict[str, Counter] = {}
    for book, chapter, verse in parse_keys(keys_text):
        counts.setdefault(book, Counter())[(chapter, verse)] += 1
    # parse_keys() returns a set: book order would be lost. The actual native
    # SWORD reader plan is independently ordered in its newline inventory.
    ordered = []
    seen = set()
    last_book = None
    for row in keys_text.splitlines():
        book, chapter, verse = row.split(".")
        if book != last_book:
            if book in seen:
                raise SecondBibleError("Noncontiguous native reader book")
            ordered.append({"osis_book_id": book, "occupied_verse_count": len(counts[book]),
                            "occupied_chapter_count": len(set(c for c, v in counts[book]))})
            seen.add(book)
            last_book = book
    return ordered


def inspect_real_source_and_native_reader(
    original_usfx_zip: Path, compiled_sword_zip: Path, native_inspector: Path
) -> dict:
    raw, original_receipt = read_source_xml(original_usfx_zip, source_format="usfx")
    original, original_groups = _source_counts_by_order(raw)
    with tempfile.TemporaryDirectory(prefix="independent-real-sword-") as tmp:
        installed = Path(tmp) / "original_module"
        original_conf = _safe_single_module(compiled_sword_zip, installed)
        keys, registry, native = collect_native_inventory(
            native_inspector, installed, original_conf["module_id"], timeout=240)
    engine_registry = parse_registry(registry, native["native_versification"])
    reader_groups = _reader_counts_by_order(keys)
    source_book_count = len(original_groups)
    numbered_source_groups = [group for group in original_groups
                              if group["authored_verse_count"] > 0]
    unnumbered_groups = [group["usfx_book_id"] for group in original_groups
                         if group["authored_verse_count"] == 0]
    reader_book_count = len(reader_groups)
    both_have_same_number_of_books = len(numbered_source_groups) == reader_book_count
    same_count_per_ordered_book = (
        both_have_same_number_of_books
        and all(source["authored_verse_count"] == reader["occupied_verse_count"]
                for source, reader in zip(numbered_source_groups, reader_groups)))
    first_diffs = []
    for index, (source, reader) in enumerate(zip(numbered_source_groups, reader_groups), 1):
        if source["authored_verse_count"] != reader["occupied_verse_count"] and len(first_diffs) < 40:
            first_diffs.append({
                "book_ordinal": index,
                "source_usfx_code": source["usfx_book_id"],
                "native_osis_code": reader["osis_book_id"],
                "source_numbered_verses": source["authored_verse_count"],
                "native_occupied_verses": reader["occupied_verse_count"],
            })
    return {
        "schema_version": 1,
        "status": "real_second_bible_independent_source_and_native_reader_inventoried",
        "publisher_original_source_format": "USFX",
        "publisher_original_usfx_zip_sha256": original_receipt["archive_sha256"],
        "publisher_original_usfx_xml_sha256": original_receipt["sha256"],
        "publisher_original_verse_count": sum(x["authored_verse_count"]
                                               for x in original_groups),
        "publisher_original_book_count": source_book_count,
        "publisher_original_books_with_numbered_verses": len(numbered_source_groups),
        "publisher_unnumbered_intro_or_nonverse_book_codes_needing_review": unnumbered_groups,
        "publisher_unnumbered_book_text_structure_verified": False,
        "publisher_source_xml_book_codes": [x["usfx_book_id"] for x in original_groups],
        "publisher_sword_zip_sha256": sha256(compiled_sword_zip.read_bytes()).hexdigest(),
        "publisher_original_sword_id": native["module_id"],
        "publisher_original_sword_version": original_conf["original_version"],
        "publisher_declared_versification": original_conf["original_versification"],
        "publisher_native_driver": native["module_driver"],
        "actual_native_reader_version": native["reader_version"],
        "native_compiled_payload_sha256": native["module_payload_sha256"],
        "actual_reader_book_count": reader_book_count,
        "actual_reader_occupied_numbered_verses": native["native_occupied_numbered_verse_count"],
        "actual_native_registry_chapter_count": len(engine_registry),
        "actual_native_verse_zero_intros": native["native_occupied_verse_zero_intro_count"],
        "actual_native_anonymous_top_records": native["native_nonaddressable_populated_top_count"],
        "source_and_reader_book_counts_equal_diagnostic_only": both_have_same_number_of_books,
        "source_and_reader_verse_counts_by_order_equal_diagnostic_only": same_count_per_ordered_book,
        "publisher_source_and_compiled_canon_scope_review_required": not both_have_same_number_of_books,
        "source_to_sword_exact_edition_identity_verified": False,
        "source_to_sword_fidelity_gate": (
            "blocked_canon_scope_mismatch_requires_edition_review"
            if not both_have_same_number_of_books
            else "not_verified_requires_independent_book_mapping_and_full_content_probe"
        ),
        "first_ordinal_book_count_differences_needing_review": first_diffs,
        "canonical_usfx_to_osis_book_mapping_verified": False,
        "source_verse_numbering_against_native_reader_verified": False,
        "source_to_sword_exact_words_punctuation_verified": False,
        "source_to_sword_note_reference_layout_parity_verified": False,
        "source_to_candidate_osis_conversion_verified": False,
        "source_license_reviewed_for_publication": False,
        "edition_for_publication_approved": False,
        "published": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-usfx-zip", type=Path, required=True)
    p.add_argument("--original-sword-zip", type=Path, required=True)
    p.add_argument("--native-inspector", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        p.error("Refusing existing/unsafe output path")
    try:
        result = inspect_real_source_and_native_reader(
            args.source_usfx_zip, args.original_sword_zip, args.native_inspector)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        p.error(str(exc))
    args.report.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
