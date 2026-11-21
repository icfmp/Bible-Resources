#!/usr/bin/env python3
"""Audit whether UBS Greek reference word positions align with MACULA ordinals.

Pure source diagnostic: never equate token positions by assumption. Compare
original 14-digit UBS LEXReferences against pinned original MACULA SBLGNT
word ordinals, calibrated over all 122,504 independently source-unique UBS
LEXID candidates and separately over all 2,728 ambiguous words. Report
both matches and mismatches. No contextual editorial choices are made.
"""
from __future__ import annotations
import argparse
import json
import re
import runpy
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCES=runpy.run_path(str(HERE/"audit_ubs_source_verse_witnesses.py"))
WORD_RE=re.compile(r"^.+!(\d+)$")
DIGITS=re.compile(r"^\d{14}$")
FACTORS=(1,2,3,4)


def locators(original_ref):
    match=WORD_RE.fullmatch(original_ref)
    if match is None:raise ValueError("Original Greek verse token ordinal missing")
    ordinal=int(match.group(1))
    verse=SOURCES["verse_key"](original_ref)
    if not 0<ordinal<25000:raise ValueError("Invalid original Greek token ordinal")
    return verse,{f:f"{verse}{f*ordinal:05d}" for f in FACTORS}


def source_refs(records):
    result={}
    for entry in records:
        mid=entry["MainId"]
        senses={}
        for base in entry.get("BaseForms") or []:
            for sense in base.get("LEXMeanings") or []:
                sid=sense.get("LEXID")
                if sid in senses:raise ValueError("Duplicated UBS source LEXID")
                raw=sense.get("LEXReferences")
                if not isinstance(raw,list) or any(not isinstance(v,str) for v in raw):
                    raise ValueError("Original UBS source references malformed")
                senses[sid]={"ln":sense.get("LEXEntryCode"),
                             "valid":set(v for v in raw if DIGITS.fullmatch(v)),
                             "bad":sorted(set(v for v in raw if not DIGITS.fullmatch(v)))}
        if mid in result:raise ValueError("Duplicated original UBS lexical headword")
        result[mid]=senses
    return result


def audit(high,batches,en,fr):
    if (high.get("provisional_source_supported_original_word_count")!=122504
        or high.get("contextual_senses_independently_verified")!=0
        or high.get("published") is not False
        or batches.get("original_multi_sense_word_count")!=2728
        or batches.get("contextually_verified")!=0
        or batches.get("published") is not False
        or high.get("source_editions")!=batches.get("source_editions")):
        raise ValueError("Original source-pinned lexical candidate inventory drift")
    accepted=high["word_id_to_provisional_ubs_lexid"]
    if len(accepted)!=122504:raise ValueError("Missing source-unique word-ID inventory")
    e=source_refs(en);f=source_refs(fr)
    if set(e)!=set(f) or len(e)!=5507:
        raise ValueError("Original UBS Greek source EN/FR headword parity drift")
    matches=Counter()
    per_book=defaultdict(Counter)
    failures=Counter()
    sample=defaultdict(list)
    for wid,word in accepted.items():
        mid=word["ubs_original_main_id"]
        sid=word["ubs_original_lexid"]
        if sid not in e[mid] or sid not in f[mid]:
            raise ValueError("Original high-confidence UBS LEXID disappeared")
        x,y=e[mid][sid],f[mid][sid]
        if x["ln"]!=y["ln"]:
            raise ValueError("Original UBS source sense code bilingual drift")
        book=word["original_reference"].split(" ",1)[0]
        verse,predicted=locators(word["original_reference"])
        if x["bad"] or y["bad"]:
            failures["nonstandard_UBS_source_reference"]+=1
            per_book[book]["nonstandard_UBS_source_reference"]+=1
            continue
        if x["valid"]!=y["valid"]:
            failures["nonidentical_UBS_source_reference_lists"]+=1
            per_book[book]["nonidentical_UBS_source_reference_lists"]+=1
            continue
        per_book[book]["source_unique_candidate_words"]+=1
        for factor,pred in predicted.items():
            if pred in x["valid"]:
                matches[factor]+=1
                per_book[book][f"factor_{factor}_exact_source_position_match"]+=1
                if len(sample[f"factor_{factor}"])<12:
                    sample[f"factor_{factor}"].append({
                        "original_word_id":wid,"original_reference":word["original_reference"],
                        "original_UBS_main_id":mid,"original_UBS_lexid":sid,
                        "authentic_UBS_reference_locator":pred})
    ambiguous={}
    patterns=Counter()
    if len(matches)>len(FACTORS):raise ValueError("Invalid reference calibration")
    for batch in batches["review_batches"]:
        mid=batch["ubs_main_id"]
        candidates=batch["candidate_ubs_lexids"]
        if not set(candidates).issubset(e[mid]) or not set(candidates).issubset(f[mid]):
            raise ValueError("Original ambiguous UBS sense candidate source missing")
        for word in batch["word_id_evidence"]:
            wid=word["original_word_id"]
            if wid in ambiguous or wid in accepted:
                raise ValueError("Original source word IDs overlap or duplicate")
            verse,pred=locators(word["original_reference"])
            conditions={}
            for factor,predicted in pred.items():
                candidate_ids=[]
                source_anomaly=False
                for sid in candidates:
                    x,y=e[mid][sid],f[mid][sid]
                    if x["ln"]!=y["ln"] or x["bad"] or y["bad"] or x["valid"]!=y["valid"]:
                        source_anomaly=True
                        break
                    if predicted in x["valid"]:candidate_ids.append(sid)
                status=("source_metadata_anomaly" if source_anomaly else
                        "unique_exact_source_position_candidate" if len(candidate_ids)==1 else
                        "multiple_exact_source_position_candidates" if len(candidate_ids)>1 else
                        "no_exact_source_position_candidate")
                conditions[str(factor)]={"status":status,"source_lexid_candidates":sorted(candidate_ids)}
                patterns[(factor,status)]+=1
            ambiguous[wid]={
                "original_word_id":wid,"original_reference":word["original_reference"],
                "original_lemma":word["original_lemma"],
                "original_strong":word["original_strong"],
                "original_ln":word["original_ln"],
                "original_class":word["original_class"],
                "original_morph":word["original_morph"],
                "ubs_original_main_id":mid,
                "all_original_candidate_lexids":sorted(set(candidates)),
                "source_position_match_diagnostics":conditions,
            }
    if len(ambiguous)!=2728:raise ValueError("Original 2728-word candidate census incomplete")
    return {
        "status":"PRIVATE_Greek_UBS_LexReferences_original_token_ordinal_alignment_DIAGNOSTIC_ONLY",
        "source_editions":high["source_editions"],
        "original_source_unique_sense_calibration_words":len(accepted),
        "source_unique_words_with_comparable_reference_metadata":sum(
            v["source_unique_candidate_words"] for v in per_book.values()),
        "calibration_matches_by_exact_UBS_to_MACULA_position_factor":dict(sorted(matches.items())),
        "calibration_source_reference_anomalies":dict(sorted(failures.items())),
        "calibration_by_original_book":{k:dict(v) for k,v in sorted(per_book.items())},
        "original_ambiguous_words":2728,
        "candidate_position_patterns":{f"factor_{factor}_{status}":n for (factor,status),n in sorted(patterns.items())},
        "word_id_to_candidate_position_diagnostics":dict(sorted(ambiguous.items())),
        "sample_calibration_matches":dict(sample),
        "new_editorial_source_senses_selected":0,
        "no_automatic_word_position_equivalence_asserted":True,
        "original_sources_modified":False,
        "published":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("high","batches","english","french","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    load=lambda f:json.loads(f.read_text(encoding="utf-8-sig"))
    out=audit(load(a.high),load(a.batches),load(a.english),load(a.french))
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,
                                  separators=(",",":"))+"\n",encoding="utf-8")
    print("UBS_GREEK_ORIGINAL_LEXREFERENCES_TOKEN_POSITION_CALIBRATION",json.dumps({
        "calibration_words":out["original_source_unique_sense_calibration_words"],
        "comparable":out["source_unique_words_with_comparable_reference_metadata"],
        "by_factor":out["calibration_matches_by_exact_UBS_to_MACULA_position_factor"],
        "ambiguous_patterns":out["candidate_position_patterns"],
        "selected":0,"published":False},sort_keys=True))


if __name__=="__main__":main()
