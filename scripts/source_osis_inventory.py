#!/usr/bin/env python3
"""Independent, text-free authorial verse-key inventory from original OSIS.

A producer for stable_sword_refs.py, NOT a replacement for the official OSIS
schema guard, an upstream USFM/USFX source audit or actual SWORD reader scan.
Unknown/malformed verse markup blocks: never silently fix source keys.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from lxml import etree

from stable_sword_refs import KEY

NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"
OSIS = f"{{{NS}}}"
MARKERS = ("title", "p", "lg", "l", "note", "reference", "w", "q", "seg")
MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_KEYS = 250_000
MAX_BOOKS = 250


class SourceInventoryError(ValueError):
    """Original edition needs editorial investigation; nothing is repaired."""


def _read_source(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise SourceInventoryError("Source must be an existing, non-symlink OSIS file")
    if not 0 < path.stat().st_size <= MAX_SOURCE_BYTES:
        raise SourceInventoryError("Empty or oversized source OSIS")
    return path.read_bytes()


def _source_tree(data: bytes) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
        huge_tree=False, recover=False, remove_comments=False)
    try:
        tree = etree.ElementTree(etree.fromstring(data, parser))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise SourceInventoryError(f"Source is not well-formed XML: {exc}") from exc
    if tree.docinfo.doctype or tree.docinfo.internalDTD or tree.docinfo.externalDTD:
        raise SourceInventoryError("DTD/entity declarations are not allowed in source inventory")
    root = tree.getroot()
    if root.tag != OSIS + "osis":
        raise SourceInventoryError("Expected official OSIS-namespace osis root")
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise SourceInventoryError("Unresolved XML entity in OSIS")
    return root


def _book_inventory(book: etree._Element) -> tuple[list[str], dict]:
    name = book.get("osisID")
    if not name or not name.isascii() or not name.isalnum() or (
            name[0].isdigit() and name[0] not in "1234"):
        raise SourceInventoryError("Unsupported book osisID")
    if len(name) > 40 or name[0] not in "1234ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
        raise SourceInventoryError(f"Unsupported book identifier: {name!r}")
    seen = set()
    keys: list[str] = []
    chapters = set()
    last = (0, 0)
    active: str | None = None
    all_markers = Counter()
    intro_markers = Counter()
    seen_first = False
    first_gaps = []
    for node in book.iter():
        if not isinstance(node.tag, str):
            continue
        local = etree.QName(node).localname
        if local == "verse" and node.tag != OSIS + "verse":
            raise SourceInventoryError(f"{name}: verse in unsupported XML namespace")
        if node.tag in {OSIS + tag for tag in MARKERS}:
            all_markers[local] += 1
            if not seen_first:
                intro_markers[local] += 1
        if node.tag != OSIS + "verse":
            continue
        if any(a.tag == OSIS + "verse" for a in node.iterancestors()):
            raise SourceInventoryError(f"{name}: nested verse markup")
        start, end, identifier = node.get("sID"), node.get("eID"), node.get("osisID")
        if end is not None:
            if start is not None or identifier is not None or not end:
                raise SourceInventoryError(f"{name}: malformed verse closing milestone")
            if active != end:
                raise SourceInventoryError(f"{name}: orphan or mismatched verse eID")
            if len(node) or (node.text or "").strip():
                raise SourceInventoryError(f"{name}: nonempty verse closing milestone")
            active = None
            continue
        if identifier is None or not KEY.fullmatch(identifier):
            raise SourceInventoryError(f"{name}: missing, ranged or unsupported verse osisID")
        book_id, ch, verse = identifier.rsplit(".", 2)
        if book_id != name:
            raise SourceInventoryError(f"{name}: verse belongs to a different OSIS book")
        position = (int(ch), int(verse))
        if identifier in seen or position <= last:
            raise SourceInventoryError(f"{name}: duplicated or out-of-order authorial verse: {identifier}")
        if active is not None:
            raise SourceInventoryError(f"{name}: previous verse sID has no matching eID")
        if start is not None and (not start or len(node) or (node.text or "").strip()):
            raise SourceInventoryError(f"{name}: malformed or nonempty opening milestone")
        if start is None and any(d.tag == OSIS + "verse" for d in node.iterdescendants()):
            raise SourceInventoryError(f"{name}: nested container verse")
        if position[0] == last[0] and position[1] > last[1] + 1 and len(first_gaps) < 25:
            first_gaps.append({"chapter": position[0], "after": last[1],
                               "before": position[1]})
        seen.add(identifier)
        keys.append(identifier)
        chapters.add(position[0])
        last = position
        seen_first = True
        if start is not None:
            active = start
        if len(keys) > MAX_KEYS:
            raise SourceInventoryError(f"{name}: unbounded verse inventory")
    if active is not None:
        raise SourceInventoryError(f"{name}: final verse sID is unclosed")
    if not keys:
        raise SourceInventoryError(f"{name}: no authored numbered verses")
    return keys, {
        "book": name,
        "source_verse_count": len(keys),
        "source_chapter_count": len(chapters),
        "first_authored_verse": keys[0],
        "last_authored_verse": keys[-1],
        "first_internal_numbering_gaps_not_missing_text_claims": first_gaps,
        "whole_book_tag_counts": {k: all_markers[k] for k in MARKERS},
        "tags_before_first_numbered_verse": {k: intro_markers[k] for k in MARKERS},
    }


def source_inventory(source: bytes) -> tuple[str, dict]:
    """Enumerate authored indexes in source order. Never synthesize missing IDs."""
    root = _source_tree(source)
    books = [node for node in root.iter(OSIS + "div")
             if node.get("type") == "book"]
    if not books or len(books) > MAX_BOOKS:
        raise SourceInventoryError("No books or implausibly many OSIS book divs")
    if any(any(parent.tag == OSIS + "div" and parent.get("type") == "book"
               for parent in book.iterancestors()) for book in books):
        raise SourceInventoryError("Nested OSIS books are not supported")
    keys: list[str] = []
    summaries = []
    names = set()
    verse_nodes = sum(1 for n in root.iter(OSIS + "verse"))
    counted_nodes = 0
    for book in books:
        name = book.get("osisID")
        if name in names:
            raise SourceInventoryError(f"Repeated book osisID: {name!r}")
        names.add(name)
        counted_nodes += sum(1 for _ in book.iter(OSIS + "verse"))
        book_keys, summary = _book_inventory(book)
        keys.extend(book_keys)
        summaries.append(summary)
        if len(keys) > MAX_KEYS:
            raise SourceInventoryError("Source verse count exceeds safe bound")
    if verse_nodes != counted_nodes:
        raise SourceInventoryError("Authored verse outside a recognized OSIS book")
    key_text = "".join(ref + "\n" for ref in keys)
    if len(set(keys)) != len(keys):
        raise SourceInventoryError("Repeated canonical verse key across OSIS books")
    return key_text, {
        "schema_version": 1,
        "status": "source_osis_verse_keys_inventoried_not_release_approved",
        "source_kind": "original_osis",
        "source_osis_sha256": sha256(source).hexdigest(),
        "source_keys_sha256": sha256(key_text.encode("utf-8")).hexdigest(),
        "source_book_count": len(summaries),
        "source_chapter_count": sum(x["source_chapter_count"] for x in summaries),
        "source_verse_count": len(keys),
        "books": summaries,
        "original_source_modified": False,
        "original_osis_schema_validated": False,
        "actual_stock_sword_reader_keys_verified": False,
        "compiled_text_notes_lexical_and_structure_verified": False,
        "source_editorial_approval": False,
        "published": False,
    }


def _write_outputs(keys_file: Path, report_file: Path, keys: str, report: dict,
                   source_path: Path) -> None:
    if len({p.resolve() for p in (keys_file, report_file, source_path)}) != 3:
        raise SourceInventoryError("Input and output paths must be distinct")
    if any(p.is_symlink() or p.exists() for p in (keys_file, report_file)):
        raise SourceInventoryError("Refusing to overwrite existing report/key file")
    for p in (keys_file, report_file):
        if not p.parent.is_dir() or p.parent.is_symlink():
            raise SourceInventoryError("Output parents must exist and not be symlinks")
    payloads = (
        (keys_file, keys.encode("utf-8")),
        (report_file, (json.dumps(report, indent=2, sort_keys=True)
                       + "\n").encode("utf-8")),
    )
    temps = []
    created = []
    try:
        for path, data in payloads:
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".osis-inventory-")
            temps.append(Path(tmp))
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
        for (dest, _), temp in zip(payloads, temps):
            if dest.exists() or dest.is_symlink():
                raise SourceInventoryError("Output appeared during inventory generation")
            os.replace(temp, dest)
            created.append(dest)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    finally:
        for temp in temps:
            temp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-osis", type=Path, required=True)
    parser.add_argument("--keys-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        keys, report = source_inventory(_read_source(args.source_osis))
        _write_outputs(args.keys_output, args.report, keys, report, args.source_osis)
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    print(f"Inventoried {report['source_verse_count']} authorial verse keys"
          f" in {report['source_book_count']} books. No publication approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
