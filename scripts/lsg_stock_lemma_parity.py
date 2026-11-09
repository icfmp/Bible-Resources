#!/usr/bin/env python3
"""Read-only lexical metadata parity: validated OSIS versus stable SWORD binary.

Compares every <w lemma> value in sequence, book by book, *including* book
and chapter verse-zero introduction entries. The compiler tool emits ONLY
lemma attributes to a temporary file. No Scripture words or note bodies are
read or exported by this new inspector. Only counts and hashes reach reports.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from html import unescape
from pathlib import Path
import os
import re
import subprocess
import tempfile

from lxml import etree

from lsg_osis_parity import OSIS, _strong_ids
from pilot_preflight import PilotError

_BOOK_ID = re.compile(r"^[0-9A-Za-z]{1,30}$")
_MAX_OUTPUT_SIZE = 120_000_000


def _books(candidate: Path):
    tree = etree.parse(str(candidate), parser=etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        recover=False, huge_tree=False))
    books = [n for n in tree.iter(OSIS + "div") if n.get("type") == "book"]
    ids = [n.get("osisID") for n in books]
    if (not ids or len(set(ids)) != len(ids)
            or any(not i or not _BOOK_ID.fullmatch(i) for i in ids)):
        raise PilotError("Untrusted or repeated source OSIS book identity")
    return books


def ordered_lemma_reader_plan(candidate: Path,
                              aliases: list[tuple[str, str]]) -> tuple[list[tuple[str,str,str]], list]:
    """Reader-key plan from independent source OSIS book/chapter order.

    Read each book: book 0:0, chapter 1:0, chapter 1 verses, chapter 2:0,
    etc. This is NOT sorted alphabetically, and it cannot silently skip
    the one owner-authorized merged source verse.
    """
    books = _books(candidate)
    by_book = defaultdict(list)
    for ref, query in aliases:
        parts = ref.rsplit(".", 2)
        if len(parts) != 3 or not all(p.isdigit() for p in parts[1:]):
            raise PilotError("Invalid compiled reader reference in lemma plan")
        by_book[parts[0]].append((int(parts[1]), int(parts[2]), query))
    expected = {node.get("osisID") for node in books}
    if set(by_book) != expected:
        raise PilotError("Compiled reader books differ from source OSIS books")
    plan = []
    normal_count = 0
    intro_count = 0
    for book in books:
        book_id = book.get("osisID")
        rows = sorted(by_book[book_id])
        if not rows or any(c < 1 or v < 1 for c, v, _ in rows):
            raise PilotError("Malformed canonical chapter or verse in lemma plan")
        book_name = rows[0][2].rsplit(" ", 1)[0]
        if not book_name or len(book_name) > 100:
            raise PilotError("Unknown compiled book name in lemma plan")
        plan.append((book_name + " 0:0", book_id, "1"))
        intro_count += 1
        previous_chapter = 0
        previous_verse = 0
        for chapter, verse, query in rows:
            if chapter != previous_chapter:
                if chapter != previous_chapter + 1:
                    raise PilotError("Source OSIS lemma plan has missing chapter")
                plan.append((f"{book_name} {chapter}:0", book_id, "1"))
                intro_count += 1
                previous_chapter = chapter
                previous_verse = 0
            if verse <= previous_verse:
                raise PilotError("Duplicate or non-monotonic reader key in lemma plan")
            previous_verse = verse
            plan.append((query, book_id, "0"))
            normal_count += 1
    if normal_count != len(aliases) or intro_count != len(books) + sum(
            1 for n in books for div in n.iter(OSIS + "chapter")
            if div.get("osisID") or div.get("sID")):
        # Some converters use paired milestone chapters and chapters
        # in separate wrapper structures; compare to the actual compiled
        # keys above, not guessed source milestone counts.
        if normal_count != len(aliases):
            raise PilotError("Reader key missing from lexical audit")
    return plan, books


def _canonical(value: str) -> tuple[str, bool]:
    # The stable raw exporter exposes XML attribute entities; lxml already
    # decoded the source XML. Strong references themselves are ASCII.
    value = " ".join(unescape(value).split())
    if "\t" in value or "\n" in value:
        raise PilotError("Malformed lexical attribute escaped whitespace")
    return value, _strong_ids(value, osis=True) is not None


def _sequence_hash(values: list[str]) -> str:
    digest = sha256()
    for value in values:
        data = value.encode("utf-8")
        digest.update(len(data).to_bytes(4, "big"))
        digest.update(data)
    return digest.hexdigest()


def compare_compiled_lemma_rows(candidate: Path, raw_rows: list[str]) -> dict:
    """Full ordered value parity, with multiset diagnostic for relocations."""
    source_books = _books(candidate)
    ids = [b.get("osisID") for b in source_books]
    compiled = defaultdict(list)
    invalid_rows = 0
    for row in raw_rows:
        pair = row.split("\t")
        if len(pair) != 2 or pair[0] not in ids:
            raise PilotError("Compiled lemma data has malformed or unknown book")
        value, valid = _canonical(pair[1])
        invalid_rows += not valid
        compiled[pair[0]].append(value)
    diagnostics = []
    total_source = total_compiled = 0
    source_unknown = 0
    exact = 0
    for book in source_books:
        name = book.get("osisID")
        source = []
        for word in book.iter(OSIS + "w"):
            value, valid = _canonical(word.get("lemma") or "")
            source_unknown += not valid
            source.append(value)
        actual = compiled[name]
        total_source += len(source)
        total_compiled += len(actual)
        count = min(len(source), len(actual))
        matches = sum(a == b for a, b in zip(source, actual))
        if len(source) == len(actual) and matches == count:
            exact += 1
        else:
            first = next((i + 1 for i, (a, b) in enumerate(zip(source, actual))
                          if a != b), count + 1)
            diagnostics.append({
                "book": name,
                "first_mismatch_word_position": first,
                "source_word_slots": len(source),
                "compiled_word_slots": len(actual),
                "matching_ordered_word_slots_before_first_difference": first - 1,
                "source_ordered_lemma_sha256": _sequence_hash(source),
                "compiled_ordered_lemma_sha256": _sequence_hash(actual),
                "book_lemma_multisets_equal": Counter(source) == Counter(actual),
            })
    approved = (source_unknown == 0 and invalid_rows == 0 and
                total_source == total_compiled and exact == len(ids))
    return {
        "status": ("compiled_ordered_lemma_attributes_verified"
                   if approved else "blocked_compiled_lemma_attributes_mismatch"),
        "books_compared": len(ids),
        "books_with_exact_ordered_lemma_values": exact,
        "source_word_slots": total_source,
        "compiled_word_slots": total_compiled,
        "unparseable_source_lemma_slots": source_unknown,
        "unparseable_compiled_lemma_slots": invalid_rows,
        "mismatching_books": diagnostics,
        "compiled_note_bodies_verified": False,
        "compiled_cross_reference_targets_verified": False,
        "source_modified": False,
        "published": False,
    }


def audit_compiled_lemma_values(candidate: Path, aliases: list[tuple[str, str]],
                                *, sword_root: Path, module_id: str,
                                inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Compiled SWORD lemma inspection executable unavailable")
    plan, books = ordered_lemma_reader_plan(candidate, aliases)
    with tempfile.TemporaryDirectory(prefix="stock-lemma-audit-") as directory:
        root = Path(directory)
        refs = root / "reader-refs.tsv"
        private = root / "lemma-only.tsv"
        refs.write_text("".join("\t".join(row) + "\n" for row in plan),
                        encoding="utf-8")
        try:
            proc = subprocess.run(
                [str(inspector), module_id, str(refs), str(private),
                 "--word-lemmas-only"],
                env=dict(os.environ, SWORD_PATH=str(sword_root)),
                capture_output=True, text=True, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Stable SWORD lemma inspection timed out") from exc
        if proc.returncode or proc.stderr or proc.stdout or not private.is_file():
            raise PilotError("Stable SWORD lemma inspector rejected a reader key or attribute "
                             f"(exit {proc.returncode})")
        if private.stat().st_size > _MAX_OUTPUT_SIZE:
            raise PilotError("Private lemma inspection exceeds output bound")
        rows = private.read_text(encoding="utf-8").splitlines()
        report = compare_compiled_lemma_rows(candidate, rows)
    report["reader_entries_inspected"] = len(plan)
    report["book_count"] = len(books)
    report["semantic_inspector"] = "released_sword_raw_word_lemma_values_only"
    return report
