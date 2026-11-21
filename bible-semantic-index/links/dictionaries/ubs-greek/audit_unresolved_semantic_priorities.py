#!/usr/bin/env python3
"""Prioritize Greek UBS contextual sense exceptions using original lexeme inventories.

Source-only diagnosis for the 15,237 original word-ID contextual
exceptions. Distinguish MACULA's *blank LN* from nonblank LN that does
not occur under the original independently supported UBS headword.
A sole UBS lexical sense without corroborating original MACULA LN is
only a possible lower-confidence editorial review target; NEVER
automatically accepted as a contextual interpretation.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def source_lexids(records):
    entries={}
    for entry in records:
        mids=defaultdict(set)
        for form in entry.get("BaseForms") or []:
            for m in form.get("LEXMeanings") or []:
                if not isinstance(m.get("LEXID"),str) or not m["LEXID"]:
                    raise ValueError("Original UBS Greek LEXID missing")
                if not isinstance(m.get("LEXEntryCode"),str):
                    raise ValueError("Original UBS Greek Louw–Nida code malformed")
                mids[m["LEXID"]].add(m["LEXEntryCode"])
        if entry["MainId"] in entries:
            raise ValueError("Duplicate original Greek UBS lexical MainId")
        entries[entry["MainId"]]=dict(mids)
    return entries

def audit(unresolved,en,fr):
    if (unresolved.get("status")!="PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review"
        or unresolved.get("unresolved_original_word_count")!=15237
        or unresolved.get("contextual_senses_independently_verified")!=0
        or unresolved.get("published") is not False
        or unresolved.get("public_release_approved") is not False):
        raise ValueError("Source Greek unresolved word-specific sense report drift")
    left=unresolved["word_id_to_unresolved_original_source_evidence"]
    if len(left)!=15237:
        raise ValueError("Greek original word-ID unresolved inventory incomplete")
    e=source_lexids(en);f=source_lexids(fr)
    if e!=f or len(e)!=5507:
        raise ValueError("Original UBS Greek EN/FR LEXID/code inventory drift")
    counts=Counter()
    by_lemma=defaultdict(Counter)
    sample=defaultdict(list)
    for wid,word in left.items():
        status=word["editorial_status"]
        mids=word["source_original_ubs_main_id_candidates"]
        ln=word["original_ln"].split()
        if status=="no_original_ln_matching_ubs_lexical_sense":
            if len(mids)!=1 or word["source_ubs_lexid_candidate_pairs"]:
                raise ValueError("Greek unmatched-LN source word-ID report contradicts raw source")
            lexical=e[mids[0]]
            if not ln:
                source="blank_MACULA_original_LN"
            else:
                source="nonblank_MACULA_LN_not_attested_under_UBS_headword"
            if not lexical:
                shape="no_original_UBS_lexical_senses"
            elif len(lexical)==1:
                shape="exactly_one_original_UBS_LEXID_without_matching_word_LN_NOT_APPROVED"
            else:
                shape="multiple_original_UBS_LEXIDs_without_matching_word_LN"
            status=source+"__"+shape
        elif status=="multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated":
            if len(mids)!=1 or len({x["original_ubs_lexid"] for x in word["source_ubs_lexid_candidate_pairs"]})<2:
                raise ValueError("Greek original multi-LEXID candidate evidence drift")
        elif status=="no_ubs_headword":
            if mids:raise ValueError("Greek missing original UBS lexeme source has MainId candidates")
        elif status=="multiple_original_ubs_lexical_headwords":
            if len(mids)<2:raise ValueError("Greek original Strong ambiguity source lost candidates")
        else:
            raise ValueError("Unexpected Greek original semantic status: "+status)
        counts[status]+=1
        by_lemma[status][word["original_lemma"]]+=1
        if len(sample[status])<10:
            sample[status].append({"original_word_id":wid,"original_lemma":word["original_lemma"],
                                   "original_LN":word["original_ln"],"original_reference":word["original_reference"],
                                   "source_lexeme_candidates":mids})
    if sum(counts.values())!=15237:
        raise ValueError("Original Greek sense exception partition incomplete")
    return {
        "status":"PRIVATE_source_review_Greek_15237_semantic_exceptions_diagnostics_ONLY",
        "all_original_unresolved_words":15237,
        "source_categories":dict(sorted(counts.items())),
        "most_frequent_original_lexeme_families":{
            s:[{"original_lemma":lemma,"original_word_ids":n}
               for lemma,n in sorted(rows.items(),key=lambda t:(-t[1],t[0]))[:25]]
            for s,rows in sorted(by_lemma.items())},
        "source_example_word_ids":dict(sorted(sample.items())),
        "provisional_new_lexids_selected":0,
        "contextual_senses_independently_verified":0,
        "original_UBS_or_MACULA_modified":False,
        "published":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("unresolved","english","french","output"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    load=lambda q:json.loads(q.read_text(encoding="utf-8-sig"))
    x=audit(load(a.unresolved),load(a.english),load(a.french))
    a.output.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_UBS_REMAINING_SOURCE_SENSE_CATEGORY_DIAGNOSTICS",json.dumps({
        "counts":x["source_categories"],
        "top_families":{k:v[:8] for k,v in x["most_frequent_original_lexeme_families"].items()},
        "new_approved":0,"published":False},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
