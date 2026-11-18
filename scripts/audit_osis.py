#!/usr/bin/env python3
"""Read-only OSIS editorial audit; structural diagnostics are NOT proposed edits.

Input can be any well-formed OSIS XML, including a source rejected by the
stricter reviewed structure gate. Do not conflate an audit with XSD approval.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from guard_osis import parse_xml, require_regular_file, MAX_SOURCE_BYTES, StructureFailure, write_report

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SIMPLE_REF = re.compile(
    r"^(?:[A-Za-z0-9_-]+:)?[1-4]?[A-Za-z][A-Za-z0-9]*"
    r"(?:\.\d+(?:\.\d+)?)?(?:-(?:[1-4]?[A-Za-z][A-Za-z0-9]*"
    r"(?:\.\d+(?:\.\d+)?)?))?$"
)
# Reviewed SWORD OSIS commentary section grammar (CrossWire OSIS_Commentaries).
# A continuous range needs TWO FULL endpoints; a discontinuous list uses
# whitespace-separated complete references. A comma is NOT a range delimiter.
SECTION_ATOM = re.compile(
    r"^(?P<book>[1-4]?[A-Za-z][A-Za-z0-9]*)"
    r"(?:\.(?P<chapter>[1-9][0-9]*)(?:\.(?P<verse>[1-9][0-9]*))?)?$"
)
SHORT_COMMA_VERSES = re.compile(
    r"(?<![A-Za-z0-9])(?:[1-9][0-9]{0,2}[.:])?"
    r"[1-9][0-9]{0,2},[1-9][0-9]{0,2}(?![0-9])"
)
MACHINE_COMMA_RANGE = re.compile(
    r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\."
    r"[1-9][0-9]*,[1-9][0-9]*$"
)
MAX_STRUCTURAL_SAMPLES = 80

def _commentary_ref_tokens(value: str) -> tuple[str, list[tuple]] :
    """Syntactically audit one complete source annotateRef without repairs.

    Return a category and full machine book/chapter/verse tuple for each
    endpoint. No canonical verse existence is inferred from a regex.
    """
    if not isinstance(value, str) or not value or value.strip() != value:
        return "missing_or_padded", []
    if "," in value:
        return ("comma_verse_list_or_range_requires_review"
                if MACHINE_COMMA_RANGE.fullmatch(value)
                else "comma_other_annotation_requires_review"), []
    if ":" in value:
        return "work_prefix_or_unreviewed_colon", []
    tokens = value.split()
    endpoints = []
    ranged = 0
    for token in tokens:
        parts = token.split("-")
        if len(parts) not in (1, 2):
            return "multi_hyphen_unsupported", []
        parsed = []
        for part in parts:
            match = SECTION_ATOM.fullmatch(part)
            if not match:
                return "unqualified_or_other_syntax", []
            book = match.group("book")
            chapter = int(match.group("chapter")) if match.group("chapter") else 0
            verse = int(match.group("verse")) if match.group("verse") else 0
            parsed.append((book, chapter, verse))
        if len(parsed) == 2:
            ranged += 1
            if parsed[0][0] != parsed[1][0]:
                return "cross_book_range_requires_order_review", []
            if parsed[0][1:] >= parsed[1][1:]:
                return "reversed_or_zero_length_range", []
            if not (parsed[0][2] and parsed[1][2]):
                return "range_needs_complete_verse_endpoints", []
        endpoints.append(tuple(parsed))
    flat = [v for group in endpoints for v in group]
    if not flat:
        return "missing_or_padded", []
    if len({v[0] for v in flat}) > 1:
        return "discontinuous_cross_book_list", flat
    if len(tokens) > 1:
        return "discontinuous_list", flat
    if ranged:
        return "continuous_verse_range", flat
    one = flat[0]
    return ("single_verse" if one[2] else
            "chapter_intro" if one[1] else "book_intro"), flat

VERSE_MARKER = re.compile(r"(?<!\d)(?:[1-9]\d{0,2})(?=\s|\u00a0|[.:])")
RISKS = {
    "long_bold_range": "typography",
    "upper_case_paragraph": "typography",
    "suspicious_heading": "typography",
    "excessive_styling": "typography",
    "unknown_style": "typography",
    "introductory_scripture_candidate": "quotation_candidate",
    "unreviewed_cross_reference": "reference_candidate",
    "invalid_cross_reference": "reference_error",
    "duplicate_verse_id": "structure_error",
    "duplicate_commentary_reference": "structure_candidate",
    "commentary_annotation_missing": "structure_error",
    "commentary_annotation_unreviewed": "structure_candidate",
    "commentary_comma_range_candidate": "structure_candidate",
    "commentary_range_reversed": "structure_error",
    "commentary_book_scope_mismatch": "structure_candidate",
    "commentary_out_of_order": "structure_candidate",
    "commentary_title_numeric_comma_candidate": "structure_candidate",
    "empty_verse_identifier": "structure_error",
    "verse_key_out_of_sequence": "structure_candidate",
}


def _tag(element) -> str:
    return element.tag[len(NS):] if isinstance(element.tag, str) and element.tag.startswith(NS) else str(element.tag)


def _where(node) -> dict:
    tree = node.getroottree()
    return {
        "xml_xpath": tree.getpath(node),
        "original_xml_line": node.sourceline,
    }


def _entry(source, node, code, *, reason, details=None):
    return dict(code=code, category=RISKS[code], severity=(
        "error" if code in {"duplicate_verse_id", "invalid_cross_reference", "empty_verse_identifier"}
        else "review"
    ), source_path=str(source), **_where(node), reason=reason,
        **({"details": details} if details else {}))


def _reference_token(value: str) -> bool:
    return bool(value and SIMPLE_REF.fullmatch(value))


def _verse_key(value: str):
    match = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return match[1], int(match[2]), int(match[3])



def compare_source_milestone_index(path: Path, *,
                                   numbered_keys: list[str],
                                   intro_keys: list[str],
                                   body_sha_by_verse: dict[str, str] | None = None) -> dict:
    """Independently compare *every* source OSIS verse/chapter/book assignment
    to the compiled SWORD's actual occupied keys.

    The OSIS source can be a Bible-structured commentary, with <verse
    osisID="Gen.1.1 Gen.1.2" sID="Gen.1.1-2" n="1-2"/> and its paired
    <verse eID="Gen.1.1-2"/>. These IDs are NOT annotateRef sections.

    Report exact/index/label/overlap anomalies only as bounded reference
    identifiers and counts. Never mutate source or infer omitted verse text.
    """
    if (not isinstance(numbered_keys, list) or not numbered_keys
            or not isinstance(intro_keys, list)
            or not isinstance(body_sha_by_verse, (dict, type(None)))):
        raise ValueError("Actual compiled native numbered/introduction keys required")
    source=Path(path).absolute()
    raw=require_regular_file(source,MAX_SOURCE_BYTES,"SOURCE_UNAVAILABLE")
    if re.search(rb"<!DOCTYPE\b",raw,flags=re.IGNORECASE):
        raise ValueError("Unreviewed source DTD")
    document=parse_xml(source,raw,"MALFORMED_XML")
    full_verse=re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)$")
    full_chapter=re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)$")
    book_id=re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*$")
    expected_k=set()
    source_chapters=set()
    source_books=set()
    groups=[]
    counts=Counter()
    cases=[]
    seen={}
    active_chapter=None
    active_verse=None
    previous_book=None
    previous_chapter=None

    def fault(code, node, ref=None):
        counts[code]+=1
        if len(cases)<MAX_STRUCTURAL_SAMPLES:
            cases.append({"code":code, "line":node.sourceline,
                          "reference":ref[:120] if isinstance(ref,str) else None})

    for el in document.iter():
        if not isinstance(el.tag,str):
            continue
        tag=_tag(el)
        if tag=="div" and el.get("type")=="book":
            ref=el.get("osisID")
            counts["source_book_divisions"]+=1
            if not ref or not book_id.fullmatch(ref) or ref in source_books:
                fault("invalid_or_repeated_book_division",el,ref)
            else:
                source_books.add(ref)
                previous_book=ref
                previous_chapter=None
        if tag=="chapter":
            opened=el.get("osisID")
            closing=el.get("eID")
            if opened is not None:
                counts["source_chapter_openers"]+=1
                if (full_chapter.fullmatch(opened) is None
                        or opened!=el.get("sID")
                        or opened in source_chapters
                        or (previous_book and not opened.startswith(previous_book+"."))):
                    fault("invalid_or_duplicate_chapter_open",el,opened)
                else:
                    source_chapters.add(opened)
                if active_chapter is not None or active_verse is not None:
                    fault("overlapping_chapter_or_unclosed_verse",el,opened)
                active_chapter=opened
                if full_chapter.fullmatch(opened):
                    chapnum=int(opened.rsplit(".",1)[-1])
                    if previous_chapter is not None and chapnum<=previous_chapter:
                        fault("chapter_number_nonincreasing",el,opened)
                    previous_chapter=chapnum
                    if el.get("n") != str(chapnum):
                        fault("chapter_display_label_disagrees",el,opened)
            elif closing is not None:
                counts["source_chapter_closers"]+=1
                if active_chapter!=closing or active_verse is not None:
                    fault("unpaired_chapter_end",el,closing)
                active_chapter=None
            else:
                fault("chapter_missing_start_and_end",el)
        if tag=="verse":
            opened=el.get("osisID")
            closing=el.get("eID")
            if opened is not None:
                counts["source_verse_group_openers"]+=1
                if active_verse is not None:
                    fault("overlapping_or_unclosed_verse",el,opened)
                active_verse=el.get("sID")
                tokens=opened.split()
                parsed=[full_verse.fullmatch(token) for token in tokens]
                if not tokens or not all(parsed):
                    fault("unparseable_source_verse_assignment",el,opened)
                    continue
                if any(token in seen for token in tokens):
                    fault("same_verse_assigned_more_than_once",el,opened)
                for token in tokens:
                    expected_k.add(token)
                    seen.setdefault(token,el.sourceline)
                first,last=tokens[0],tokens[-1]
                fb,fc,fv=parsed[0].groups()
                lb,lc,lv=parsed[-1].groups()
                if active_chapter!=f"{fb}.{fc}" or previous_book != fb:
                    fault("verse_not_in_its_source_chapter_or_book",el,first)
                numbers=[int(match.group(3)) for match in parsed]
                same_chapter=all(match.group(1)==fb and match.group(2)==fc
                                 for match in parsed)
                contiguous=same_chapter and numbers==list(range(numbers[0],numbers[0]+len(numbers)))
                if not contiguous:
                    fault("noncontiguous_or_crosschapter_verse_group",el,opened)
                expected_sid=(first if len(tokens)==1
                              else f"{first}-{lv}" if same_chapter else None)
                expected_label=(str(fv) if len(tokens)==1
                                else f"{fv}-{lv}" if same_chapter else None)
                if expected_sid is None or el.get("sID")!=expected_sid:
                    fault("verse_start_label_disagrees_with_osisID_list",el,opened)
                if expected_label is None or el.get("n")!=expected_label:
                    fault("visible_verse_range_label_needs_harmonization",el,
                          el.get("n"))
                groups.append((tokens,el.sourceline))
            elif closing is not None:
                counts["source_verse_group_closers"]+=1
                if not active_verse or closing!=active_verse:
                    fault("unpaired_or_mismatched_verse_end",el,closing)
                active_verse=None
            else:
                fault("verse_without_machine_marker",el)
    if active_chapter is not None:
        counts["unterminated_chapter_at_end_of_source"]+=1
    if active_verse is not None:
        counts["unterminated_verse_at_end_of_source"]+=1

    native_k=set(numbered_keys)
    native_i=set(intro_keys)
    expected_i=source_books | source_chapters
    missing_k=expected_k-native_k
    extra_k=native_k-expected_k
    missing_i=expected_i-native_i
    extra_i=native_i-expected_i
    if body_sha_by_verse is not None:
        if set(body_sha_by_verse)!=native_k:
            raise ValueError("Native linked-body digest covers different keys")
        for group,line in groups:
            if len(group)>1 and all(key in body_sha_by_verse for key in group):
                counts["native_linked_groups_checked"]+=1
                if len({body_sha_by_verse[key] for key in group})!=1:
                    counts["native_group_has_different_entry_bodies"]+=1
                    if len(cases)<MAX_STRUCTURAL_SAMPLES:
                        cases.append({"code":"native_group_has_different_entry_bodies",
                                      "line":line,"reference":group[0]})
    counts["distinct_source_verse_osisIDs"]=len(expected_k)
    counts["distinct_source_intro_osisIDs"]=len(expected_i)
    counts["native_numbered_refs"]=len(native_k)
    counts["native_intro_refs"]=len(native_i)
    counts["missing_source_verses_in_native"]=len(missing_k)
    counts["native_verses_without_source_osisID"]=len(extra_k)
    counts["missing_source_intros_in_native"]=len(missing_i)
    counts["native_intros_without_source_intro_osisID"]=len(extra_i)
    for code,refs in (("missing_source_verses_in_native",missing_k),
                      ("native_verses_without_source_osisID",extra_k),
                      ("missing_source_intros_in_native",missing_i),
                      ("native_intros_without_source_intro_osisID",extra_i)):
        for ref in sorted(refs)[:max(0,MAX_STRUCTURAL_SAMPLES-len(cases))]:
            cases.append({"code":code,"reference":ref,"line":None})
    problems={key:value for key,value in counts.items()
              if key.startswith(("invalid_","overlapping_","unpaired_",
                                 "chapter_number_nonincreasing",
                                 "verse_start_label_disagrees",
                                 "visible_verse_range_label_needs",
                                 "noncontiguous_","same_verse_","verse_not_",
                                 "verse_without_","chapter_missing_",
                                 "unterminated_","missing_source_",
                                 "native_verses_without_","native_intros_without_",
                                 "native_group_has_")) and value}
    return {
        "schema_version":1,
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "status":"SOURCE_NATIVE_INDEX_AND_MILESTONE_GEOMETRY_MATCH"
                 if not problems else "SOURCE_NATIVE_STRUCTURE_REQUIRES_REVIEW",
        "all_source_verse_ids_match_occupied_native_keys":not (missing_k or extra_k),
        "all_source_book_chapter_ids_match_occupied_native_intros":not (missing_i or extra_i),
        "all_linked_verse_bodies_consistent_if_checked":not counts["native_group_has_different_entry_bodies"],
        "structure_counts":dict(sorted(counts.items())),
        "anomaly_counts":problems,
        "bounded_reference_only_findings":cases,
        "source_text_or_notes_changed":False,
        "historical_edition_text_verified":False,
        "published":False,
    }



def source_commentary_overlap_witness(
        path: Path, *, groups_out: list | None = None
) -> tuple[dict, set[str]]:
    """Observe overlapping authorial verse-group bodies without rewriting them.

    A group may span many verse IDs. This private in-memory witness retains
    original text temporarily for strict comparison with native SWORD.
    Public diagnostics must contain counts, line numbers, references and SHA,
    not the source prose. A group can be retrieved at another verse even if
    one overlapping key is overwritten; do not equate overlap with text loss.
    """
    raw=require_regular_file(Path(path).absolute(),MAX_SOURCE_BYTES,"SOURCE_UNAVAILABLE")
    root=parse_xml(Path(path).absolute(),raw,"MALFORMED_XML")
    owners=defaultdict(list)
    groups=[]
    active=[None]
    def finish(node):
        current=active[0]
        if current is None or node.get("eID")!=current["sID"]:
            raise ValueError("Unbalanced original commentary verse group")
        current["text"]="".join(current.pop("parts"))
        if len(current["text"]) > 1000000:
            raise ValueError("Oversized original commentary group text")
        for key in current["keys"]:
            owners[key].append(current)
        groups.append(current)
        active[0]=None
    def walk(node):
        if not isinstance(node.tag,str):
            return
        if _tag(node)=="verse" and node.get("sID"):
            if active[0] is not None:
                raise ValueError("Source commentary verse groups nested unexpectedly")
            active[0]={
                "sID":node.get("sID"),
                "keys":tuple((node.get("osisID") or "").split()),
                "line":node.sourceline,
                "parts":[],
                "semantic_nodes":[],
            }
        elif _tag(node)=="verse" and node.get("eID"):
            finish(node)
        if (active[0] is not None and _tag(node) in {"note","reference"}):
            active[0]["semantic_nodes"].append({
                "tag":_tag(node),
                "body":"".join(node.itertext()),
                "attributes":dict(node.attrib),
            })
        if active[0] is not None and node.text:
            active[0]["parts"].append(node.text)
        for child in node:
            walk(child)
            if active[0] is not None and child.tail:
                active[0]["parts"].append(child.tail)
    walk(root.getroot())
    if active[0] is not None:
        raise ValueError("Original commentary verse group remains unclosed")
    if len(groups)==0:
        raise ValueError("No actual original authored commentary groups")
    if groups_out is not None:
        if not isinstance(groups_out,list) or groups_out:
            raise ValueError("Private source group output must be an empty list")
        groups_out.extend(groups)
    overlapping={
        key:tuple(chapters) for key,chapters in owners.items()
        if len(chapters)>1
    }
    needed={key for instances in overlapping.values()
            for instance in instances for key in instance["keys"]}
    return overlapping, needed


def compare_source_overlap_native_bodies(
        overlapping: dict, native_raw: dict[str, bytes],
        *, max_cases: int = 35) -> dict:
    """Classify per-*authored group* whether its full word stream survives.

    Matching raw source prose against any indexed SWORD key is stronger than
    counting verse-address collisions; however exact word substring checks
    alone cannot prove full notes/markup fidelity or printed edition identity.
    """
    from lxml import etree
    from commentary_nonlink_word_alignment import exact_unicode_source_ordered_subsequence
    if (not isinstance(overlapping,dict) or not overlapping
            or not isinstance(native_raw,dict) or not native_raw):
        raise ValueError("No source/native overlap evidence")
    involved={}
    for key,groups in overlapping.items():
        for group in groups:
            involved[id(group)]=group
    required={key for g in involved.values() for key in g["keys"]}
    if not required.issubset(native_raw):
        raise ValueError("Native commentary overlap group keys not all available")
    native_words={}
    for key in required:
        raw=native_raw[key]
        if not isinstance(raw,bytes) or len(raw)>2*1024*1024:
            raise ValueError("Untrusted compiled overlap XML frame")
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,recover=False,huge_tree=False)
        try:
            root=etree.fromstring(b"<fragment>"+raw+b"</fragment>",parser)
        except etree.XMLSyntaxError:
            raise ValueError("Unparseable compiled overlap frame") from None
        native_words[key]=" ".join(re.findall(r"\w+",
                                              "".join(root.itertext()).casefold()))
    cases=[]
    counts=Counter()
    for group in sorted(involved.values(),key=lambda x:x["line"]):
        words=" ".join(re.findall(r"\w+",group["text"].casefold()))
        if not words:
            classification="source_group_without_searchable_words"
            matching=[]
        else:
            matching=[key for key in group["keys"] if
                      words in native_words[key]]
            if len(matching)==len(group["keys"]):
                classification="full_prose_in_every_original_native_key"
            elif matching:
                classification="full_prose_present_in_some_native_keys"
            else:
                classification="full_source_word_sequence_not_found_in_group_native_keys"
        # Full contiguous string mismatches may arise from interleaved
        # passages: compare whole source words in order, then 40-word blocks,
        # with explicit word boundaries. Partial presence is NOT a loss proof.
        tokens=words.split()
        ordered_keys=[
            key for key in group["keys"] if
            exact_unicode_source_ordered_subsequence(
                tokens,native_words[key].split()) is True
        ] if tokens else []
        chunk_width=40
        chunks=[tokens[i:i+chunk_width] for i in range(0,len(tokens),chunk_width)]
        chunks_found=sum(
            any((" "+" ".join(chunk)+" ") in (" "+native_words[key]+" ")
                for key in group["keys"]) for chunk in chunks
        )
        chunk_fraction=(round(chunks_found/len(chunks),4) if chunks else None)
        if not matching and ordered_keys:
            counts["no_contiguous_match_but_full_source_words_in_native_order"]+=1
        if not matching and chunk_fraction is not None and chunk_fraction<1:
            counts["no_contiguous_match_with_some_unmatched_40word_blocks"]+=1
        counts[classification]+=1
        # Independent stronger missing-text check: fixed long word shingles
        # from start, quarters, midpoint and end of EACH authored source.
        # Full contiguous prose can fail when XML import inserts labels or
        # nested notes, whereas a truly dropped section has no native shingles.
        parts=words.split()
        width=min(24,max(4,len(parts)//6)) if parts else 0
        positions=(sorted(set(
            (0,(len(parts)-width)//4,(len(parts)-width)//2,
             3*(len(parts)-width)//4,len(parts)-width)))
            if width else [])
        shingles=[" ".join(parts[pos:pos+width]) for pos in positions]
        hit_count=sum(any(shingle in native_words[key]
                          for key in group["keys"]) for shingle in shingles)
        counts["source_group_shingles_checked"]+=len(shingles)
        counts["source_group_shingles_found_in_native"]+=hit_count
        if shingles and not hit_count:
            counts["source_groups_with_zero_native_shingle_evidence"]+=1
        if len(cases)<max_cases:
            cases.append({
                "source_xml_line":group["line"],
                "original_source_sid":group["sID"],
                "authored_verse_addresses":len(group["keys"]),
                "full_source_word_count":len(words.split()),
                "full_source_word_stream_sha256":hashlib.sha256(
                    words.encode("utf-8")).hexdigest(),
                "indexed_key_word_sequence_matches":len(matching),
                "fixed_source_shingles_checked":len(shingles),
                "fixed_source_shingles_found_in_any_claimed_native_key":hit_count,
                "source_shingle_word_width":width,
                "first_matching_native_key":matching[0] if matching else None,
                "source_words_in_order_native_keys":len(ordered_keys),
                "source_40word_chunk_count":len(chunks),
                "source_40word_chunks_found_in_any_group_native_key":chunks_found,
                "source_40word_chunks_found_fraction":chunk_fraction,
                "class":classification,
            })
    return {
        "schema_version":1,
        "status":"SOURCE_NATIVE_OVERLAP_WORD_PRESENCE_TRIAGE_NOT_FINAL_PARITY",
        "source_keys_claimed_by_multiple_groups":len(overlapping),
        "source_distinct_overlapping_groups_examined":len(involved),
        "all_related_native_keys_read":len(required),
        "classification_counts":dict(sorted(counts.items())),
        "bounded_source_group_cases":cases,
        "source_group_text_or_native_body_exported":False,
        "all_word_streams_in_source_evaluated":True,
        "notes_markup_and_independent_editions_not_verified":True,
        "source_or_sword_edited_or_released":False,
    }


def compare_all_commentary_source_group_words(
        groups: list[dict], native_first_raw: dict[str,bytes],
        *, max_cases: int = 50) -> dict:
    """Read every authored source group against its compiled native first key.

    Stronger than a native key count. A missing 40-word block is a REVIEW
    finding, not proof that particular Bible words were never authored.
    No source prose, note body, inline XML or raw SWORD is released.
    """
    from lxml import etree
    if (not isinstance(groups,list) or not 1 <= len(groups) <= 100000
            or not isinstance(native_first_raw,dict)
            or not 0 <= max_cases <= 100):
        raise ValueError("Unbounded or missing source/native groups")
    first_refs={g["keys"][0] for g in groups if g.get("keys")}
    if not first_refs or first_refs!=set(native_first_raw):
        raise ValueError("Native first-key raw frames do not match source groups")
    native_words={}
    for key,raw in native_first_raw.items():
        if not isinstance(raw,bytes) or len(raw)>2*1024*1024:
            raise ValueError("Oversized or non-binary native commentary body")
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,recover=False,huge_tree=False)
        try:
            root=etree.fromstring(b"<fragment>"+raw+b"</fragment>",parser)
        except (ValueError,etree.XMLSyntaxError):
            raise ValueError("Unparseable compiled native commentary body") from None
        native_words[key]=" ".join(re.findall(r"\w+",
                                              "".join(root.itertext()).casefold()))
    counts=Counter()
    problematic=[]
    for group in groups:
        if not isinstance(group.get("text"),str) or not group.get("keys"):
            raise ValueError("Invalid private source group body or verse scope")
        ref=group["keys"][0]
        words=" ".join(re.findall(r"\w+",group["text"].casefold()))
        tokens=words.split()
        compiled=native_words[ref]
        counts["authored_groups_checked"]+=1
        if not tokens:
            counts["source_groups_without_word_tokens"]+=1
            continue
        counts["authored_word_tokens_checked"]+=len(tokens)
        if words in compiled:
            counts["groups_with_contiguous_full_source_word_stream"]+=1
            continue
        chunks=[tokens[i:i+40] for i in range(0,len(tokens),40)]
        hits=sum((" "+" ".join(chunk)+" ") in (" "+compiled+" ")
                 for chunk in chunks)
        counts["groups_without_full_contiguous_word_match"]+=1
        counts["unmatched_group_40word_chunks"]+=len(chunks)-hits
        if hits==len(chunks):
            counts["groups_with_all_40word_chunks_present"]+=1
        else:
            counts["groups_with_missing_40word_chunks"]+=1
            if len(problematic)<max_cases:
                problematic.append({
                    "source_line":group["line"],
                    "source_section":group["sID"],
                    "native_first_ref":ref,
                    "source_word_count":len(tokens),
                    "source_word_stream_sha256":hashlib.sha256(
                        words.encode("utf-8")).hexdigest(),
                    "source_40word_chunks":len(chunks),
                    "chunks_present_in_native_first_key":hits,
                })
    return {
        "schema_version":1,
        "status":("PRIVATE_ALL_AUTHORED_GROUP_WORD_BLOCKS_PRESENT_NOT_NOTE_PARITY"
                  if not counts["groups_with_missing_40word_chunks"] else
                  "PRIVATE_SOURCE_NATIVE_GROUP_WORDS_REQUIRE_REVIEW"),
        "counts":dict(sorted(counts.items())),
        "bounded_reference_only_missing_word_cases":problematic,
        "entire_authorial_source_reviewed_against_native_keys":True,
        "exact_note_and_markup_parity_verified":False,
        "published":False,
    }


def source_commentary_introductions(path: Path) -> dict[str,dict]:
    """Extract authorial book/chapter pre-verse introductions without editing.

    A book introduction is source text prior to its first chapter opener; a
    chapter introduction is source text after its chapter opener but before
    its first verse opener. Content in other/ambiguous scopes is not silently
    assigned to an introduction. Original prose stays only in private memory.
    """
    from lxml import etree
    raw=require_regular_file(Path(path).absolute(),MAX_SOURCE_BYTES,"SOURCE_UNAVAILABLE")
    document=parse_xml(Path(path).absolute(),raw,"MALFORMED_XML")
    result={}
    for book in document.iter():
        if not isinstance(book.tag,str) or _tag(book)!="div" or book.get("type")!="book":
            continue
        book_ref=book.get("osisID")
        if not book_ref or book_ref in result:
            raise ValueError("Missing/duplicate authored commentary book")
        result[book_ref]={"parts":[],"semantic_nodes":[],"line":book.sourceline}
        active=[book_ref]
        chapter=[None]
        def walk(node):
            if not isinstance(node.tag,str):
                return
            kind=_tag(node)
            if kind=="chapter" and node.get("osisID"):
                chap=node.get("osisID")
                if not chap.startswith(book_ref+".") or chap in result:
                    raise ValueError("Unparseable or duplicate source chapter intro")
                result[chap]={"parts":[],"semantic_nodes":[],"line":node.sourceline}
                active[0]=chap
                chapter[0]=chap
            elif kind=="verse" and node.get("osisID"):
                active[0]=None
            elif (active[0] is not None and active[0]==chapter[0]
                  and ((kind=="div" and node.get("type")=="section")
                       or (kind=="title" and node.get("type")
                           not in {"main","chapter","sub"}))):
                # osis2mod assigns subsequent material to the FIRST verse.
                # Distinguish pre-verse section prose from genuine chapter I.
                # https://wiki.crosswire.org/Osis2mod
                result[active[0]]["preverse_boundary"]={
                    "kind":kind,
                    "type":node.get("type"),
                    "line":node.sourceline,
                }
                active[0]=None
            elif kind=="chapter" and node.get("eID"):
                if chapter[0]!=node.get("eID"):
                    raise ValueError("Unpaired source chapter boundary")
                active[0]=None
                chapter[0]=None
            if active[0] is not None:
                if kind in {"note","reference"}:
                    result[active[0]]["semantic_nodes"].append({
                        "tag":kind, "body":"".join(node.itertext()),
                        "attributes":dict(node.attrib),
                    })
                if node.text:
                    result[active[0]]["parts"].append(node.text)
            for child in node:
                walk(child)
                if active[0] is not None and child.tail:
                    result[active[0]]["parts"].append(child.tail)
        walk(book)
    if not result:
        raise ValueError("No authored source introductions")
    for record in result.values():
        record["text"]="".join(record.pop("parts"))
        record.setdefault("preverse_boundary",None)
    return result


def compare_commentary_source_native_introductions(
        source: dict[str,dict], native_intro: dict[str,bytes],
        *, max_cases: int = 40) -> dict:
    """Research-only book/chapter source→SWORD introduction parity screen."""
    from lxml import etree
    import unicodedata
    if (not isinstance(source,dict) or not source or
            not isinstance(native_intro,dict) or set(source)!=set(native_intro)
            or not 0<=max_cases<=100):
        raise ValueError("Source/native introduction key coverage mismatch")
    def fold(t):
        return " ".join(unicodedata.normalize("NFC",t).split())
    count=Counter()
    issues=[]
    for ref,original in source.items():
        raw=native_intro[ref]
        if not isinstance(raw,bytes) or len(raw)>2*1024*1024:
            raise ValueError("Unsafe native introduction payload")
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,recover=False,huge_tree=False)
        try:
            doc=etree.fromstring(b"<fragment>"+raw+b"</fragment>",parser)
        except (etree.XMLSyntaxError,ValueError):
            raise ValueError("Unparseable SWORD book/chapter introduction") from None
        native_text="".join(doc.itertext())
        text=original["text"]
        count["source_intro_records"]+=1
        count["authored_intro_word_tokens"]+=len(re.findall(r"\w+",text))
        if not text.strip():
            count["source_intro_no_visible_text"]+=1
        elif text in native_text:
            count["source_intro_exact_unicode_text_in_native"]+=1
        elif fold(text) in fold(native_text):
            count["source_intro_text_equal_after_nfc_whitespace_folding"]+=1
        elif (" ".join(re.findall(r"\w+",text.casefold())) in
              " ".join(re.findall(r"\w+",native_text.casefold()))):
            count["source_intro_words_present_but_punctuation_differs"]+=1
            if len(issues)<max_cases:
                issues.append({"intro_key":ref,"line":original["line"],
                               "category":"intro_punctuation_spacing_requires_review"})
        else:
            count["source_intro_words_not_contiguously_present"]+=1
            if len(issues)<max_cases:
                issues.append({"intro_key":ref,"line":original["line"],
                               "category":"intro_source_word_stream_not_found"})
        native_sem=[{
            "tag":n.tag.rsplit("}",1)[-1],
            "body":"".join(n.itertext()),
            "attrs":dict(n.attrib),
        } for n in doc.iter() if isinstance(n.tag,str)
          and n.tag.rsplit("}",1)[-1] in {"note","reference"}]
        for kind in ("note","reference"):
            src=[n for n in original["semantic_nodes"] if n["tag"]==kind]
            out=[n for n in native_sem if n["tag"]==kind]
            count["source_intro_"+kind+"_elements"]+=len(src)
            from collections import Counter as Bag
            one=Bag((fold(n["body"]),n["attributes"].get("osisRef"),
                     n["attributes"].get("type"),n["attributes"].get("n"))
                    for n in src)
            two=Bag((fold(n["body"]),n["attrs"].get("osisRef"),
                     n["attrs"].get("type"),n["attrs"].get("n"))
                    for n in out)
            missing=sum((one-two).values())
            count["source_intro_"+kind+"_body_metadata_missing_from_native"]+=missing
            if missing and len(issues)<max_cases:
                issues.append({"intro_key":ref,"line":original["line"],
                               "category":kind+"_body_metadata_not_identical",
                               "original_count":len(src),"native_count":len(out),
                               "missing_original":missing})
    return {
        "schema_version":1,
        "status":"PRIVATE_INTRO_TEXT_NOTE_LINK_AUDIT_NOT_EDITION_PARITY",
        "counts":dict(sorted(count.items())),
        "bounded_reference_only_cases":issues,
        "all_source_and_native_introductions_indexed":True,
        "original_text_or_notes_exposed":False,
        "editorial_or_licensing_approved":False,
    }


def triage_commentary_introduction_relocation(
        source_intros: dict[str,dict],
        native_intros: dict[str,bytes],
        native_first_verses: dict[str,bytes],
        *, max_cases: int = 80) -> dict:
    """Locate apparently absent intro wording/notes in SAME BOOK native slots.

    A source-vs-own-intro mismatch can be a libSWORD scope relocation, not
    lost prose. Compare independently retrieved I and K frames first;
    never silently change authorial locations or approve a different scope.
    """
    from lxml import etree
    if (not source_intros or set(source_intros)!=set(native_intros)
            or not native_first_verses or not 0<=max_cases<=120):
        raise ValueError("Source/native introduction inventories incomplete")
    frames={}
    def parsed(kind,ref,raw):
        if not isinstance(raw,bytes) or len(raw)>2*1024*1024:
            raise ValueError("Unsafe intro relocation frame")
        try:
            root=etree.fromstring(b"<fragment>"+raw+b"</fragment>",
                etree.XMLParser(resolve_entities=False,load_dtd=False,
                                no_network=True,recover=False,huge_tree=False))
        except (ValueError,etree.XMLSyntaxError):
            raise ValueError("Unparseable native intro relocation frame") from None
        words=" ".join(re.findall(r"\w+","".join(root.itertext()).casefold()))
        sem=Counter()
        for node in root.iter():
            if not isinstance(node.tag,str):
                continue
            name=node.tag.rsplit("}",1)[-1]
            if name in {"note","reference"}:
                sem[(name,
                     " ".join("".join(node.itertext()).split()),
                     node.get("osisRef"),node.get("type"),node.get("n"))]+=1
        frames[(kind,ref)]={"words":words,"semantic":sem}
    for ref,raw in native_intros.items():
        parsed("I",ref,raw)
    for ref,raw in native_first_verses.items():
        parsed("K",ref,raw)
    bybook=defaultdict(list)
    for kind,ref in frames:
        bybook[ref.split(".",1)[0]].append((kind,ref))
    counts=Counter()
    cases=[]
    for ref,original in source_intros.items():
        orig_words=" ".join(re.findall(r"\w+",original["text"].casefold()))
        book=ref.split(".",1)[0]
        home=("I",ref)
        counts["source_intro_scopes_checked"]+=1
        # Inspect source note/reference identity separately: even when the
        # prose is at its home key, XML note callers may have moved or lost
        # attributes. A match in any alternative slot is evidence of
        # relocation only, never proof of identical display placement.
        for name in ("note","reference"):
            for element in original["semantic_nodes"]:
                if element["tag"]!=name:
                    continue
                attr=element["attributes"]
                value=(name," ".join(element["body"].split()),
                       attr.get("osisRef"),attr.get("type"),attr.get("n"))
                if frames[home]["semantic"].get(value,0):
                    counts[name+"_metadata_present_in_original_intro_slot"]+=1
                    continue
                counts[name+"_metadata_absent_from_original_intro_slot"]+=1
                alternatives=[
                    dest for dest in bybook[book] if dest!=home
                    and frames[dest]["semantic"].get(value,0)
                ]
                if not alternatives:
                    counts[name+"_metadata_not_relocated_in_same_book_I_or_first_K"]+=1
                elif any(dest==("I",book) for dest in alternatives):
                    counts[name+"_metadata_relocated_to_book_intro"]+=1
                elif any(dest[0]=="I" for dest in alternatives):
                    counts[name+"_metadata_relocated_to_other_chapter_intro"]+=1
                elif any(dest[0]=="K" and (
                    (ref==book and dest[1].startswith(book+".1."))
                    or (ref!=book and dest[1].startswith(ref+".")))
                         for dest in alternatives):
                    counts[name+"_metadata_relocated_to_same_chapter_first_K"]+=1
                else:
                    counts[name+"_metadata_relocated_to_other_first_K"]+=1
        if not orig_words or orig_words in frames[home]["words"]:
            continue
        matches=[
            dest for dest in bybook[book]
            if dest!=home and orig_words in frames[dest]["words"]
        ]
        if not matches:
            status="intro_word_stream_not_found_contiguously_in_same_book_I_or_first_K"
        elif any(dest==("I",book) for dest in matches):
            status="intro_word_stream_found_in_book_intro"
        elif any(dest[0]=="I" for dest in matches):
            status="intro_word_stream_found_in_other_chapter_intro"
        elif any(dest[0]=="K" and dest[1].startswith(ref+".")
                 for dest in matches):
            status="intro_word_stream_found_in_same_chapter_numbered_commentary"
        else:
            status="intro_word_stream_found_in_other_first_verse"
        counts[status]+=1
        if len(cases)<max_cases:
            cases.append({
                "source_intro":ref,"source_line":original["line"],
                "classification":status,
                "matching_native_slot_count":len(matches),
                "first_matching_native_slot":("/".join(matches[0]) if matches else None),
                "original_intro_word_count":len(orig_words.split()),
            })
    return {
        "schema_version":1,
        "status":"INTRO_SCOPE_RELOCATION_RESEARCH_ONLY_NO_TEXT_RELEASE",
        "counts":dict(sorted(counts.items())),
        "bounded_source_scope_cases":cases,
        "source_intro_wording_exposed":False,
        "publication_approved":False,
    }


def _source_native_interword_punctuation_shape(source: str, native: str) -> dict:
    """Compare punctuation-only gaps aligned by the complete source word run.

    Never print original words or punctuation strings: only categorical
    per-position differences. A repeated phrase in native requires review.
    """
    import unicodedata
    a=unicodedata.normalize("NFC",source)
    b=unicodedata.normalize("NFC",native)
    src=list(re.finditer(r"\w+",a))
    nat=list(re.finditer(r"\w+",b))
    tokens=[m.group().casefold() for m in src]
    native_tokens=[m.group().casefold() for m in nat]
    if not tokens:
        return {"class":"source_no_word_tokens"}
    starts=[i for i,tok in enumerate(native_tokens) if tok==tokens[0]
            and native_tokens[i:i+len(tokens)]==tokens]
    if len(starts)!=1:
        return {"class":"ambiguous_or_unaligned_source_word_window",
                "matching_windows":len(starts)}
    base=starts[0]
    changes=Counter()
    examples=[]
    for pos in range(len(src)-1):
        left=a[src[pos].end():src[pos+1].start()]
        right=b[nat[base+pos].end():nat[base+pos+1].start()]
        if left==right:
            changes["exact_interword_gaps"]+=1
        elif " ".join(left.split())==" ".join(right.split()):
            changes["whitespace_only_interword_gaps"]+=1
        elif "".join(left.split())=="".join(right.split()):
            changes["all_whitespace_removed_gap_equal"]+=1
        else:
            changes["punctuation_codepoints_differ"]+=1
            if len(examples)<12:
                examples.append({
                    "gap_ordinal":pos+1,
                    "source_nonspace_symbols":len("".join(left.split())),
                    "native_nonspace_symbols":len("".join(right.split())),
                    "source_symbol_categories":dict(sorted(Counter(
                        unicodedata.category(x) for x in left if not x.isspace()
                    ).items())),
                    "native_symbol_categories":dict(sorted(Counter(
                        unicodedata.category(x) for x in right if not x.isspace()
                    ).items())),
                })
    left_prefix=a[:src[0].start()]
    right_prefix=b[:nat[base].start()]
    left_suffix=a[src[-1].end():]
    right_suffix=b[nat[base+len(src)-1].end():]
    def symbol_fingerprint(value):
        nonspace="".join(value.split())
        return {
            "nonspace_symbols":len(nonspace),
            "unicode_category_counts":dict(sorted(Counter(
                unicodedata.category(x) for x in nonspace).items())),
            "symbol_sha256":hashlib.sha256(nonspace.encode("utf-8")).hexdigest(),
        }
    prefix_equal="".join(left_prefix.split())=="".join(right_prefix.split())
    suffix_equal="".join(left_suffix.split())=="".join(right_suffix.split())
    return {
        "class":("punctuation_changes_between_word_anchors"
                 if changes["punctuation_codepoints_differ"] else
                 "boundary_punctuation_differs" if not(prefix_equal and suffix_equal)
                 else "word_internal_gaps_equal_or_whitespace_only"),
        "counts":dict(sorted(changes.items())),
        "bounded_symbol_category_examples":examples,
        "word_run_start_native_ordinal":base+1,
        "prefix_symbols_equal_ignoring_whitespace":prefix_equal,
        "suffix_symbols_equal_ignoring_whitespace":suffix_equal,
        "source_prefix_symbols":symbol_fingerprint(left_prefix),
        "native_prefix_symbols":symbol_fingerprint(right_prefix),
        "source_suffix_symbols":symbol_fingerprint(left_suffix),
        "native_suffix_symbols":symbol_fingerprint(right_suffix),
        "unreviewed_boundary_text":not(prefix_equal and suffix_equal),
    }


def compare_all_commentary_source_group_semantics(
        groups: list[dict], native_first_raw: dict[str,bytes],
        *, max_cases: int = 40) -> dict:
    """Research-only source↔native punctuation, note and reference inventory.

    Structural normalization in osis2mod may add wrappers or change layouts.
    Full text and note-body equality is stronger than word parity; a mismatch
    is reported for review, NEVER auto-modified or certified as text loss.
    All source/private note text, reference labels and raw XML stay in memory.
    """
    from lxml import etree
    import unicodedata
    if (not isinstance(groups,list) or not groups or len(groups)>100000
            or not isinstance(native_first_raw,dict)
            or not 0<=max_cases<=100):
        raise ValueError("Invalid or oversized source-native semantic witness")
    first={g["keys"][0] for g in groups if g.get("keys")}
    if not first or set(native_first_raw)!=first:
        raise ValueError("Native first keys incomplete for semantic comparison")

    def folded(t):
        return " ".join(unicodedata.normalize("NFC",t).split())

    def sem(e):
        tag=e.tag.rsplit("}",1)[-1]
        return {"tag":tag,"body":"".join(e.itertext()),
                "attributes":dict(e.attrib)}

    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    frames={}
    for ref,raw in native_first_raw.items():
        if not isinstance(raw,bytes) or len(raw)>2*1024*1024:
            raise ValueError("Unsafe raw native SWORD body")
        try:
            root=etree.fromstring(b"<fragment>"+raw+b"</fragment>",parser)
        except (etree.XMLSyntaxError,ValueError):
            raise ValueError("Unparseable native commentary raw frame") from None
        frames[ref]={
            "text":"".join(root.itertext()),
            "semantic":[sem(n) for n in root.iter()
                        if isinstance(n.tag,str)
                        and n.tag.rsplit("}",1)[-1] in {"note","reference"}],
        }
    counts=Counter()
    cases=[]
    for group in groups:
        if not isinstance(group.get("text"),str) or not isinstance(
                group.get("semantic_nodes"),list) or not group.get("keys"):
            raise ValueError("Incomplete original authored group semantics")
        native=frames[group["keys"][0]]
        source_text=group["text"]
        compiled=native["text"]
        counts["source_groups"]+=1
        counts["source_text_codepoints"]+=len(source_text)
        if source_text in compiled:
            counts["source_text_exact_raw_unicode_substring"]+=1
        elif folded(source_text) in folded(compiled):
            counts["source_text_equal_after_nfc_whitespace_folding"]+=1
        elif folded(source_text).casefold() in folded(compiled).casefold():
            counts["source_text_equal_after_unicode_casefold"]+=1
        else:
            counts["source_group_full_punctuation_or_spacing_needs_review"]+=1
            if len(cases)<max_cases:
                cases.append({
                    "source_line":group["line"],
                    "source_ref":group["sID"],
                    "category":"source_text_punctuation_or_spacing_diff",
                    "source_text_sha256":hashlib.sha256(source_text.encode()).hexdigest(),
                    "aligned_punctuation":_source_native_interword_punctuation_shape(
                        source_text,compiled),
                })
        for tag in ("note","reference"):
            source_nodes=[n for n in group["semantic_nodes"] if n["tag"]==tag]
            native_nodes=[n for n in native["semantic"] if n["tag"]==tag]
            counts["source_"+tag+"_elements"]+=len(source_nodes)
            counts["native_"+tag+"_elements_seen_on_source_first_keys"]+=len(native_nodes)
            from collections import Counter as Bag
            source_bodies=Bag(folded(n["body"]) for n in source_nodes)
            native_bodies=Bag(folded(n["body"]) for n in native_nodes)
            missing_bodies=sum((source_bodies-native_bodies).values())
            counts["source_"+tag+"_bodies_missing_from_native"]+=missing_bodies
            source_exact=Bag((
                folded(n["body"]),
                n["attributes"].get("osisRef"),
                n["attributes"].get("type"),
                n["attributes"].get("n"),
            ) for n in source_nodes)
            native_exact=Bag((
                folded(n["body"]),
                n["attributes"].get("osisRef"),
                n["attributes"].get("type"),
                n["attributes"].get("n"),
            ) for n in native_nodes)
            missing_semantic=sum((source_exact-native_exact).values())
            counts["source_"+tag+"_body_and_metadata_not_exactly_in_native"]+=missing_semantic
            if (missing_bodies or missing_semantic) and len(cases)<max_cases:
                cases.append({
                    "source_line":group["line"],
                    "source_ref":group["sID"],
                    "category":tag+"_semantic_mismatch",
                    "source_element_count":len(source_nodes),
                    "native_element_count":len(native_nodes),
                    "original_bodies_missing":missing_bodies,
                    "body_and_allowlisted_metadata_not_exact":missing_semantic,
                })
    return {
        "schema_version":1,
        "status":"PRIVATE_SOURCE_NATIVE_PUNCTUATION_NOTE_LINK_TRIAGE_NOT_EDITION_PARITY",
        "counts":dict(sorted(counts.items())),
        "bounded_reference_only_findings":cases,
        "all_source_groups_examined":True,
        "raw_xml_or_note_bodies_exported":False,
        "editorial_changes":False,
        "publication_approved":False,
    }


def audit_osis(path: Path, *, kind: str = "bible") -> dict:
    if kind not in {"bible", "commentary"}:
        raise ValueError("Only Bible/commentary OSIS sources are supported")
    path = Path(path).absolute()
    raw = require_regular_file(path, MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
    if re.search(rb"<!DOCTYPE\b", raw, flags=re.IGNORECASE):
        raise StructureFailure(path, 1, "DOCTYPE_UNREVIEWED", "DOCTYPE declarations must not be parsed")
    document = parse_xml(path, raw, "MALFORMED_XML")
    if document.getroot().tag != NS + "osis":
        raise StructureFailure(path, document.getroot().sourceline or 1,
                               "UNEXPECTED_ROOT", "Expected an OSIS document")
    findings = []
    counts = Counter()
    verses = {}
    annotations = defaultdict(list)
    paragraph_count = 0
    previous_verse = None
    commentary_shape_counts = Counter()
    commentary_reference_examples = []
    last_commentary_by_book = {}
    source_annotated_count = 0
    bounded_source_structural_findings = Counter()

    for node in document.iter():
        if not isinstance(node.tag, str):
            continue
        name = _tag(node)
        counts[name] += 1
        content = "".join(node.itertext())
        if name == "hi" and node.get("type") in {"bold", "bolditalic"}:
            if len(content) >= 170:
                findings.append(_entry(path,node,"long_bold_range",
                    reason="Long emphasized span; inspect whether an authorial heading or formatting was flattened",
                    details={"characters": len(content)}))
        if name == "p":
            paragraph_count += 1
            letters = [x for x in content if x.isalpha()]
            if len(letters) >= 80 and sum(x.isupper() for x in letters) / len(letters) >= 0.8:
                findings.append(_entry(path,node,"upper_case_paragraph",
                    reason="All-caps paragraph candidate; preserve possible authorial emphasis",
                    details={"letters": len(letters)}))
            if len(content) >= 1800:
                findings.append(_entry(path,node,"excessive_styling",
                    reason="Very long paragraph candidate; investigate printed edition before splitting",
                    details={"characters": len(content)}))
        if name == "title" and (len(content) >= 190 or
                                (len(content) >= 40 and content.isupper())):
            findings.append(_entry(path,node,"suspicious_heading",
                reason="Unusually long or uppercase heading; do not rewrite without editorial review",
                details={"characters": len(content)}))
        attrs = set(node.attrib)
        styles = sorted(x for x in attrs if x.lower() in
                        {"color", "font", "style", "font-family", "font-size", "background"})
        if styles:
            findings.append(_entry(path,node,"unknown_style",
                reason="Non-standard presentation attribute needs schema and publisher review",
                details={"attributes": styles}))
        if name == "seg" and node.get("type", "").lower().startswith(("font-size", "color", "font")):
            findings.append(_entry(path,node,"unknown_style",
                reason="Presentation-only segment; verify OSIS semantics and rendering",
                details={"segment_type": node.get("type", "")[:100]}))
        if name == "reference":
            reference = node.get("osisRef")
            if not reference or not reference.strip():
                findings.append(_entry(path,node,"invalid_cross_reference",
                    reason="Reference element lacks a usable osisRef"))
            else:
                # Complex OSIS work references and discontinuous ranges can be
                # legitimate; never mark them invalid without canonical v11n.
                parts = reference.split()
                if any(not _reference_token(piece) for piece in parts):
                    findings.append(_entry(path,node,"unreviewed_cross_reference",
                        reason="Cross reference needs a verified OSIS grammar/versification check",
                        details={"osis_ref": reference[:150]}))
        if name == "verse":
            ref = node.get("osisID") or node.get("sID")
            if not ref and not node.get("eID"):
                findings.append(_entry(path,node,"empty_verse_identifier",
                    reason="Verse has no OSIS identifier or milestone key"))
            if ref:
                if ref in verses:
                    findings.append(_entry(path,node,"duplicate_verse_id",
                        reason="Repeated verse opening/key; check actual SWORD verse indexes",
                        details={"osis_ref": ref, "first_xml_line": verses[ref]}))
                else:
                    verses[ref] = node.sourceline
                key = _verse_key(ref)
                if previous_verse and key and key[0] == previous_verse[0] and (
                    key[1], key[2]) < (previous_verse[1], previous_verse[2]):
                    findings.append(_entry(path,node,"verse_key_out_of_sequence",
                        reason="Source-order verse keys decrease within a book; validate against module versification",
                        details={"osis_ref": ref}))
                if key:
                    previous_verse = key
        if kind == "commentary" and name == "div" and (
                node.get("annotateType") == "commentary" or "annotateRef" in node.attrib):
            source_annotated_count += 1
            reference = node.get("annotateRef") or ""
            typ = node.get("annotateType")
            category, endpoints = _commentary_ref_tokens(reference)
            commentary_shape_counts[category] += 1
            if typ != "commentary" or not reference:
                code = "commentary_annotation_missing"
                reason = "Missing or non-commentary annotated section type/reference"
            elif category.startswith("comma_"):
                code = "commentary_comma_range_candidate"
                reason = "Comma inside source annotation is not a SWORD range"
            elif category == "reversed_or_zero_length_range":
                code = "commentary_range_reversed"
                reason = "Source annotation has non-increasing range endpoints"
            elif category in {"single_verse","chapter_intro","book_intro",
                              "continuous_verse_range","discontinuous_list",
                              "discontinuous_cross_book_list"}:
                code = None
                reason = None
            else:
                code = "commentary_annotation_unreviewed"
                reason = "Unsupported source annotation syntax needs reviewed normalization"
            if code:
                bounded_source_structural_findings[code] += 1
                if bounded_source_structural_findings[code] <= MAX_STRUCTURAL_SAMPLES:
                    findings.append(_entry(path,node,code,reason=reason,
                        details={"source_annotation_sha256":hashlib.sha256(
                            reference.encode("utf-8")).hexdigest(),
                                 "reference_shape":category}))
            if reference:
                if reference in annotations:
                    if len(annotations[reference]) < MAX_STRUCTURAL_SAMPLES:
                        findings.append(_entry(path,node,"duplicate_commentary_reference",
                            reason="Repeated entire source scope; needs collision review",
                            details={"reference_sha256":hashlib.sha256(
                                reference.encode("utf-8")).hexdigest(),
                                "other_entries":len(annotations[reference])}))
                annotations[reference].append(node.sourceline)
            if endpoints:
                first = endpoints[0]
                enclosing = next(
                    (anc.get("osisID") for anc in node.iterancestors()
                     if anc.get("type") == "book" and anc.get("osisID")), None)
                if enclosing and enclosing != first[0]:
                    bounded_source_structural_findings["commentary_book_scope_mismatch"] += 1
                    if bounded_source_structural_findings["commentary_book_scope_mismatch"] <= MAX_STRUCTURAL_SAMPLES:
                        findings.append(_entry(path,node,"commentary_book_scope_mismatch",
                            reason="Annotated section book differs from enclosing source book",
                            details={"enclosing_book":enclosing,
                                     "section_first_book":first[0]}))
                if first[0] in last_commentary_by_book:
                    last = last_commentary_by_book[first[0]]
                    if first[1:] < last:
                        bounded_source_structural_findings["commentary_out_of_order"] += 1
                        if bounded_source_structural_findings["commentary_out_of_order"] <= MAX_STRUCTURAL_SAMPLES:
                            findings.append(_entry(path,node,"commentary_out_of_order",
                                reason="Commentary sections decrease in verse order within the same book",
                                details={"reference_sha256":hashlib.sha256(reference.encode()).hexdigest()}))
                last_commentary_by_book[first[0]] = first[1:]
            if (category not in {"single_verse", "continuous_verse_range"}
                    and len(commentary_reference_examples) < MAX_STRUCTURAL_SAMPLES):
                commentary_reference_examples.append({
                    "line":node.sourceline, "shape":category,
                    "source_ref_sha256":hashlib.sha256(reference.encode()).hexdigest(),
                })
        if kind == "commentary" and name == "title" and len(content) <= 110:
            if SHORT_COMMA_VERSES.search(content):
                bounded_source_structural_findings["commentary_title_numeric_comma_candidate"] += 1
                if bounded_source_structural_findings["commentary_title_numeric_comma_candidate"] <= MAX_STRUCTURAL_SAMPLES:
                    findings.append(_entry(path,node,"commentary_title_numeric_comma_candidate",
                        reason="Displayed verse list may differ from machine annotation; do not auto-convert commas into ranges",
                        details={"title_sha256":hashlib.sha256(content.encode()).hexdigest()}))

        # A likely Bible quotation repeated in commentary is NOT automatically
        # removable. Limit to styled segments/paragraphs with several numbered
        # verse markers; this is a deliberately conservative candidate signal.
        if kind == "commentary" and name in {"p", "seg"} and len(content) >= 200:
            if name == "seg" and any(_tag(parent) == "seg" for parent in node.iterancestors()):
                continue
            number_hits = len(VERSE_MARKER.findall(content))
            if number_hits >= 5 and (
                name == "p" and not any(_tag(x) == "seg" for x in node)
                or name == "seg" and node.get("type", "").startswith("font-size")
            ):
                findings.append(_entry(path,node,"introductory_scripture_candidate",
                    reason="Numbered Bible-text block candidate; retain until excerpt boundaries and role are verified",
                    details={"numbered_markers":number_hits}))

    findings.sort(key=lambda x: (x["original_xml_line"] or 0, x["code"], x["xml_xpath"]))
    return {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "source_path": str(path),
        "kind": kind,
        "status": "audited_not_normalized",
        "source_schema_validated": False,
        "findings": findings,
        "summary": {
            "elements": dict(sorted(counts.items())),
            "verse_keys": len(verses),
            "commentary_reference_keys": len(annotations),
            "paragraphs": paragraph_count,
            "commentary_annotated_section_count": source_annotated_count,
            "commentary_annotation_scope_shapes": dict(sorted(commentary_shape_counts.items())),
            "commentary_annotation_structural_counts": dict(sorted(bounded_source_structural_findings.items())),
            "commentary_nonstandard_scope_examples": commentary_reference_examples,
            "commentary_section_shape_review_does_not_validate_canonical_versification": True,
            "finding_counts": dict(sorted(Counter(x["code"] for x in findings).items())),
        },
        "no_content_changes": True,
        "requires_editorial_review": bool(findings),
        "caveat": "Syntactic source audit, not SWORD-versification proof, compiled-index audit, or publication approval.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--kind", choices=("bible", "commentary"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_osis(args.source, kind=args.kind)
        code = 0
    except (OSError, ValueError, StructureFailure) as exc:
        diagnostic = exc.as_dict() if isinstance(exc, StructureFailure) else {"detail":str(exc)}
        result = {"status": "blocked", "diagnostic": diagnostic, "no_content_changes": True}
        code = 1
    write_report(args.report, result)
    print(f"Source audit: {result['status']}; report: {args.report}")
    return code


if __name__ == "__main__":
    sys.exit(main())
