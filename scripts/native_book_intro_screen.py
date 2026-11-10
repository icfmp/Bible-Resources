#!/usr/bin/env python3
"""Compare private USFX prefatory paragraph words to actual native SWORD intros.

Generic research-only evidence. The publisher source and stock SWORD bytes
remain immutable. No preface text, native XML or attribute values are logged.
A substring match NEVER establishes exact editorial event/position fidelity.
"""
from __future__ import annotations

from collections import Counter
from lxml import etree

from source_native_paragraph_counts import audit_usfx_book_prefaces, IGNORE_CONTAINER
from native_milestone_pair_audit import _strict_root, NativeMilestoneAuditError
from sword_native_inventory import INTRO

MAX_SAMPLE = 24
MAX_ENTRY = 2 * 1024 * 1024


class BookIntroScreenError(ValueError):
    """Cannot independently validate the authorial/native intro scope."""


def _authored_words(node):
    """Flatten an element's authored characters, excluding note bodies only."""
    bits = []

    def visit(element):
        if not isinstance(element.tag, str):
            return
        tag = etree.QName(element).localname
        if tag in IGNORE_CONTAINER:
            return
        if element.text:
            bits.append(element.text)
        for child in element:
            visit(child)
            if child.tail:
                bits.append(child.tail)

    visit(node)
    return "".join(bits)


def _fold_space(value):
    return " ".join(value.split())


def private_original_preface_text(xml: bytes, mapping):
    """Source text stays in private memory; cross-check the existing audit."""
    classified = audit_usfx_book_prefaces(xml, mapping)
    crosswalk = dict(mapping)
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise BookIntroScreenError("Cannot independently read source prefaces") from exc
    private = {}
    for book in root.iter("book"):
        original_code = book.get("id")
        if original_code not in crosswalk:
            continue
        native = crosswalk[original_code]
        paras = []
        for node in book.iter():
            if not isinstance(node.tag, str):
                continue
            tag = etree.QName(node).localname
            if tag == "c":
                break
            if tag != "p":
                continue
            parent = node.getparent()
            embedded_note = False
            while parent is not None and parent is not book:
                if isinstance(parent.tag, str) and etree.QName(parent).localname in IGNORE_CONTAINER:
                    embedded_note = True
                    break
                parent = parent.getparent()
            if embedded_note:
                continue
            # Nested original <c>/<v> in prechapter p is not automatically
            # treated as a title or harmless text.
            if any(isinstance(child.tag, str)
                   and etree.QName(child).localname in {"c", "v", "ve"}
                   for child in node.iterdescendants()):
                raise BookIntroScreenError("Prefatory paragraph includes numbered milestone")
            paras.append(_authored_words(node))
        private[native] = paras
    if set(private) != set(crosswalk.values()):
        raise BookIntroScreenError("Source prefatory text book scope disagrees")
    expected = classified["prefatory_source_p_class_counts"]["prefatory_p_elements"]
    actual = sum(len(v) for v in private.values())
    if expected != actual:
        raise BookIntroScreenError("Independent source prefatory paragraph counts disagree")
    return private, classified


class NativeBookIntroScreen:
    """Collect real original-stock native book and first-chapter intro text.

    Intro raw XML is parsed strictly and discarded after the stage-4 scan.
    """

    def __init__(self):
        self._entries = {}
        self._counts = Counter()

    def observe(self, kind, ref, raw):
        if kind != "I":
            return
        if not INTRO.fullmatch(ref) or len(raw) > MAX_ENTRY:
            raise BookIntroScreenError("Untrusted native intro reference or size")
        book = ref.split(".", 1)[0]
        if ref in {book, book + ".0.0"}:
            scope = "book"
        elif ref in {book + ".1", book + ".1.0"}:
            scope = "first_chapter"
        else:
            return
        slot = (book, scope)
        if slot in self._entries:
            raise BookIntroScreenError("Duplicate native book/chapter intro slot")
        self._counts[f"observed_{scope}_intro_entries"] += 1
        try:
            root = _strict_root(raw)
        except NativeMilestoneAuditError:
            self._entries[slot] = None
            self._counts[f"unparseable_{scope}_intro_entries"] += 1
            return
        self._counts[f"parseable_{scope}_intro_entries"] += 1
        text = _authored_words(root)
        divs = Counter()
        tags = Counter()
        for node in root.iterdescendants():
            if not isinstance(node.tag, str):
                continue
            tag = etree.QName(node).localname
            if tag in {"div", "p", "l", "lg", "title"}:
                tags[tag] += 1
                if tag == "div":
                    kind = node.get("type", "")
                    divs[kind if kind in {"book", "bookGroup", "x-p", "x-milestone", "paragraph"}
                         else "other_unreviewed_type"] += 1
        self._entries[slot] = (text, divs, tags)

    def finish(self, private_prefaces, source_classification):
        count = Counter(self._counts)
        samples = []
        for book in sorted(private_prefaces):
            count["source_mapped_book_count"] += 1
            for raw in private_prefaces[book]:
                count["source_preface_paragraph_checked"] += 1
                source = _fold_space(raw)
                if not source:
                    count["source_preface_paragraph_without_non_note_text"] += 1
                    continue
                count["source_preface_paragraph_with_non_note_text"] += 1
                located = []
                for scope in ("book", "first_chapter"):
                    record = self._entries.get((book, scope))
                    if record is None:
                        continue
                    native, _divs, _tags = record
                    if source in _fold_space(native):
                        located.append(scope)
                if located:
                    count["preface_text_detected_in_book_or_first_chapter_intro"] += 1
                    count["text_detected_at_book_scope" if "book" in located
                          else "text_detected_at_first_chapter_scope_only"] += 1
                else:
                    count["preface_text_not_contiguous_in_checked_native_intros"] += 1
                    if len(samples) < MAX_SAMPLE:
                        samples.append({"book": book,
                                        "classification":"no_contiguous_whitespace_folded_intro_match"})
        for (_book, scope), item in self._entries.items():
            if item is None:
                continue
            _text, divs, tags = item
            for typ,n in divs.items():
                count[f"native_{scope}_div_type_{typ}"] += n
            for tag,n in tags.items():
                count[f"native_{scope}_tag_{tag}"] += n
        source_counts = source_classification["prefatory_source_p_class_counts"]
        if count["source_preface_paragraph_checked"] != source_counts["prefatory_p_elements"]:
            raise BookIntroScreenError("Preface summary disagrees with original source classification")
        if count["source_mapped_book_count"] != source_counts["mapped_original_books"]:
            raise BookIntroScreenError("Source book scope disagrees with independently checked prefaces")
        return {
            "schema_version":1,
            "source_prefatory_paragraph_vs_native_intro_counts":dict(sorted(count.items())),
            "first_unmatched_preface_book_codes_only":samples,
            "source_preface_text_not_in_artifact":True,
            "native_intro_raw_markup_not_in_artifact":True,
            "matched_intro_prose_does_not_establish_original_layout":True,
            "source_native_prefatory_paragraph_position_parity_verified":False,
            "source_or_native_content_mutated":False,
            "editorial_or_publication_approved":False,
        }
