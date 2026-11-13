#!/usr/bin/env python3
"""Private original ThML book-code vs physical div1 document ancestry census.

Do NOT equate a source scripCom book code with an original editorial book
identity without separately verifying the original div1 heading/edition.
Two original div1 sections using the same osisRef book/start code are
collisions for review, not a license to relocate commentary verses.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from pilot_preflight import PilotError

SHA = re.compile(r"[a-f0-9]{64}\Z")
MAX_SOURCE_UNITS = 30_000
MAX_DIV1 = 500
MAX_COLLISION_CASES = 20
MAX_SHARED_GROUPS = 8


def _digest(s:str)->str:
    return sha256(s.encode("utf-8")).hexdigest()


def private_original_div1_book_code_consistency(
    source:dict[str,list[dict]], shared_source_run_report:dict
) -> dict:
    """Return only bounded source lines, strong hashes, original div1 ordinals."""
    if not isinstance(source,dict) or not source:
        raise PilotError("Original verse/range scripCom corpus missing")
    book_divisions=defaultdict(set)
    div1_book_units=defaultdict(Counter)
    div1_context={}
    start_divisions=defaultdict(set)
    start_items=defaultdict(list)
    source_seen=set()
    original_units=0
    for start,units in source.items():
        if not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*",start):
            raise PilotError("Original verse-range start key has unknown grammar")
        book=start.split(".",1)[0]
        for unit in units:
            original_units+=1
            if original_units>MAX_SOURCE_UNITS:
                raise PilotError("Original source div1 census exceeded reviewed bounds")
            line=unit.get("original_source_line")
            orig_ref_sha=unit.get("original_full_reference_sha256")
            body_sha=unit.get("original_text_sha256")
            div1=unit.get("private_original_enclosing_div1_document_ordinal")
            total=unit.get("private_original_total_div1_in_document")
            heading_sha=unit.get("private_original_div1_heading_sha256")
            heading_origin=unit.get("private_original_div1_heading_origin")
            attr_names=unit.get("private_original_div1_attribute_name_types")
            if (type(line) is not int or line<1 or
                    any(not isinstance(s,str) or not SHA.fullmatch(s)
                        for s in (orig_ref_sha,body_sha)) or
                    type(div1) is not int or type(total) is not int or
                    not 1<=div1<=total<=MAX_DIV1 or
                    (heading_sha is not None and (
                        not isinstance(heading_sha,str) or not SHA.fullmatch(heading_sha)
                    )) or
                    heading_origin not in {
                        "title_attribute","immediate_original_h1_or_title_child","absent"
                    } or
                    not isinstance(attr_names,list) or
                    any(not isinstance(a,str) or
                        not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,95}",a)
                        for a in attr_names)):
                raise PilotError("Original div1 ancestry or source title SHA is not authenticated")
            if (heading_origin=="absent")!=(heading_sha is None):
                # An explicit but blank heading must still be documented as unreviewed.
                if not (heading_origin!="absent" and heading_sha is None):
                    raise PilotError("Original div1 heading identity disagreement")
            identity=(line,orig_ref_sha,body_sha)
            if identity in source_seen:
                raise PilotError("Duplicate original source annotation full identity")
            source_seen.add(identity)
            context=(heading_origin,heading_sha,tuple(attr_names),total)
            if div1 in div1_context and div1_context[div1]!=context:
                raise PilotError("Inconsistent title/attribute metadata for one original div1")
            div1_context[div1]=context
            book_divisions[book].add(div1)
            div1_book_units[div1][book]+=1
            start_divisions[start].add(div1)
            start_items[start].append({
                "original_source_line":line,
                "original_full_reference_sha256":orig_ref_sha,
                "original_body_sha256":body_sha,
                "original_div1_document_ordinal":div1,
            })
    totals={c[3] for c in div1_context.values()}
    if len(totals)!=1:
        raise PilotError("Original source units disagree about whole document div1 count")
    full_div1_count=next(iter(totals))
    repeated_books={book:ordinals for book,ordinals in book_divisions.items()
                    if len(ordinals)>1}
    repeated_starts={key:ordinals for key,ordinals in start_divisions.items()
                     if len(ordinals)>1}
    cross_div1_repeated_keys=sorted(
        repeated_starts,key=lambda key:(
            -max(repeated_starts[key])+min(repeated_starts[key]),
            key,
        )
    )
    # High-confidence focus: only original units already proven to share
    # actual stock bytes. Never look up a plausible book title by guessing.
    shared_groups=shared_source_run_report.get(
        "bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports",[]
    )
    if not isinstance(shared_groups,list) or len(shared_groups)>MAX_SHARED_GROUPS:
        raise PilotError("Original shared native stock context exceeds reviewed bounds")
    authentic_items={
        (item["original_source_line"],item["original_full_reference_sha256"],
         item["original_body_sha256"]):item
        for items in start_items.values() for item in items
    }
    focused=[]
    focused_unit_count=0
    for group in shared_groups:
        members=group.get(
            "original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order"
        )
        if not isinstance(members,list) or len(members)>16:
            raise PilotError("Source original shared K-run member inventory incomplete")
        actual=[]
        book_sha_set=set()
        title_hashes=set()
        member_divisions=set()
        target_book=None
        for member in members:
            ident=(
                member["original_source_line"],
                member["original_full_reference_sha256"],
                member["original_source_body_sha256"],
            )
            corresponding=authentic_items.get(ident)
            if corresponding is None:
                raise PilotError("Original marker group does not reconcile with full div1 census")
            actual_div1=corresponding["original_div1_document_ordinal"]
            if actual_div1!=member["original_enclosing_div1_ordinal_in_original_XML_document"]:
                raise PilotError("Source div1 identity disagrees with the previous complete audit")
            matches=[
                start for start,rows in start_items.items()
                if any((p["original_source_line"],p["original_full_reference_sha256"],
                        p["original_body_sha256"])==ident for p in rows)
            ]
            if len(matches)!=1:
                raise PilotError("Original source identity has ambiguous biblical start ref")
            book=matches[0].split(".",1)[0]
            book_sha=_digest(book)
            book_sha_set.add(book_sha)
            if target_book is None:
                target_book=book
            member_divisions.add(actual_div1)
            title_origin,title_sha,attributes,_total=div1_context[actual_div1]
            if title_sha is not None:
                title_hashes.add(title_sha)
            actual.append({
                "original_source_line":ident[0],
                "original_full_reference_sha256":ident[1],
                "original_body_sha256":ident[2],
                "original_reference_start_key_sha256":_digest(matches[0]),
                "original_scripCom_declared_book_token_sha256":book_sha,
                "original_div1_document_ordinal":actual_div1,
                "original_div1_title_or_direct_heading_origin":title_origin,
                "original_div1_title_or_direct_heading_sha256":title_sha,
                "original_div1_original_attribute_names":list(attributes),
                "original_div1_distinct_declared_osisRef_book_tokens":
                    len(div1_book_units[actual_div1]),
                "original_div1_scripCom_units_claiming_this_book_token":
                    div1_book_units[actual_div1][book],
                "same_book_code_reused_in_multiple_original_div1_sections":
                    len(book_divisions[book])>1,
                "source_context_is_not_authored_stock_verse_section_approval":True,
            })
            focused_unit_count+=1
        if len(actual)!=group["distinct_original_scripCom_source_units_starting_in_shared_run"]:
            raise PilotError("Original group lost a source member")
        focused.append({
            "native_shared_compiled_raw_SHA256":group["native_shared_raw_SHA256"],
            "original_source_unit_count":len(actual),
            "distinct_original_div1_count":len(member_divisions),
            "original_div1_document_ordinals":sorted(member_divisions),
            "distinct_original_declared_book_token_count":len(book_sha_set),
            "distinct_nonempty_original_div1_heading_SHA256_count":len(title_hashes),
            "all_original_source_units_claim_same_osisRef_book_code":len(book_sha_set)==1,
            "same_claimed_book_code_occurs_in_multiple_original_div1_sections":
                len(member_divisions)>1 and len(book_sha_set)==1,
            "original_source_div1_heading_hashes_distinct_when_present":
                len(title_hashes)==len(member_divisions),
            "actual_original_units_grouped_only_by_compiled_reference_not_original_div1":True,
            "source_members_line_sha256_and_div1_heading_metadata":actual,
        })
    histogram=Counter(len(books) for books in div1_book_units.values())
    source_book_histogram=Counter(len(d) for d in book_divisions.values())
    title_origin_counts=Counter(ctx[0] for ctx in div1_context.values())
    candidates=[]
    for start in cross_div1_repeated_keys[:MAX_COLLISION_CASES]:
        entries=sorted(start_items[start],key=lambda x:x["original_source_line"])
        if len(entries)>MAX_COLLISION_CASES:
            raise PilotError("Original repeated-source-start identity cases exceed bound")
        candidates.append({
            "original_osisRef_start_key_sha256":_digest(start),
            "original_osisRef_book_code_sha256":_digest(start.split(".",1)[0]),
            "distinct_original_div1_document_ordinals":sorted(repeated_starts[start]),
            "original_source_line_and_full_ref_body_SHA256":entries,
            "source_reused_start_in_different_div1_is_not_evidence_of_same_authored_book":True,
        })
    return {
        "original_source_div1_document_total":full_div1_count,
        "original_div1_with_at_least_one_verse_range_source_marker_count":len(div1_context),
        "original_verse_range_source_units_considered":original_units,
        "distinct_original_osisRef_book_code_count":len(book_divisions),
        "original_osisRef_book_tokens_used_in_more_than_one_div1_count":len(repeated_books),
        "original_scripCom_start_key_reused_across_different_div1_count":len(repeated_starts),
        "original_div1_distinct_declared_osisRef_book_token_count_distribution":
            dict(sorted(histogram.items())),
        "original_osisRef_book_tokens_original_div1_occurrence_count_distribution":
            dict(sorted(source_book_histogram.items())),
        "original_source_div1_heading_origin_counts":dict(sorted(title_origin_counts.items())),
        "bounded_cross_div1_same_original_osisRef_start_key_sha256_cases":candidates,
        "cross_div1_source_start_collision_examples_truncated":
            len(repeated_starts)>len(candidates),
        "focused_shared_raw_source_group_original_bookcode_and_div1_heading_evidence":focused,
        "focused_original_source_units_reconciled":focused_unit_count,
        "original_div1_title_metadata_only_not_certified_canonical_book_name":True,
        "same_osisRef_book_code_across_original_div1_not_automatically_a_source_error":True,
        "source_annotation_reference_work_and_div1_book_identity_not_normalized":True,
        "no_original_book_names_heading_words_reference_values_or_native_keys_output":True,
        "original_source_or_stock_bytes_modified":False,
    }
