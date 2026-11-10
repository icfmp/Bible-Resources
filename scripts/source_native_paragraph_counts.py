#!/usr/bin/env python3
"""Compare original USFX <p> inventory with *typed* native SWORD x-p pairs.

Unmatched authorial paragraph events are not silently accepted or assumed
lost. This is a bounded per-book research receipt, never editorial approval.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from lxml import etree

from source_usfx_structure import audit_source_usfx

MAX_EXAMPLES = 24
IGNORE_CONTAINER = frozenset({"f", "fe", "x", "ef", "ex", "note"})


class ParagraphAuditError(ValueError):
    """Original authorial paragraph scope could not be validated."""


def _within_note(node, book):
    parent = node.getparent()
    while parent is not None and parent is not book:
        if isinstance(parent.tag, str) and etree.QName(parent).localname in IGNORE_CONTAINER:
            return True
        parent = parent.getparent()
    return False


def compare_authored_native_paragraphs(xml: bytes, mapping: list[tuple[str,str]],
                                      native_x_p_by_book: dict[str,int]) -> dict:
    """Inspect original USFX book positions, never return paragraph text/notes."""
    proof = audit_source_usfx(xml)
    if proof["source_structural_issues"]:
        raise ParagraphAuditError("Unresolved original authorial source structure")
    if (not mapping or len({a for a,b in mapping}) != len(mapping)
            or len({b for a,b in mapping}) != len(mapping)):
        raise ParagraphAuditError("Ambiguous original/native book mapping")
    crosswalk=dict(mapping)
    if set(crosswalk.values()) != set(native_x_p_by_book) and (
        not set(native_x_p_by_book).issubset(set(crosswalk.values()))
    ):
        raise ParagraphAuditError("Unexpected compiled paragraph book outside source crosswalk")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,
                           recover=False,huge_tree=False)
    try:
        root=etree.fromstring(xml,parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise ParagraphAuditError("Cannot parse original source paragraph positions") from exc
    totals=Counter()
    by_book={}
    findings=[]
    overall=Counter()
    seen=set()
    for book in root.iter("book"):
        src=book.get("id")
        if not src or src in seen:
            raise ParagraphAuditError("Missing or duplicated original source book")
        seen.add(src)
        if src not in crosswalk:
            # Never silently discard additional authorial books. The existing
            # full-corpus source/native scope checker separately blocks
            # unrepresented books; this audit must still return evidence.
            totals["unmapped_source_book_count"] += 1
            totals["unmapped_source_p_element_count"] += sum(
                1 for node in book.iter()
                if isinstance(node.tag,str) and etree.QName(node).localname=="p")
            continue
        code=crosswalk[src]
        counters=Counter()
        before_first_verse=True
        chapter_seen=False
        chapter_has_verse=False
        for element in book.iter():
            if not isinstance(element.tag,str):
                continue
            tag=etree.QName(element).localname
            if tag=="c":
                chapter_seen=True
                chapter_has_verse=False
            elif tag=="v":
                before_first_verse=False
                chapter_has_verse=True
            elif tag=="p":
                counters["all_original_p_elements"]+=1
                if _within_note(element,book):
                    counters["original_p_nested_in_note"]+=1
                if before_first_verse:
                    counters["original_p_before_first_book_verse"]+=1
                if not chapter_seen:
                    counters["original_p_before_first_chapter"]+=1
                elif not chapter_has_verse:
                    counters["original_p_before_first_verse_of_chapter"]+=1
        by_book[code]=dict(counters)
        overall.update(counters)
        authored=counters["all_original_p_elements"]
        compiled=native_x_p_by_book.get(code,0)
        totals["authorial_p_events"]+=authored
        totals["native_typed_x_p_pairs"]+=compiled
        if authored!=compiled:
            totals["books_with_p_pair_count_mismatch"]+=1
            difference=authored-compiled
            totals["signed_authorial_minus_native_paragraph_pair_difference"]+=difference
            if len(findings)<MAX_EXAMPLES:
                findings.append({
                    "native_book":code,
                    "original_p_element_count":authored,
                    "actual_stock_div_x_p_pair_count":compiled,
                    "signed_difference":difference,
                    "original_p_before_first_book_verse":
                        counters["original_p_before_first_book_verse"],
                    "original_p_before_first_chapter":
                        counters["original_p_before_first_chapter"],
                })
        else:
            totals["books_with_exact_p_pair_count"]+=1
    if len(seen)!=proof["source_book_count"] or not set(crosswalk).issubset(seen):
        raise ParagraphAuditError("Original source book inventory disagrees with declared mapping")
    if (overall["all_original_p_elements"] +
            totals["unmapped_source_p_element_count"] !=
            proof["source_element_counts"].get("p",0)):
        raise ParagraphAuditError("Original USFX paragraph scanners disagree")
    # Keep zero-count result fields stable; absence of findings must be an
    # explicit checked zero rather than an omitted machine-report key.
    for field in ("books_with_p_pair_count_mismatch",
                  "books_with_exact_p_pair_count",
                  "signed_authorial_minus_native_paragraph_pair_difference"):
        totals.setdefault(field, 0)
    ordered={k:by_book[k] for k in sorted(by_book)}
    original_distribution=sha256(json.dumps(ordered,sort_keys=True,
        separators=(",",":")).encode("ascii")).hexdigest()
    return {
        "schema_version":1,
        "source_original_book_count":len(seen),
        "source_mapped_book_count":len(by_book),
        "unmapped_original_book_scope_requires_separate_review":bool(
            totals["unmapped_source_book_count"]),
        "authorial_native_typed_paragraph_totals":dict(sorted(totals.items())),
        "original_p_position_class_counts":dict(sorted(overall.items())),
        "first_per_book_mismatches_no_text":findings,
        "original_authorial_book_paragraph_distribution_sha256":original_distribution,
        "every_original_book_has_one_extra_p_vs_compiled":bool(
            len(by_book)>0 and not totals["unmapped_source_book_count"]
            and totals["books_with_p_pair_count_mismatch"]==len(by_book)
            and totals["signed_authorial_minus_native_paragraph_pair_difference"]==len(by_book)
            and all(by_book[code]["all_original_p_elements"]-
                    native_x_p_by_book.get(code,0)==1 for code in by_book)),
        "mismatched_paragraph_counts_are_anomalies_not_proven_text_loss":True,
        "source_to_compiled_exact_paragraph_position_equivalence_verified":False,
        "no_original_text_or_note_bodies_returned":True,
        "source_or_compiled_modified":False,
        "publication_approved":False,
    }
