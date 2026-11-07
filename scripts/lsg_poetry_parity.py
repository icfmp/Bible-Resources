#!/usr/bin/env python3
"""Read-only poetry segmentation diagnostics for publisher USFX -> candidate OSIS.

A source <q> marker and candidate <l> node need not have identical
serialization, but changes to their number, level, or boundaries require
review. Never treat identical Bible words as editorial layout equivalence.
Only aggregate metadata, bounded references and SHA-256 digests leave CI.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import unicodedata

from lxml import etree

from lsg_sword_compare import NON_VERSE_TEXT_ELEMENTS, NON_VERSE_PARAGRAPH_STYLES
from pilot_preflight import PilotError

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SKIP_TARGET={"note","title","header","revisionDesc","description"}


def _name(node) -> str:
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _canonical_line_text(node) -> str:
    """Only body words in a line, excluding annotation or editorial apparatus."""
    def visit(element):
        if not isinstance(element.tag,str):
            return ""
        if _name(element) in {"note","x","f","fe","ex","ef","title","s"}:
            return ""
        result=[element.text or ""]
        for child in element:
            result.append(visit(child))
            result.append(child.tail or "")
        return "".join(result)
    return unicodedata.normalize("NFC",visit(node))


def _line_signature(node, *, source: bool) -> dict:
    text=_canonical_line_text(node)
    compact="".join(text.split())
    boundary_tags={"v","ve"} if source else {"verse"}
    markers=[n for n in node.iterdescendants()
             if isinstance(n.tag,str) and _name(n) in boundary_tags]
    crossing=bool(markers)
    return {
        "level": node.get("level") or node.get("sfm") or node.get("style"),
        "verse_start_markers":tuple(
            (item.get("id") if source else item.get("osisID") or item.get("sID"))
            for item in markers if ((source and _name(item)=="v" and item.get("id"))
                                    or (not source and (item.get("osisID") or item.get("sID"))))
        ),
        "verse_end_markers":tuple(
            (item.get("id") if source else item.get("eID"))
            for item in markers if ((not source and item.get("eID"))
                                    or (source and _name(item)=="ve" and item.get("id")))
        ),
        "characters_without_whitespace":len(compact),
        "has_text":bool(compact),
        "text_sha256":hashlib.sha256(compact.encode("utf-8")).hexdigest(),
        "embedded_verse_markers":crossing,
    }


def _extract_source(root) -> dict:
    lines=defaultdict(list)
    if _name(root)!="usfx":
        raise PilotError("Poetry audit needs publisher USFX")
    for book in root.iter("book"):
        code=book.get("id")
        chapter=None
        current=None
        def visit(node):
            nonlocal chapter,current
            if not isinstance(node.tag,str):
                return
            name=_name(node)
            if name=="c":
                value=node.get("id")
                if not value or not value.isdecimal():
                    raise PilotError("Unreviewed USFX chapter in poetry audit")
                chapter=int(value)
            elif name=="v":
                value=node.get("id")
                if chapter is None or not value or not value.isdecimal():
                    raise PilotError("Unreviewed USFX verse in poetry audit")
                current=(code,chapter,int(value))
            elif name=="ve":
                current=None
            if name=="q" and current is not None:
                lines[current].append(_line_signature(node,source=True))
            if (name in NON_VERSE_TEXT_ELEMENTS or
                    (name=="p" and (node.get("sfm") or node.get("style"))
                     in NON_VERSE_PARAGRAPH_STYLES)):
                return
            for child in node:
                visit(child)
        visit(book)
    return lines


def _extract_candidate(root) -> dict:
    lines=defaultdict(list)
    if root.tag != OSIS+"osis":
        raise PilotError("Poetry audit needs candidate OSIS")
    for book in root.iter(OSIS+"div"):
        if book.get("type")!="book":
            continue
        current=None
        def visit(node):
            nonlocal current
            if isinstance(node,etree._Comment):
                return
            if not isinstance(node.tag,str):
                raise PilotError("Unexpected non-element OSIS poetry node")
            name=_name(node)
            if name=="verse":
                start=node.get("osisID") or node.get("sID")
                end=node.get("eID")
                if start:
                    current=start
                elif end:
                    if current!=end:
                        raise PilotError("Unpaired OSIS verse in poetry audit")
                    current=None
                else:
                    raise PilotError("Unreviewed OSIS verse in poetry audit")
                return
            if name=="l" and current is not None:
                lines[current].append(_line_signature(node,source=False))
            if name in SKIP_TARGET:
                return
            for child in node:
                visit(child)
        visit(book)
        if current is not None:
            raise PilotError("Unclosed OSIS verse in poetry audit")
    return lines


def audit_poetry(source_root, candidate_root, mapping, all_source_keys) -> dict:
    if isinstance(candidate_root,etree._ElementTree):
        candidate_root=candidate_root.getroot()
    source=_extract_source(source_root)
    candidate=_extract_candidate(candidate_root)
    source_all_q=[n for book in source_root.iter("book")
                  for n in book.iter("q")]
    candidate_all_l=[n for book in candidate_root.iter(OSIS+"div")
                     if book.get("type")=="book"
                     for n in book.iter(OSIS+"l")]
    delta_hist=Counter()
    per_book=Counter()
    categories=Counter()
    original_total=0
    converted_total=0
    matches=0
    source_empty=0
    target_empty=0
    samples=[]
    source_keys=set(all_source_keys)
    unexpected_source_keys=set(source)-source_keys
    expected_candidate_keys={f"{mapping[b]}.{c}.{v}" for b,c,v in source_keys}
    unexpected_candidate_keys=set(candidate)-expected_candidate_keys
    for book,chapter,verse in all_source_keys:
        key=(book,chapter,verse)
        target_key=f"{mapping[book]}.{chapter}.{verse}"
        original=source.get(key,[])
        converted=candidate.get(target_key,[])
        original_total+=len(original)
        converted_total+=len(converted)
        source_empty+=sum(not item["has_text"] for item in original)
        target_empty+=sum(not item["has_text"] for item in converted)
        delta=len(converted)-len(original)
        delta_hist[delta]+=1
        if delta==0:
            matches+=1
            continue
        per_book[book]+=1
        src_empty=sum(not item["has_text"] for item in original)
        dst_empty=sum(not item["has_text"] for item in converted)
        if delta>0 and dst_empty>src_empty:
            category="additional_empty_candidate_lines_present"
        elif delta>0:
            category="additional_populated_candidate_line_or_split"
        elif src_empty>dst_empty:
            category="fewer_empty_candidate_lines"
        else:
            category="fewer_populated_candidate_lines_or_merged"
        categories[category]+=1
        if len(samples)<80:
            samples.append({
                "reference":f"{book}.{chapter}.{verse}",
                "source_line_count":len(original),
                "candidate_line_count":len(converted),
                "source_empty_line_count":src_empty,
                "candidate_empty_line_count":dst_empty,
                "source_levels":[item["level"] for item in original],
                "candidate_levels":[item["level"] for item in converted],
                "source_line_nested_verse_starts":[
                    list(item["verse_start_markers"]) for item in original],
                "candidate_line_nested_verse_starts":[
                    list(item["verse_start_markers"]) for item in converted],
                "candidate_line_nested_verse_ends":[
                    list(item["verse_end_markers"]) for item in converted],
                "source_line_text_hashes":[item["text_sha256"] for item in original],
                "candidate_line_text_hashes":[item["text_sha256"] for item in converted],
                "source_lines_with_embedded_verse_marker":sum(
                    item["embedded_verse_markers"] for item in original),
                "candidate_lines_with_embedded_verse_marker":sum(
                    item["embedded_verse_markers"] for item in converted),
                "classification":category,
            })
    all_keys_match=not unexpected_source_keys and not unexpected_candidate_keys
    return {
        "source_poetry_line_count":original_total,
        "candidate_poetry_line_count":converted_total,
        "all_original_usfx_q_elements":len(source_all_q),
        "all_candidate_osis_l_elements":len(candidate_all_l),
        "source_q_elements_with_nested_verse_start":sum(
            any(_name(child)=="v" for child in q.iterdescendants()
                if isinstance(child.tag,str))
            for q in source_all_q),
        "candidate_l_elements_with_nested_verse_start":sum(
            any(_name(child)=="verse" and
                (child.get("osisID") or child.get("sID"))
                for child in line.iterdescendants() if isinstance(child.tag,str))
            for line in candidate_all_l),
        "source_q_elements_not_counted_in_active_verses":
            len(source_all_q)-original_total,
        "candidate_l_elements_not_counted_in_active_verses":
            len(candidate_all_l)-converted_total,
        "source_empty_poetry_line_count":source_empty,
        "candidate_empty_poetry_line_count":target_empty,
        "matching_per_verse_line_counts":matches,
        "per_verse_line_count_delta_histogram":dict(sorted(delta_hist.items())),
        "mismatching_verse_counts_by_book":dict(sorted(per_book.items())),
        "mismatch_classifications":dict(sorted(categories.items())),
        "source_poetry_markers_outside_original_verse_keys":len(unexpected_source_keys),
        "candidate_poetry_lines_outside_original_verse_keys":len(unexpected_candidate_keys),
        "line_references_resolved":all_keys_match,
        "first_mismatches":samples,
        "all_poetry_line_counts_verified":matches==len(all_source_keys) and all_keys_match,
        "all_poetry_layout_verified":False,
        "limitation":"A counted source <q> and OSIS <l> may segment verse content differently. "
                     "Hashes describe full line elements (which can cross verse milestones); "
                     "no line text is exported. Do not infer stylistic fidelity from counts alone.",
    }
