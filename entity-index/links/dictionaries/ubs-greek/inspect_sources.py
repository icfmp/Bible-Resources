#!/usr/bin/env python3
"""Read-only schema inventory for pinned UBS Greek bilingual linking."""
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

def shape(obj, depth=2):
    if depth == 0:
        return type(obj).__name__
    if isinstance(obj, dict):
        return {k: shape(v, depth-1) for k,v in list(obj.items())[:25]}
    if isinstance(obj, list):
        return {"length": len(obj), "first": shape(obj[0], depth-1) if obj else None}
    if isinstance(obj, str):
        return obj[:110]
    return obj

def inspect_ubs(path):
    raw=path.read_bytes()
    d=json.loads(raw)
    print("UBS_FILE",path.name,"size",len(raw),"sha256",hashlib.sha256(raw).hexdigest())
    print("UBS_ROOT",json.dumps(shape(d,3),ensure_ascii=False)[:5000])
    if isinstance(d,list):
        for i,row in enumerate(d[:4]):
            print("UBS_SAMPLE",i,json.dumps(shape(row,4),ensure_ascii=False)[:2700])
    elif isinstance(d,dict):
        for k,v in list(d.items())[:5]:
            print("UBS_TOP_KEY",k,type(v).__name__,len(v) if hasattr(v,"__len__") else "")
            if isinstance(v,list):
                for row in v[:2]:
                    print("UBS_SAMPLE",k,json.dumps(shape(row,4),ensure_ascii=False)[:2800])

def inspect_macula(path):
    print("MACULA_FILE",path.name)
    with path.open(encoding="utf-8-sig",newline="") as f:
        r=csv.reader(f,delimiter="\t")
        header=next(r)
        print("MACULA_HEADER",json.dumps(header,ensure_ascii=False))
        for i,row in zip(range(3),r):
            print("MACULA_SAMPLE",i,json.dumps(dict(zip(header,row)),ensure_ascii=False)[:3000])

if __name__=="__main__":
    inspect_ubs(Path(sys.argv[1]))
    inspect_ubs(Path(sys.argv[2]))
    inspect_macula(Path(sys.argv[3]))
