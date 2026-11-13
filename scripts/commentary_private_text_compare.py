#!/usr/bin/env python3
"""Research-only exact text comparison of source ThML body and stock zCom raw.

The trusted previous stages establish source scripCom→next <div> adjacency,
stock occupied anchors, and complete native stock raw corpus enumeration.
This step joins those EVIDENCES by exact original verse/range start anchors.
Original contents are never logged, committed, published or silently rewritten.
Differences are diagnostic; no text or structural parity is certified here.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import zipfile

from lxml import etree

from commentary_chapter_neighbors import (original_chapter_neighbors, compare_chapter_neighbors,
                                          ChapterNeighborNumberedProbe)
from commentary_chapter_cross_slot import ChapterNeighborSameBookAlternativeProbe
from commentary_chapter_paragraph_overlap import OriginalChapterParagraphSpanProbe
from commentary_chapter_p_boundaries import ChapterParagraphBoundaryProbe
from commentary_reference_cross_slot import ReferenceCrossSlotTopology
from commentary_prose_cross_slot import OriginalProseAlternativeNativeSlotProbe
from commentary_source_native_boundaries import original_marker_boundary, NativeRawRunBoundaryInventory
from commentary_shared_raw_source_units import inspect_shared_original_units_in_native_runs
from commentary_intake import load_manifest
from commentary_text_delta import punctuation_relationship, word_relationship, nonword_symbol_excess
from commentary_unresolved_lexical_triage import (
    UnresolvedLexicalSelectionCensus, marked_word_token_indices,
)
from commentary_stock_prefix_topology import (
    source_word_prefix_topology, aligned_punctuation_gap_diagnostics,
    stock_prefixed_source_body_concordance, unexplained_word_boundary_census,
    stock_prefix_context_correspondence,
)
from commentary_xml_witness import _parse_reference, WORK_REF, OSIS_LOC, xml_structure, MAX_XML
from commentary_native_raw_inventory import _safe_stock_install, private_crosscheck
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

MAX_DIAGNOSTICS=20


def _original_thml_neighbor_candidates(marker) -> list[tuple[str,str]]:
    """Private, bounded actual source metadata, not inferred SWORD headings.

    Candidate matches to *compiled* metadata are only observations: a
    chapter-title or marker-passage attribute is not automatically the title
    of the following commentary body, and a nearby heading might belong to
    an earlier source section. Never publish these original strings.
    """
    candidates=[]
    for name, value in (
        ("source_marker_passage_attribute", marker.get("passage", "")),
    ):
        if value:
            candidates.append((name,value))
    for ancestor in marker.iterancestors():
        if not isinstance(ancestor.tag,str):
            continue
        local=ancestor.tag.rsplit("}",1)[-1]
        if local in ("div1","div2") and ancestor.get("title"):
            candidates.append(("source_"+local+"_title_attribute",ancestor.get("title")))
    preceding=marker.getprevious()
    if preceding is not None and isinstance(preceding.tag,str):
        local=preceding.tag.rsplit("}",1)[-1]
        if local in {"title","h1","h2","h3","h4","h5","h6"}:
            original_heading="".join(preceding.itertext())
            if original_heading.strip():
                candidates.append(("source_immediate_previous_heading_element",original_heading))
    if len(candidates)>8 or any(len(text)>2048 for _kind,text in candidates):
        raise PilotError("Original neighboring source heading metadata exceeds review bounds")
    return candidates


def _original_source_markers(xml_bytes: bytes) -> tuple[dict[str,list[dict]],dict]:
    # Must scan the entire actual original with network/entity resolution off.
    whole=xml_structure(xml_bytes)
    try:
        root=etree.fromstring(xml_bytes,parser=etree.XMLParser(
            resolve_entities=False,no_network=True,load_dtd=False,
            recover=False,huge_tree=False,remove_blank_text=False))
    except (ValueError,etree.XMLSyntaxError):
        raise PilotError("Invalid complete original XML; cannot form commentary units") from None
    # Map actual document-order top-level ThML commentary divisions, not
    # a guessed OSIS book or a marker's biblical reference value. A marker
    # sharing a verse anchor with another marker in a DIFFERENT original div1
    # must not be treated as the same authorial section.
    original_div1_nodes=[
        n for n in root.iter()
        if isinstance(n.tag,str) and n.tag.rsplit("}",1)[-1]=="div1"
    ]
    original_div1_order={n:i+1 for i,n in enumerate(original_div1_nodes)}
    if (len(original_div1_order)!=len(original_div1_nodes)
            or len(original_div1_nodes)!=whole["element_counts"].get("div1",0)):
        raise PilotError("Original document-order ThML div1 inventory differs from whole XML scan")
    sources={}
    counts=Counter()
    original_map_digest=sha256()
    for node in root.iter():
        if not isinstance(node.tag,str) or node.tag.rsplit("}",1)[-1]!="scripCom":
            continue
        original_ref=node.get("osisRef","")
        kind,book=_parse_reference(original_ref)
        counts[kind]+=1
        if kind not in ("work_qualified_verse","work_qualified_same_book_verse_range"):
            continue
        match=WORK_REF.fullmatch(original_ref)
        if not match:
            raise PilotError("Previously reviewed original annotation is no longer qualified")
        source_div1=next((ancestor for ancestor in node.iterancestors()
                          if ancestor in original_div1_order),None)
        if source_div1 is None:
            raise PilotError("Original scripture annotation has no verifiable enclosing ThML div1")
        source_div1_ordinal=original_div1_order[source_div1]
        original_div1_title=source_div1.get("title")
        heading_origin="title_attribute" if original_div1_title is not None else "absent"
        if original_div1_title is None:
            for heading in source_div1:
                if (isinstance(heading.tag,str) and
                        heading.tag.rsplit("}",1)[-1] in {"h1","title"}):
                    original_div1_title="".join(heading.itertext())
                    heading_origin="immediate_original_h1_or_title_child"
                    break
        if original_div1_title is not None and len(original_div1_title)>4096:
            raise PilotError("Original div1 heading exceeds private source-review bound")
        original_div1_heading_sha=(
            sha256(original_div1_title.encode("utf-8")).hexdigest()
            if original_div1_title is not None and original_div1_title.strip()
            else None
        )
        source_endpoints=match.group(2).split("-",1)
        start=source_endpoints[0]
        original_declared_end=source_endpoints[-1]
        if not OSIS_LOC.fullmatch(start) or not OSIS_LOC.fullmatch(original_declared_end):
            raise PilotError("Original chapter/verse start or end anchor is unreviewed")
        sibling=node.getnext()
        if sibling is None or not isinstance(sibling.tag,str) or sibling.tag.rsplit("}",1)[-1]!="div":
            raise PilotError("Original verse/range annotation has no exact adjacent div body")
        if node.tail and node.tail.strip():
            raise PilotError("Nonwhitespace original source text between marker and body")
        txt="".join(sibling.itertext())
        if not txt.strip():
            raise PilotError("Empty original source commentary div body")
        text_bytes=txt.encode("utf-8")
        full_ref_bytes=original_ref.encode("utf-8")
        original_map_digest.update(
            len(full_ref_bytes).to_bytes(4,"big")+full_ref_bytes
            +len(text_bytes).to_bytes(8,"big")
            +sha256(text_bytes).digest()
        )
        sources.setdefault(start,[]).append({
            "original_source_line":node.sourceline,
            "original_full_reference_sha256":sha256(full_ref_bytes).hexdigest(),
            "private_original_declared_range_end_key":original_declared_end,
            "private_original_enclosing_div1_document_ordinal":source_div1_ordinal,
            "private_original_total_div1_in_document":len(original_div1_nodes),
            "private_original_div1_heading_origin":heading_origin,
            "private_original_div1_heading_sha256":original_div1_heading_sha,
            "private_original_div1_attribute_name_types":sorted(
                k.rsplit("}",1)[-1] for k in source_div1.attrib
            ),
            "original_text":txt,
            "original_text_sha256":sha256(text_bytes).hexdigest(),
            "original_characters":len(txt),
            "private_original_neighbor_candidates":_original_thml_neighbor_candidates(node),
            "private_source_marker_boundary":original_marker_boundary(
                node,sibling,original_ref,start
            ),
            "private_original_body_tag_counts": dict(sorted(Counter(
                x.tag.rsplit("}",1)[-1] for x in sibling.iter()
                if x is not sibling and isinstance(x.tag,str)
            ).items())),
            "private_original_scripRef_word_indices": marked_word_token_indices(
                sibling, "scripRef", txt
            ),
            "private_original_scripRef_links": [
                {
                    "text": "".join(ref.itertext()),
                    "private_original_osisRef_target": ref.get("osisRef", ""),
                    "attribute_name_types": sorted(
                        key.rsplit("}",1)[-1] for key in ref.attrib
                    ),
                }
                for ref in sibling.iter()
                if isinstance(ref.tag,str) and ref.tag.rsplit("}",1)[-1] == "scripRef"
            ],
        })
    if sum(len(rows) for rows in sources.values()) != (
        counts["work_qualified_verse"]+counts["work_qualified_same_book_verse_range"]
    ):
        raise PilotError("Original source annotation count diverged from body inventory")
    if original_map_digest.hexdigest()!=whole[
        "verse_or_range_immediate_div_ordered_unmodified_text_sha256"
    ]:
        raise PilotError("Original body text order and reference digest disagree with prior source scanner")
    return sources,{
        "source_xml_sha256":whole["xml_sha256"],
        "source_marker_total":whole["element_counts"]["scripCom"],
        "original_verse_or_range_body_count":sum(map(len,sources.values())),
        "distinct_original_start_anchors":len(sources),
        "original_ordered_verse_and_range_body_text_sha256":original_map_digest.hexdigest(),
        "chapter_source_markers_not_compared":counts["work_qualified_chapter"],
        "original_unmarked_chapter_division_content_compared":False,
    }


def raw_as_strict_xml_text(raw: bytes) -> str | None:
    """No HTML recovery: malformed raw markup remains unverified."""
    if len(raw)>2*1024*1024 or b"\x00" in raw:
        return None
    try:
        fragment=etree.fromstring(
            b"<original>" + raw + b"</original>",
            parser=etree.XMLParser(
                resolve_entities=False,no_network=True,load_dtd=False,
                recover=False,huge_tree=False,remove_blank_text=False))
        if any(isinstance(node,etree._Entity) for node in fragment.iter()):
            return None
        return "".join(fragment.itertext())
    except (ValueError,UnicodeError,etree.XMLSyntaxError):
        return None


def compare_private_texts(source:dict[str,list[dict]], stocked:dict[str,bytes],
                          *, on_unresolved_word_case=None) -> dict:
    counters=Counter()
    issues=[]
    lexical_details=Counter()
    punctuation_change_subtypes=Counter()
    word_relationship_subtypes=Counter()
    word_overlap_buckets=Counter()
    stock_containment_locations=Counter()
    stock_extra_prefix_token_bins=Counter()
    stock_source_boundary_top_level_tags=Counter()
    stock_prefix_full_sibling_top_level_tags=Counter()
    stock_prefix_has_full_sibling_element=0
    stock_prefix_owners_before_original_body=Counter()
    stock_original_body_suffix_concordance=Counter()
    stock_heading_source_candidate_types=Counter()
    stock_heading_source_match_classes=Counter()
    stock_heading_context_earlier_tag_counts=Counter()
    stock_heading_source_any_exact_match_entries=0
    stock_heading_source_any_word_only_match_entries=0
    stock_heading_source_covered_entries=0
    stock_original_body_suffix_glyph_classes=Counter()
    stock_original_body_suffix_glyph_replacements=Counter()
    stock_original_body_suffix_changed_gaps=0
    divergent_word_boundary_suffix_bins=Counter()
    divergent_word_boundary_placement=Counter()
    divergent_original_middle_word_bins=Counter()
    divergent_stock_middle_word_bins=Counter()
    divergent_word_boundary_scanned=0
    unresolved_lexical_census=UnresolvedLexicalSelectionCensus()
    punctuation_aligned_gap_classes=Counter()
    punctuation_aligned_numeric_substitutions=Counter()
    punctuation_entries_with_only_one_to_one_glyph_changes=0
    punctuation_changed_gap_count=0
    stock_extra_suffix_token_bins=Counter()
    source_nonword_glyph_excess=Counter()
    stock_nonword_glyph_excess=Counter()
    bounded_priority_examples=[]
    priority_example_counts=Counter()
    per_book={}
    tested=0
    for start,items in source.items():
        book=start.split(".")[0]
        book_counts=per_book.setdefault(book,Counter())
        raw=stocked.get(start)
        for item in items:
            tested+=1
            if raw is None:
                status="missing_original_start_in_native_raw"
                compiled=None
            else:
                compiled=raw_as_strict_xml_text(raw)
                if compiled is None:
                    status="stock_raw_fragment_not_strict_xml"
                elif compiled==item["original_text"]:
                    status="exact_unicode_text_match"
                elif compiled.strip()==item["original_text"].strip():
                    status="edge_whitespace_difference_only"
                elif " ".join(compiled.split())==" ".join(item["original_text"].split()):
                    status="interior_whitespace_difference_only"
                else:
                    status="lexical_text_or_punctuation_difference"
            if status=="lexical_text_or_punctuation_difference" and compiled is not None:
                a=" ".join(item["original_text"].split())
                b=" ".join(compiled.split())
                if a and a in b:
                    lexical_details["full_original_whitespace_collapsed_body_inside_stock"]+=1
                elif b and b in a:
                    lexical_details["full_stock_whitespace_collapsed_body_inside_original"]+=1
                else:
                    source_tokens=re.findall(r"\w+",a)
                    stock_tokens=re.findall(r"\w+",b)
                    if source_tokens==stock_tokens:
                        lexical_details["same_unicode_word_tokens_different_punctuation"]+=1
                        punctuation_change_subtypes[punctuation_relationship(a,b)]+=1
                        extra_source,extra_stock=nonword_symbol_excess(a,b)
                        source_nonword_glyph_excess.update(extra_source)
                        stock_nonword_glyph_excess.update(extra_stock)
                        aligned=aligned_punctuation_gap_diagnostics(a,b)
                        punctuation_aligned_gap_classes.update(aligned["punctuation_gap_classes"])
                        punctuation_aligned_numeric_substitutions.update(
                            aligned["one_to_one_unicode_numeric_glyph_replacements"]
                        )
                        punctuation_changed_gap_count+=aligned["punctuation_gap_changes"]
                        if aligned["all_nonword_glyph_differences_consistently_mapped"]:
                            punctuation_entries_with_only_one_to_one_glyph_changes+=1
                    else:
                        if [t.casefold() for t in source_tokens]==[t.casefold() for t in stock_tokens]:
                            lexical_details["same_casefolded_word_tokens_different_case_or_punctuation"]+=1
                        else:
                            lexical_details["different_unicode_word_token_sequence_or_selection"]+=1
                        diagnostic=word_relationship(a,b)
                        category=diagnostic["relationship"]
                        word_relationship_subtypes[category]+=1
                        word_overlap_buckets[diagnostic["overlap_bucket"]]+=1
                        if category=="source_words_contiguous_inside_longer_stock":
                            position=diagnostic["original_words_contiguous_in_stock_location"]
                            stock_containment_locations[position]+=1
                            topology=source_word_prefix_topology(item["original_text"], raw)
                            stock_source_boundary_top_level_tags[
                                topology["source_word_boundary_stock_top_level_owner"]]+=1
                            previous=topology["top_level_element_types_wholly_before_original_source_words"]
                            stock_prefix_full_sibling_top_level_tags.update(previous)
                            if previous:
                                stock_prefix_has_full_sibling_element+=1
                            stock_prefix_owners_before_original_body.update(
                                topology["prefix_text_top_level_owner_types"]
                            )
                            suffix_result=stock_prefixed_source_body_concordance(item["original_text"],raw)
                            if suffix_result["stock_extra_prefix_word_tokens"]!=diagnostic[
                                "additional_stock_word_tokens_before_source"
                            ]:
                                raise PilotError("Original stock suffix does not match independent token-prefix audit")
                            stock_original_body_suffix_concordance[
                                suffix_result["original_source_body_to_stock_suffix_class"]
                            ]+=1
                            stock_original_body_suffix_glyph_classes.update(
                                suffix_result["aligned_suffix_gap_class_counts"]
                            )
                            stock_original_body_suffix_glyph_replacements.update(
                                suffix_result["aligned_suffix_one_to_one_numeric_glyph_substitutions"]
                            )
                            stock_original_body_suffix_changed_gaps+=suffix_result[
                                "aligned_suffix_changed_nonword_gaps"
                            ]
                            source_context=stock_prefix_context_correspondence(
                                item["original_text"],raw,item["private_original_neighbor_candidates"]
                            )
                            stock_heading_source_covered_entries+=1
                            stock_heading_source_candidate_types.update(
                                source_context["authenticated_source_neighbor_candidate_type_counts"]
                            )
                            stock_heading_source_match_classes.update(
                                source_context["source_neighbor_to_stock_element_correspondence_classes"]
                            )
                            stock_heading_context_earlier_tag_counts.update(
                                source_context["preceding_stock_metadata_element_count_by_tag"]
                            )
                            if source_context["any_exact_source_neighbor_text_in_stock_metadata"]:
                                stock_heading_source_any_exact_match_entries+=1
                            if source_context["any_only_word_token_source_neighbor_in_stock_metadata"]:
                                stock_heading_source_any_word_only_match_entries+=1
                            for value,bins in (
                                (diagnostic["additional_stock_word_tokens_before_source"],stock_extra_prefix_token_bins),
                                (diagnostic["additional_stock_word_tokens_after_source"],stock_extra_suffix_token_bins),
                            ):
                                if value==0: b="0"
                                elif value<=4: b="1_to_4"
                                elif value<=9: b="5_to_9"
                                elif value<=29: b="10_to_29"
                                else: b="30_or_more"
                                bins[b]+=1
                        if category=="different_word_order_or_selection_requires_review":
                            unresolved_lexical_census.observe(item,compiled,raw,book)
                            if on_unresolved_word_case is not None:
                                on_unresolved_word_case(start,item,raw)
                            unresolved=unexplained_word_boundary_census(item["original_text"],compiled)
                            divergent_word_boundary_scanned+=1
                            divergent_word_boundary_suffix_bins[unresolved[
                                "common_suffix_fraction_bucket"]]+=1
                            if unresolved["changed_only_at_start_of_word_sequence"]:
                                divergent_word_boundary_placement["only_start"]+=1
                            elif unresolved["changed_only_at_end_of_word_sequence"]:
                                divergent_word_boundary_placement["only_end"]+=1
                            elif unresolved["changed_in_middle_with_both_matching_boundaries"]:
                                divergent_word_boundary_placement["middle_with_shared_edges"]+=1
                            else:
                                divergent_word_boundary_placement["complex_or_disjoint_boundaries"]+=1
                            for value,bins in (
                                (unresolved["source_middle_different_word_tokens"],divergent_original_middle_word_bins),
                                (unresolved["stock_middle_different_word_tokens"],divergent_stock_middle_word_bins),
                            ):
                                if value==0: label="none"
                                elif value==1: label="one_word"
                                elif value<=5: label="two_to_five_words"
                                elif value<=20: label="six_to_twenty_words"
                                else: label="over_twenty_words"
                                bins[label]+=1
                        if priority_example_counts[category]<4:
                            priority_example_counts[category]+=1
                            bounded_priority_examples.append({
                                "source_line":item["original_source_line"],
                                "original_reference_sha256":item["original_full_reference_sha256"],
                                "original_unicode_characters":item["original_characters"],
                                "stock_raw_sha256":sha256(raw).hexdigest(),
                                "original_word_token_count":diagnostic["original_word_token_count"],
                                "stock_word_token_count":diagnostic["stock_word_token_count"],
                                "shared_word_token_occurrences":diagnostic["shared_word_token_multiset_occurrences"],
                                "relationship":category,
                                "word_overlap_bucket":diagnostic["overlap_bucket"],
                            })
            counters[status]+=1
            book_counts[status]+=1
            if status!="exact_unicode_text_match" and len(issues)<MAX_DIAGNOSTICS:
                issues.append({
                    "source_line":item["original_source_line"],
                    "original_reference_sha256":item["original_full_reference_sha256"],
                    "original_text_sha256":item["original_text_sha256"],
                    "original_unicode_characters":item["original_characters"],
                    "stock_raw_sha256":sha256(raw).hexdigest() if raw is not None else None,
                    "stock_raw_bytes":len(raw) if raw is not None else None,
                    "status":status,
                })
    if tested!=sum(map(len,source.values())):
        raise PilotError("Original commentary text comparison was incomplete")
    if sum(counters.values())!=tested:
        raise PilotError("Original commentary text status totals are inconsistent")
    if sum(lexical_details.values())!=counters["lexical_text_or_punctuation_difference"]:
        raise PilotError("Detailed text discrepancy census does not reconcile with every source body")
    if sum(punctuation_change_subtypes.values())!=lexical_details["same_unicode_word_tokens_different_punctuation"]:
        raise PilotError("Punctuation discrepancy subtotals do not account for all matching word sequences")
    if sum(word_relationship_subtypes.values())!=(
        lexical_details["same_casefolded_word_tokens_different_case_or_punctuation"]
        +lexical_details["different_unicode_word_token_sequence_or_selection"]
    ):
        raise PilotError("Unequal-word relationships have incomplete full-corpus accounting")
    if sum(word_overlap_buckets.values())!=sum(word_relationship_subtypes.values()):
        raise PilotError("Word overlap ratio categories have incomplete accounting")
    if sum(stock_containment_locations.values())!=word_relationship_subtypes[
        "source_words_contiguous_inside_longer_stock"
    ]:
        raise PilotError("Full original-in-stock containment location census is incomplete")
    if (sum(stock_extra_prefix_token_bins.values())!=sum(stock_containment_locations.values())
            or sum(stock_extra_suffix_token_bins.values())!=sum(stock_containment_locations.values())):
        raise PilotError("Extra stock word prefix/suffix bins do not account for the complete containment group")
    if sum(stock_source_boundary_top_level_tags.values())!=sum(stock_containment_locations.values()):
        raise PilotError("Private XML boundary topology does not account for every stock prefix case")
    if stock_prefix_has_full_sibling_element>sum(stock_containment_locations.values()):
        raise PilotError("Stock top-level sibling count exceeds prefix cases")
    if punctuation_entries_with_only_one_to_one_glyph_changes>lexical_details[
        "same_unicode_word_tokens_different_punctuation"
    ]:
        raise PilotError("Aligned punctuation entry count exceeds source divergence census")
    if sum(punctuation_aligned_gap_classes.values())!=punctuation_changed_gap_count:
        raise PilotError("Aligned punctuation gaps incomplete")
    if stock_heading_source_covered_entries!=sum(stock_containment_locations.values()):
        raise PilotError("Stock metadata/source neighboring context census is incomplete")
    if stock_heading_context_earlier_tag_counts!=Counter({
        kind:number
        for kind,number in stock_prefix_full_sibling_top_level_tags.items()
        if kind in {"title","table","reference"}
    }):
        raise PilotError("Stock prefix metadata element counts disagree with independent XML topology")
    if (stock_heading_source_any_exact_match_entries>stock_heading_source_covered_entries
            or stock_heading_source_any_word_only_match_entries>stock_heading_source_covered_entries):
        raise PilotError("Source neighbor/title textual match observations exceed stock entries")
    if sum(stock_original_body_suffix_concordance.values())!=sum(stock_containment_locations.values()):
        raise PilotError("Unmodified original source body suffix comparison omitted stock-prefixed entries")
    if sum(stock_original_body_suffix_glyph_classes.values())!=stock_original_body_suffix_changed_gaps:
        raise PilotError("Punctuation changes inside stock suffix do not reconcile")
    if divergent_word_boundary_scanned!=word_relationship_subtypes[
        "different_word_order_or_selection_requires_review"
    ] or unresolved_lexical_census.total!=divergent_word_boundary_scanned:
        raise PilotError("Unexplained lexical source-to-stock cases not fully enumerated")
    if (sum(divergent_word_boundary_suffix_bins.values())!=divergent_word_boundary_scanned
            or sum(divergent_word_boundary_placement.values())!=divergent_word_boundary_scanned
            or sum(divergent_original_middle_word_bins.values())!=divergent_word_boundary_scanned
            or sum(divergent_stock_middle_word_bins.values())!=divergent_word_boundary_scanned):
        raise PilotError("Unexplained source-versus-stock word-boundary totals diverged")
    if len(bounded_priority_examples)>40:
        raise PilotError("Private difference sample exceeds reviewed non-text bound")
    return {
        "source_verse_or_range_bodies_compared":tested,
        "same_words_different_punctuation_subtypes":dict(sorted(punctuation_change_subtypes.items())),
        "different_word_sequence_relationship_subtypes":dict(sorted(word_relationship_subtypes.items())),
        "different_word_sequence_overlap_buckets":dict(sorted(word_overlap_buckets.items())),
        "stock_containment_additional_word_position_counts":dict(sorted(stock_containment_locations.items())),
        "stock_containment_extra_stock_prefix_word_token_bins":dict(sorted(stock_extra_prefix_token_bins.items())),
        "stock_containment_extra_stock_suffix_word_token_bins":dict(sorted(stock_extra_suffix_token_bins.items())),
        "punctuation_nonword_glyph_excess_source_total":sum(source_nonword_glyph_excess.values()),
        "punctuation_nonword_glyph_excess_stock_total":sum(stock_nonword_glyph_excess.values()),
        "punctuation_nonword_glyph_excess_source_top_numeric_codepoints":dict(source_nonword_glyph_excess.most_common(16)),
        "punctuation_nonword_glyph_excess_stock_top_numeric_codepoints":dict(stock_nonword_glyph_excess.most_common(16)),
        "punctuation_codepoint_frequency_is_not_authorial_approval":True,
        "punctuation_aligned_source_stock_gap_classes":dict(sorted(punctuation_aligned_gap_classes.items())),
        "punctuation_aligned_one_to_one_numeric_unicode_replacements":
            dict(punctuation_aligned_numeric_substitutions.most_common(20)),
        "punctuation_aligned_total_changed_gaps":punctuation_changed_gap_count,
        "punctuation_entries_with_exclusively_one_to_one_glyph_changes":
            punctuation_entries_with_only_one_to_one_glyph_changes,
        "punctuation_alignment_does_not_authorize_normalization":True,
        "stock_prefixed_body_first_source_word_top_level_tag_counts":
            dict(sorted(stock_source_boundary_top_level_tags.items())),
        "stock_prefix_complete_top_level_elements_preceding_source_word_by_tag":
            dict(sorted(stock_prefix_full_sibling_top_level_tags.items())),
        "stock_prefix_cases_with_at_least_one_complete_prior_top_level_element":
            stock_prefix_has_full_sibling_element,
        "stock_prefix_text_owner_types_before_source_word":
            dict(sorted(stock_prefix_owners_before_original_body.items())),
        "original_source_word_contiguity_does_not_identify_or_approve_stock_added_material":True,
        "stock_original_body_suffix_exact_unicode_and_difference_classes":
            dict(sorted(stock_original_body_suffix_concordance.items())),
        "stock_original_body_suffix_punctuation_gap_classes":
            dict(sorted(stock_original_body_suffix_glyph_classes.items())),
        "stock_original_body_suffix_one_to_one_numeric_glyph_changes":
            dict(stock_original_body_suffix_glyph_replacements.most_common(16)),
        "stock_original_body_suffix_total_changed_punctuation_gaps":
            stock_original_body_suffix_changed_gaps,
        "stock_body_suffix_comparison_does_not_approve_omitted_prefix_or_layout":True,
        "source_neighbor_compared_to_stock_prefix_entry_count":stock_heading_source_covered_entries,
        "source_neighbor_candidate_type_counts":dict(sorted(stock_heading_source_candidate_types.items())),
        "stock_prefix_matched_authentic_source_neighbor_context_classes":
            dict(sorted(stock_heading_source_match_classes.items())),
        "source_neighbor_exact_context_match_stock_entry_count":
            stock_heading_source_any_exact_match_entries,
        "source_neighbor_same_word_tokens_not_exact_context_match_stock_entry_count":
            stock_heading_source_any_word_only_match_entries,
        "stock_metadata_top_level_tag_counts_crosschecked_against_existing_prefix_inventory":
            dict(sorted(stock_heading_context_earlier_tag_counts.items())),
        "source_neighbor_textual_match_does_not_confirm_authorial_edition_or_license":True,
        "unexplained_original_to_stock_word_boundary_count":divergent_word_boundary_scanned,
        "unresolved_source_stock_lexical_selection_triage":(
            unresolved_lexical_census.report() if unresolved_lexical_census.total
            else {"source_vs_stock_unresolved_word_selection_cases":0,
                  "no_unresolved_lexical_cases_to_triage":True}
        ),
        "unexplained_original_to_stock_common_suffix_fraction_buckets":
            dict(sorted(divergent_word_boundary_suffix_bins.items())),
        "unexplained_original_to_stock_changed_segment_positions":
            dict(sorted(divergent_word_boundary_placement.items())),
        "unexplained_source_changed_middle_word_token_count_buckets":
            dict(sorted(divergent_original_middle_word_bins.items())),
        "unexplained_stock_changed_middle_word_token_count_buckets":
            dict(sorted(divergent_stock_middle_word_bins.items())),
        "unexplained_word_boundary_counts_do_not_prove_compiled_loss":True,
        "bounded_private_prioritized_hash_line_diagnostics":bounded_priority_examples,
        "all_detailed_difference_diagnostics_are_research_only":True,
        "lexical_disagreement_classification":dict(sorted(lexical_details.items())),
        "disagreement_categories_are_only_exploratory_not_text_parity":True,
        "per_source_marker_text_diagnostic_counts":dict(sorted(counters.items())),
        "book_counts":{name:dict(sorted(counts.items())) for name,counts in sorted(per_book.items())},
        "bounded_private_content_discrepancy_hash_samples":issues,
        "whitespace_only_status_is_not_exact_text_parity":True,
        "no_autocorrection_or_content_normalization_performed":True,
        "all_selected_verse_range_body_text_exact_matches":counters["exact_unicode_text_match"]==tested,
        "original_paragraphs_notes_and_quotations_verified":False,
        "full_authored_to_stock_parity_verified":False,
    }


def run(resource_id: str, index_binary: Path, raw_binary: Path) -> dict:
    manifest=load_manifest(resource_id)
    original_config=manifest.get("commentary_source",{})
    url=original_config.get("xml_witness_url")
    original_sha=original_config.get("xml_witness_sha256")
    stock_sha=manifest.get("archive_sha256")
    if not all(isinstance(v,str) and len(v)==64 for v in (original_sha,stock_sha)):
        raise PilotError("Exact original XML and SWORD SHA-256 pins required")
    if not isinstance(url,str) or not url.startswith("https://www.ccel.org/ccel/h/"):
        raise PilotError("Unreviewed original source URL")
    if any(path.is_symlink() or not path.is_file() for path in (index_binary,raw_binary)):
        raise PilotError("Trusted native engine executable unavailable")
    with tempfile.TemporaryDirectory(prefix="commentary-private-text-compare-") as temp:
        root=Path(temp)
        xml_file=root/"original.xml"
        stock_file=root/"stock.zip"
        obs_xml=fetch(url,xml_file,"ccel")
        obs_stock=fetch(manifest["sword_zip_url"],stock_file,manifest["provider"])
        if obs_xml["sha256"]!=original_sha or obs_stock["sha256"]!=stock_sha:
            raise PilotError("Original CCEL text or CrossWire ZIP changed; abort text comparison")
        if obs_xml["bytes"]>MAX_XML:
            raise PilotError("Pinned XML exceeds original-source maximum")
        original_xml=xml_file.read_bytes()
        source,source_proof=_original_source_markers(original_xml)
        chapter_neighbors,chapter_proof=original_chapter_neighbors(original_xml)
        if chapter_proof["explicit_chapter_source_marker_count"]!=source_proof["chapter_source_markers_not_compared"]:
            raise PilotError("Original chapter marker count differs from full independent source audit")
        stock_meta=inspect_archive(stock_file,source_kind="sword",
                                   expected_module_id=manifest["module_id"],
                                   expected_category="commentary")
        conf=stock_meta["sword_conf"]
        if conf["version"]!=manifest["version"] or conf["language"]!=manifest["language"]:
            raise PilotError("Unexpected stock SWORD version/language")
        installed=root/"installed"
        _safe_stock_install(stock_file,stock_meta["members"],installed)
        env=dict(os.environ,SWORD_PATH=str(installed))
        try:
            ix=subprocess.run([str(index_binary),manifest["module_id"]],
                              capture_output=True,timeout=60,env=env,check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Original native index timed out") from None
        if ix.returncode or len(ix.stdout)>12*1024*1024:
            raise PilotError("Original native occupied key index not independently available")
        process=None
        rows=[]
        matches={}
        chapter_intros={}
        numbered_probe=ChapterNeighborNumberedProbe(chapter_neighbors)
        alternate_probe=ChapterNeighborSameBookAlternativeProbe(chapter_neighbors)
        source_p_overlap_probe=OriginalChapterParagraphSpanProbe(chapter_neighbors)
        source_p_boundary_probe=ChapterParagraphBoundaryProbe(chapter_neighbors)
        reference_cross_slot=ReferenceCrossSlotTopology(source)
        native_run_boundaries=NativeRawRunBoundaryInventory()
        try:
            process=subprocess.Popen(["timeout","360s",str(raw_binary),manifest["module_id"]],
                                     stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env)
            if process.stdout is None:
                raise PilotError("Cannot capture stock raw XML privately")
            def collect(kind,ref,raw):
                rows.append((kind,ref))
                if kind=="K" and ref in source:
                    matches[ref]=raw
                numbered_probe.observe(kind,ref,raw,raw_as_strict_xml_text)
                alternate_probe.observe(kind,ref,raw,raw_as_strict_xml_text)
                source_p_overlap_probe.observe(kind,ref,raw,raw_as_strict_xml_text)
                source_p_boundary_probe.observe(kind,ref,raw,raw_as_strict_xml_text)
                reference_cross_slot.observe_stock(kind,ref,raw)
                native_run_boundaries.observe(kind,ref,raw)
                if kind=="I" and (ref in chapter_neighbors or
                                   (ref.endswith(".0") and ref[:-2] in chapter_neighbors)):
                    chapter_intros[ref]=raw
            raw_summary,_,_,_=parse_native_raw_corpus(process.stdout,on_entry=collect)
            process.stdout.close()
            status=process.wait(timeout=15)
            if status!=0:
                raise PilotError("Stock SWORD native text reader failed to finish its complete stream")
        except BaseException:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            raise
        crosscheck=private_crosscheck(ix.stdout,manifest["module_id"],rows,raw_summary)
        analysis=compare_private_texts(source,matches,
            on_unresolved_word_case=reference_cross_slot.observe_unresolved)
        lexical=analysis['unresolved_source_stock_lexical_selection_triage']
        reference_cross_slot_report=reference_cross_slot.report(lexical)
        pending_plain_relations={
            "plain_word_order_or_selection_requires_editorial_review",
            "same_plain_word_multiset_but_different_order",
            "source_plain_words_only_after_removing_stock_scripture_labels",
        }
        plain_review_total=sum(
            lexical["original_prose_outside_link_word_relation_counts"].get(k,0)
            for k in pending_plain_relations
        )
        plain_payload_topology=reference_cross_slot.report_nonlink_plain_word_stock_payloads(
            lexical["bounded_plain_word_nontrivial_differences_line_and_hash_cases"],
            total_nonlink_review_cases=plain_review_total,
        )
        large_plain_cases=[
            case for case in lexical["bounded_plain_word_nontrivial_differences_line_and_hash_cases"]
            if (case["exact_plain_word_alignment"][
                    "original_plain_words_not_matched_in_exact_order"] is not None
                and case["exact_plain_word_alignment"][
                    "original_plain_words_not_matched_in_exact_order"] > 10)
        ]
        if not large_plain_cases:
            alternative_prose={
                "original_source_large_plain_word_cases":0,
                "no_large_original_plain_word_cases_to_scan":True,
            }
        else:
            alternative_probe=OriginalProseAlternativeNativeSlotProbe(
                source,large_plain_cases
            )
            replay_rows=[]
            replay_process=None
            try:
                replay_process=subprocess.Popen(
                    ["timeout","360s",str(raw_binary),manifest["module_id"]],
                    stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env
                )
                if replay_process.stdout is None:
                    raise PilotError("Second exact native stock reader cannot stream")
                def collect_original_prose_alternatives(kind,ref,raw):
                    replay_rows.append((kind,ref))
                    alternative_probe.observe(kind,ref,raw)
                replay_summary,_,_,_=parse_native_raw_corpus(
                    replay_process.stdout,on_entry=collect_original_prose_alternatives
                )
                replay_process.stdout.close()
                replay_status=replay_process.wait(timeout=15)
                if replay_status != 0:
                    raise PilotError("Second original native raw reader did not complete")
                if replay_summary != raw_summary or replay_rows != rows:
                    raise PilotError(
                        "Original stock native replay content or occupied K/I key order changed"
                    )
            except BaseException:
                if replay_process is not None and replay_process.poll() is None:
                    replay_process.kill()
                    replay_process.wait()
                raise
            alternative_prose=alternative_probe.report()
            if alternative_prose["all_native_raw_entries_replayed"] != len(rows):
                raise PilotError("Original second native prose scan omitted occupied keys")
        if large_plain_cases:
            boundary_case_report=native_run_boundaries.report(source,large_plain_cases)
            complete_shared_run_sources=inspect_shared_original_units_in_native_runs(
                source,native_run_boundaries,matches,large_plain_cases
            )
        else:
            boundary_case_report={
                "source_marker_case_count":0,
                "no_original_large_prose_cases_to_check":True,
            }
            complete_shared_run_sources={
                "multi_original_source_start_same_native_raw_run_groups":0,
                "full_authentic_original_source_units_in_those_runs":0,
                "no_large_original_prose_cases_to_inspect":True,
            }
        chapter_analysis=compare_chapter_neighbors(
            chapter_neighbors,chapter_intros,raw_as_strict_xml_text
        )
        chapter_numbered_location=numbered_probe.report()
        chapter_other_slot_location=alternate_probe.report(numbered_probe)
        original_p_word_overlap=source_p_overlap_probe.report(chapter_other_slot_location)
        original_p_boundaries=source_p_boundary_probe.report(
            chapter_other_slot_location,original_p_word_overlap
        )
        if chapter_analysis["original_chapter_source_siblings_compared"]!=chapter_proof[
            "explicit_chapter_source_marker_count"
        ]:
            raise PilotError("Chapter neighbor readback omitted original markers")
    return {
        "schema_version":1,
        "resource_id":resource_id,
        "status":"full_source_verse_and_range_body_to_stock_raw_text_diagnostics_not_release_approval",
        "source_original_sha256":original_sha,
        "stock_sword_archive_sha256":stock_sha,
        "stock_sword_conf_sha256":conf["conf_sha256"],
        "stock_full_raw_content_sha256":raw_summary["all_native_raw_entries_ordered_sha256"],
        "stock_native_key_order_sha256":crosscheck["native_key_order_sha256"],
        "native_full_corpus_rechecked":True,
        "source_original_verse_and_range_body_evidence":source_proof,
        "text_diagnostic":analysis,
        "source_unpaired_reference_cross_native_slots":reference_cross_slot_report,
        "source_nonlink_prose_review_stock_raw_duplicate_topology":plain_payload_topology,
        "source_large_nonlink_prose_native_alternative_locations":alternative_prose,
        "source_large_prose_marker_to_native_raw_run_boundary_diagnostics":boundary_case_report,
        "source_complete_original_units_within_shared_stock_raw_K_runs":complete_shared_run_sources,
        "source_original_chapter_neighbor_evidence":chapter_proof,
        "source_chapter_neighbor_to_stock_intro_diagnostics":chapter_analysis,
        "source_chapter_neighbor_to_same_chapter_numbered_location":chapter_numbered_location,
        "source_chapter_neighbor_to_same_book_alternative_slots":chapter_other_slot_location,
        "source_chapter_p_source_to_stock_word_contiguity":original_p_word_overlap,
        "source_chapter_p_boundaries_in_stock":original_p_boundaries,
        "original_source_divisions_without_markers_compared":False,
        "chapter_intro_and_body_lexical_parity_compared":False,
        "original_exact_edition_proven":False,
        "original_structure_notes_quotes_and_paragraphs_parity_proven":False,
        "copyright_and_redistribution_approved":False,
        "editorial_approved":False,
        "published":False,
        "source_text_or_sword_bytes_in_receipt":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id",required=True)
    p.add_argument("--native-index-binary",required=True,type=Path)
    p.add_argument("--native-raw-binary",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        result=run(args.resource_id,args.native_index_binary,args.native_raw_binary)
        code=0
    except (ValueError,OSError,RuntimeError,zipfile.BadZipFile) as exc:
        result={"status":"blocked","resource_id":args.resource_id,"reason":str(exc),
                "full_authored_to_stock_parity_verified":False,"published":False}
        code=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Commentary original ↔ stock text diagnostics: "+result["status"]+" (no original text disclosed)")
    return code


if __name__=="__main__":
    raise SystemExit(main())
