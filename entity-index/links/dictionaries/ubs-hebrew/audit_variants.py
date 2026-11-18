#!/usr/bin/env python3
"""Read-only diagnosis of the dominant unresolved MACULA Hebrew suffix families.

Group by exact source code, morphology/class, SDBH coverage and parent-code
availability. Inspect one word per family. Do not infer links from the stem.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

def analyze(index, lexicon, tsv, expected_rows=None):
    from runpy import run_path
    lookup=run_path(str(Path(__file__).with_name("build_index.py")))["lookup"]
    by_base=defaultdict(set)
    by_main={}
    for e in lexicon:
        by_main[e["MainId"]]=e
        for code in e.get("StrongCodes") or []:
            if len(code)>2 and code[0] in ("H","A"):
                digits="".join(ch for ch in code[1:] if ch.isdigit())
                if digits:
                    by_base[(code[0],int(digits))].add(e["MainId"])
    aggregate=defaultdict(lambda:{"rows":0,"classes":Counter(),"morph":Counter(),
      "lemmas":Counter(),"sdbh_populated":0,"prefix_in_ubs":0,"base_in_ubs":0,
      "samples":[]})
    overall=Counter()
    by_class=defaultdict(Counter)
    by_morph=defaultdict(Counter)
    by_language=defaultdict(Counter)
    with Path(tsv).open(encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream,delimiter="\t"):
            r=lookup(index,row["sdbh"],row["strongnumberx"],row["lang"])
            status="sense" if r["sense_ids"] else ("entry_only" if r["entry_ids"] else "unresolved")
            by_class[row["class"]][status]+=1
            by_morph[row["morph"][:2]][status]+=1
            by_language[row["lang"]][status]+=1
            if r["entry_ids"]:
                continue
            code=row["strongnumberx"]
            if not (code and code[-1:].islower() and code[:-1].isdigit()):
                continue
            lang=row["lang"]
            if lang not in ("H","A"):
                continue
            key=lang+code
            a=aggregate[key]
            a["rows"]+=1
            a["classes"][row["class"]]+=1
            a["morph"][row["morph"][:3]]+=1
            a["lemmas"][row["lemma"]]+=1
            if row["sdbh"]:
                a["sdbh_populated"]+=1
            parent=(row["sdbh"][:6]+"000000000") if len(row["sdbh"])==15 and row["sdbh"].isdigit() else None
            if parent in by_main:
                a["prefix_in_ubs"]+=1
            base_candidates=by_base.get((lang,int(code[:-1])),set())
            if base_candidates:
                a["base_in_ubs"]+=1
            if len(a["samples"])<2:
                a["samples"].append({
                  "id":row["xml:id"],"reference":row["ref"],"word":row["text"],
                  "lemma":row["lemma"],"class":row["class"],"morph":row["morph"],
                  "sdbh":row["sdbh"],"parent_entry_id":parent if parent in by_main else None,
                  "base_ubs_entries":sorted(base_candidates)[:5],
                  "base_ubs_lemmas":[by_main[x]["Lemma"] for x in sorted(base_candidates)[:5]],
                })
            overall["unmatched_suffix_rows"]+=1
    top=[]
    for code,a in sorted(aggregate.items(),key=lambda x:(-x[1]["rows"],x[0]))[:40]:
        top.append({"source_strong":code,"rows":a["rows"],
          "classes":a["classes"].most_common(5),
          "morph":a["morph"].most_common(5),
          "lemmas":a["lemmas"].most_common(4),
          "sdbh_populated":a["sdbh_populated"],"parent_in_ubs":a["prefix_in_ubs"],
          "base_ubs_exists":a["base_in_ubs"],"examples":a["samples"]})
    # Editorially transparent reporting subset, NOT a new matching policy.
    lexical_classes=("noun","verb","adj","adv","num")
    lexical_senses=sum(by_class[x]["sense"] for x in lexical_classes)
    lexical_entries=sum(by_class[x]["entry_only"] for x in lexical_classes)
    lexical_unresolved=sum(by_class[x]["unresolved"] for x in lexical_classes)
    lexical_total=lexical_senses+lexical_entries+lexical_unresolved
    corpus_total=sum(sum(counts.values()) for counts in by_class.values())
    if expected_rows is not None and corpus_total != expected_rows:
        raise ValueError(f"Source corpus size mismatch: {corpus_total} != {expected_rows}")
    lexical_coverage={
        "selected_source_classes":list(lexical_classes),
        "total":lexical_total, "exact_sense":lexical_senses,
        "entry_only":lexical_entries,
        "unresolved":lexical_unresolved,
        "with_ubs_entry":lexical_senses+lexical_entries,
        "percentage":round(100*(lexical_senses+lexical_entries)/lexical_total,2),
        "interpretation":"source_class_subset_not_a_word_type_or_dictionary_completeness_claim",
    }
    return {"summary":dict(overall),"distinct_suffix_families":len(aggregate),
        "lexical_class_coverage":lexical_coverage,
        "by_original_class":{k:dict(v) for k,v in sorted(by_class.items())},
        "by_morph_prefix":{k:dict(v) for k,v in sorted(by_morph.items())},
        "by_original_language":{k:dict(v) for k,v in sorted(by_language.items())},
        "families":top}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--index",required=True,type=Path)
    p.add_argument("--english",required=True,type=Path)
    p.add_argument("--macula",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--expected-rows",type=int)
    a=p.parse_args()
    result=analyze(json.loads(a.index.read_text()),json.loads(a.english.read_text()),a.macula,a.expected_rows)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("VARIANT_TOTAL",result["summary"])
    print("VARIANT_DISTINCT_FAMILIES",result["distinct_suffix_families"])
    print("LEXICAL_CLASS_COVERAGE",json.dumps(result["lexical_class_coverage"],ensure_ascii=False))
    print("COVERAGE_BY_ORIGINAL_CLASS",json.dumps(result["by_original_class"],ensure_ascii=False))
    print("COVERAGE_BY_MORPH_PREFIX",json.dumps(result["by_morph_prefix"],ensure_ascii=False))
    print("COVERAGE_BY_ORIGINAL_LANGUAGE",json.dumps(result["by_original_language"],ensure_ascii=False))
    for row in result["families"][:20]:
        print("VARIANT_FAMILY",json.dumps(row,ensure_ascii=False))
if __name__=="__main__":
    main()
