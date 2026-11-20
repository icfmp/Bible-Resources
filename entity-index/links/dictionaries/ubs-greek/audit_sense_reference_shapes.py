#!/usr/bin/env python3
"""Audit original UBS Greek LEXReferences shapes for future contextual matching.

Read the pinned Greek EN/FR source and the full 2,728-word private source
review register. Inventory only reference metadata (not dictionary prose);
no cross-resource verse mapping or semantic LEXID is inferred.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def describe(value):
    if value is None:return {"type":"null"}
    if isinstance(value,list):
        kinds=Counter(type(v).__name__ for v in value)
        samples=[]
        for item in value[:2]:
            if isinstance(item,dict):
                samples.append({"dict_keys":sorted(item)})
            elif isinstance(item,str):
                samples.append({"string_sample":item[:90]})
            else:
                samples.append({"value_type":type(item).__name__})
        return {"type":"list","length":len(value),"item_types":dict(kinds),"sample_shapes":samples}
    if isinstance(value,dict):
        return {"type":"dict","keys":sorted(value)}
    return {"type":type(value).__name__,"sample":str(value)[:90]}


def audit(batches,en,fr):
    if (batches.get("status")!="PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET"
        or batches.get("original_multi_sense_word_count")!=2728
        or batches.get("contextually_verified")!=0
        or batches.get("published") is not False):
        raise ValueError("Private original Greek ambiguity evidence drift")
    candidates=defaultdict(set)
    original_lemmas=Counter()
    seen_word_ids=set()
    for batch in batches["review_batches"]:
        mid=batch["ubs_main_id"]
        if not isinstance(mid,str) or not mid or not batch["candidate_ubs_lexids"]:
            raise ValueError("Invalid original UBS source headword/sense batch")
        for w in batch["word_id_evidence"]:
            wid=w["original_word_id"]
            if wid in seen_word_ids:
                raise ValueError("Duplicate original Greek word ID")
            seen_word_ids.add(wid)
        for sid in batch["candidate_ubs_lexids"]:
            candidates[mid].add(sid)
        original_lemmas[(batch["original_lemma"],mid)]+=len(batch["word_id_evidence"])
    if len(seen_word_ids)!=2728 or not candidates:
        raise ValueError("Incomplete original Greek UBS source review inventory")
    inventories={}
    for language,records in (("en",en),("fr",fr)):
        matched={}
        for entry in records:
            mid=entry.get("MainId")
            if mid not in candidates:continue
            senses={}
            for form in entry.get("BaseForms") or []:
                for meaning in form.get("LEXMeanings") or []:
                    sid=meaning.get("LEXID")
                    if sid not in candidates[mid]:continue
                    if sid in senses:raise ValueError("Duplicated source UBS sense ID")
                    senses[sid]={
                        "source_ln":meaning.get("LEXEntryCode"),
                        "source_reference_shape":describe(meaning.get("LEXReferences")),
                    }
            if set(senses)!=candidates[mid]:
                raise ValueError("Missing UBS original sense reference evidence")
            matched[mid]=senses
        if set(matched)!=set(candidates):
            raise ValueError("Missing UBS original Greek MainId")
        inventories[language]=matched
    mismatches=[]
    shape_counts=Counter()
    for mid in sorted(candidates):
        for sid in sorted(candidates[mid]):
            e=inventories["en"][mid][sid]
            f=inventories["fr"][mid][sid]
            if e["source_ln"]!=f["source_ln"]:
                raise ValueError("Original bilingual UBS Louw-Nida differs")
            e_shape=e["source_reference_shape"]
            f_shape=f["source_reference_shape"]
            shape_counts[f"{e_shape['type']}/{f_shape['type']}"]+=1
            if e_shape!=f_shape and len(mismatches)<30:
                mismatches.append({"mid":mid,"lexid":sid,"english":e_shape,"french":f_shape})
    priority=sorted(original_lemmas.items(),key=lambda x:(-x[1],x[0]))[:25]
    preview=[]
    for (lemma,mid),word_count in priority:
        preview.append({
            "original_lemma":lemma,"ubs_main_id":mid,"original_word_count":word_count,
            "candidate_senses":[{
                "lexid":sid,
                "original_ln":inventories["en"][mid][sid]["source_ln"],
                "english_reference_shape":inventories["en"][mid][sid]["source_reference_shape"],
                "french_reference_shape":inventories["fr"][mid][sid]["source_reference_shape"],
            } for sid in sorted(candidates[mid])],
        })
    return {
        "status":"PRIVATE_original_UBS_Greek_sense_reference_metadata_diagnostic_ONLY",
        "source_editions":batches["source_editions"],
        "original_multivalent_words":2728,
        "original_ubs_headwords_inspected":len(candidates),
        "distinct_candidate_ubs_lexids":sum(map(len,candidates.values())),
        "reference_shape_counts":dict(sorted(shape_counts.items())),
        "bilingual_reference_metadata_discrepancy_count":sum(
            inventories["en"][mid][sid]["source_reference_shape"]!=inventories["fr"][mid][sid]["source_reference_shape"]
            for mid in candidates for sid in candidates[mid]),
        "bilingual_reference_metadata_discrepancy_examples":mismatches,
        "highest_volume_original_lemma_reference_shapes":preview,
        "contextual_senses_selected":0,
        "source_modified":False,
        "published":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("batches","english","french","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    r=audit(read(a.batches),read(a.english),read(a.french))
    a.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_UBS_ORIGINAL_LEXREFERENCES_STRUCTURE",json.dumps({
        "headwords":r["original_ubs_headwords_inspected"],
        "source_senses":r["distinct_candidate_ubs_lexids"],
        "reference_shapes":r["reference_shape_counts"],
        "bilingual_discrepancies":r["bilingual_reference_metadata_discrepancy_count"],
        "selected":0,"published":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
