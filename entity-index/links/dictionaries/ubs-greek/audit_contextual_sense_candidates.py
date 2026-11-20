#!/usr/bin/env python3
"""Original-word census of UBS Greek contextual lexical sense *candidates*.

Independent read of the entire pinned SBLGNT 137,741-word source and
original UBS 1.0 bilingual LEXID/Louw–Nida inventories. A unique
source-attested lexical sense candidate is evidence, NOT yet proof
of its meaning in the specific verse. Nothing is written to the Greek
source, historical index, reviewed headword overlay or UBS dictionary.
"""
from __future__ import annotations
import argparse
import csv
import json
import runpy
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BUILD=runpy.run_path(str(ROOT/"build_index.py"))
SOURCE_ROWS=137741
COVERED=137694
EXCEPTIONS=47
AMBIGUOUS=224
REVIEWED_AMBIGUOUS=220

def extract_lexical_senses(records):
    result={}
    for rec in records:
        senses=set()
        for form in rec.get("BaseForms") or []:
            for s in form.get("LEXMeanings") or []:
                sid=s.get("LEXID")
                code=s.get("LEXEntryCode")
                if not isinstance(sid,str) or not sid or not isinstance(code,str):
                    raise ValueError("UBS original lexical sense has invalid LEXID/LN: "+repr({"main_id":rec["MainId"],"lexid":sid,"ln_code":code}))
                # Genuine original UBS source senses can have an empty LN code.
                # Preserve them in the full source inventory but never fabricate
                # an LN-backed word-specific sense candidate from a blank code.
                if code:
                    senses.add((sid,code))
        if rec["MainId"] in result:
            raise ValueError("Duplicate original UBS Greek entry")
        result[rec["MainId"]]=senses
    return result

def verify_sources(index,en,fr):
    if index.get("coverage",{}).get("macula_words")!=SOURCE_ROWS:
        raise ValueError("Pinned Greek original-word census changed")
    # Recompute exact original bilingual lexical crosswalk. Definitions are never copied.
    rebuilt=BUILD["build"](en,fr)
    for key in rebuilt:
        if key=="coverage":
            continue
        if rebuilt[key]!=index[key]:
            raise ValueError("Original UBS bilingual Greek source/index diverged: "+key)
    e=extract_lexical_senses(en)
    f=extract_lexical_senses(fr)
    if e!=f or len(e)!=5507:
        raise ValueError("Original UBS Greek EN/FR LEXID or LN differences")
    raw_source_count=sum(len(form.get("LEXMeanings") or []) for entry in en for form in entry.get("BaseForms") or [])
    if raw_source_count!=9160:
        raise ValueError("Original 9160 UBS source lexical sense inventory drift")
    return e

def original_word(row):
    return {
        "original_word_id":row["xml:id"],
        "original_reference":row["ref"],
        "original_lemma":row["lemma"],
        "original_strong":row["strong"],
        "original_ln":row["ln"],
        "original_class":row["class"],
        "original_morph":row["morph"],
    }

def candidates_for_original_word(row,index,reviewed,senses):
    word_id=row["xml:id"]
    old=BUILD["lookup"](index,row["strong"],row["ln"])
    lexical=reviewed["by_macula_word"].get(word_id)
    ambiguity=reviewed["by_macula_ambiguous_word"].get(word_id)
    if lexical is not None and ambiguity is not None:
        raise ValueError("Original Greek word ID counted in overlapping candidate overlays")
    if lexical is not None:
        if old["entry_ids"]:
            raise ValueError("Original Greek lexical headword overlay conflicts with baseline Strong index")
        for k,source in (("original_lemma","lemma"),("original_strong","strong"),("original_ln","ln"),
                         ("original_reference","ref"),("original_class","class"),("original_morph","morph")):
            if lexical[k]!=row[source]:
                raise ValueError("Original Greek word-specific lexical candidate source witness drift: "+word_id)
        mids=[lexical["entry_id"]]
        group="reviewed_original_source_word_headword"
    elif len(old["entry_ids"])==1:
        if ambiguity is not None:
            raise ValueError("Reviewed Greek Strong ambiguity incorrectly assigned to unique original candidate")
        mids=old["entry_ids"]
        group="historical_unique_strong_headword"
    elif len(old["entry_ids"])>1:
        if ambiguity is not None:
            for k,source in (("original_lemma","lemma"),("original_strong","strong"),("original_ln","ln"),
                             ("original_reference","ref"),("original_class","class"),("original_morph","morph")):
                if ambiguity[k]!=row[source]:
                    raise ValueError("Original Greek reviewed Strong ambiguity source witness drift: "+word_id)
            if ambiguity["entry_id"] not in old["entry_ids"]:
                raise ValueError("Original reviewed Greek Strong ambiguity is outside authentic UBS baseline candidates")
            mids=[ambiguity["entry_id"]]
            group="reviewed_original_strong_ambiguity_headword"
        else:
            mids=old["entry_ids"]
            group="unresolved_historical_multiheadword_strong"
    else:
        if ambiguity is not None:
            raise ValueError("Original word-specific ambiguity without authentic baseline Strong entries")
        mids=[]
        group="no_source_supported_ubs_headword"
    if len(mids)!=len(set(mids)):
        raise ValueError("Duplicated Greek original lexical MainId")
    original_ln=set(row["ln"].split())
    candidates=sorted(set((mid,lexid,code)
        for mid in mids
        for lexid,code in senses[mid]
        if code in original_ln))
    return group,mids,candidates

def audit(index,reviewed,en,fr,macula):
    senses=verify_sources(index,en,fr)
    if (reviewed["editorial_candidate"].get("reviewed_original_headword_words_total")!=9604
        or reviewed["editorial_candidate"].get("publication_approved") is not False
        or reviewed["word_aware_coverage"].get("word_aware_entry_candidate_words")!=COVERED
        or reviewed["word_aware_coverage"].get("remaining_no_ubs_headword_candidate_original_words")!=EXCEPTIONS
        or len(reviewed.get("by_macula_word",{}))!=9604
        or len(reviewed.get("by_macula_ambiguous_word",{}))!=REVIEWED_AMBIGUOUS):
        raise ValueError("Original Greek source-reviewed word-specific headword overlay changed")
    for k,v in index.items():
        if reviewed.get(k)!=v:
            raise ValueError("Historical original UBS Greek source index modified")
    ids=set()
    total=0
    totals=Counter()
    outcomes=Counter()
    group_counts=Counter()
    multi_examples=[]
    no_code_examples=[]
    no_entry_examples=[]
    ambiguous_examples=[]
    unique_by_original_ln=defaultdict(Counter)
    original_multi_ln=0
    unique_lexid_multi_codes=0
    with macula.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream,delimiter="\t")
        required={"xml:id","ref","lemma","strong","ln","class","morph"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Original MACULA Greek columns drifted")
        for row in reader:
            wid=row["xml:id"]
            if wid in ids or not wid.startswith("n"):
                raise ValueError("Duplicate/malformed original Greek word ID")
            ids.add(wid);total+=1
            group,mids,possible=candidates_for_original_word(row,index,reviewed,senses)
            group_counts[group]+=1
            if len(row["ln"].split())>1:
                original_multi_ln+=1
            if not mids:
                outcome="no_ubs_headword"
            elif len(mids)>1:
                outcome="multiple_original_ubs_lexical_headwords"
            elif not possible:
                outcome="no_original_ln_matching_ubs_lexical_sense"
            elif len({lexid for _,lexid,_ in possible})==1:
                outcome="unique_source_attested_ubs_lexid_candidate_NOT_contextually_validated"
                if len(possible)>1:
                    unique_lexid_multi_codes+=1
            else:
                outcome="multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated"
            outcomes[outcome]+=1
            if outcome.startswith("unique_source"):
                unique_by_original_ln["original_source_class"][row["class"]]+=1
                unique_by_original_ln["source_method"][group]+=1
            sample={**original_word(row),
                    "headword_provenance":group,
                    "original_ubs_main_id_candidates":mids,
                    "source_attested_ubs_sense_pairs":[{"ubs_main_id":mid,"lexid":lexid,"ln_code":code}
                                                       for mid,lexid,code in possible[:12]],
                    "sense_candidate_count":len({(m,s) for m,s,_ in possible}),
                    "semantic_disposition":outcome}
            if outcome=="multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated" and len(multi_examples)<35:
                multi_examples.append(sample)
            if outcome=="no_original_ln_matching_ubs_lexical_sense" and len(no_code_examples)<35:
                no_code_examples.append(sample)
            if outcome=="no_ubs_headword" and len(no_entry_examples)<47:
                no_entry_examples.append(sample)
            if outcome=="multiple_original_ubs_lexical_headwords" and len(ambiguous_examples)<12:
                ambiguous_examples.append(sample)
    if total!=SOURCE_ROWS or len(ids)!=SOURCE_ROWS:
        raise ValueError("Source original Greek word census is incomplete")
    if (group_counts["historical_unique_strong_headword"]!=128090-AMBIGUOUS
        or group_counts["reviewed_original_strong_ambiguity_headword"]!=REVIEWED_AMBIGUOUS
        or group_counts["unresolved_historical_multiheadword_strong"]!=AMBIGUOUS-REVIEWED_AMBIGUOUS
        or group_counts["reviewed_original_source_word_headword"]!=9604
        or group_counts["no_source_supported_ubs_headword"]!=EXCEPTIONS
        or sum(group_counts.values())!=SOURCE_ROWS
        or sum(outcomes.values())!=SOURCE_ROWS
        or outcomes["no_ubs_headword"]!=EXCEPTIONS
        or outcomes["multiple_original_ubs_lexical_headwords"]!=4):
        raise ValueError("Original Greek lexical/sense census or original headword accounting drift: "+repr(group_counts))
    return {
        "status":"PRIVATE_SOURCE_UBS_Greek_v1_0_original_word_sense_CANDIDATE_CENSUS_NOT_SEMANTIC_VALIDATION",
        "source_editions":{"ubs_greek_revision":BUILD["UBS_REVISION"],"macula_sblgnt_revision":BUILD["MACULA_REVISION"]},
        "original_word_ids":total,
        "source_ubs_entries":len(senses),
        "source_ubs_sense_pairs":9160,
        "source_ubs_sense_pairs_with_nonblank_original_ln":sum(len(x) for x in senses.values()),
        "distinct_original_word_headword_provenance":dict(sorted(group_counts.items())),
        "original_word_sense_candidate_outcomes":dict(sorted(outcomes.items())),
        "original_word_ids_with_multiple_MACULA_LN_codes":original_multi_ln,
        "unique_UBS_LEXID_but_multiple_source_codes":unique_lexid_multi_codes,
        "unique_candidate_breakdowns":{k:dict(sorted(v.items())) for k,v in unique_by_original_ln.items()},
        "sample_multiple_ubs_sense_candidates":multi_examples,
        "sample_original_lexical_headword_no_ln_correspondence":no_code_examples,
        "sample_missing_original_ubs_lexical_headword":no_entry_examples,
        "sample_original_ubs_headword_ambiguity":ambiguous_examples,
        "original_index_and_corpus_modified":False,
        "lexical_sense_contextually_verified":0,
        "automatic_contextual_lexid_assignments":0,
        "publication_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("index","reviewed","english","french","macula","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    r=audit(read(a.index),read(a.reviewed),read(a.english),read(a.french),a.macula)
    a.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_UBS_CONTEXTUAL_SENSE_CANDIDATE_CORPUS_CENSUS",json.dumps({
        "original_word_ids":r["original_word_ids"],
        "headword_provenance":r["distinct_original_word_headword_provenance"],
        "sense_dispositions":r["original_word_sense_candidate_outcomes"],
        "original_multi_ln":r["original_word_ids_with_multiple_MACULA_LN_codes"],
        "unique_lexid_multiple_source_codes":r["unique_UBS_LEXID_but_multiple_source_codes"],
        "sample_multi":r["sample_multiple_ubs_sense_candidates"][:8],
        "sample_missing_ln":r["sample_original_lexical_headword_no_ln_correspondence"][:8],
        "approved_contextual_lexids":0,"published":False
    },ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
