#!/usr/bin/env python3
"""Stage 40 PRIVATE Greek UBS token-locator provisional source choices.

An independently source-pinned 122,504-word calibration found the exact
original UBS word locator at twice the MACULA token ordinal for 115,145 of
119,761 comparable source-unique candidates. This is empirical support,
not an assumption that the two source editions always align. Only one
authentic original UBS LEXID citing the exact reconstructed original
source locator can be a lower-confidence PROVISIONAL editorial default.
No independent verse-context semantic verification is claimed.
"""
from __future__ import annotations
import argparse,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=runpy.run_path(str(HERE/"audit_ubs_token_position_alignment.py"))
EXPECTED=40


def make(position,unresolved,high,low,form,verse):
    if (position.get("status")!="PRIVATE_Greek_UBS_LexReferences_original_token_ordinal_alignment_DIAGNOSTIC_ONLY"
        or position.get("original_source_unique_sense_calibration_words")!=122504
        or position.get("source_unique_words_with_comparable_reference_metadata")!=119761
        or position.get("calibration_matches_by_exact_UBS_to_MACULA_position_factor",{}).get("2")!=115145
        or position.get("original_ambiguous_words")!=2728
        or position.get("new_editorial_source_senses_selected")!=0
        or position.get("no_automatic_word_position_equivalence_asserted") is not True
        or position.get("published") is not False):
        raise ValueError("Original UBS token position calibration source/provenance drift")
    if (unresolved.get("unresolved_original_word_count")!=15237
        or unresolved.get("published") is not False
        or high.get("provisional_source_supported_original_word_count")!=122504
        or high.get("published") is not False
        or low.get("additional_original_word_ids")!=170 or low.get("published") is not False
        or form.get("additional_original_word_provisional_choices")!=223
        or form.get("published") is not False
        or verse.get("new_source_verse_supported_provisional_word_count")!=258
        or verse.get("published") is not False):
        raise ValueError("Original Greek prior provisional source tiers drift")
    if any(x.get("source_editions")!=position["source_editions"]
           for x in (unresolved,high,low,form,verse)):
        raise ValueError("Original UBS and MACULA revisions do not match")
    existing=[
        set(high["word_id_to_provisional_ubs_lexid"]),
        set(low["word_id_to_lower_confidence_provisional_ubs_lexid"]),
        set(form["new_word_id_to_source_form_supported_provisional_lexid"]),
        set(verse["word_id_to_new_UBS_source_verse_provisional_lexid"]),
    ]
    if [len(x) for x in existing]!=[122504,170,223,258]:
        raise ValueError("Prior Greek provisional source word-ID counts drift")
    for i,a in enumerate(existing):
        for b in existing[i+1:]:
            if a&b:raise ValueError("Prior Greek provisional word-ID overlap")
    source=unresolved["word_id_to_unresolved_original_source_evidence"]
    raw=position["word_id_to_candidate_position_diagnostics"]
    if len(source)!=15237 or len(raw)!=2728:
        raise ValueError("Original word-ID provenance register incomplete")
    if existing[0]&set(source) or len(existing[0]|set(source))!=137741:
        raise ValueError("Original source corpus 137741-word accountability drift")
    matched={wid for wid,w in raw.items() if w["source_position_match_diagnostics"]["2"]["status"]==
             "unique_exact_source_position_candidate"}
    if len(matched)!=511:
        raise ValueError("Exact original source token locator one-to-one count drift")
    new=matched-existing[2]-existing[3]
    if len(new)!=EXPECTED or len(matched&existing[2])!=220 or len(matched&existing[3])!=251:
        raise ValueError("Position matched Greek word-ID set overlaps changed")
    decisions={}
    for wid in sorted(new):
        word=raw[wid]
        original=source[wid]
        if original["editorial_status"]!="multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated":
            raise ValueError("Position candidate is not an original multi-UBS-LEXID word")
        keys=("original_word_id","original_reference","original_lemma",
              "original_strong","original_ln","original_class","original_morph")
        if any(word[k]!=original[k] for k in keys) or wid!=word["original_word_id"]:
            raise ValueError("Original Greek source word-specific witness drift")
        if original["source_original_ubs_main_id_candidates"]!=[word["ubs_original_main_id"]]:
            raise ValueError("Original UBS source lexical headword drift")
        hits=word["source_position_match_diagnostics"]["2"]["source_lexid_candidates"]
        old={p["original_ubs_lexid"] for p in original["source_ubs_lexid_candidate_pairs"]}
        if len(hits)!=1 or hits[0] not in old or len(old)<2 or set(word["all_original_candidate_lexids"])!=old:
            raise ValueError("Original UBS LEXID source choices are not uniquely supported")
        ref,locators=SOURCE["locators"](word["original_reference"])
        if len(locators[2])!=14:
            raise ValueError("Original UBS word locator malformed")
        decisions[wid]={
            **{k:word[k] for k in keys},
            "ubs_original_main_id":word["ubs_original_main_id"],
            "source_position_provisional_ubs_lexid":hits[0],
            "other_original_ubs_lexid_candidates":sorted(old-{hits[0]}),
            "authentic_original_UBS_reference_locator":locators[2],
            "source_position_calibration_exact_match_words":115145,
            "source_position_calibration_comparable_words":119761,
            "confidence":"LOWER_CONFIDENCE_PROVISIONAL_exact_UBS_source_token_locator_after_empirical_calibration_NOT_contextually_validated",
            "independently_contextually_validated":False,
        }
    return {
        "status":"PRIVATE_Greek_UBS_40_original_source_position_provisional_choices_NOT_contextually_verified",
        "source_editions":position["source_editions"],
        "new_position_supported_provisional_word_count":len(decisions),
        "all_five_disjoint_private_provisional_tier_word_count":123155+len(decisions),
        "original_words_still_without_unique_provisional_lexid":137741-(123155+len(decisions)),
        "original_multi_lexid_words_still_without_unique_provisional_choice":2728-223-258-len(decisions),
        "word_id_to_source_position_provisional_lexid":decisions,
        "original_corpus_or_dictionaries_modified":False,
        "historical_index_modified":False,
        "independently_contextually_verified":0,
        "published":False,
        "publication_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("position","unresolved","high","low","form","verse","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args();load=lambda q:json.loads(q.read_text(encoding="utf-8-sig"))
    out=make(load(a.position),load(a.unresolved),load(a.high),load(a.low),load(a.form),load(a.verse))
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("GREEK_UBS_40_SOURCE_POSITION_SUPPORTED_PROVISIONAL_SENSE_CHOICES",json.dumps({
        "new":out["new_position_supported_provisional_word_count"],
        "all_provisional":out["all_five_disjoint_private_provisional_tier_word_count"],
        "remaining":out["original_words_still_without_unique_provisional_lexid"],
        "contextually_validated":0,"published":False},sort_keys=True))


if __name__=="__main__":main()
