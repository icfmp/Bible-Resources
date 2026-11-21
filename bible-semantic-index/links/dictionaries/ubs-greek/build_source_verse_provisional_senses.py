#!/usr/bin/env python3
"""Stage PRIVATE reversible UBS source-verse provisional sense choices.

Original word-specific EN/FR UBS citations are source evidence, not
independently verified contextual semantics. Earlier overlays and originals
remain unchanged.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

EXPECTED=258
TOTAL=137741

def make(report,unresolved,high,low,form):
    if (report.get("status")!="PRIVATE_UBS_Greek_word_specific_original_source_verse_sense_candidate_AUDIT_NOT_CONTEXT_VALIDATION"
        or report.get("all_initial_original_multi_lexid_words")!=2728
        or report.get("previously_staged_source_form_word_ids")!=223
        or report.get("original_reference_witness_candidate_word_count")!=EXPECTED
        or report.get("independently_contextually_validated")!=0
        or report.get("published") is not False or report.get("publication_approved") is not False):
        raise ValueError("Source-verse candidate audit drift")
    if (unresolved.get("unresolved_original_word_count")!=15237
        or unresolved.get("status")!="PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review"
        or unresolved.get("published") is not False
        or high.get("provisional_source_supported_original_word_count")!=122504
        or high.get("published") is not False
        or low.get("additional_original_word_ids")!=170 or low.get("published") is not False
        or form.get("additional_original_word_provisional_choices")!=223
        or form.get("published") is not False):
        raise ValueError("Prior source provisional ledgers drift")
    for name,item in (("unresolved",unresolved),("high",high),("low",low),("form",form)):
        if item.get("source_editions")!=report["source_editions"]:
            raise ValueError("Pinned source revision mismatch: "+name)
    source=unresolved["word_id_to_unresolved_original_source_evidence"]
    highids=high["word_id_to_provisional_ubs_lexid"]
    lowids=low["word_id_to_lower_confidence_provisional_ubs_lexid"]
    formids=form["new_word_id_to_source_form_supported_provisional_lexid"]
    proposed=report["word_id_to_possible_UBS_original_source_reference_sense"]
    if (len(source)!=15237 or len(highids)!=122504 or len(lowids)!=170
        or len(formids)!=223 or len(proposed)!=EXPECTED):
        raise ValueError("Original word-ID inventory drift")
    if set(source)&set(highids) or len(set(source)|set(highids))!=TOTAL:
        raise ValueError("Original corpus full word-ID accounting drift")
    if not (set(lowids)|set(formids)|set(proposed)).issubset(source):
        raise ValueError("Missing original Greek source-word evidence")
    if set(lowids)&set(formids) or set(lowids)&set(proposed) or set(formids)&set(proposed):
        raise ValueError("Overlapping provisional source sense tiers")
    decisions={}
    for wid,proposal in sorted(proposed.items()):
        orig=source[wid]
        mid=proposal["ubs_original_main_id"]
        sid=proposal["source_ubs_original_lexid_reference_candidate"]
        if (orig["editorial_status"]!="multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated"
            or orig["source_original_ubs_main_id_candidates"]!=[mid]
            or orig["verse_context_semantically_verified"] is not False
            or proposal["independently_verse_context_semantically_verified"] is not False):
            raise ValueError("Original word-specific lexeme/semantic witness drift")
        candidates={p["original_ubs_lexid"] for p in orig["source_ubs_lexid_candidate_pairs"]}
        if (sid not in candidates or len(candidates)<2
            or set(proposal["other_original_UBS_lexid_candidates"])!=candidates-{sid}):
            raise ValueError("Missing original UBS lexical sense alternatives")
        keys=("original_word_id","original_reference","original_lemma",
              "original_strong","original_ln","original_class","original_morph")
        if any(orig[k]!=proposal[k] for k in keys) or wid!=proposal["original_word_id"]:
            raise ValueError("Original MACULA word witness was modified")
        decisions[wid]={
            **{k:orig[k] for k in keys},
            "ubs_original_main_id":mid,
            "source_reference_supported_provisional_ubs_lexid":sid,
            "other_original_source_ubs_lexid_candidates":sorted(candidates-{sid}),
            "source_verse_reference_key":proposal["original_MACULA_verse_key"],
            "editorial_evidence":"bilingual pinned original UBS LEXReferences citation and exactly one source-linked UBS lexical headword in MACULA verse",
            "confidence":"PROVISIONAL_original_source_verse_citation_NOT_independently_contextually_validated",
            "independently_contextually_validated":False,
        }
    if len(decisions)!=EXPECTED:
        raise ValueError("Missing original source verse-linked provisional word ID")
    selected=122504+170+223+len(decisions)
    return {
        "status":"PRIVATE_Greek_UBS_source_verse_provisional_editorial_senses_NOT_validated",
        "source_editions":report["source_editions"],
        "all_original_greek_word_ids":TOTAL,
        "source_LN_unique_provisional_word_count":122504,
        "source_single_sense_weaker_provisional_word_count":170,
        "source_form_supported_provisional_word_count":223,
        "new_source_verse_supported_provisional_word_count":len(decisions),
        "all_provisional_original_word_ids_across_disjoint_tiers":selected,
        "remaining_without_a_unique_provisional_UBS_LEXID":TOTAL-selected,
        "unresolved_original_multi_lexid_after_form_and_verse":2728-223-len(decisions),
        "word_id_to_new_UBS_source_verse_provisional_lexid":dict(sorted(decisions.items())),
        "previous_private_tiers_modified":False,
        "original_UBS_or_MACULA_modified":False,
        "independently_contextually_validated":0,
        "published":False,
        "publication_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("report","unresolved","high","low","form","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    load=lambda f:json.loads(f.read_text(encoding="utf-8-sig"))
    r=make(load(a.report),load(a.unresolved),load(a.high),load(a.low),load(a.form))
    a.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("GREEK_UBS_SOURCE_VERSE_PROVISIONAL_EDITORIAL_WORD_SENSES",json.dumps({
        "new_source_verse_provisional":r["new_source_verse_supported_provisional_word_count"],
        "all_provisional":r["all_provisional_original_word_ids_across_disjoint_tiers"],
        "still_without_unique_provisional":r["remaining_without_a_unique_provisional_UBS_LEXID"],
        "multi_sense_remaining":r["unresolved_original_multi_lexid_after_form_and_verse"],
        "independently_contextually_validated":0,"published":False},sort_keys=True))


if __name__=="__main__":main()
