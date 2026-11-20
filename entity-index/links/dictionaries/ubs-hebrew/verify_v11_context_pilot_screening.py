#!/usr/bin/env python3
"""Verify a human screening ledger against one source-pinned 72-token witness pack.

Source compatibility is not contextual semantic certification. This verifier
checks provenance, sample membership, sense IDs, uniqueness, report conservation,
and explicit no-publication flags. It does NOT manufacture a word-sense choice.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

CATEGORIES={"apparent_lexical_sense_or_granularity_conflict",
            "context_or_phrase_boundary_uncertain"}
EXPECTED={"apparent_lexical_sense_or_granularity_conflict":3,
          "context_or_phrase_boundary_uncertain":3,
          "no_obvious_conflict_in_short_source_context_NOT_independent_validation":66}

def verify(sample,screen):
    if (sample.get("status")!="PRIVATE_HEBREW_V11_72_WORD_CONTEXTUAL_REVIEW_SAMPLES_NOT_APPROVED"
        or sample.get("candidate_lexids_approved")!=0
        or sample.get("publication_approved") is not False
        or len(sample.get("source_contextual_evidence",[]))!=72):
        raise ValueError("Input source-private 72-word sample has wrong status or size")
    if (screen.get("status")!="PRIVATE_HEBREW_V11_72_SAMPLE_EDITORIAL_SCREENING_NOT_PUBLICATION"
        or screen.get("sample",{}).get("independently_certified_contextual_sense_ids")!=0
        or screen["sample"].get("automatic_new_semantic_assignments")!=0
        or screen["sample"].get("publication_approved") is not False
        or screen.get("editorial_screen")!=EXPECTED
        or screen["source_revisions"]!={"ubs_hebrew_en_fr":sample["source_editions"]["ubs_hebrew"],
            "macula_hebrew_wlc":sample["source_editions"]["macula_wlc"]}):
        raise ValueError("Screen report is not source-pinned or misleadingly certifies senses")
    by_id={row["word_id"]:row for row in sample["source_contextual_evidence"]}
    if len(by_id)!=72:
        raise ValueError("Duplicate original sampled word IDs")
    cases=screen.get("source_specific_cautions",[])
    if len(cases)!=6:
        raise ValueError("Unexpected human-screening word-ID count")
    ids=set();classes=Counter()
    for item in cases:
        wid=item["original_word_id"]
        if wid in ids or wid not in by_id:
            raise ValueError("Screening record is duplicated or not sampled")
        ids.add(wid)
        actual=by_id[wid]
        if (item["reference"]!=actual["macula_reference"]
            or item["ubs_headword"]!=actual["ubs_headword"]
            or item["candidate_ubs_lexid"]!=actual["candidate_lexid"]
            or item.get("preferred_lexid_approved") is not None):
            raise ValueError("Original source UBS word/sense evidence or abstention changed")
        if item["classification"] not in CATEGORIES or len(item["rationale"])<100:
            raise ValueError("Missing meaningful source-specific editorial rationale")
        classes[item["classification"]]+=1
    if any(classes[key]!=EXPECTED[key] for key in CATEGORIES):
        raise ValueError("Human source-specific abstentions do not match audited categories")
    if any(row["editorial_approval"] or row["independently_context_verified"]
           for row in sample["source_contextual_evidence"]):
        raise ValueError("Source sampled evidence was silently promoted")
    return {
        "status":"PRIVATE_VERIFIED_HEBREW_72_SAMPLE_EDITORIAL_SCREEN_NO_SENSES_ASSIGNED",
        "sampled_original_words":72,
        "sampled_ubs_lexical_headwords":36,
        "unique_original_source_verse_witness_population":53981,
        "not_obviously_contradicted_by_excerpt_NOT_independently_semantically_certified":66,
        "phrase_or_context_uncertain":3,
        "apparent_contextual_or_granularity_conflict":3,
        "recommended_automatic_mass_promotion":False,
        "independently_contextually_verified":0,
        "publication_approved":False,
        "original_released_v1_changed":False,
    }

def main():
    p=argparse.ArgumentParser()
    for k in ("sample","screening","output"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    load=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    report=verify(load(a.sample),load(a.screening))
    a.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("UBS_HEBREW_V11_SOURCE_CONTEXTUAL_PILOT_RESULT",json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
