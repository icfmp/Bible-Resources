#!/usr/bin/env python3
"""Audit whether pinned Macula WLC sdbh annotations are exact UBS lexical sense IDs."""
import csv
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

def records(entry):
    for form in entry.get("BaseForms") or []:
        for sense in form.get("LEXMeanings") or []:
            yield sense

en=json.loads(Path(sys.argv[1]).read_text())
fr=json.loads(Path(sys.argv[2]).read_text())
print("EN_FR_ROOT_COUNT", len(en),len(fr))
ena={x["MainId"]:x for x in en}
fra={x["MainId"]:x for x in fr}
print("MAINID_UNIQUENESS",len(ena),len(fra),"shared",len(ena.keys()&fra.keys()))
def sig(r):
    return (r["Lemma"],tuple(r.get("StrongCodes") or []),tuple(sorted((x["LEXID"],str(x.get("LEXEntryCode"))) for x in records(r))))
parity=[k for k in (ena.keys()&fra.keys()) if sig(ena[k])!=sig(fra[k])]
print("BILINGUAL_DRIFT",len(parity),"examples",parity[:12])
for k in parity[:3]:
    print("DRIFT_SAMPLE",k,json.dumps(sig(ena[k]),ensure_ascii=False)[:450],json.dumps(sig(fra[k]),ensure_ascii=False)[:450])
strong=defaultdict(set)
lex=defaultdict(set)
lexcode=defaultdict(set)
for entry in en:
    mid=entry["MainId"]
    for s in entry.get("StrongCodes") or []:
        strong[str(s)].add(mid)
    for x in records(entry):
        lex[str(x["LEXID"])].add(mid)
        lexcode[str(x.get("LEXEntryCode"))].add((mid,x["LEXID"]))
print("UBS_COUNTS",len(strong),len(lex),len(lexcode),"sense_assignments",sum(map(len,lex.values())))
for entry in en[:3]:
    print("UBS_EXAMPLE",entry["MainId"],entry["Lemma"],entry.get("StrongCodes"),[(x["LEXID"],x.get("LEXEntryCode")) for x in list(records(entry))[:4]])
ct=Counter()
unknown=Counter()
samples=[]
with Path(sys.argv[3]).open(encoding="utf-8",newline="") as source:
    for row in csv.DictReader(source,delimiter="\t"):
        ct["rows"]+=1
        sdbh=row.get("sdbh","").strip()
        strongnumber=row.get("strongnumberx","").strip()
        if sdbh:
            ct["sdbh_populated"]+=1
            matches=lex.get(sdbh)
            if matches:
                ct["sdbh_exact_match"]+=1
                if len(matches)>1:ct["sdbh_multi_entry"]+=1
            else:
                unknown[sdbh]+=1
        if strongnumber:
            ct["strong_populated"]+=1
        if len(samples)<10 and sdbh:
            samples.append((row["xml:id"],row["lang"],strongnumber,sdbh,sorted(lex.get(sdbh,[]))))
print("MACULA_COUNTERS",dict(ct))
print("UNKNOWN_SDBH",len(unknown),unknown.most_common(10))
for row in samples:print("WORD_SAMPLE",json.dumps(row,ensure_ascii=False))
