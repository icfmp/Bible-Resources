#!/usr/bin/env python3
"""Unmodified ThML source div1 coverage, especially divisions without scripCom.

A division or chapter without source scripture markers is not automatically
empty, erroneous, or attributable to an invented Bible reference. This is a
read-only complete original XML structural audit; no private text or actual
reference values leave the returned report.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from lxml import etree

from commentary_xml_witness import _parse_reference, xml_structure
from pilot_preflight import PilotError

MAX_DIVISIONS=500
MAX_NO_MARKER=500

def _tag(node):
    return node.tag.rsplit("}",1)[-1] if isinstance(node.tag,str) else "_non_element"

def source_div1_coverage(xml_bytes:bytes) -> dict:
    reviewed=xml_structure(xml_bytes)
    try:
        root=etree.fromstring(xml_bytes, parser=etree.XMLParser(
            resolve_entities=False,no_network=True,load_dtd=False,
            recover=False,huge_tree=False,remove_blank_text=False))
    except (ValueError,etree.XMLSyntaxError):
        raise PilotError("Unreviewed original div1 source XML") from None
    if any(isinstance(x,etree._Entity) for x in root.iter()):
        raise PilotError("Original XML contains unresolved entity nodes")
    divisions=[x for x in root.iter() if _tag(x)=="div1"]
    if not divisions or len(divisions)>MAX_DIVISIONS:
        raise PilotError("Original XML div1 structure exceeded bounds")
    summary=Counter()
    absent=[]
    for ordinal,division in enumerate(divisions,start=1):
        chapters=[x for x in division if _tag(x)=="div2"]
        markers=[x for x in division.iter() if _tag(x)=="scripCom"]
        marker_classes=Counter()
        for marker in markers:
            kind,_book=_parse_reference(marker.get("osisRef",""))
            marker_classes[kind]+=1
        verse_count=(marker_classes["work_qualified_verse"]+
                     marker_classes["work_qualified_same_book_verse_range"])
        paragraph_nodes=[x for x in division.iter() if _tag(x)=="p"]
        nonempty_paragraphs=sum(bool("".join(x.itertext()).strip()) for x in paragraph_nodes)
        chapter_full_texts=["".join(x.itertext()) for x in chapters]
        full_text="".join(division.itertext())
        title=division.get("title")
        summary["all_div1"]+=1
        summary["all_div1_direct_div2"]+=len(chapters)
        summary["all_scripCom"]+=len(markers)
        summary["all_verse_range_scripCom"]+=verse_count
        if chapters:
            summary["div1_with_direct_div2"]+=1
        if markers:
            summary["div1_with_any_scripCom"]+=1
        else:
            summary["div1_without_any_scripCom"]+=1
            if len(absent)>=MAX_NO_MARKER:
                raise PilotError("Original no-marker division case limit reached")
            chapter_tags=Counter()
            for chapter in chapters:
                chapter_tags.update(_tag(x) for x in chapter if isinstance(x.tag,str))
            content_tags=Counter(
                _tag(x) for x in division.iter()
                if isinstance(x.tag,str) and x is not division
            )
            absent.append({
                "original_div1_document_ordinal":ordinal,
                "original_div1_title_sha256":
                    sha256((title or "").encode("utf-8")).hexdigest(),
                "original_div1_has_title_attribute":title is not None,
                "original_div1_direct_chapter_div2_count":len(chapters),
                "original_div1_scripCom_count":0,
                "original_div1_text_unicode_character_count":len(full_text),
                "original_div1_full_text_sha256":sha256(full_text.encode()).hexdigest(),
                "original_div1_paragraph_nonempty_element_count":nonempty_paragraphs,
                "original_div1_chapter_text_nonempty_count":
                    sum(bool(text.strip()) for text in chapter_full_texts),
                "original_div1_scripRef_element_count":content_tags.get("scripRef",0),
                "original_div1_note_element_count":content_tags.get("note",0),
                "original_div1_heading_element_count":
                    sum(content_tags.get(tag,0) for tag in ("h1","h2","h3","h4","h5","h6")),
                "original_div1_table_element_count":content_tags.get("table",0),
                "original_direct_chapter_child_tag_counts":dict(sorted(chapter_tags.items())),
                "original_div1_descendant_tag_counts":dict(sorted(content_tags.items())),
                "original_div1_content_not_assigned_a_scripture_reference":True,
            })
    known=reviewed["source_chapter_bearing_div1_without_scripCom"]
    known_by_ordinal={x["source_div1_ordinal"]:x for x in known}
    if (len(known_by_ordinal)!=len(known)
            or summary["all_div1"]!=reviewed["element_counts"].get("div1",0)
            or summary["all_div1_direct_div2"]!=reviewed["source_direct_chapters_inside_div1"]
            or summary["div1_with_direct_div2"]!=reviewed["source_div1_with_direct_chapters"]
            or summary["all_scripCom"]!=reviewed["element_counts"].get("scripCom",0)
            or summary["all_verse_range_scripCom"]!=
                (reviewed["candidate_commentary_reference_classes"].get(
                    "work_qualified_verse",0)+reviewed[
                    "candidate_commentary_reference_classes"].get(
                    "work_qualified_same_book_verse_range",0))):
        raise PilotError("Independent complete original div1 XML inventory disagrees")
    chapters_div1_ordinal=0
    for entry in absent:
        if entry["original_div1_direct_chapter_div2_count"]:
            chapters_div1_ordinal += 1
            # The independent xml_structure receipt numbers only div1s with
            # direct div2; calculate that ordinal from original document.
            div1=divisions[entry["original_div1_document_ordinal"]-1]
            chapter_bearing_ordinal=sum(
                any(_tag(y)=="div2" for y in d)
                for d in divisions[:entry["original_div1_document_ordinal"]]
            )
            witness=known_by_ordinal.get(chapter_bearing_ordinal)
            if witness is None or (
                witness["original_text_stream_sha256"]!=entry["original_div1_full_text_sha256"]
                or witness["chapter_count"]!=entry["original_div1_direct_chapter_div2_count"]
                or witness["original_text_unicode_characters"]!=entry[
                    "original_div1_text_unicode_character_count"]
                or witness["nonempty_paragraph_elements"]!=entry[
                    "original_div1_paragraph_nonempty_element_count"]
            ):
                raise PilotError("Unmarked source section disagrees with independent original XML inventory")
    if sum(int(bool(x["original_div1_direct_chapter_div2_count"])) for x in absent)!=len(known):
        raise PilotError("Unmarked chapter-bearing div1 count differs from independent source audit")
    return {
        "source_all_div1_total":summary["all_div1"],
        "source_div1_with_direct_chapters":summary["div1_with_direct_div2"],
        "source_total_direct_chapters":summary["all_div1_direct_div2"],
        "source_div1_with_any_scripCom":summary["div1_with_any_scripCom"],
        "source_div1_without_any_scripCom":summary["div1_without_any_scripCom"],
        "source_all_scripCom_count":summary["all_scripCom"],
        "source_verse_or_range_scripCom_count":summary["all_verse_range_scripCom"],
        "source_unmarked_div1_with_direct_chapters":len(known),
        "source_unmarked_div1_without_direct_chapters":len(absent)-len(known),
        "original_no_scripCom_div1_exact_content_hash_and_tag_name_only_cases":absent,
        "source_unmarked_division_has_no_inferred_biblical_book_or_verse_reference":True,
        "source_div1_title_hash_does_not_establish_canonical_book_identity":True,
        "source_original_content_unchanged":True,
        "all_original_source_words_title_text_and_osisRef_values_private":True,
    }
