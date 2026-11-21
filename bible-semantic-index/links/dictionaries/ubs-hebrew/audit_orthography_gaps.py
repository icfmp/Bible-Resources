#!/usr/bin/env python3
"""Investigate unresolved WLC content words with conservative Hebrew spelling evidence.

Read-only: normalized spellings are *candidate evidence*, never validated
lexical identity; do not silently change any dictionary lookup.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

STRONG = re.compile(r"^([HA])0*([0-9]+)([a-z]?)$")
MACULA = re.compile(r"^([0-9]+)([a-z]?)$")
CLASSES = {"noun","verb","adj","adv","num"}

def consonants(text):
    # Hebrew vowel points and cantillation are meaningful: stripping is
    # *only* to triage and must never authorize a lexical ID on its own.
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))

def analyze(index, entries, source):
    from runpy import run_path
    build = run_path(str(Path(__file__).with_name("build_index.py")))
    lookup_word = build["lookup_word"]
    lexical = defaultdict(set)
    for entry in entries:
        for raw in entry.get("StrongCodes") or []:
            m = STRONG.fullmatch(str(raw))
            if m:
                lexical[(m.group(1),int(m.group(2)))].add(entry["MainId"])
    by_id={e["MainId"]:e for e in entries}
    groups=defaultdict(lambda:{"rows":0,"source_codes":Counter(),"source_sdbh":Counter(),"examples":[],"candidates":[]})
    buckets=Counter()
    by_class=defaultdict(Counter)
    for row in csv.DictReader(Path(source).open(encoding="utf-8-sig",newline=""),delimiter="\t"):
        if row["class"] not in CLASSES:
            continue
        existing=lookup_word(index,row["xml:id"],row["sdbh"],row["strongnumberx"],row["lang"],row["lemma"])
        if existing["entry_ids"]:
            continue
        m=MACULA.fullmatch(row["strongnumberx"])
        if not m or row["lang"] not in ("H","A"):
            category="missing_or_complex_original_strong"
            members=[]
        else:
            ids=sorted(lexical.get((row["lang"],int(m.group(1))),[]))
            if not ids:
                category="no_same_strong_family_in_ubs"
                members=[]
            else:
                unpointed=consonants(row["lemma"])
                members=[mid for mid in ids if consonants(by_id[mid]["Lemma"]) == unpointed]
                if len(members)==1:
                    category="single_consonantal_match_REVIEW_ONLY"
                elif len(members)>1:
                    category="multiple_consonantal_matches_REVIEW_ONLY"
                else:
                    category="different_consonants_same_strong_family"
        buckets[category]+=1
        by_class[row["class"]][category]+=1
        key=(category,row["lang"],row["lemma"],row["strongnumberx"],tuple(members))
        g=groups[key];g["rows"]+=1
        if row["sdbh"]:g["source_sdbh"][row["sdbh"]]+=1
        if len(g["examples"])<3:
            g["examples"].append({"id":row["xml:id"],"ref":row["ref"],"class":row["class"],
                                  "source_lemma":row["lemma"],"source_strong":row["strongnumberx"],
                                  "source_sdbh":row["sdbh"],
                                  "ubs_candidates":[{"id":mid,"lemma":by_id[mid]["Lemma"],
                                                      "strong":by_id[mid]["StrongCodes"]} for mid in members[:4]]})
    ranked=sorted(({"category":k[0],"language":k[1],"lemma":k[2],"strong":k[3],
                    "ids":list(k[4]),"rows":v["rows"],"sdbh":v["source_sdbh"].most_common(3),
                    "examples":v["examples"]} for k,v in groups.items()),
                  key=lambda x:(-x["rows"],x["language"],x["lemma"]))
    return {"total_unmatched":sum(buckets.values()),"by_reason":dict(buckets),
            "by_class":{key:dict(value) for key,value in by_class.items()},
            "distinct_groups":len(ranked),"top_groups":ranked[:80]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("index","english","macula","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    result=analyze(json.loads(a.index.read_text(encoding="utf-8")),
                   json.loads(a.english.read_text(encoding="utf-8")),a.macula)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ORTHOGRAPHY_GAP_COUNTS",json.dumps(result["by_reason"],ensure_ascii=False))
    print("ORTHOGRAPHY_GAP_BY_CLASS",json.dumps(result["by_class"],ensure_ascii=False))
    for item in result["top_groups"][:35]:
        print("ORTHOGRAPHY_GAP_TOP",json.dumps(item,ensure_ascii=False))

if __name__=="__main__":
    main()
