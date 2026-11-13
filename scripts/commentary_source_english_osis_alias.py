#!/usr/bin/env python3
"""Private, read-only source div1 heading ↔ canonical English OSIS alias witness.

A source title is an original editorial string; the repo's 66-book crosswalk
and English diatheke aliases are *candidate* external metadata, not authority
to normalize an original ThML scripCom reference or infer its authorial book.
No original heading, book code, or scripture reference leaves this classifier.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

from pilot_preflight import PilotError

SHA_RE=re.compile(r"[a-f0-9]{64}\Z")
MAX_DIV1=500
MAX_EXAMPLES=20
CATEGORIES={
    "original_title_exact_english_alias_matches_claimed_book_code",
    "original_title_contains_english_alias_matching_claimed_book_code",
    "original_title_exact_english_alias_points_to_different_book_code",
    "original_title_contains_english_alias_for_different_book_code",
    "original_title_no_canonical_english_alias_found_unreviewed",
    "original_title_matches_multiple_canonical_aliases_unreviewed",
    "original_div1_title_missing_unreviewed",
    "original_scripCom_book_code_not_in_known_66_osis_crosswalk",
}


def _hash(s:str)->str:
    return sha256(s.encode("utf-8")).hexdigest()


def _canon_name(title:str)->str:
    # Conservative comparison only, never change source identifiers.
    return " ".join(unicodedata.normalize("NFKC",title).casefold().split())


def read_existing_66_book_english_aliases() -> tuple[dict[str,str],dict]:
    root=Path(__file__).resolve().parents[1]
    crosswalk=root/"config/standard_usfm_osis_66.json"
    aliases=root/"config/diatheke-usfm-book-aliases.json"
    if any(p.is_symlink() or not p.is_file() or p.stat().st_size>100_000 for p in (
        crosswalk,aliases
    )):
        raise PilotError("Existing reviewed 66-book OSIS/English alias registries unavailable")
    raw_a=crosswalk.read_bytes()
    raw_b=aliases.read_bytes()
    try:
        registry=json.loads(raw_a)
        english=json.loads(raw_b)
    except (UnicodeError, ValueError):
        raise PilotError("Reviewed 66-book OSIS/English alias JSON invalid") from None
    if (registry.get("schema_version")!=1 or english.get("schema_version")!=1 or
            registry.get("scope")!="protestant_66_standard_usfm_to_stock_sword_osis" or
            not isinstance(registry.get("books"),list) or
            len(registry["books"])!=66 or
            not isinstance(english.get("aliases"),dict) or
            len(english["aliases"])!=66):
        raise PilotError("Source canonical crosswalk was replaced or changed scope")
    seen_usfm=set()
    seen_osis=set()
    code_to_alias={}
    for entry in registry["books"]:
        if not isinstance(entry,dict) or set(entry)!={"usfm","osis"}:
            raise PilotError("Canonical book crosswalk has unexpected fields")
        usfm,osis=entry["usfm"],entry["osis"]
        if (not isinstance(usfm,str) or not isinstance(osis,str) or
                not re.fullmatch(r"[1-4]?[A-Z][A-Z0-9]{1,3}",usfm) or
                not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]{1,15}",osis) or
                usfm in seen_usfm or osis in seen_osis):
            raise PilotError("Canonical 66-book crosswalk contains duplicate/unreviewed IDs")
        seen_usfm.add(usfm)
        seen_osis.add(osis)
        value=english["aliases"].get(usfm)
        if not isinstance(value,str) or not 1<=len(value)<=60:
            raise PilotError("Canonical English book name alias absent from existing registry")
        code_to_alias[osis]=value
    if set(english["aliases"])!=seen_usfm or len(code_to_alias)!=66:
        raise PilotError("Canonical book and English alias entries differ")
    return code_to_alias,{
        "canonical_usfm_osis_66_config_sha256":sha256(raw_a).hexdigest(),
        "canonical_english_diatheke_alias_config_sha256":sha256(raw_b).hexdigest(),
        "comparison_uses_exact_existing_66_book_registry_without_edits":True,
    }


def _classify(source_title:str,original_book:str,code_to_alias:dict[str,str]) -> tuple[str,str|None,int]:
    if not source_title.strip():
        return "original_div1_title_missing_unreviewed",None,0
    if original_book not in code_to_alias:
        return "original_scripCom_book_code_not_in_known_66_osis_crosswalk",None,0
    heading=_canon_name(source_title)
    candidates=[]
    for code,alias in code_to_alias.items():
        name=_canon_name(alias)
        if not name:
            raise PilotError("Existing canonical alias is empty")
        if re.search(r"(?<!\w)"+re.escape(name)+r"(?!\w)",heading):
            candidates.append(code)
    if not candidates:
        return "original_title_no_canonical_english_alias_found_unreviewed",None,0
    if len(candidates)!=1:
        return "original_title_matches_multiple_canonical_aliases_unreviewed",None,len(candidates)
    one=candidates[0]
    exact=heading==_canon_name(code_to_alias[one])
    if one==original_book:
        return (
            "original_title_exact_english_alias_matches_claimed_book_code" if exact
            else "original_title_contains_english_alias_matching_claimed_book_code"
        ),one,1
    return (
        "original_title_exact_english_alias_points_to_different_book_code" if exact
        else "original_title_contains_english_alias_for_different_book_code"
    ),one,1


def original_div1_english_alias_vs_declared_osis(source:dict,shared_report:dict)->dict:
    code_to_alias,registry_meta=read_existing_66_book_english_aliases()
    doc_source={}
    by_ident={}
    for start,units in source.items():
        book=start.split(".",1)[0]
        for u in units:
            ident=(u["original_source_line"],u["original_full_reference_sha256"],
                   u["original_text_sha256"])
            if ident in by_ident:
                raise PilotError("Duplicate original source comment identity in alias audit")
            by_ident[ident]=(start,u)
            ordinal=u.get("private_original_enclosing_div1_document_ordinal")
            total=u.get("private_original_total_div1_in_document")
            heading=u.get("private_original_div1_heading_text")
            heading_sha=u.get("private_original_div1_heading_sha256")
            if (type(ordinal) is not int or type(total) is not int or
                    not 1<=ordinal<=total<=MAX_DIV1 or
                    not isinstance(heading,str) or len(heading)>4096 or
                    (sha256(heading.encode("utf-8")).hexdigest() if heading.strip() else None)
                        !=heading_sha):
                raise PilotError("Original ThML div1 title/sha or ordinal changed unexpectedly")
            record=doc_source.setdefault(ordinal,{"heading":heading,"sha":heading_sha,
                                                    "total":total,"books":Counter(),
                                                    "lines":set()})
            if record["heading"]!=heading or record["sha"]!=heading_sha or record["total"]!=total:
                raise PilotError("Different original heading values inside same structural div1")
            record["books"][book]+=1
            record["lines"].add(ident[0])
    if not doc_source:
        raise PilotError("Original source text has no reviewable book headings")
    original_div1_types=Counter()
    source_units_classes=Counter()
    suspect=[]
    per_doc={}
    for div1,entry in doc_source.items():
        claims=entry["books"]
        if len(claims)!=1:
            original_div1_types["multiple_declared_book_codes_one_source_div1_unreviewed"]+=1
            continue
        source_book=next(iter(claims))
        cls,candidate,matched_count=_classify(entry["heading"],source_book,code_to_alias)
        if cls not in CATEGORIES:
            raise PilotError("Unreviewed source vs original English title class")
        original_div1_types[cls]+=1
        source_units_classes[cls]+=claims[source_book]
        per_doc[div1]={
            "original_div1_document_ordinal":div1,
            "original_div1_title_SHA256":entry["sha"],
            "claimed_original_osis_book_code_SHA256":_hash(source_book),
            "unique_canonical_english_aliases_matched":matched_count,
            "unambiguous_english_title_candidate_osis_SHA256":
                _hash(candidate) if candidate is not None else None,
            "original_div1_alias_vs_scripCom_book_code_class":cls,
            "original_scripCom_source_unit_count":claims[source_book],
            "original_div1_source_line_min":min(entry["lines"]),
            "original_div1_source_line_max":max(entry["lines"]),
            "source_title_candidate_does_not_authorize_reference_rewrite":True,
        }
        if cls in {
            "original_title_exact_english_alias_points_to_different_book_code",
            "original_title_contains_english_alias_for_different_book_code",
        }:
            suspect.append(per_doc[div1])
    suspect.sort(key=lambda r:(r["original_div1_document_ordinal"]))
    focused=[]
    for group in shared_report.get(
        "bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports",[]
    ):
        entries=[]
        for m in group["original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order"]:
            ident=(m["original_source_line"],m["original_full_reference_sha256"],
                   m["original_source_body_sha256"])
            item=by_ident.get(ident)
            if item is None:
                raise PilotError("Original selected source raw group not in same CCEL ThML")
            start,u=item
            info=per_doc.get(u["private_original_enclosing_div1_document_ordinal"])
            if info is None:
                raise PilotError("Original source division has ambiguous book identities")
            if info["claimed_original_osis_book_code_SHA256"]!=_hash(start.split(".",1)[0]):
                raise PilotError("Original ThML title audit book code differs from source marker")
            entries.append({
                "original_source_line":ident[0],
                "original_full_reference_sha256":ident[1],
                "original_body_sha256":ident[2],
                "original_div1_document_ordinal":info["original_div1_document_ordinal"],
                "original_div1_title_SHA256":info["original_div1_title_SHA256"],
                "original_scripCom_osis_book_code_SHA256":
                    info["claimed_original_osis_book_code_SHA256"],
                "unambiguous_canonical_english_title_candidate_osis_SHA256":
                    info["unambiguous_english_title_candidate_osis_SHA256"],
                "english_title_alias_vs_actual_original_osis_claim_class":
                    info["original_div1_alias_vs_scripCom_book_code_class"],
                "canonical_alias_only_a_read_only_source_title_witness":True,
            })
        focused.append({
            "native_shared_stock_raw_sha256":group["native_shared_raw_SHA256"],
            "original_source_units_checked":len(entries),
            "source_line_original_full_hash_and_title_alias_class_members":entries,
        })
    return {
        **registry_meta,
        "source_div1_with_exactly_one_declared_book_code_title_compared":
            len(per_doc),
        "source_div1_total_with_any_annotations":len(doc_source),
        "source_original_div1_title_vs_canonical_english_alias_classes":
            dict(sorted(original_div1_types.items())),
        "original_verse_range_source_unit_counts_by_title_alias_class":
            dict(sorted(source_units_classes.items())),
        "canonical_english_alias_heading_conflicts_found":len(suspect),
        "bounded_original_div1_english_title_alias_conflicts_line_sha256_cases":
            suspect[:MAX_EXAMPLES],
        "english_alias_title_conflicts_truncated":len(suspect)>MAX_EXAMPLES,
        "focused_shared_stock_raw_original_source_book_title_alias_checks":focused,
        "book_codes_or_original_source_titles_exposed":False,
        "canonical_alias_is_not_proof_of_source_editorial_book_identity":True,
        "no_original_source_osisRef_or_title_value_modified":True,
    }
