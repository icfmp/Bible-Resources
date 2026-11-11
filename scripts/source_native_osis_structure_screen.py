#!/usr/bin/env python3
"""Metadata-only original OSIS vs compiled raw-SWORD structural census.

This is a necessary *screen*, never a source-relative start/end or renderer
proof. Count explicit markup outside footnotes without exposing source text.
"""
from __future__ import annotations

from collections import Counter

from lxml import etree

from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY

STYLES = frozenset({"p", "l", "lg", "lb", "title"})


class OSISStructureScreenError(ValueError):
    """Unsafe or ambiguous original/native structural XML."""


def _name(element):
    return etree.QName(element).localname if isinstance(element.tag, str) else ""


def _markup_elements(root):
    for element in root.iter():
        name = _name(element)
        if not name:
            continue
        if any(_name(parent) in {"note", "header"} for parent in element.iterancestors()):
            continue
        if name in {"note", "header"}:
            continue
        yield element, name


def authorial_structures(xml: bytes) -> dict[str, int]:
    root = _source_tree(xml)  # strict, publisher namespace and DTD validation
    counts = Counter()
    for element, name in _markup_elements(root):
        if name in STYLES:
            counts[f"source_{name}_elements"] += 1
        elif name == "div" and element.get("type") == "paragraph":
            counts["source_paragraph_div_elements"] += 1
    return dict(sorted(counts.items()))


class NativeStructuralCensus:
    """One-by-one isolated raw entry ingestion, excluding notes/headings."""

    def __init__(self):
        self.counts = Counter()
        self.records = 0

    def observe(self, raw: bytes):
        try:
            root = etree.fromstring(
                b"<census>"+raw+b"</census>",
                etree.XMLParser(resolve_entities=False, load_dtd=False,
                                no_network=True, recover=False, huge_tree=False))
        except etree.XMLSyntaxError as exc:
            raise OSISStructureScreenError("Invalid native raw XML structure") from exc
        if any(isinstance(x, etree._Entity) for x in root.iter()):
            raise OSISStructureScreenError("Unresolved native XML entity")
        self.records += 1
        for element, name in _markup_elements(root):
            if name == "div" and element.get("type") == "x-p":
                if element.get("sID") and not element.get("eID"):
                    self._event("paragraph_open")
                elif element.get("eID") and not element.get("sID"):
                    self._event("paragraph_close")
                else:
                    raise OSISStructureScreenError("Ambiguous native paragraph milestone")
            elif name in {"p", "l", "lg", "lb", "title"}:
                if element.get("sID") or element.get("eID"):
                    if element.get("sID") and not element.get("eID"):
                        self._event(name + "_open")
                    elif element.get("eID") and not element.get("sID"):
                        self._event(name + "_close")
                    else:
                        raise OSISStructureScreenError("Ambiguous native structure milestone")
                else:
                    self._event(name + "_container")

    def _event(self, kind):
        self.counts[f"native_{kind}_elements"] += 1

    def receipt(self):
        if self.records <= 0:
            raise OSISStructureScreenError("No native original-SWORD records inspected")
        return {
            "original_to_native_editorial_structure_counts": dict(sorted(self.counts.items())),
            "actual_compiled_raw_entries_scanned": self.records,
            "semantic_source_native_event_position_or_scope_verified": False,
            "source_native_structural_count_equality_not_inferred": True,
            "editorial_layout_and_visual_signoff_deferred_to_stage_5": True,
        }


def authorial_body_opening_sequences(xml: bytes):
    """Original per-book p/l opening kind order; private verse labels only.

    Comparisons to native milestone order are not a word-position, end-boundary,
    note, heading or reader-layout certificate.
    """
    root = _source_tree(xml)
    books = [n for n in root.iter(OSIS+"div") if n.get("type") == "book"]
    if not books or len(books) > 250:
        raise OSISStructureScreenError("Missing or implausible authored book scope")
    output = {}
    counts = Counter()
    for book in books:
        ident=book.get("osisID")
        if not ident or not ident.isascii() or not ident.isalnum() or len(ident)>40:
            raise OSISStructureScreenError("Unsafe original book key")
        if ident in output:
            raise OSISStructureScreenError("Duplicate original book key")
        if any(p.tag==OSIS+"div" and p.get("type")=="book"
               for p in book.iterancestors()):
            raise OSISStructureScreenError("Nested authored book")
        last_ref=ident
        events=[]
        for n in book.iter():
            if not isinstance(n.tag,str):
                continue
            if n.tag==OSIS+"verse" and n.get("osisID"):
                ref=n.get("osisID")
                if not KEY.fullmatch(ref) or not ref.startswith(ident+"."):
                    raise OSISStructureScreenError("Invalid source location for structure")
                last_ref=ref
            if n.tag not in {OSIS+"p",OSIS+"l"}:
                continue
            if any(a.tag in {OSIS+"note",OSIS+"header",OSIS+"title"}
                   for a in n.iterancestors() if a is not book):
                counts["excluded_annotation_embedded_structure"]+=1
                continue
            kind="p" if n.tag==OSIS+"p" else "q"
            events.append((kind,last_ref))
            counts["source_body_"+kind+"_openings"]+=1
        output[ident]=events
    return output,dict(sorted(counts.items()))
