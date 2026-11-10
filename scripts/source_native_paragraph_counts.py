#!/usr/bin/env python3
"""Compare original USFX <p> inventory with *typed* native SWORD x-p pairs.

Unmatched authorial paragraph events are not silently accepted or assumed
lost. This is a bounded per-book research receipt, never editorial approval.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re
from lxml import etree

from source_usfx_structure import audit_source_usfx

MAX_EXAMPLES = 24
IGNORE_CONTAINER = frozenset({"f", "fe", "x", "ef", "ex", "note"})

# Original USFX <p> can describe headings and book titles as well as body
# paragraphs: the source's own SFM style must not be silently discarded.
# Published USFM style codes are allowlisted. Unknown authored values never
# enter metadata artifacts (and are never classified as harmless prose).
_BOOK_TITLE_STYLE = re.compile(r"^(?:mt|mte|imt|imte|toc)[1-4]?$")
_SECTION_HEADING_STYLE = re.compile(r"^(?:s|ms|is|io)[1-4]?$")
_OTHER_HEADING_STYLE = frozenset({"h", "sr", "r", "d", "cl"})
_BODY_PARAGRAPH_STYLE = re.compile(
    r"^(?:p|m|mi|pi|pm|pc|ph|pr|nb|b|cls|sp|ps|psi)[1-4]?$"
)


def classify_prefatory_p_sfm(sfm: str | None) -> tuple[str, str]:
    """Return a public style *family* and an allowlisted code only.

    This is a semantic clue from the author's markup, not publisher or
    stock-SWORD editorial approval. Never return unknown literal values.
    """
    if sfm is None:
        return "implicit_p", "implicit_p"
    if not isinstance(sfm, str):
        raise ParagraphAuditError("Unsupported source paragraph style type")
    if _BOOK_TITLE_STYLE.fullmatch(sfm):
        return "book_title_style", sfm
    if _SECTION_HEADING_STYLE.fullmatch(sfm):
        return "section_heading_style", sfm
    if sfm in _OTHER_HEADING_STYLE:
        return "other_heading_style", sfm
    if _BODY_PARAGRAPH_STYLE.fullmatch(sfm):
        return "body_paragraph_style", sfm
    return "unreviewed_sfm_value", "other_unreviewed_style"


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


def audit_usfx_book_prefaces(xml: bytes, mapping: list[tuple[str, str]]) -> dict:
    """Classify every authored pre-first-chapter p without leaking its content.

    This is a source-only diagnostic. Text within notes/headings is counted
    separately rather than silently called Scripture. No assertion that
    native SWORD preserves any paragraph is made here.
    """
    proof = audit_source_usfx(xml)
    if proof["source_structural_issues"]:
        raise ParagraphAuditError("Original source structure unresolved")
    crosswalk = dict(mapping)
    if (not mapping or len(crosswalk) != len(mapping)
            or len(set(crosswalk.values())) != len(mapping)):
        raise ParagraphAuditError("Ambiguous book mapping")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise ParagraphAuditError("Unparseable original prefatory structure") from exc
    totals = Counter()
    examples = []
    style_totals = Counter()
    style_examples = []
    seen = set()
    for book in root.iter("book"):
        source_id = book.get("id")
        if not source_id or source_id in seen:
            raise ParagraphAuditError("Missing or duplicate original book")
        seen.add(source_id)
        if source_id not in crosswalk:
            totals["unmapped_original_books"] += 1
            continue
        native_book = crosswalk[source_id]
        totals["mapped_original_books"] += 1
        prefatory = []
        # Iterate in *document order*; nested headings/notes are not lost.
        for node in book.iter():
            if not isinstance(node.tag, str):
                continue
            tag = etree.QName(node).localname
            if tag == "c":
                break
            if tag == "p":
                prefatory.append(node)
        totals["prefatory_p_elements"] += len(prefatory)
        if len(prefatory) != 1:
            totals["books_without_exactly_one_prefatory_p"] += 1
        for p in prefatory:
            nested_in_note = _within_note(p, book)
            if nested_in_note:
                totals["prefatory_p_nested_in_note"] += 1
            # Exclude note/heading branches from the distinct main-content
            # signal; this is only a classification of authored XML text.
            def text_outside_annotations(node):
                if not isinstance(node.tag, str):
                    return ""
                local = etree.QName(node).localname
                if local in IGNORE_CONTAINER or local in {
                    "s", "mt", "ms", "r", "d", "cl", "toc", "rem"
                }:
                    return ""
                output = node.text or ""
                for child in node:
                    output += text_outside_annotations(child)
                    output += child.tail or ""
                return output
            any_text = any(t.strip() for t in p.itertext())
            main_text = bool(text_outside_annotations(p).strip())
            descendants = [etree.QName(ch).localname for ch in p.iterdescendants()
                           if isinstance(ch.tag, str)]
            has_markers = any(t in {"c", "v", "ve"} for t in descendants)
            attrs = bool(p.attrib)
            totals["prefatory_p_with_any_descendant_text" if any_text
                   else "prefatory_p_without_descendant_text"] += 1
            totals["prefatory_p_with_non_annotation_text" if main_text
                   else "prefatory_p_without_non_annotation_text"] += 1
            if descendants:
                totals["prefatory_p_with_child_markup"] += 1
            if has_markers:
                totals["prefatory_p_with_chapter_or_verse_marker"] += 1
            if attrs:
                totals["prefatory_p_with_attributes"] += 1

            sfm = p.get("sfm")
            family, allowlisted_code = classify_prefatory_p_sfm(sfm)
            style_totals[f"family_{family}"] += 1
            style_totals[f"sfm_{allowlisted_code}"] += 1
            if sfm is not None:
                style_totals["with_explicit_sfm"] += 1
            if "style" in p.attrib:
                # Original USFX "style" is a separate attribute. Do not
                # assume it is interchangeable with "sfm" or print it.
                style_totals["with_separate_style_attribute"] += 1
                if sfm is not None and p.get("style") != sfm:
                    style_totals["sfm_and_style_differ"] += 1
            if "level" in p.attrib:
                style_totals["with_level_attribute"] += 1
            if len(style_examples) < MAX_EXAMPLES:
                style_examples.append({
                    "native_book":native_book,
                    "sfm_family":family,
                    "allowlisted_sfm_code":allowlisted_code,
                    "has_separate_style_attribute":"style" in p.attrib,
                    "has_level_attribute":"level" in p.attrib,
                })
            if len(examples) < MAX_EXAMPLES:
                examples.append({
                    "native_book": native_book,
                    "has_descendant_text": any_text,
                    "has_non_annotation_text": main_text,
                    "has_child_markup": bool(descendants),
                    "has_chapter_or_verse_marker": has_markers,
                    "has_attributes": attrs,
                    "nested_in_note": nested_in_note,
                })
    if not set(crosswalk).issubset(seen):
        raise ParagraphAuditError("Missing mapped original book")
    return {
        "schema_version": 1,
        "prefatory_source_p_class_counts": dict(sorted(totals.items())),
        "first_prefatory_p_classifications_no_text": examples,
        "prefatory_p_sfm_style_counts": dict(sorted(style_totals.items())),
        "first_prefatory_p_sfm_styles_no_text": style_examples,
        "all_prefatory_p_have_allowlisted_book_title_sfm": bool(
            totals["prefatory_p_elements"]
            and style_totals["family_book_title_style"] == totals["prefatory_p_elements"]
        ),
        "unknown_sfm_values_are_not_exposed": True,
        "source_sfm_to_native_title_semantics_verified": False,
        "all_mapped_original_books_checked": totals["mapped_original_books"] == len(crosswalk),
        "compiled_book_intro_structure_verified": False,
        "prefatory_source_native_position_equivalence_verified": False,
        "source_or_compiled_modified": False,
        "publication_approved": False,
    }
