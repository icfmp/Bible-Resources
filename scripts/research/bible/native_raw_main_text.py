"""Source-format-independent, strict private SWORD raw main-text reader.

Used by OSIS and legacy USFX source/native audits. No prose is returned in
reports, and malformed native XML never receives a silent repair.
"""
from __future__ import annotations

from collections import Counter

from lxml import etree

from research.bible.native_sword_markup_census import NativeMarkupCensus

MAX_VERSE = 2 * 1024 * 1024
NATIVE_SKIP = {"note", "title"}


class MainTextParityError(ValueError):
    """Authored or native text could not be independently audited."""


def native_raw_main_text(raw: bytes, *, markup_census: NativeMarkupCensus | None = None,
                         reference: str | None = None) -> tuple[str, dict]:
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
    if markup_census is not None:
        if reference is None:
            raise MainTextParityError("Native markup census needs an actual reader reference")
        markup_census.observe(reference, root)
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
