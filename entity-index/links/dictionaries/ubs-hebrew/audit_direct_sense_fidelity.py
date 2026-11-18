#!/usr/bin/env python3
"""Audit whether original WLC SDBH tokens truly refer to matching UBS senses.

Crucial: identical 15-digit IDs across editions need not preserve lexeme
identity. Never change the biblical corpus, original source annotations, or
dictionary entries. This tool reports evidence only.
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
WLC_STRONG = re.compile(r"^([0-9]+)([a-z]?)$")
LEX = re.compile(r"^[0-9]{15}$")

def inspect(index, dictionary, source):
    sense_entry = defaultdict(set)
    by_id = {}
    by_lemma = defaultdict(set)
    for e in dictionary:
        mid=e["MainId"]
        by_id[mid]=e
        by_lemma[unicodedata.normalize("NFC",e["Lemma"])].add(mid)
        for f in e.get("BaseForms") or []:
            for meaning in f.get("LEXMeanings") or []:
                sense_entry[str(meaning["LEXID"])].add(mid)
    direct_rows=Counter()
    by_reason=Counter()
    by_class=defaultdict(Counter)
    by_source_strong=defaultdict(Counter)
    by_ubs_id=defaultdict(Counter)
    witnesses={}
    samples=defaultdict(list)
    with Path(source).open(encoding="utf-8-sig", newline="") as stream:
        rd=csv.DictReader(stream,delimiter="\t")
        for row in rd:
            sid=row["sdbh"].strip()
            if not LEX.fullmatch(sid) or sid not in sense_entry:
                continue
            ids=sense_entry[sid]
            direct_rows["exact_id_matches"]+=1
            if len(ids)!=1:
                by_reason["multiple_ubs_owners"]+=1
                continue
            mid=next(iter(ids))
            entry=by_id[mid]
            lemma_match=unicodedata.normalize("NFC",row["lemma"])==unicodedata.normalize("NFC",entry["Lemma"])
            source_strong=WLC_STRONG.fullmatch(row["strongnumberx"].strip())
            strong_numeric=False
            strong_exact=False
            for raw in entry.get("StrongCodes") or []:
                match=STRONG.fullmatch(str(raw))
                if not match or not source_strong or match.group(1)!=row["lang"]:
                    continue
                if int(match.group(2))==int(source_strong.group(1)):
                    strong_numeric=True
                    if match.group(3)==source_strong.group(2):
                        strong_exact=True
            kind=("same_lemma" if lemma_match else "different_lemma")
            if strong_exact:kind+="_exact_strong"
            elif strong_numeric:kind+="_same_strong_base_only"
            else:kind+="_different_strong"
            by_reason[kind]+=1
            by_class[row["class"]][kind]+=1
            by_source_strong[row["strongnumberx"]][kind]+=1
            by_ubs_id[mid][kind]+=1
            if len(samples[kind])<12:
                samples[kind].append({
                    "original_word_id":row["xml:id"],"original_ref":row["ref"],
                    "macula_lemma":row["lemma"],"macula_strong":row["strongnumberx"],
                    "macula_sdbh":sid,"macula_lang":row["lang"],"macula_class":row["class"],
                    "ubs_entry":mid,"ubs_lemma":entry["Lemma"],
                    "ubs_strong_codes":entry.get("StrongCodes") or []
                })
    if sum(by_reason.values())!=direct_rows["exact_id_matches"]:
        raise AssertionError("Audit did not classify every exact SDBH match")
    contradictory=["different_lemma_different_strong",
                   "different_lemma_same_strong_base_only",
                   "different_lemma_exact_strong"]
    wrong_by_source=Counter()
    for strong,count in by_source_strong.items():
        wrong_by_source[strong]=sum(count.get(k,0) for k in contradictory)
    return {
       "policy":"read_only_original_sense_id_identity_crosscheck",
       "totals":dict(direct_rows),
       "classification":dict(by_reason),
       "by_macula_original_class":{k:dict(v) for k,v in sorted(by_class.items())},
       "top_contradictory_macula_strong":[{"code":s,"rows":n} for s,n in wrong_by_source.most_common(30) if n],
       "examples":dict(samples),
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("index","english","macula","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    report=inspect(json.loads(a.index.read_text()),json.loads(a.english.read_text()),a.macula)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    for name in ("totals","classification","top_contradictory_macula_strong","examples"):
        print("SDBH_ID_INTEGRITY",name,json.dumps(report[name],ensure_ascii=False)[:16000])

if __name__=="__main__":
    main()
