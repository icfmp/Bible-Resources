#!/usr/bin/env python3
"""Private source-authoritative inventory of ALL ThML units sharing a native raw run.

A group is nominated by >=2 independently audited large prose anomalies that
resolve inside the SAME contiguous occupied native K-key run with identical
raw bytes. Then every genuine source scripCom marker whose start is in that
run is included, even if that original source unit was NOT a lexical anomaly.

Never assign commentary to verses based on stock repetition. All source
words/targets, true native K keys, source XML, and SWORD payload bytes remain
only in the temporary private runner. Reports contain bounded counts, closed
class names and cryptographic SHA-256 identities.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_prose_cross_slot import strict_native_stock_plain_words
from commentary_unresolved_lexical_triage import WORD
from commentary_xml_witness import OSIS_LOC
from pilot_preflight import PilotError

SHA_RE = re.compile(r"[a-f0-9]{64}\Z")
MAX_GROUPS = 8
MAX_SOURCE_UNITS_PER_GROUP = 16
MAX_INPUT_CASES = 20
MAX_RANGE_NUMERIC_VERSES = 500


def _real_source_plain_words(unit: dict) -> list[str]:
    original = unit.get("original_text")
    if not isinstance(original, str):
        raise PilotError("Original source body missing")
    if sha256(original.encode("utf-8")).hexdigest() != unit.get("original_text_sha256"):
        raise PilotError("Original source body bytes differ from source scanner")
    words=WORD.findall(original)
    marked=unit.get("private_original_scripRef_word_indices")
    if (not isinstance(marked,list) or len(set(marked))!=len(marked)
            or any(type(p) is not int or p<0 or p>=len(words) for p in marked)):
        raise PilotError("Original source link label word indices not authenticated")
    removed=set(marked)
    return [w for i,w in enumerate(words) if i not in removed]


def _original_numeric_span(start: str, unit: dict) -> tuple[str,int,int]:
    end=unit.get("private_original_declared_range_end_key")
    if (not isinstance(start,str) or not isinstance(end,str)
            or not OSIS_LOC.fullmatch(start) or not OSIS_LOC.fullmatch(end)):
        raise PilotError("Original explicit source range endpoint not authenticated")
    first_chap,first=start.rsplit(".",1)
    last_chap,last=end.rsplit(".",1)
    if first_chap!=last_chap or not 0<int(first)<=int(last) or (
        int(last)-int(first)+1>MAX_RANGE_NUMERIC_VERSES
    ):
        raise PilotError("Original source range requires a separate chapter-aware review")
    return first_chap,int(first),int(last)


def _sha(value:str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def inspect_shared_original_units_in_native_runs(
    source:dict[str,list[dict]],
    ledger,  # Existing fully enumerated NativeRawRunBoundaryInventory
    matches:dict[str,bytes],
    serious_cases:list[dict],
) -> dict:
    """Return only source-line/full-hash/numeric evidence; never source words."""
    if not isinstance(serious_cases,list) or not 1<=len(serious_cases)<=MAX_INPUT_CASES:
        raise PilotError("Original serious prose case selection unbounded")
    by_identity={}
    for start, units in source.items():
        for unit in units:
            ident=(unit["original_source_line"],unit["original_full_reference_sha256"],
                   unit["original_text_sha256"])
            if ident in by_identity:
                raise PilotError("Original source full identity reused")
            by_identity[ident]=(start,unit)
    nominated=defaultdict(set)
    book_ledger_index={}
    for book, entries in ledger.entries.items():
        positions={}
        for i,(key,chapter,digest) in enumerate(entries):
            if key in positions:
                raise PilotError("Native corpus has duplicated numbered K-key identities")
            positions[key]=i
        book_ledger_index[book]=positions
    for case in serious_cases:
        ident=(case["original_source_line"],case["original_full_reference_sha256"],
               case["original_body_sha256"])
        if (type(ident[0]) is not int or ident[0]<1 or
                any(not isinstance(v,str) or not SHA_RE.fullmatch(v) for v in ident[1:]) or
                ident not in by_identity):
            raise PilotError("Original serious prose case not source-authenticated")
        start, original=by_identity[ident]
        book=start.split(".",1)[0]
        raw=case.get("stock_raw_sha256")
        if not isinstance(raw,str) or not SHA_RE.fullmatch(raw):
            raise PilotError("Original selected compiled raw SHA missing")
        if start not in book_ledger_index.get(book,{}):
            raise PilotError("Original serious source start absent from native K-index")
        entries=ledger.entries[book]
        i=book_ledger_index[book][start]
        if entries[i][2]!=raw or sha256(matches[start]).hexdigest()!=raw:
            raise PilotError("Source-anchored compiled raw hash differs from independent K-index")
        left=i
        right=i
        while left>0 and entries[left-1][2]==raw:
            left-=1
        while right+1<len(entries) and entries[right+1][2]==raw:
            right+=1
        nominated[(book,left,right,raw)].add(ident)
    multi=[(key,ids) for key,ids in nominated.items() if len(ids)>=2]
    if len(multi)>MAX_GROUPS:
        raise PilotError("Multiple source→one native raw run groups exceed reviewed bound")
    results=[]
    source_units_total=0
    newly_identified=0
    per_group_source_alignment=Counter()
    source_scope_counts=Counter()
    original_div1_group_shapes=Counter()
    for (book,left,right,raw_sha),original_cases in sorted(
        multi,key=lambda g:(g[0][0],g[0][1],g[0][2])
    ):
        entries=ledger.entries[book]
        run=entries[left:right+1]
        if len(run)<2 or len({digest for _key,_ch,digest in run})!=1:
            raise PilotError("Shared original source group has inconsistent native raw run")
        if len({chapter for _key,chapter,_raw in run})!=1:
            raise PilotError("Source shared group crosses a native chapter unexpectedly")
        chapter=run[0][1]
        run_keys={key for key,_chapter,_raw in run}
        source_starts=[]
        for start,units in source.items():
            if start in run_keys:
                for unit in units:
                    source_starts.append((unit["original_source_line"],start,unit))
        source_starts.sort(key=lambda triple:(triple[0],triple[1]))
        if not 2<=len(source_starts)<=MAX_SOURCE_UNITS_PER_GROUP:
            raise PilotError("Source-authoritative native-run group does not have bounded units")
        if len(original_cases)>len(source_starts):
            raise PilotError("Source serious-case identities not inside original run unit inventory")
        true_member_identities={
            (unit["original_source_line"],unit["original_full_reference_sha256"],
             unit["original_text_sha256"])
            for _line,start,unit in source_starts
        }
        if not original_cases.issubset(true_member_identities):
            raise PilotError("Source original known anomalies not contained in shared stock raw run")
        witness_start=source_starts[0][1]
        selected_stock=matches.get(witness_start)
        if selected_stock is None or sha256(selected_stock).hexdigest()!=raw_sha:
            raise PilotError("Stock shared raw has no source-start-anchored native witness")
        compiled_words=strict_native_stock_plain_words(selected_stock)
        compiled_unmarked_words_count=len(compiled_words)
        source_member_receipts=[]
        all_source_words=[]
        actual_source_div1_ordinals=[]
        run_source_coverage=Counter()
        for line,start,unit in source_starts:
            if (unit["original_source_line"]!=line or
                    not SHA_RE.fullmatch(unit["original_full_reference_sha256"]) or
                    not SHA_RE.fullmatch(unit["original_text_sha256"])):
                raise PilotError("Source group has unauthenticated original line and hashes")
            if (start not in matches or sha256(matches[start]).hexdigest()!=raw_sha or
                    ledger.entries[book][book_ledger_index[book][start]][2]!=raw_sha):
                raise PilotError("An original source member does not begin inside selected compiled raw")
            boundary=unit.get("private_source_marker_boundary")
            if not isinstance(boundary,dict) or not boundary.get(
                "source_original_marker_and_body_unmodified"
            ):
                raise PilotError("Original source marker/body adjacency not proven")
            src_chapter,verse_start,verse_end=_original_numeric_span(start,unit)
            if src_chapter!=chapter:
                raise PilotError("Original source member chapter differs from compiled raw group")
            for key,_nchap,_digest in run:
                verse=int(key.rsplit(".",1)[-1])
                if verse_start<=verse<=verse_end:
                    run_source_coverage[key]+=1
            source_in_range=[
                (key,digest) for key,k_chapter,digest in entries
                if k_chapter==src_chapter and verse_start<=int(key.rsplit(".",1)[-1])<=verse_end
            ]
            if not source_in_range or start not in {key for key,_hash in source_in_range}:
                raise PilotError("Original source range has no authentic numbered K start")
            ordinal=unit.get("private_original_enclosing_div1_document_ordinal")
            total_div1=unit.get("private_original_total_div1_in_document")
            if (type(ordinal) is not int or type(total_div1) is not int
                    or not 1<=ordinal<=total_div1<=500):
                raise PilotError("Original source div1 XML document ancestry is unverified")
            actual_source_div1_ordinals.append(ordinal)
            plain=_real_source_plain_words(unit)
            all_source_words.extend(plain)
            aligned=plain_word_alignment(plain,compiled_words)
            if aligned["original_plain_word_tokens"] != len(plain):
                raise PilotError("Original source plain-word alignment stream mismatch")
            classification=aligned["exact_unicode_ordered_alignment_class"]
            per_group_source_alignment[classification]+=1
            serious_id=(
                line,unit["original_full_reference_sha256"],unit["original_text_sha256"]
            )
            in_serious=serious_id in original_cases
            source_scope_counts["previously_known_large_prose_case" if in_serious else
                                "newly_discovered_source_unit_in_shared_stock_run"]+=1
            if not in_serious:
                newly_identified+=1
            native_orig_start_index=book_ledger_index[book][start]-left+1
            membership={
                "original_source_line":line,
                "original_full_reference_sha256":unit["original_full_reference_sha256"],
                "original_source_body_sha256":unit["original_text_sha256"],
                "original_enclosing_div1_ordinal_in_original_XML_document":ordinal,
                "total_div1_ancestors_enumerated_in_original_XML_document":total_div1,
                "original_source_start_key_sha256":_sha(start),
                "original_source_end_key_sha256":_sha(
                    unit["private_original_declared_range_end_key"]
                ),
                "original_source_marker_reference_kind":boundary[
                    "original_annotation_reference_kind"
                ],
                "original_source_direct_body_tag_counts":unit[
                    "private_original_body_tag_counts"
                ],
                "original_source_numeric_verse_span":verse_end-verse_start+1,
                "original_source_genuine_native_occupied_K_in_declared_span":
                    len(source_in_range),
                "source_declared_range_native_K_same_raw_as_group":
                    sum(digest==raw_sha for _key,digest in source_in_range),
                "source_declared_range_native_K_other_raw":
                    sum(digest!=raw_sha for _key,digest in source_in_range),
                "original_declared_source_start_ordinal_inside_identical_raw_native_run":
                    native_orig_start_index,
                "original_declared_source_end_key_within_shared_raw_run":
                    unit["private_original_declared_range_end_key"] in run_keys,
                "original_source_comment_was_one_of_previously_seven_large_discrepancies":
                    in_serious,
                "original_source_scripRef_element_count":unit[
                    "private_original_body_tag_counts"
                ].get("scripRef",0),
                "original_source_plain_word_token_count":len(plain),
                "compiled_shared_raw_plain_word_token_count":compiled_unmarked_words_count,
                "source_unit_vs_shared_stock_plain_word_order_alignment":aligned,
                "source_range_and_native_raw_bytes_not_reassigned_or_modified":True,
            }
            source_member_receipts.append(membership)
        # Every original start is authenticated by the exact native K and
        # independently compared with the same byte-identical compiled payload.
        if len({r["original_full_reference_sha256"] for r in source_member_receipts})!=len(source_member_receipts):
            raise PilotError("Original shared run contains ambiguous original source references")
        if len(run_source_coverage)>len(run):
            raise PilotError("Original numerical source range coverage exceeds raw run")
        covered=sum(n>0 for n in run_source_coverage.values())
        overlap=sum(n>1 for n in run_source_coverage.values())
        combined_alignment=plain_word_alignment(all_source_words,compiled_words)
        div1_ordinal_set=set(actual_source_div1_ordinals)
        if len({m["total_div1_ancestors_enumerated_in_original_XML_document"]
                for m in source_member_receipts})!=1:
            raise PilotError("Original source units disagree about one actual div1 inventory")
        division_class=(
            "multiple_distinct_original_div1_documents_in_same_stock_raw_run"
            if len(div1_ordinal_set)>1
            else "all_original_source_units_from_one_original_div1"
        )
        group={
            "native_shared_raw_SHA256":raw_sha,
            "native_shared_first_numbered_K_key_SHA256":_sha(run[0][0]),
            "native_shared_last_numbered_K_key_SHA256":_sha(run[-1][0]),
            "native_occupied_numbered_K_keys_in_shared_raw_run":len(run),
            "distinct_original_scripCom_source_units_starting_in_shared_run":
                len(source_member_receipts),
            "distinct_original_div1_document_divisions_in_shared_stock_raw_run":
                len(div1_ordinal_set),
            "original_div1_document_ordinals_represented_in_shared_stock_raw_run":
                sorted(div1_ordinal_set),
            "original_div1_structure_class":division_class,
            "sharing_a_native_K_key_does_not_prove_same_original_div1_book_or_section":True,
            "previously_known_serious_original_prose_cases_in_this_run":len(original_cases),
            "additional_authentic_original_source_units_identified":
                len(source_member_receipts)-len(original_cases),
            "original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order":
                source_member_receipts,
            "native_raw_run_K_keys_covered_by_at_least_one_actual_original_source_range":
                covered,
            "native_raw_run_K_keys_claimed_by_multiple_original_source_ranges":
                overlap,
            "native_raw_run_K_keys_uncovered_by_original_source_ranges_starting_in_run":
                len(run)-covered,
            "combined_original_source_plain_word_token_count":len(all_source_words),
            "combined_original_source_plain_words_in_original_XML_unit_order_vs_one_stock_raw":
                combined_alignment,
            "repeated_compiled_native_payload_is_not_original_source_section_parity":True,
            "concatenated_source_text_from_different_original_div1_is_not_authorial_text":True,
            "original_source_prose_or_range_edited":False,
        }
        source_units_total+=len(source_member_receipts)
        original_div1_group_shapes[division_class]+=1
        results.append(group)
    return {
        "multi_original_source_start_same_native_raw_run_groups":len(results),
        "full_authentic_original_source_units_in_those_runs":source_units_total,
        "previously_unreviewed_original_source_units_now_identified":newly_identified,
        "source_unit_plain_word_alignments_to_shared_native_raw_closed_categories":
            dict(sorted(per_group_source_alignment.items())),
        "source_marker_scope_evidence_class_counts":dict(sorted(source_scope_counts.items())),
        "source_div1_ancestry_structure_class_counts":dict(sorted(original_div1_group_shapes.items())),
        "bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports":
            results,
        "no_inferred_missing_original_source_marker_or_fabricated_verse_range":True,
        "source_word_overlap_does_not_authorize_original_section_to_compiled_raw_mapping":True,
        "original_source_values_native_keys_and_compiled_raw_bytes_not_output":True,
        "original_source_or_stock_compiled_module_content_changed":False,
    }
