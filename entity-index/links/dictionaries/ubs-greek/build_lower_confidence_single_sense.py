#!/usr/bin/env python3
"""Lower-confidence provisional Greek UBS editorial default: sole available source LEXID.

There are exactly 170 original MACULA Greek words with a *supported,
unique source lexical headword*, NO matching word-specific LN, and
exactly one authentic UBS EN+FR LEXID under that headword. A single
source sense is a reasonable editorial default, but its meaning
remains UNCONFIRMED in the specific verse; do not invent, rewrite or
silently repair original MACULA LN, original UBS codes, Greek or Strong.
Keep these separate from the 122,504 stronger LN-backed provisional
choices and the complete 15,237-word unresolved register.
"""
from __future__ import annotations
import argparse,json,hashlib,runpy
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
AUDIT=runpy.run_path(str(HERE/"audit_unresolved_semantic_priorities.py"))
SOURCE_CATEGORIES={
    "blank_MACULA_original_LN__exactly_one_original_UBS_LEXID_without_matching_word_LN_NOT_APPROVED":120,
    "nonblank_MACULA_LN_not_attested_under_UBS_headword__exactly_one_original_UBS_LEXID_without_matching_word_LN_NOT_APPROVED":50,
}

def build(unresolved,priorities,en,fr):
    if (unresolved.get("status")!="PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review"
        or len(unresolved.get("word_id_to_unresolved_original_source_evidence",{}))!=15237
        or unresolved.get("published") is not False
        or priorities.get("status")!="PRIVATE_source_review_Greek_15237_semantic_exceptions_diagnostics_ONLY"
        or priorities.get("source_categories") is None
        or priorities.get("provisional_new_lexids_selected")!=0
        or priorities.get("published") is not False):
        raise ValueError("Original Greek source-priority report provenance drift")
    for k,v in SOURCE_CATEGORIES.items():
        if priorities["source_categories"].get(k)!=v:
            raise ValueError("Unique original UBS lexical sense metadata unexpectedly changed")
    entries=AUDIT["source_lexids"](en)
    if entries!=AUDIT["source_lexids"](fr) or len(entries)!=5507:
        raise ValueError("Original UBS Greek bilingual LEXID inventories drift")
    choices={}
    categories=Counter()
    for wid,word in unresolved["word_id_to_unresolved_original_source_evidence"].items():
        if word["editorial_status"]!="no_original_ln_matching_ubs_lexical_sense":
            continue
        mids=word["source_original_ubs_main_id_candidates"]
        if len(mids)!=1 or word["source_ubs_lexid_candidate_pairs"]:
            raise ValueError("Uncorroborated original Greek word-ID sense candidate provenance drift")
        mid=mids[0]
        lexids=entries[mid]
        if len(lexids)!=1:
            continue
        sid=next(iter(lexids))
        original_ln=word["original_ln"]
        source_codes=sorted(lexids[sid])
        if set(original_ln.split())&set(source_codes):
            raise ValueError("Unique Greek source LN sense should already be included in 122504 higher-confidence pool")
        basis=("blank_original_macula_ln" if not original_ln else "original_macula_ln_not_in_authentic_ubs_headword")
        categories[basis]+=1
        choices[wid]={
            "original_word_id":wid,
            "original_reference":word["original_reference"],
            "original_lemma":word["original_lemma"],
            "original_strong":word["original_strong"],
            "original_ln":original_ln,
            "original_class":word["original_class"],
            "original_morph":word["original_morph"],
            "original_lexical_headword_review":word["original_headword_evidence"],
            "original_ubs_main_id":mid,
            "original_ubs_unique_lexid":sid,
            "original_ubs_lexid_ln_codes_unaltered":source_codes,
            "reason_no_corresponding_original_word_ln":basis,
            "editorial_status":"LOWER_CONFIDENCE_PROVISIONAL_single_UBS_lexid_without_original_MACULA_LN_correspondence_NOT_contextually_verified",
            "verse_context_semantically_verified":False,
        }
    if len(choices)!=170 or categories!={"blank_original_macula_ln":120,"original_macula_ln_not_in_authentic_ubs_headword":50}:
        raise ValueError("170 original Greek source-supported lower-confidence lexical sense opportunities drift")
    return {
        "status":"PRIVATE_Greek_170_reasonable_lower_confidence_single_UBS_LEXID_provisional_source_decisions_ONLY",
        "source_editions":unresolved["source_editions"],
        "additional_original_word_ids":170,
        "original_source_status_counts":dict(sorted(categories.items())),
        "word_id_to_lower_confidence_provisional_ubs_lexid":dict(sorted(choices.items())),
        "original_macula_ln_changed":False,
        "original_ubs_lexical_data_changed":False,
        "original_strong_or_greek_changed":False,
        "contextual_senses_independently_verified":0,
        "published":False,
        "publication_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("unresolved","priorities","english","french","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args();load=lambda q:json.loads(q.read_text(encoding="utf-8-sig"))
    x=build(load(a.unresolved),load(a.priorities),load(a.english),load(a.french))
    a.output.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("GREEK_170_LOWER_CONFIDENCE_SOURCE_ONLY_SINGLE_UBS_SENSE_EDITORIAL_DEFAULTS",json.dumps({
        "provisional_words":x["additional_original_word_ids"],
        "original_source_code_status":x["original_source_status_counts"],
        "contextually_validated":0,
        "published":False,
        "sha256":hashlib.sha256(a.output.read_bytes()).hexdigest()
    },sort_keys=True))
if __name__=="__main__":main()
