#!/usr/bin/env python3
"""Inspect pinned UBS Hebrew bilingual schemas and Macula WLC headers only.

Read-only: does not rewrite or relicense upstream sources.
"""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from pathlib import Path

def outline(value, depth=2):
    if depth <= 0:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: outline(item, depth - 1) for key, item in list(value.items())[:30]}
    if isinstance(value, list):
        return {"length": len(value), "first": outline(value[0], depth - 1) if value else None}
    if isinstance(value, str):
        return value[:90]
    return value

def inspect_lexicon(path):
    data = path.read_bytes()
    obj = json.loads(data)
    print("HEBREW_SOURCE", path.name, "sha256", hashlib.sha256(data).hexdigest(), "size", len(data))
    print("HEBREW_ROOT", json.dumps(outline(obj, 3), ensure_ascii=False)[:6000])
    if isinstance(obj, list):
        for index, entry in enumerate(obj[:3]):
            print("HEBREW_ENTRY", index, json.dumps(outline(entry, 5), ensure_ascii=False)[:5000])
    elif isinstance(obj, dict):
        for key, value in list(obj.items())[:5]:
            print("HEBREW_DICT_KEY", key, type(value).__name__)
            if isinstance(value, list):
                for entry in value[:2]:
                    print("HEBREW_ENTRY", key, json.dumps(outline(entry, 5), ensure_ascii=False)[:5000])

def inspect_macula(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows=csv.reader(source, delimiter="\t")
        names=next(rows)
        print("WLC_COLUMNS", json.dumps(names, ensure_ascii=False))
        for n, row in zip(range(5), rows):
            print("WLC_WORD", n, json.dumps(dict(zip(names,row)), ensure_ascii=False)[:3500])

if __name__=="__main__":
    inspect_lexicon(Path(sys.argv[1]))
    inspect_lexicon(Path(sys.argv[2]))
    inspect_macula(Path(sys.argv[3]))
