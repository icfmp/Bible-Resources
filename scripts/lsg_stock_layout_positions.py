#!/usr/bin/env python3
"""Text-free position audit for compiled SWORD layout-start boundaries.

Counts of <p>, <title>, <lg>, and <q> tags are insufficient to establish
placement. Compare every source layout *start* against its position in the
full canonical book-wide ordered <w> stream, including verse-zero entries.
This tolerates SWORD moving interverse XML to a neighboring VerseKey, not
source-content loss or relocation to a different place in the word stream.

Report only book IDs, marker categories, counts and numeric word offsets.
Does not approve textual punctuation/whitespace positioning, end boundaries,
title hierarchy or visual renderer behavior.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import os
import re
import subprocess
import tempfile

from lxml import etree

from lsg_osis_parity import OSIS
from lsg_stock_lemma_parity import _books, ordered_lemma_reader_plan
from pilot_preflight import PilotError

MARKERS=("p","title","lg","q")
_EVENT=re.compile(r"^(p|title|lg|q):([0-9]+)$")


def _source_book_starts(book) -> tuple[int,dict[str,list[int]],list[tuple[str,int]]]:
    words=0
    starts={tag:[] for tag in MARKERS}
    ordered=[]
    for action,node in etree.iterwalk(book,events=("start","end")):
        if action!="start" or not isinstance(node.tag,str):
            continue
        if node.tag == OSIS+"w":
            words+=1
            continue
        if not node.tag.startswith(OSIS):
            continue
        name=node.tag[len(OSIS):]
        if name=="div" and node.get("type") in ("x-p","paragraph"):
            name="p"
        if name not in MARKERS:
            continue
        if node.get("sID") is not None and node.get("eID") is not None:
            raise PilotError("Malformed source OSIS layout milestone")
        if node.get("eID") is not None:
            continue
        starts[name].append(words)
        ordered.append((name,words))
    return words,starts,ordered


def compare_compiled_layout_start_positions(
    candidate:Path, reader_plan:list[tuple[str,str,str]],
    rows:list[str],
) -> dict:
    books=_books(candidate)
    known={b.get("osisID") for b in books}
    if not reader_plan or len(rows)!=len(reader_plan):
        raise PilotError("Missing compiled layout position reader entries")
    compiled_words=defaultdict(int)
    compiled_starts=defaultdict(lambda:{tag:[] for tag in MARKERS})
    compiled_order=defaultdict(list)
    for row,(expected_key,book,_intro) in zip(rows,reader_plan):
        cols=row.split("\t")
        if len(cols)!=4 or cols[:2]!=[book,expected_key] or book not in known:
            raise PilotError("Compiled layout start positions returned wrong key")
        try:
            word_count=int(cols[2])
        except ValueError as exc:
            raise PilotError("Invalid compiled layout word count") from exc
        if word_count<0 or word_count>5000:
            raise PilotError("Out-of-range compiled layout word count")
        prefix=compiled_words[book]
        events=cols[3].split(",") if cols[3] else []
        if len(events)>5000:
            raise PilotError("Excessive compiled layout markers in one reader entry")
        for event in events:
            matched=_EVENT.fullmatch(event)
            if not matched:
                raise PilotError("Malformed compiled layout marker position")
            tag=matched.group(1)
            local=int(matched.group(2))
            if local>word_count:
                raise PilotError("Compiled layout start outside reader word stream")
            position=prefix+local
            compiled_starts[book][tag].append(position)
            compiled_order[book].append((tag,position))
        compiled_words[book]+=word_count

    exact_books=0
    exact_by_kind=Counter()
    total_source=Counter()
    total_compiled=Counter()
    word_differences=[]
    marker_differences=[]
    cross_type_order_match=0
    for book in books:
        name=book.get("osisID")
        source_word_count,source_starts,source_order=_source_book_starts(book)
        actual_starts=compiled_starts[name]
        if source_word_count!=compiled_words[name] and len(word_differences)<66:
            word_differences.append({
                "book":name,"source_word_tags":source_word_count,
                "compiled_word_tags":compiled_words[name]})
        all_kinds=True
        for kind in MARKERS:
            source=source_starts[kind]
            actual=actual_starts[kind]
            total_source[kind]+=len(source)
            total_compiled[kind]+=len(actual)
            if source==actual:
                exact_by_kind[kind]+=1
            else:
                all_kinds=False
                if len(marker_differences)<100:
                    first=next((i+1 for i,(a,b) in enumerate(zip(source,actual))
                                if a!=b),min(len(source),len(actual))+1)
                    marker_differences.append({
                        "book":name,"marker":kind,
                        "source_starts":len(source),
                        "compiled_starts":len(actual),
                        "first_different_ordinal":first,
                        "source_word_offset_at_difference":(
                            source[first-1] if first<=len(source) else None),
                        "compiled_word_offset_at_difference":(
                            actual[first-1] if first<=len(actual) else None),
                    })
        exact_books+=all_kinds and source_word_count==compiled_words[name]
        cross_type_order_match+=source_order==compiled_order[name]
    verified=(exact_books==len(books) and not word_differences
              and not marker_differences)
    return {
        "status":("compiled_book_global_layout_start_positions_verified"
                  if verified else "compiled_layout_start_positions_need_review"),
        "books_compared":len(books),
        "books_matching_all_layout_start_word_offsets":exact_books,
        "books_matching_each_kind":{k:int(exact_by_kind[k]) for k in MARKERS},
        "source_layout_starts_by_kind":{k:int(total_source[k]) for k in MARKERS},
        "compiled_layout_starts_by_kind":{k:int(total_compiled[k]) for k in MARKERS},
        "books_matching_full_cross_type_start_order":cross_type_order_match,
        "first_books_with_word_count_differences":word_differences,
        "first_layout_word_offset_differences":marker_differences,
        "end_boundaries_verified":False,
        "punctuation_and_whitespace_relative_position_verified":False,
        "visual_and_typography_rendering_verified":False,
        "source_modified":False,
        "published":False,
    }


def audit_compiled_layout_start_positions(
    candidate:Path, aliases:list[tuple[str,str]], *,
    sword_root:Path, module_id:str, inspector:Path
) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("SWORD layout start-position inspector not found")
    plan,_books_in_order=ordered_lemma_reader_plan(candidate,aliases)
    with tempfile.TemporaryDirectory(prefix="stock-layout-positions-") as tmp:
        root=Path(tmp)
        refs=root/"reader-keys.tsv"
        output=root/"layout-start-offsets.tsv"
        refs.write_text(
            "".join("\t".join(row)+"\n" for row in plan),encoding="utf-8")
        try:
            proc=subprocess.run(
                [str(inspector),module_id,str(refs),str(output),
                 "--layout-start-word-positions-only"],
                env=dict(os.environ,SWORD_PATH=str(sword_root)),
                capture_output=True,text=True,timeout=200,check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("SWORD layout word-offset inspection timed out") from exc
        if (proc.returncode or proc.stderr or proc.stdout
                or not output.is_file() or output.stat().st_size>7_000_000):
            raise PilotError(
                f"SWORD layout word-offset inspector failed ({proc.returncode})")
        rows=output.read_text(encoding="utf-8").splitlines()
        result=compare_compiled_layout_start_positions(candidate,plan,rows)
    result["reader_entries_inspected"]=len(plan)
    return result
