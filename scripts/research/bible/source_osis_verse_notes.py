"""Strict, read-only original OSIS verse/note parser shared by source-native checks.

This module returns private in-memory text to its checked callers; never export
these text and note bodies in public metadata receipts. This is a source
inspector, not a source correction, USFX conversion or release approval.
"""
from __future__ import annotations

from collections import Counter
import unicodedata

from lxml import etree

from source_osis_inventory import source_inventory, _source_tree, OSIS
from stable_sword_refs import KEY

MAX_NOTE_TEXT = 2 * 1024 * 1024
EXCLUDED_MAIN = frozenset({"note", "title", "header"})


class OSISSourceReaderError(ValueError):
    """Untrusted, contradictory or unsafe authored OSIS source evidence."""


def _nonspace(value: str) -> str:
    return "".join(c for c in value if not c.isspace())


def _fold(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def original_osis_verses_and_notes(xml: bytes):
    """Independently reconstruct verse prose, note bodies and note anchors.

    Only explicit verse IDs are used. Verse milestones must pair exactly;
    neither malformed tags nor unknown source text is silently discarded.
    """
    # This already rejects wrong namespace, DTD and duplicate/out-of-order
    # verse milestones under the approved original-source OSIS grammar.
    source_keys, structural = source_inventory(xml)
    root = _source_tree(xml)
    books = root.findall(".//" + OSIS + "div[@type='book']")
    if not books or len(books)>250:
        raise OSISSourceReaderError("Unrecognized publisher OSIS book divisions")
    text = {}
    notes = {}
    extra = Counter()
    seen_books = set()
    for book in books:
        book_id = book.get("osisID")
        if (not isinstance(book_id,str) or not book_id
                or book_id in seen_books):
            raise OSISSourceReaderError("Duplicate or unreviewed OSIS book ID")
        seen_books.add(book_id)
        current = None
        codepoints = 0
        verse_container = []

        def append(fragment):
            nonlocal codepoints
            if current is not None and fragment:
                text[current].append(fragment)
                codepoints += sum(not character.isspace() for character in fragment)

        def visit(node, depth=0):
            nonlocal current, codepoints
            if depth > 256:
                raise OSISSourceReaderError("Excessive official OSIS nesting")
            if not isinstance(node.tag,str):
                return
            local=etree.QName(node).localname
            if local in EXCLUDED_MAIN:
                if any(x.tag == OSIS+"verse" for x in node.iterdescendants()):
                    raise OSISSourceReaderError(
                        "Publisher heading/note encloses verse numbering")
                if local == "note":
                    body="".join(node.itertext())
                    if len(body.encode("utf-8")) > MAX_NOTE_TEXT:
                        raise OSISSourceReaderError("Oversized official source note")
                    if current is None:
                        extra["notes_outside_numbered_verses"] += 1
                    else:
                        # Preserve original labels and linked explicit targets
                        # privately; only safe aggregates leave this module.
                        notes[current].append({
                            "body":body,
                            "caller":node.get("n"),
                            "type":node.get("type"),
                            "point":codepoints,
                            "targets":tuple(
                                x.get("osisRef") for x in node.iterdescendants()
                                if x.tag == OSIS+"reference" and x.get("osisRef")
                            ),
                        })
                return

            is_container=False
            if node.tag == OSIS+"verse":
                closing=node.get("eID")
                start=node.get("sID")
                reference=node.get("osisID")
                if closing:
                    if current != closing or start or reference:
                        raise OSISSourceReaderError(
                            "Mispaired publisher OSIS verse milestone")
                    current=None
                    return
                if not reference or KEY.fullmatch(reference) is None:
                    raise OSISSourceReaderError(
                        "Invalid publisher OSIS numbered verse identifier")
                if (start and start != reference) or current is not None:
                    raise OSISSourceReaderError(
                        "Overlapping publisher OSIS verse scope")
                if reference in text or not reference.startswith(book_id+"."):
                    raise OSISSourceReaderError(
                        "Publisher OSIS verse duplicates or leaves its book")
                text[reference]=[]
                notes[reference]=[]
                current=reference
                codepoints=0
                is_container=not bool(start)
                if is_container:
                    verse_container.append(reference)
            append(node.text)
            for child in node:
                visit(child, depth+1)
                append(child.tail)
            if is_container:
                if current != verse_container.pop():
                    raise OSISSourceReaderError(
                        "Publisher OSIS container verse cannot be closed")
                current=None

        visit(book)
        if current is not None or verse_container:
            raise OSISSourceReaderError("Unclosed publisher OSIS verse/book boundary")
    if set(text)!=set(source_keys.splitlines()):
        raise OSISSourceReaderError(
            "Independent source inventory and text reader disagree on verse scope")
    if len(seen_books)!=structural["source_book_count"]:
        raise OSISSourceReaderError(
            "Original OSIS book metadata disagrees with independent inspector")
    strings={ref:"".join(parts) for ref,parts in text.items()}
    if any(len(s.encode("utf-8"))>MAX_NOTE_TEXT for s in strings.values()):
        raise OSISSourceReaderError("Oversized publisher Bible verse")
    return strings,notes,{
        "publisher_book_count":len(seen_books),
        "publisher_numbered_verse_count":len(strings),
        "publisher_numbered_note_count":sum(map(len,notes.values())),
        "publisher_notes_outside_numbered_verses":
            extra["notes_outside_numbered_verses"],
        "source_osis_verse_key_sha256":structural["source_keys_sha256"],
        "source_osis_schema_version":1,
    }


