#!/usr/bin/env python3
"""Read-only source USFX pre-chapter paragraph versus native book-intro scope.

This is deliberately NOT equivalence or publication approval. Maintext and
note bodies never leave temporary process memory, and no original XML is
uploaded. The primary question: are pre-chapter <p>s empty markers or authored
content, and are book intro slots present to account for them?
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

from lxml import etree

from source_usfx_structure import audit_source_usfx
from native_milestone_pair_audit import _strict_root
from sword_native_inventory import INTRO

MAX_EXAMPLES = 24
SKIP = frozenset({"f", "fe", "x", "ef", "ex", "note", "title"})
WORD = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)


class BookPrefaceError(ValueError):
    """Untrusted original structure or unsupported source/native scope."""


def _main_text(node) -> str:
    bits = []

    def walk(element):
        if not isinstance(element.tag, str):
            return
        tag = etree.QName(element).localname
        if tag in SKIP:
            return
        if tag not in {"c", "v"} and element.text:
            bits.append(element.text)
        for child in element:
            walk(child)
            if child.tail:
                bits.append(child.tail)

    walk(node)
    return "".join(bits)


def _nfc_words(value: str) -> str:
    return " ".join(value.split())


def original_book_prefaces(xml: bytes, mapping: list[tuple[str, str]]):
    """Keep authored pre-chapter p contents private, return no Scripture."""
    checked = audit_source_usfx(xml)
    if checked["source_structural_issues"]:
        raise BookPrefaceError("Original USFX structural anomalies")
    if not mapping or len(mapping) != len(set(mapping)):
        raise BookPrefaceError("Duplicate original/native book crosswalk")
    pairs = dict(mapping)
    if len(pairs) != len(mapping) or len(set(pairs.values())) != len(mapping):
        raise BookPrefaceError("Ambiguous original/native book crosswalk")

    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise BookPrefaceError("Original USFX cannot be parsed") from exc
    counts = Counter()
    per_book = {}
    seen = set()
    for book in root.iter("book"):
        source_code = book.get("id", "")
        if source_code in seen or not source_code:
            raise BookPrefaceError("Duplicate or unidentified authorial book")
        seen.add(source_code)
        if source_code not in pairs:
            counts["unmapped_original_book"] += 1
            continue
        target = pairs[source_code]
        first_chapter = next((child for child in book.iterdescendants()
                              if isinstance(child.tag, str)
                              and etree.QName(child).localname == "c"), None)
        if first_chapter is None:
            raise BookPrefaceError("Authorial book lacks chapter")
        prefatory = []
        for child in book.iterdescendants():
            if child is first_chapter:
                break
            if not isinstance(child.tag, str) or etree.QName(child).localname != "p":
                continue
            # This audit studies markup outside notes, headings or other
            # editorial containers, not their internal paragraph elements.
            parent = child.getparent()
            nested = False
            while parent is not None and parent is not book:
                if isinstance(parent.tag, str) and etree.QName(parent).localname in SKIP:
                    nested = True
                    break
                parent = parent.getparent()
            if nested:
                counts["pre_chapter_p_inside_annotation"] += 1
                continue
            if any(isinstance(n.tag, str) and etree.QName(n).localname in {"c", "v"}
                   for n in child.iterdescendants()):
                raise BookPrefaceError("Source prechapter p contains numbered milestones")
            text = _main_text(child)
            tokens = len(WORD.findall(text))
            prefatory.append(text)
            counts["source_pre_chapter_p"] += 1
            counts["source_pre_chapter_p_with_authored_words" if tokens
                   else "source_pre_chapter_p_without_authored_words"] += 1
            if not tokens and text:
                counts["source_pre_chapter_p_only_whitespace_or_symbols"] += 1
            if len(child):
                counts["source_pre_chapter_p_with_nested_elements"] += 1
        per_book[target] = prefatory
    if len(seen) != checked["source_book_count"] or not set(pairs).issubset(seen):
        raise BookPrefaceError("Source book census disagrees with original inventory")
    return per_book, dict(sorted(counts.items()))


class NativeBookPrefaceEvidence:
    """Observe book-level I entries (not chapter-zero or numbered verses)."""

    def __init__(self):
        self._entries = {}
        self._bad = Counter()

    def observe(self, kind: str, ref: str, raw: bytes):
        if kind != "I" or not INTRO.fullmatch(ref):
            return
        # Explicitly distinguish native chapter intros from book-level
        # intro slots; no inferring a missing slot from chapter data.
        if "." in ref and not ref.endswith(".0.0"):
            return
        book = ref.split(".", 1)[0]
        if book in self._entries:
            raise BookPrefaceError("Duplicate book intro identity")
        try:
            root = _strict_root(raw)
        except ValueError:
            self._bad["unparseable_native_book_intro"] += 1
            self._entries[book] = None
            return
        original_text = _main_text(root)
        typed_div = sum(
            1 for node in root.iterdescendants()
            if isinstance(node.tag, str) and etree.QName(node).localname == "div"
            and node.get("type") == "x-p"
        )
        structural = Counter()
        for node in root.iterdescendants():
            if isinstance(node.tag, str):
                tag = etree.QName(node).localname
                if tag in {"div", "l", "lg", "p", "milestone", "title"}:
                    structural[tag] += 1
        self._entries[book] = {
            "text": original_text,
            "x_p_element_count": typed_div,
            "structural":structural,
        }

    def finish(self, prefaces: dict[str, list[str]], source_counts: dict):
        counts = Counter(source_counts)
        samples = []
        checked = 0
        source_words_in_intro = 0
        for book, texts in prefaces.items():
            checked += 1
            native = self._entries.get(book)
            if native is None:
                counts["books_without_parseable_native_book_intro"] += 1
                if len(samples) < MAX_EXAMPLES:
                    samples.append({"book": book, "condition": "no_parseable_book_intro"})
                continue
            counts["books_with_parseable_native_book_intro"] += 1
            counts["native_book_intro_typed_x_p_elements"] += native["x_p_element_count"]
            for tag, count in native["structural"].items():
                counts[f"native_book_intro_{tag}_elements"] += count
            for src in texts:
                if not WORD.findall(src):
                    continue
                counts["source_p_with_words_and_parseable_native_book_intro"] += 1
                # This is only a whole-intro lexical containment diagnostic;
                # intro may contain unrelated headings and repeated phrases.
                src_norm = _nfc_words(src)
                native_norm = _nfc_words(native["text"])
                if src_norm and src_norm in native_norm:
                    source_words_in_intro += 1
                else:
                    counts["source_p_text_not_contiguous_in_native_intro"] += 1
                    if len(samples) < MAX_EXAMPLES:
                        samples.append({"book":book,"condition":"preface_text_not_contiguous"})
        counts["source_p_text_contiguous_in_native_intro_only"] = source_words_in_intro
        counts["mapped_books_inspected"] = checked
        counts["observed_native_book_intro_entry_count"] = len(self._entries)
        return {
            "schema_version": 1,
            "preface_inventory_counts": dict(sorted(counts.items())),
            "first_findings_no_text": samples,
            "no_scripture_or_raw_markup_in_receipt": True,
            "original_p_text_rewritten_or_trimmed": False,
            "book_intro_contains_text_is_not_source_layout_parity": True,
            "original_preface_p_to_typed_div_position_parity_verified": False,
            "editorial_and_publication_approved": False,
        }
