#!/usr/bin/env python3
"""Quantify high-confidence *candidates* for UBS Strong split/merge reconciliation.

Never rewrite the MACULA code or pretend UBS suffix and source code are equal.
Independent evidence requires: exact NFC Hebrew lemma, same Strong numeric stem,
same H/A language, and only one UBS lexical MainId for that combination.
All results are proposals for review, not accepted contextual sense mappings.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

UBS_CODE = re.compile(r"^([HA])0*([0-9]+)([a-z]?)$")
MACULA_CODE = re.compile(r"^([0-9]+)([a-z]?)$")
LEXICAL = {"noun","verb","adj","adv","num"}


def build_candidates(dictionary):
    entries={}
    by_joint=defaultdict(set)
    family_codes=defaultdict(set)
    for entry in dictionary:
        mid=entry["MainId"]
        entries[mid]=entry
        lemma=unicodedata.normalize("NFC",entry["Lemma"])
        for raw in entry.get("StrongCodes") or []:
            m=UBS_CODE.fullmatch(str(raw))
            if not m: continue
            joint=(m.group(1),int(m.group(2)),lemma)
            by_joint[joint].add(mid)
            family_codes[joint].add(raw)
    return entries,by_joint,family_codes


def analyze(index,dictionary,macula):
    from runpy import run_path
    lookup=run_path(str(Path(__file__).with_name("build_index.py")))["lookup"]
    entries,by_joint,family_codes=build_candidates(dictionary)
    counts=Counter()
    groups=defaultdict(lambda:{"occurrences":0,"word_ids":[],"source_strongs":Counter(),
                                 "classes":Counter(),"sdbh":Counter()})
    eligible_status=Counter()
    rejected_examples=[]
    with Path(macula).open(encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream,delimiter="\t"):
            if row["class"] not in LEXICAL:continue
            status=lookup(index,row["sdbh"],row["strongnumberx"],row["lang"])
            if status["entry_ids"]:continue
            counts["unresolved_lexical_rows"]+=1
            m=MACULA_CODE.fullmatch(row["strongnumberx"])
            if not m or row["lang"] not in ("H","A"):
                counts["unsupported_source_strong"]+=1
                continue
            lemma=unicodedata.normalize("NFC",row["lemma"])
            key=(row["lang"],int(m.group(1)),lemma)
            ids=by_joint.get(key,set())
            if not ids:
                counts["no_exact_joint_evidence"]+=1
                continue
            if len(ids)!=1:
                counts["ambiguous_joint_evidence"]+=1
                if len(rejected_examples)<15:
                    rejected_examples.append({"original_word_id":row["xml:id"],
                        "source_strong":row["strongnumberx"],"lemma":row["lemma"],
                        "candidate_ids":sorted(ids)})
                continue
            only=next(iter(ids))
            codes=family_codes[key]
            exact_code=f"{row['lang']}{int(m.group(1))}{m.group(2)}"
            if any((lambda x: x and (int(x.group(2)),x.group(3)) ==
                    (int(m.group(1)),m.group(2)))(UBS_CODE.fullmatch(c)) for c in codes):
                # There should already be an exact lookup. If not, audit bug.
                raise AssertionError("Unexpected already exact Strong match: "+exact_code)
            counts["dual_evidence_candidate_occurrences"]+=1
            if m.group(2) and any(not UBS_CODE.fullmatch(c).group(3) for c in codes):
                eligible_status["macula_suffixed_ubs_unsuffixed"]+=1
            elif not m.group(2) and any(UBS_CODE.fullmatch(c).group(3) for c in codes):
                eligible_status["macula_unsuffixed_ubs_suffixed"]+=1
            else:
                eligible_status["different_ubs_suffix"]+=1
            g=groups[key]
            g["occurrences"]+=1
            g["source_strongs"][row["strongnumberx"]]+=1
            g["classes"][row["class"]]+=1
            if row["sdbh"]:g["sdbh"][row["sdbh"]]+=1
            if len(g["word_ids"])<4:
                g["word_ids"].append({"word_id":row["xml:id"],"ref":row["ref"],
                                     "lemma":row["lemma"],"strong":row["strongnumberx"],
                                     "sdbh":row["sdbh"],"morph":row["morph"]})
    ranked=[]
    for (lang,num,lemma),g in groups.items():
        key=(lang,num,lemma)
        only=next(iter(by_joint[key]))
        ranked.append({
            "language":lang,"lemma":lemma,"strong_numeric_family":num,
            "ubs_main_id":only,"ubs_lemma":entries[only]["Lemma"],
            "ubs_exact_strong_codes":sorted(family_codes[key]),
            "macula_exact_strong_codes":g["source_strongs"].most_common(),
            "occurrences":g["occurrences"],"source_classes":dict(g["classes"]),
            "source_sdbh":g["sdbh"].most_common(5),
            "examples":g["word_ids"],
            "verification_state":"candidate_only_not_accepted_link",
        })
    ranked.sort(key=lambda x:(-x["occurrences"],x["language"],x["lemma"],x["strong_numeric_family"]))
    if sum(x["occurrences"] for x in ranked)!=counts["dual_evidence_candidate_occurrences"]:
        raise AssertionError("Candidate token conservation failed")
    return {"counts":dict(counts),"patterns":dict(eligible_status),
            "distinct_candidate_lexemes":len(ranked),
            "top_10_candidate_tokens":sum(x["occurrences"] for x in ranked[:10]),
            "rejected_ambiguous_examples":rejected_examples,
            "candidates":ranked}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for a in ("index","english","macula","output"):
        p.add_argument("--"+a,type=Path,required=True)
    a=p.parse_args()
    data=analyze(json.loads(a.index.read_text()),json.loads(a.english.read_text()),a.macula)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STRONG_RECONCILIATION_COUNTS",json.dumps(data["counts"],ensure_ascii=False))
    print("STRONG_RECONCILIATION_PATTERNS",json.dumps(data["patterns"],ensure_ascii=False))
    print("STRONG_RECONCILIATION_LEXEMES",data["distinct_candidate_lexemes"])
    for row in data["candidates"][:30]:
        print("STRONG_RECONCILIATION_TOP",json.dumps(row,ensure_ascii=False))


if __name__=="__main__":
    main()
