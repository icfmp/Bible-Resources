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



def source_commentary_overlap_witness(path: Path) -> tuple[dict, set[str]]:
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
                "parts":[]
            }
        elif _tag(node)=="verse" and node.get("eID"):
            finish(node)
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
        counts[classification]+=1
        if len(cases)<max_cases:
            cases.append({
                "source_xml_line":group["line"],
                "original_source_sid":group["sID"],
                "authored_verse_addresses":len(group["keys"]),
                "full_source_word_count":len(words.split()),
                "full_source_word_stream_sha256":hashlib.sha256(
                    words.encode("utf-8")).hexdigest(),
                "indexed_key_word_sequence_matches":len(matching),
                "first_matching_native_key":matching[0] if matching else None,
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
