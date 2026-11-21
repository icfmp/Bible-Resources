#!/usr/bin/env python3
"""Select a bounded, reproducible contextual-review sample from the Hebrew UBS v1.1 audit.

This is a PRIVATE editorial witness pack, not an automatic LEXID assignment.
It includes small original source excerpts only in a temporary private Actions
artifact; do not commit it, publish it, or use it as dictionary distribution.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,runpy
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUDIT=runpy.run_path(str(HERE/"audit_v11_semantic_feasibility.py"))
BUILD=runpy.run_path(str(HERE/"build_index.py"))


def _rank(wid):
    return hashlib.sha256(("hebrew-v11-context-pilot-v1|"+wid).encode()).hexdigest()


def sample(report, english, french, macula):
    if (report["status"] != "PRIVATE_UBS_HEBREW_V11_SOURCE_ONLY_SEMANTIC_FEASIBILITY_AUDIT_NO_CHOICES"
        or report["candidate_word_count"] != 53981
        or report["independently_contextually_validated"] != 0):
        raise ValueError("Not the pinned 53,981-candidate no-choice source audit")
    candidates=report["original_word_id_to_private_verse_witness_candidate"]
    if len(candidates)!=53981:
        raise ValueError("Incomplete word candidate evidence")
    en={e["MainId"]:e for e in english}
    fr={e["MainId"]:e for e in french}
    if len(en)!=7943 or set(en)!=set(fr):
        raise ValueError("UBS Hebrew pinned bilingual headword drift")
    byfamily=defaultdict(list)
    for wid,item in candidates.items():
        byfamily[item["ubs_headword"]].append(wid)
    # Independently seeded reproducible selection across frequency strata.
    families=sorted(byfamily,key=lambda mid:(-len(byfamily[mid]),mid))
    high=families[:12]
    middle=families[len(families)//2-6:len(families)//2+6]
    rare=[mid for mid in families if len(byfamily[mid])<=3][:12]
    family_slots=[("frequent",mid,3) for mid in high]+[
        ("middle",mid,2) for mid in middle]+[
        ("rare",mid,1) for mid in rare]
    chosen=[]
    for tier,mid,n in family_slots:
        ids=sorted(byfamily[mid],key=_rank)
        distinct_books=set()
        kept=[]
        for wid in ids:
            book=wid[1:3]
            if book not in distinct_books:
                distinct_books.add(book)
                kept.append(wid)
                if len(kept)==n:break
        if len(kept)<n:
            kept.extend(w for w in ids if w not in kept)
        for wid in kept[:n]:
            chosen.append((tier,wid))
    if len(chosen)!=72 or len({w for _,w in chosen})!=72:
        raise ValueError("Stratified pilot isn't exactly 72 distinct source words")
    selected={wid for _,wid in chosen}
    byverse=defaultdict(list)
    allseen=set()
    with macula.open(encoding="utf-8-sig",newline="") as handle:
        rows=csv.DictReader(handle,delimiter="\t")
        for row in rows:
            wid=row["xml:id"]
            if wid in allseen: raise ValueError("Repeated original WLC ID")
            allseen.add(wid)
            verse=AUDIT["verse_from_word_id"](wid)
            if any(AUDIT["verse_from_word_id"](candidate)==verse for candidate in selected):
                byverse[verse].append({
                    "word_id":wid,"lemma":row["lemma"],
                    "english":row.get("english",""),
                    "gloss":row.get("gloss",""),
                    "pos":row.get("pos",""),"morph":row.get("morph",""),
                    "class":row["class"],"sdbh":row["sdbh"],
                    "strong":row["strongnumberx"],
                })
    if len(allseen)!=475911:raise ValueError("Original WLC word census drift")
    result=[]
    for tier,wid in chosen:
        item=candidates[wid]
        mid=item["ubs_headword"]
        sid=item["source_candidate_lexid"]
        entries={}
        for language,dictionary in (("en",en),("fr",fr)):
            original=dictionary[mid]
            meanings={str(s["LEXID"]):s for s in BUILD["senses"](original)}
            if sid not in meanings:raise ValueError("Source UBS LEXID vanished")
            selected_sense=meanings[sid]
            # Preserve authentic UBS source fields; no invented glosses or
            # deterministic interpretation. Limit *each* string to 700 chars.
            snippets={}
            for key,value in selected_sense.items():
                if key in ("LEXID","LEXReferences"):continue
                if isinstance(value,str):snippets[key]=value[:700]
                elif isinstance(value,(dict,list)):
                    snippets[key]=json.dumps(value,ensure_ascii=False)[:700]
            other_sense_headers=[]
            for other_id,sense in meanings.items():
                if other_id==sid:continue
                other_sense_headers.append({
                    "lexid":other_id,
                    "source_sense_glosses":[
                        {"glosses":(meaning.get("Glosses") or []),
                         "definition":str(meaning.get("DefinitionShort") or "")[:250]}
                        for meaning in (sense.get("LEXSenses") or [])
                        if isinstance(meaning,dict)
                    ],
                    "source_domains":[x.get("Domain","") for x in
                        (sense.get("LEXDomains") or []) if isinstance(x,dict)],
                    "source_form_constraints":sense.get("LEXForms") or [],
                })
            entries[language]={
                "source_lemma":original["Lemma"],
                "source_alt_lemmas":original.get("AlternateLemmas") or [],
                "source_strong":original.get("StrongCodes") or [],
                "candidate_original_sense_fields":snippets,
                "other_source_senses":other_sense_headers[:12],
                "candidate_original_reference_count":len(selected_sense.get("LEXReferences") or []),
            }
        verse=AUDIT["verse_from_word_id"](wid)
        tokens=byverse[verse]
        matching=[i for i,token in enumerate(tokens) if token["word_id"]==wid]
        if len(matching)!=1:raise ValueError("Original word missing in contextual source verse")
        at=matching[0]
        result.append({
            "tier":tier,"word_id":wid,"macula_reference":item["original_reference"],
            "ubs_headword":mid,"candidate_lexid":sid,
            "all_original_senses":item["all_original_ubs_senses_for_entry"],
            "original_wlc_word":tokens[at],
            "same_verse_source_context":tokens[max(0,at-7):at+8],
            "source_ubs":entries,
            "editorial_approval":False,
            "independently_context_verified":False,
        })
    return {
        "status":"PRIVATE_HEBREW_V11_72_WORD_CONTEXTUAL_REVIEW_SAMPLES_NOT_APPROVED",
        "source_editions":report["source_editions"],
        "selection":"SHA256 word-ID stratified 12 frequent x 3, 12 median x 2, 12 rare x 1",
        "sample_words":len(result),
        "sample_family_count":len({item["ubs_headword"] for item in result}),
        "candidate_population":53981,
        "source_contextual_evidence":result,
        "all_words_independently_contextually_verified":False,
        "candidate_lexids_approved":0,
        "publication_approved":False,
    }


def main():
    p=argparse.ArgumentParser()
    for k in ("audit","english","french","macula","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    load=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    result=sample(load(a.audit),load(a.english),load(a.french),a.macula)
    a.output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("UBS_HEBREW_V11_CONTEXTUAL_PILOT_PRIVATE",json.dumps({
        "source_words":result["sample_words"],"families":result["sample_family_count"],
        "semantic_approvals":0,"published":False}))


if __name__=="__main__":
    main()
