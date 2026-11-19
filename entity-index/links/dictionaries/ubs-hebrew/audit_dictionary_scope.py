#!/usr/bin/env python3
"""Audit non-matches against the *entire* pinned UBS headword inventory.

Distinguish:
- no original Strong family AND no identical/fully consonantal UBS headword
  in the complete edition: outside the *verifiable headword scope*;
- a headword attested under a different Strong family: needs ID review;
- same Strong family but lemma or homograph ambiguity: needs ID review.

This metric never changes a dictionary lookup and does not claim that a
word cannot appear within prose or alternate editorial spellings in UBS.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LEXICAL_CLASSES = frozenset(("noun","verb","adj","adv","num"))
UBS_STRONG = re.compile(r"^([HA])0*([0-9]+)([a-z]?)$")
MACULA_STRONG = re.compile(r"^([0-9]+)([a-z]?)$")


def consonants(value):
    value = unicodedata.normalize("NFD",value)
    return "".join(
        ch for ch in value
        if not unicodedata.combining(ch) or ch in ("\u05c1","\u05c2")
    )


def inventory(english):
    by_family=defaultdict(set)
    by_full_lemma=defaultdict(set)
    by_consonants=defaultdict(set)
    by_id={}
    for entry in english:
        mid=entry["MainId"]
        by_id[mid]=entry
        # Source-authored AlternateLemmas are genuine UBS headword
        # inventory evidence, not inferred spelling. Never exclude a WLC
        # occurrence from denominator merely because it is listed under an
        # official alternate spelling instead of the canonical Lemma.
        attested_forms=[entry["Lemma"],*(entry.get("AlternateLemmas") or [])]
        for attested in attested_forms:
            if not isinstance(attested,str) or not attested:
                continue
            by_full_lemma[unicodedata.normalize("NFC",attested)].add(mid)
            by_consonants[consonants(attested)].add(mid)
        for raw in entry.get("StrongCodes") or []:
            match=UBS_STRONG.fullmatch(str(raw))
            if match:
                by_family[(match.group(1),int(match.group(2)))].add(mid)
    return by_family,by_full_lemma,by_consonants,by_id


def analyze(index, english, macula):
    from runpy import run_path
    lookup_word=run_path(str(Path(__file__).with_name("build_index.py")))["lookup_word"]
    family,exact,plain,ubs=inventory(english)
    summary=Counter()
    by_class=defaultdict(Counter)
    groups=defaultdict(lambda:{"occurrences":0,"examples":[],"ubs_entry_ids":[]})
    with Path(macula).open(encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle,delimiter="\t")
        required={"xml:id","lemma","lang","strongnumberx","sdbh","class","ref"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError("Incomplete original Macula WLC columns")
        for row in reader:
            if row["class"] not in LEXICAL_CLASSES:
                continue
            summary["lexical_source_occurrences"]+=1
            old=lookup_word(index,row["xml:id"],row["sdbh"],row["strongnumberx"],row["lang"],row["lemma"])
            if old["entry_ids"]:
                summary["linked_occurrences"]+=1
                continue
            m=MACULA_STRONG.fullmatch(row["strongnumberx"])
            has_family=bool(m and row["lang"] in ("H","A") and family.get((row["lang"],int(m.group(1)))))
            full=sorted(exact.get(unicodedata.normalize("NFC",row["lemma"]),()))
            consonantal=sorted(plain.get(consonants(row["lemma"]),()))
            if not m or row["lang"] not in ("H","A"):
                group="source_code_unreadable_review"
            elif has_family:
                group="matching_strong_family_unresolved_review"
            elif full:
                group="different_strong_same_exact_headword_review"
            elif consonantal:
                group="different_strong_same_consonants_review"
            else:
                group="no_matching_strong_or_headword_in_ubs_inventory"
            summary[group]+=1
            by_class[row["class"]][group]+=1
            gkey=(group,row["lang"],row["lemma"],row["strongnumberx"])
            grp=groups[gkey]
            grp["occurrences"]+=1
            if len(grp["examples"])<3:
                grp["examples"].append({"word_id":row["xml:id"],"ref":row["ref"],
                    "sdbh":row["sdbh"],"class":row["class"]})
                grp["ubs_entry_ids"]=(full or consonantal)[:12]
    if summary["linked_occurrences"]+sum(summary[k] for k in (
            "source_code_unreadable_review","matching_strong_family_unresolved_review",
            "different_strong_same_exact_headword_review",
            "different_strong_same_consonants_review",
            "no_matching_strong_or_headword_in_ubs_inventory")) != summary["lexical_source_occurrences"]:
        raise AssertionError("Loss of original WLC occurrences")
    excluded=summary["no_matching_strong_or_headword_in_ubs_inventory"]
    denominator=summary["lexical_source_occurrences"]-excluded
    summary["outside_indexed_ubs_headword_scope"]=excluded
    summary["indexable_scope_denominator"]=denominator
    summary["indexable_scope_unresolved"]=denominator-summary["linked_occurrences"]
    summary["indexable_scope_coverage_pct"]=(round(100*summary["linked_occurrences"]/denominator,3) if denominator else None)
    summary["all_source_lexical_coverage_pct"]=round(100*summary["linked_occurrences"]/summary["lexical_source_occurrences"],3)
    ranked=sorted(({"reason":key[0],"language":key[1],"lemma":key[2],
                    "strong":key[3],"occurrences":val["occurrences"],
                    "example_words":val["examples"],"ubs_headword_candidates":val["ubs_entry_ids"]}
                   for key,val in groups.items()),key=lambda v:(-v["occurrences"],v["language"],v["lemma"]))
    return {"policy":"absence_means_no_matching_ubs_strong_and_no_exact_or_shin_sin_preserving_consonantal_indexed_canonical_or_alternate_lemma_anywhere",
            "dictionary_edition":"UBS Hebrew 0.9.4","scope_notice":"headword_inventory_only_not_dictionary_prose_or_semantic_completeness",
            "summary":dict(summary),
            "by_source_class":{k:dict(v) for k,v in sorted(by_class.items())},
            "top_groups":ranked[:70]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("index","english","macula","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    result=analyze(json.loads(a.index.read_text(encoding="utf-8")),
                   json.loads(a.english.read_text(encoding="utf-8")),a.macula)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("UBS_SCOPE_COUNTS",json.dumps(result["summary"],ensure_ascii=False,sort_keys=True))
    print("UBS_SCOPE_CLASS",json.dumps(result["by_source_class"],ensure_ascii=False,sort_keys=True))
    for entry in result["top_groups"][:30]:
        print("UBS_SCOPE_TOP",json.dumps(entry,ensure_ascii=False))

if __name__=="__main__":
    main()
