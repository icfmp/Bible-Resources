#!/usr/bin/env python3
"""Flag potential editorial problems; NEVER rewrite content automatically."""
import argparse,json,re
from pathlib import Path

def audit(text):
    findings=[]
    for i,line in enumerate(text.splitlines(),1):
        stripped=line.strip()
        if re.search(r"\*\*.{150,}\*\*",stripped):
            findings.append({"line":i,"type":"long_bold_paragraph"})
        chars=[c for c in stripped if c.isalpha()]
        if len(chars)>75 and sum(c.isupper() for c in chars)/len(chars)>0.8:
            findings.append({"line":i,"type":"all_caps_block"})
    verse_lines=sum(bool(re.match(r"^\s*>\s*(?:\*\*)?[0-9¹²³⁴⁵⁶⁷⁸⁹⁰]+",s)) for s in text.splitlines())
    if verse_lines>=5:
        findings.append({"line":0,"type":"scripture_block_candidate","count":verse_lines})
    return findings

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("file",type=Path);a=p.parse_args()
    print(json.dumps(audit(a.file.read_text(encoding="utf-8")),ensure_ascii=False,indent=2))
