#!/usr/bin/env python3
"""Compare independently collected USFM/USFX verse IDs with native SWORD refs.

This is a *scoped reference-index* audit, never full source-to-reader content
fidelity. Mapping is explicit, standards-based and independently reviewed;
unmapped books and introductions remain documented, NOT silently deleted.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from stable_sword_refs import parse_keys

USFM_BOOK = re.compile(r"^[0-9]?[A-Z][A-Z0-9]{2}$")
SWORD_BOOK = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*$")


class BookScopeError(ValueError):
    """Cannot establish a lossless and unambiguous mapped reference scope."""


def read_crosswalk(path: Path) -> list[tuple[str, str]]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128_000:
        raise BookScopeError("Missing, linked or oversized reviewed crosswalk")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("schema_version") != 1 or not isinstance(doc.get("books"), list)
            or not 1 <= len(doc["books"]) <= 250):
        raise BookScopeError("Unsupported canonical identifier crosswalk format")
    pairs = []
    a, b = set(), set()
    for row in doc["books"]:
        if not isinstance(row, dict) or set(row) != {"usfm", "osis"}:
            raise BookScopeError("Malformed identifier crosswalk record")
        usfm, osis = row["usfm"], row["osis"]
        if (not isinstance(usfm, str) or not isinstance(osis, str)
                or not USFM_BOOK.fullmatch(usfm) or not SWORD_BOOK.fullmatch(osis)
                or usfm in a or osis in b):
            raise BookScopeError("Unsafe, ambiguous or duplicate USFM/OSIS book identifier")
        a.add(usfm)
        b.add(osis)
        pairs.append((usfm, osis))
    return pairs


def _digest_osis_references(references: set[str], order: dict[str, int]) -> str:
    h = sha256()
    for key in sorted(references, key=lambda x: (
            order[x.split(".", 1)[0]],
            *map(int, x.split(".")[1:]))):
        payload = key.encode("ascii")
        h.update(len(payload).to_bytes(2, "big"))
        h.update(payload)
    return h.hexdigest()


def compare_mapped_scope(
    source_books: list[str], source_keys: list[tuple[str, int, int]],
    native_keys_text: str, pairs: list[tuple[str, str]]
) -> dict:
    """No inferred books, renumbering, omitted verse or edition-specific rule."""
    if not pairs or len(set(pairs)) != len(pairs):
        raise BookScopeError("Empty or duplicate canonical mapping")
    map_usfm = dict(pairs)
    mapped_order = {name: i for i, (_src, name) in enumerate(pairs)}
    if len(map_usfm) != len(pairs) or len(mapped_order) != len(pairs):
        raise BookScopeError("Ambiguous source/native canonical book mapping")
    if (not source_books or len(source_books) != len(set(source_books))
            or any(not USFM_BOOK.fullmatch(code) for code in source_books)):
        raise BookScopeError("Ambiguous source book inventory")
    source_book_set = set(source_books)
    source_seen: set[tuple[str, int, int]] = set()
    source_mapped = set()
    extras = {}
    for book, chapter, verse in source_keys:
        if (book not in source_book_set
                or not isinstance(chapter, int) or not isinstance(verse, int)
                or chapter < 1 or verse < 1):
            raise BookScopeError("Source verse outside identified book/chapter/verse")
        ref = (book, chapter, verse)
        if ref in source_seen:
            raise BookScopeError("Repeated source-authored verse identifier")
        source_seen.add(ref)
        if book in map_usfm:
            source_mapped.add(f"{map_usfm[book]}.{chapter}.{verse}")
        else:
            extras[book] = extras.get(book, 0) + 1
    # Preserve unnumbered source books as well (FRT/GLO, etc.).
    source_out_of_scope = [
        {"source_usfm_code": book, "authored_numbered_verses": extras.get(book, 0)}
        for book in source_books if book not in map_usfm]
    native_set = {"%s.%d.%d" % item for item in parse_keys(native_keys_text)}
    native_books_in_order = []
    previous = None
    for line in native_keys_text.splitlines():
        book = line.split(".", 1)[0]
        if book != previous:
            if book in native_books_in_order:
                raise BookScopeError("Native reader returned noncontiguous books")
            native_books_in_order.append(book)
            previous = book
    source_canon_order = [code for code in source_books if code in map_usfm]
    expected_src = [p[0] for p in pairs]
    expected_native = [p[1] for p in pairs]
    same_authorial_book_order = source_canon_order == expected_src
    same_native_book_order = native_books_in_order == expected_native
    native_extra_books = [book for book in native_books_in_order
                          if book not in mapped_order]
    if native_extra_books:
        # Never compare a different native canon by silently discarding data.
        native_canonical = {ref for ref in native_set
                            if ref.split(".", 1)[0] in mapped_order}
    else:
        native_canonical = native_set
    missing = source_mapped - native_canonical
    additional = native_canonical - source_mapped
    canonical_index_exact = bool(
        same_authorial_book_order and same_native_book_order
        and not missing and not additional
    )
    if not same_authorial_book_order or not same_native_book_order:
        status = "blocked_crosswalk_book_scope_or_order_mismatch"
    elif missing or additional:
        status = "blocked_mapped_canonical_verse_key_difference"
    elif source_out_of_scope:
        status = "canonical_index_exact_source_has_extra_authored_books_to_review"
    else:
        status = "canonical_index_exact_but_compiled_content_unverified"
    return {
        "schema_version": 1,
        "status": status,
        "mapping_source": "explicit_reviewed_usfm_to_native_osis_crosswalk",
        "mapped_book_count": len(pairs),
        "source_mapped_book_count": len(source_canon_order),
        "native_mapped_book_count": len(native_books_in_order) - len(native_extra_books),
        "source_canonical_book_order_verified": same_authorial_book_order,
        "native_canonical_book_order_verified": same_native_book_order,
        "source_canonical_numbered_key_count": len(source_mapped),
        "native_canonical_numbered_key_count": len(native_canonical),
        "source_canonical_keys_sha256": _digest_osis_references(source_mapped, mapped_order),
        "native_canonical_keys_sha256": _digest_osis_references(native_canonical, mapped_order),
        "canonical_verse_keys_exact_after_explicit_book_mapping": canonical_index_exact,
        "source_canonical_refs_unreachable_in_reader_count": len(missing),
        "native_canonical_refs_not_authored_in_source_count": len(additional),
        "first_unreachable_source_refs": sorted(missing)[:30],
        "first_unexpected_reader_refs": sorted(additional)[:30],
        "additional_original_source_book_count": len(source_out_of_scope),
        "additional_original_source_numbered_verse_count": sum(extras.values()),
        "all_original_extra_source_books_preserved_as_evidence": source_out_of_scope,
        "unexpected_native_book_codes": native_extra_books,
        "out_of_scope_source_text_notes_and_structure_verified": False,
        "exact_original_source_edition_and_revision_equals_sword_verified": False,
        "source_to_compiled_text_notes_lexical_and_layout_verified": False,
        "authorial_full_source_to_compiled_scope_fidelity_verified": False,
        "official_schema_and_conversion_independently_verified": False,
        "rights_and_publication_approved": False,
        "published": False,
    }
