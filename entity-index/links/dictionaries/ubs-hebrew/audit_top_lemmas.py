#!/usr/bin/env python3
"""Full-source investigation of the most frequent unresolved UBS Hebrew lemmas.

No guessing. Compare exact Strong, SDBH prefix, script-only spelling, and
source IDs independently; print candidate evidence but never publish a link.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LEXICAL = {"noun","verb","adj","adv","num"}
TOP = [("H","כֹּל"),("H","אַל"),("H","כֹּה"),("H","קוֹל"),
       ("H","עוֹד"),("H","טוֹב"),("H","רַע"),("H","מְאֹד"),
       ("H","חָטָא"),("H","חוה")]
HEB_MARK = re.compile(r"[\u0591-\u05c7]")

def unpoint(lemma):
    return HEB_MARK.sub("", unicodedata.normalize("NFD", lemma)).replace("ׇ", "")

def collect(dictionary):
    entries={e["MainId"]: e for e in dictionary}
    by_lemma=defaultdict(set)
    by_plain=defaultdict(set)
    by_strong=defaultdict(set)
    by_lex=defaultdict(set)
    for mid,e in entries.items():
        by_lemma[unicodedata.normalize("NFC",e["Lemma"])].add(mid)
        by_plain[unpoint(e["Lemma"])].add(mid)
        for strong in e.get("StrongCodes") or []:
            by_strong[strong].add(mid)
        for form in e.get("BaseForms") or []:
            for meaning in form.get("LEXMeanings") or []:
                by_lex[meaning["LEXID"]].add(mid)
    return entries,by_lemma,by_plain,by_strong,by_lex

def analyze(index,dictionary,macula):
    from runpy import run_path
    lookup=run_path(str(Path(__file__).with_name("build_index.py")))["lookup"]
    entries,by_lemma,by_plain,by_strong,by_lex=collect(dictionary)
    tracked={k:{"occurrences":0,"unmatched_strong":Counter(),
               "sdbh":Counter(),"status":Counter(),"classes":Counter(),
               "examples":[],"ubs_exact_ids":[],"ubs_unpointed_ids":[],
               "ubs_candidates":[]} for k in TOP}
    with Path(macula).open(encoding="utf-8-sig",newline="") as handle:
        for row in csv.DictReader(handle,delimiter="\t"):
            if row["class"] not in LEXICAL: continue
            key=(row["lang"],row["lemma"])
            if key not in tracked: continue
            out=lookup(index,row["sdbh"],row["strongnumberx"],row["lang"])
            if out["entry_ids"]: continue
            x=tracked[key]
            x["occurrences"]+=1
            x["unmatched_strong"][row["strongnumberx"]]+=1
            if row["sdbh"]:x["sdbh"][row["sdbh"]]+=1
            x["status"][out["status"]]+=1
            x["classes"][row["class"]]+=1
            if len(x["examples"])<5:
                x["examples"].append({k:row[k] for k in ("xml:id","ref","lemma","text","class","morph","strongnumberx","sdbh")})
    report=[]
    for lang,lemma in TOP:
        x=tracked[lang,lemma]
        exact=sorted(by_lemma.get(unicodedata.normalize("NFC",lemma),[]))
        stripped=sorted(by_plain.get(unpoint(lemma),[]))
        raw_sdbh=x["sdbh"].most_common(8)
        parent=sorted(set(s[:6]+"000000000" for s in x["sdbh"] if re.fullmatch(r"[0-9]{15}",s)))
        raw_strong=x["unmatched_strong"].most_common(8)
        strong_entries={s:sorted(by_strong.get(lang+s.zfill(4),set()) | by_strong.get(lang+s,set())) for s,_ in raw_strong}
        candidate_ids=set(exact+stripped+parent+sum(strong_entries.values(),[]))
        candidate_rows=[]
        for mid in sorted(candidate_ids):
            e=entries.get(mid)
            if e:
                candidate_rows.append({
                    "main_id":mid,"lemma":e["Lemma"],
                    "strong_codes":e.get("StrongCodes"),
                    "sense_ids":[a["LEXID"] for f in e.get("BaseForms") or [] for a in f.get("LEXMeanings") or []][:8],
                    "provenance":{
                        "same_lemma":mid in exact,
                        "consonantal_only":mid in stripped,
                        "macula_sdbh_parent":mid in parent,
                        "same_strong":any(mid in v for v in strong_entries.values()),
                    }
                })
        report.append({
            "lang":lang,"macula_lemma":lemma,
            "unresolved_occurrences":x["occurrences"],
            "source_strongs":raw_strong,
            "source_sdbh":raw_sdbh,
            "sdbh_parent_candidates":parent,
            "exact_lemma_candidates":exact,
            "unpointed_lemma_candidates":stripped,
            "same_strong_candidates":strong_entries,
            "ubs_candidates":candidate_rows[:25],
            "examples":x["examples"],
            "source_classes":dict(x["classes"]),
            "policy":"candidates_not_verified_no_automatic_link",
        })
    return {"edition":"UBS Hebrew 0.9.4 EN","source":"pinned Macula WLC","top_lemmas":report}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("index","english","macula","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    result=analyze(json.loads(a.index.read_text(encoding="utf-8")),
                   json.loads(a.english.read_text(encoding="utf-8")),a.macula)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in result["top_lemmas"]:
        print("TOP_HEBREW_DIAGNOSTIC",json.dumps(x,ensure_ascii=False)[:13000])

if __name__=="__main__":
    main()
