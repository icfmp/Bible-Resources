#!/usr/bin/env python3
"""Research-only transport of selected *original* numbered SWORD raw XML to OSIS.

The output is private temporary test material, NEVER a curated commentary
edition. Original K raw fragments are inserted verbatim, without HTML escaping,
punctuation normalization or re-authoring. Contiguous native keys whose bytes
are exactly identical can be represented by one range; this is a transport
compression only, NOT proof that an author intended a joint editorial section.

I introductions and U TOP are deliberately NOT included; this script MUST NOT
be used to create a distributable module. The caller must separately check all
original native entries and the independently determined editorial scopes.
"""
from __future__ import annotations

from hashlib import sha256
import re
from lxml import etree

KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)\.([1-9]\d*)$")
WORK = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,39}$")
MAX_FRAGMENTS = 12000
MAX_BYTES = 160 * 1024 * 1024
OSIS_NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def _strict_parser():
    return etree.XMLParser(resolve_entities=False, no_network=True,
                           load_dtd=False, recover=False, huge_tree=False,
                           remove_blank_text=False, strip_cdata=False)


def _source_visible_text(raw: bytes) -> str:
    try:
        root = etree.fromstring(b"<fragment>" + raw + b"</fragment>",
                               parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original SWORD XML is not safely parseable") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError("Unresolved source XML entity")
    return "".join(root.itertext())


def build_numbered_transport_sample(entries: list[tuple[str, bytes]],
                                    *, work_id: str) -> tuple[bytes, dict]:
    """Return private syntactically parsed OSIS bytes plus text-free receipt."""
    if not WORK.fullmatch(work_id):
        raise ValueError("Invalid isolated synthetic transport module work ID")
    if not entries or len(entries) > MAX_FRAGMENTS:
        raise ValueError("Empty or excessive sampled commentary K records")

    groups = []
    seen = set()
    total_bytes = 0
    last_pos = None
    last_book_chapter = None
    for ref, raw in entries:
        matched = KEY.fullmatch(ref) if isinstance(ref, str) else None
        if (matched is None or ref in seen or not isinstance(raw, bytes)
                or b"\x00" in raw or not raw.strip()):
            raise ValueError("Unreviewed original sampled K frame")
        seen.add(ref)
        book, chapter, verse = matched.group(1), int(matched.group(2)), int(matched.group(3))
        location = (book, chapter, verse)
        if last_pos is not None and (book, chapter) == last_book_chapter and verse <= last_pos[2]:
            raise ValueError("Original native K frame order is not increasing within chapter")
        # The independent full raw stream controls canonical inter-book order.
        if last_pos is not None and (book, chapter) != last_book_chapter:
            if (book, chapter) in {group["chapter_key"] for group in groups}:
                raise ValueError("Original chapter appeared non-contiguously in sampled stream")
        total_bytes += len(raw)
        if total_bytes > MAX_BYTES:
            raise ValueError("Selected original raw content exceeds bounded private OSIS probe")
        _source_visible_text(raw)
        digest = sha256(raw).hexdigest()
        if (groups and groups[-1]["chapter_key"] == (book, chapter)
                and groups[-1]["digest"] == digest
                and groups[-1]["last_verse"] + 1 == verse):
            groups[-1]["last_verse"] = verse
            groups[-1]["native_key_count"] += 1
        else:
            groups.append({
                "chapter_key": (book, chapter),
                "first_verse": verse, "last_verse": verse,
                "digest": digest, "raw": raw, "native_key_count": 1
            })
        last_book_chapter = book, chapter
        last_pos = location

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>'.encode(),
        f'<osis xmlns="{OSIS_NS}">'.encode(),
        f'<osisText osisIDWork="{work_id}" osisRefWork="Commentary" xml:lang="en" canonical="true">'.encode(),
        (f'<header><work osisWork="{work_id}"><title>Synthetic temporary original-'
         f'raw OSIS transport probe</title><identifier type="OSIS">'
         f'{work_id}</identifier><refSystem>Bible.KJV</refSystem></work></header>').encode(),
        b'<div type="bookGroup">',
    ]
    current_book = None
    current_chapter = None
    for group in groups:
        book, chapter = group["chapter_key"]
        if book != current_book:
            if current_chapter is not None:
                parts.append(b"</div>")
            if current_book is not None:
                parts.append(b"</div>")
            parts.append(f'<div type="book" osisID="{book}">'.encode())
            current_book = book
            current_chapter = None
        if chapter != current_chapter:
            if current_chapter is not None:
                parts.append(b"</div>")
            parts.append(f'<div type="chapter" osisID="{book}.{chapter}">'.encode())
            current_chapter = chapter
        first, last = group["first_verse"], group["last_verse"]
        ref = f"{book}.{chapter}.{first}"
        if last != first:
            ref += f"-{book}.{chapter}.{last}"
        parts.append(
            f'<div type="section" annotateType="commentary" annotateRef="{ref}">'.encode()
        )
        parts.append(group["raw"])
        parts.append(b"</div>")
    if current_chapter is not None:
        parts.append(b"</div>")
    if current_book is not None:
        parts.append(b"</div>")
    parts.extend([b"</div>", b"</osisText>", b"</osis>"])
    xml = b"\n".join(parts)
    if len(xml) > MAX_BYTES + MAX_FRAGMENTS * 320:
        raise ValueError("Private transport document exceeds safe length")

    try:
        parsed = etree.fromstring(xml, parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Verbatim source fragments do not form a valid OSIS XML document") from None
    if any(isinstance(node, etree._Entity) for node in parsed.iter()):
        raise ValueError("Unsafe entity in selected transport OSIS document")
    wrapped_sections = parsed.xpath(
        "//*[local-name()='div' and @annotateType='commentary']"
    )
    if len(wrapped_sections) != len(groups):
        raise ValueError("Verbatim source sections were not preserved in standard OSIS wrapper")
    for group, section in zip(groups, wrapped_sections):
        if "".join(section.itertext()) != _source_visible_text(group["raw"]):
            raise ValueError("Original fragment lost or changed Unicode characters in OSIS wrapper")
    return xml, {
        "status": "ORIGINAL_NUMBERED_ONLY_TEMPORARY_TRANSPORT_NOT_EDITION",
        "input_numbered_native_keys": len(entries),
        "contiguous_identical_raw_body_groups": len(groups),
        "groups_with_multiple_original_native_verse_keys":
            sum(group["native_key_count"] > 1 for group in groups),
        "source_original_raw_bytes_in_reviewed_input": total_bytes,
        "source_original_raw_bytes_included_verbatim_in_osis": sum(
            len(group["raw"]) for group in groups
        ),
        "temporary_osis_bytes": len(xml),
        "source_unmodified_unicode_visible_text_in_syntax_approved_osis": True,
        "original_introductions_preserved_in_candidate": False,
        "original_top_preserved_in_candidate": False,
        "compiler_roundtrip_parity_proven": False,
        "authorial_scope_approved": False,
        "no_publication": True,
    }
