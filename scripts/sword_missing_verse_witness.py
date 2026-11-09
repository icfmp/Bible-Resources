#!/usr/bin/env python3
"""Text-free diagnostic: look for source-only verse *words* in nearby real SWORD raw.

Never proves original punctuation, text order beyond token runs, headings,
footnotes, original verse addresses, complete book fidelity or publication.
Works on a separately sourced real USFX + stock libsword RawText/zText pair.
The missing verse keys come from an independent mapped native index, never
from hardcoded translation-specific fixes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata

from lxml import etree

from lsg_source_compare import read_source_xml, scan_usfx
from real_second_bible_probe import _safe_single_module
from source_native_scope import compare_mapped_scope, read_crosswalk
from stable_sword_refs import KEY, parse_keys, module_payload_digest
from sword_native_inventory import collect_native_inventory

MAX_SOURCE_VERSE_TOKENS = 12000
MAX_RAW_TOKENS = 100000
MAX_MISSING_REFS = 60
MAX_RAW_BYTES = 2 * 1024 * 1024
WORDS = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)
SKIP_USFX_NOTES = {"f", "fe", "note", "x"}
SKIP_SWORD_NOTES = {"note"}


class MissingVerseWitnessError(ValueError):
    """Untrusted evidence: source/native identity or extraction is ambiguous."""


def _tokens(text: str) -> list[str]:
    return [unicodedata.normalize("NFC", word.casefold())
            for word in WORDS.findall(text)]


def _token_hash(words: list[str]) -> str:
    digest = sha256()
    for word in words:
        encoded = word.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def extract_usfx_main_verse_tokens(
    xml: bytes, book: str, chapter: int, verses: set[int]
) -> dict[int, list[str]]:
    """Extract authored USFX verse text in source document order.

    Notes and cross-reference subtrees are excluded as separate editorial
    data, not erased from the original source. This is a diagnostic lane ONLY.
    """
    if not book or chapter < 1 or not verses or any(v < 1 for v in verses):
        raise MissingVerseWitnessError("Invalid requested authored source scope")
    if b"<!DOCTYPE" in xml.upper():
        raise MissingVerseWitnessError("DTD forbidden in authorial USFX")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    root = etree.fromstring(xml, parser)
    if etree.QName(root).localname != "usfx":
        raise MissingVerseWitnessError("Not an original USFX XML source")
    matched = [n for n in root.iter()
               if isinstance(n.tag, str) and etree.QName(n).localname == "book"
               and n.get("id") == book]
    if len(matched) != 1:
        raise MissingVerseWitnessError("Requested USFX book missing or duplicated")
    chunks: dict[int, list[str]] = {v: [] for v in verses}
    active_chapter = None
    active_verse = None

    def visit(node, depth=0):
        nonlocal active_chapter, active_verse
        if depth > 256:
            raise MissingVerseWitnessError("USFX nesting exceeds safe bound")
        if not isinstance(node.tag, str):
            return
        local = etree.QName(node).localname
        if local in SKIP_USFX_NOTES:
            return
        if local == "c":
            value = node.get("id", "")
            if not value.isdigit() or int(value) <= 0:
                raise MissingVerseWitnessError("Unsupported USFX chapter marker")
            active_chapter = int(value)
            active_verse = None
        if local == "v":
            value = node.get("id", "")
            if not value.isdigit() or int(value) <= 0 or active_chapter is None:
                # A verse range cannot safely be split across the indexed slots.
                raise MissingVerseWitnessError("Ambiguous original USFX verse milestone")
            active_verse = int(value)
        if node.text and active_chapter == chapter and active_verse in chunks:
            chunks[active_verse].append(node.text)
        for child in node:
            visit(child, depth + 1)
            if (child.tail and active_chapter == chapter
                    and active_verse in chunks):
                chunks[active_verse].append(child.tail)

    visit(matched[0])
    return {v: _tokens("".join(chunks[v])) for v in verses}


class _NativeVisibleText(HTMLParser):
    """Diagnostic extraction of visible unfiltered OSIS fragment text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.notes = 0
        self.content: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_SWORD_NOTES:
            self.notes += 1

    def handle_startendtag(self, tag, attrs):
        # A self-closing <note/> must not suppress the rest of the verse.
        pass

    def handle_endtag(self, tag):
        if tag in SKIP_SWORD_NOTES and self.notes:
            self.notes -= 1

    def handle_data(self, data):
        if not self.notes:
            self.content.append(data)


def native_main_tokens(raw: bytes) -> list[str]:
    if len(raw) > MAX_RAW_BYTES:
        raise MissingVerseWitnessError("Stock SWORD raw entry too large")
    reader = _NativeVisibleText()
    reader.feed(raw.decode("utf-8", errors="strict"))
    reader.close()
    if reader.notes:
        raise MissingVerseWitnessError("Unclosed native note content in raw fragment")
    words = _tokens("".join(reader.content))
    if len(words) > MAX_RAW_TOKENS:
        raise MissingVerseWitnessError("Too many native visible word tokens")
    return words


def _find_tokens(haystack: list[str], needle: list[str]) -> int | None:
    if len(needle) < 3 or len(needle) > MAX_SOURCE_VERSE_TOKENS:
        return None
    if len(haystack) < len(needle):
        return None
    first = needle[0]
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i] == first and haystack[i:i+len(needle)] == needle:
            return i
    return None


def compare_unindexed_source_text(
    source_usfx: bytes, source_book_codes: list[str],
    missing_native_refs: list[str], mapped_books: list[tuple[str, str]],
    occupied_reader_keys: str, fetch_unfiltered_raw
) -> dict:
    """Resolve every source-only key against a neighboring *actual native slot*.

    A positive result proves only a diagnostic contiguous token witness in
    that raw entry, not complete text/markup fidelity or correct versification.
    """
    if len(missing_native_refs) > MAX_MISSING_REFS:
        raise MissingVerseWitnessError("Too many unmatched source keys for bounded raw probe")
    if not source_book_codes or len(source_book_codes) != len(set(source_book_codes)):
        raise MissingVerseWitnessError("Unreliable source book inventory")
    from_native = {osis: usfm for usfm, osis in mapped_books}
    if len(from_native) != len(mapped_books):
        raise MissingVerseWitnessError("Ambiguous native-to-USFX book mapping")
    occupied = {"%s.%d.%d" % x for x in parse_keys(occupied_reader_keys)}
    canonical_missing = []
    requested: dict[tuple[str, int], set[int]] = {}
    for ref in missing_native_refs:
        match = KEY.fullmatch(ref)
        if match is None or ref in occupied or ref in canonical_missing:
            raise MissingVerseWitnessError("Unreliable source-only missing reference")
        name, ch, verse = match.group(1), int(match.group(2)), int(match.group(3))
        code = from_native.get(name)
        if code is None or code not in source_book_codes:
            raise MissingVerseWitnessError("Missing reference has no authored book mapping")
        canonical_missing.append(ref)
        requested.setdefault((code, ch), set()).add(verse)
    original_main_tokens = {
        (code, ch): extract_usfx_main_verse_tokens(source_usfx, code, ch, verses)
        for (code, ch), verses in requested.items()
    }
    rows = []
    raw_cache: dict[str, tuple[bytes, list[str]]] = {}
    for ref in canonical_missing:
        match = KEY.fullmatch(ref)
        name, ch, verse = match.group(1), int(match.group(2)), int(match.group(3))
        src = from_native[name]
        before = [int(part.rsplit(".", 1)[1]) for part in occupied
                  if part.startswith(f"{name}.{ch}.")
                  and int(part.rsplit(".", 1)[1]) < verse]
        previous_ref = f"{name}.{ch}.{max(before)}" if before else None
        source_words = original_main_tokens[(src, ch)][verse]
        if len(source_words) > MAX_SOURCE_VERSE_TOKENS:
            raise MissingVerseWitnessError("Source verse has too many word tokens")
        row = {
            "unindexed_original_source_ref": ref,
            "source_authored_book": src,
            "source_main_word_token_count": len(source_words),
            "source_main_words_sha256": _token_hash(source_words),
            "preceding_occupied_native_ref": previous_ref,
            "original_verse_reference_still_unindexed": True,
            "original_verse_text_and_punctuation_verified": False,
        }
        if previous_ref is None:
            row["diagnostic"] = "no_preceding_occupied_native_entry_in_same_chapter"
        elif len(source_words) < 3:
            row["diagnostic"] = "too_few_source_tokens_for_content_witness"
        else:
            if previous_ref not in raw_cache:
                raw = fetch_unfiltered_raw(previous_ref)
                if not isinstance(raw, bytes):
                    raise MissingVerseWitnessError("Native raw inspector returned non-bytes")
                raw_cache[previous_ref] = (raw, native_main_tokens(raw))
            raw, native_words = raw_cache[previous_ref]
            index = _find_tokens(native_words, source_words)
            row.update({
                "native_entry_unfiltered_sha256": sha256(raw).hexdigest(),
                "native_entry_unfiltered_byte_count": len(raw),
                "native_entry_main_word_token_count": len(native_words),
                "source_word_run_found_contiguously_in_native_entry": index is not None,
                "source_word_run_start_ordinal": index,
                "diagnostic": ("contiguous_source_word_run_found_in_preceding_native_entry"
                               if index is not None
                               else "source_word_run_not_found_in_preceding_native_entry"),
            })
        rows.append(row)
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if row["preceding_occupied_native_ref"] is not None:
            groups.setdefault(row["preceding_occupied_native_ref"], []).append(row)
    ordered_groups = []
    for ref, group in sorted(groups.items()):
        indices = [r.get("source_word_run_start_ordinal") for r in group]
        all_found = all(v is not None for v in indices)
        ordered_groups.append({
            "preceding_native_ref": ref,
            "missing_source_verse_count": len(group),
            "all_missing_source_word_runs_found": all_found,
            "missing_source_word_runs_in_source_order": (
                all_found and indices == sorted(indices)
            ),
        })
    return {
        "schema_version": 1,
        "status": "private_lexical_presence_witness_only_not_fidelity_approval",
        "source_scope_missing_native_verse_count": len(canonical_missing),
        "source_missing_native_verses": rows,
        "grouped_preceding_native_entries": ordered_groups,
        "inspected_unique_native_raw_entries": len(raw_cache),
        "readback_source": "actual_stock_libsword_unfiltered_native_entry",
        "publisher_original_verse_numbering_preserved": True,
        "actual_missing_refs_are_not_reintroduced": True,
        "source_to_compiled_exact_punctuation_verified": False,
        "note_callers_bodies_anchors_verified": False,
        "lexical_attributes_and_structure_verified": False,
        "same_publisher_edition_revision_verified": False,
        "authorial_complete_text_preservation_verified": False,
        "approved_for_publication": False,
        "published": False,
    }


def inspect_missing_verse_content(
    original_usfx_zip: Path, original_sword_zip: Path,
    native_index_inspector: Path, native_raw_inspector: Path,
    crosswalk: Path
) -> dict:
    xml, source = read_source_xml(original_usfx_zip, source_format="usfx")
    source_info, source_keys = scan_usfx(xml)
    pairs = read_crosswalk(crosswalk)
    if native_raw_inspector.is_symlink() or not native_raw_inspector.is_file():
        raise MissingVerseWitnessError("Missing or linked trusted native raw-entry inspector")
    with tempfile.TemporaryDirectory(prefix="real-native-content-") as tmp:
        isolated = Path(tmp) / "original"
        original_conf = _safe_single_module(original_sword_zip, isolated)
        occupied_keys, _registry, native = collect_native_inventory(
            native_index_inspector, isolated, original_conf["module_id"], timeout=240)
        scoped = compare_mapped_scope(
            source_info["original_books"], source_keys, occupied_keys, pairs)
        if (not scoped["source_canonical_book_order_verified"]
                or not scoped["native_canonical_book_order_verified"]
                or scoped["native_canonical_refs_not_authored_in_source_count"]):
            raise MissingVerseWitnessError("Cannot probe ambiguous original↔native canonical scope")
        if scoped["source_canonical_refs_unreachable_in_reader_count"] > MAX_MISSING_REFS:
            raise MissingVerseWitnessError("Unbounded number of unindexed source verses")
        if (scoped["source_canonical_refs_unreachable_in_reader_count"]
                != len(scoped["first_unreachable_source_refs"])):
            raise MissingVerseWitnessError("Bounded scope report does not list every missing verse")
        before_hash = module_payload_digest(isolated)
        env = dict(os.environ, SWORD_PATH=str((isolated / "payload").resolve()))
        binary = str(native_raw_inspector.resolve(strict=True))

        def fetch(ref: str) -> bytes:
            try:
                run = subprocess.run(
                    [binary, original_conf["module_id"], ref],
                    env=env, capture_output=True, check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise MissingVerseWitnessError("Native raw reader unavailable") from exc
            if run.returncode != 0:
                # Raw stdout/stderr deliberately never included in logs.
                raise MissingVerseWitnessError(
                    f"Native raw entry readback rejected reference (exit {run.returncode})")
            if len(run.stdout) > MAX_RAW_BYTES:
                raise MissingVerseWitnessError("Excessive native entry raw length")
            return run.stdout

        report = compare_unindexed_source_text(
            xml, source_info["original_books"],
            scoped["first_unreachable_source_refs"], pairs,
            occupied_keys, fetch)
        if before_hash != module_payload_digest(isolated):
            raise MissingVerseWitnessError("Module changed while reading native raw entries")
    report["original_usfx_archive_sha256"] = source["archive_sha256"]
    report["original_usfx_document_sha256"] = source["sha256"]
    report["original_sword_archive_sha256"] = sha256(original_sword_zip.read_bytes()).hexdigest()
    report["original_compiled_sword_payload_sha256"] = native["module_payload_sha256"]
    report["native_sword_version"] = native["reader_version"]
    report["native_sword_driver"] = native["module_driver"]
    report["native_module_id"] = native["module_id"]
    report["standard_book_crosswalk_sha256"] = sha256(crosswalk.read_bytes()).hexdigest()
    report["scope_index_audit_status"] = scoped["status"]
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-usfx-zip", required=True, type=Path)
    p.add_argument("--original-sword-zip", required=True, type=Path)
    p.add_argument("--native-index-inspector", required=True, type=Path)
    p.add_argument("--native-raw-inspector", required=True, type=Path)
    p.add_argument("--crosswalk", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    if (args.report.exists() or args.report.is_symlink()
            or not args.report.parent.is_dir() or args.report.parent.is_symlink()
            or args.report.resolve() in
            (args.source_usfx_zip.resolve(), args.original_sword_zip.resolve())):
        p.error("Refusing unsafe or existing evidence report")
    try:
        result = inspect_missing_verse_content(
            args.source_usfx_zip, args.original_sword_zip,
            args.native_index_inspector, args.native_raw_inspector,
            args.crosswalk)
        data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
        fd, tmp = tempfile.mkstemp(dir=args.report.parent, prefix=".raw-witness-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if args.report.exists() or args.report.is_symlink():
                raise MissingVerseWitnessError("Evidence report destination appeared")
            os.replace(tmp, args.report)
        finally:
            Path(tmp).unlink(missing_ok=True)
    except (OSError, ValueError, UnicodeError) as exc:
        p.error(str(exc))
    print("Read back", result["inspected_unique_native_raw_entries"],
          "independent native raw records and checked",
          result["source_scope_missing_native_verse_count"],
          "source-only verse key lexical witnesses. No release approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
