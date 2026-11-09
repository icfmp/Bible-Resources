#!/usr/bin/env python3
"""Compare semantic XML start/end boundaries with real compiled SWORD markup.

For p/title/lg/q, represent each original source element as an ordered
opening or closing event at the absolute index in its book-wide <w> sequence.
Accept standard OSIS sID/eID milestone representation, but do not assume that
the SWORD compiler preserved an XML closing boundary merely because all
opening markers survived. The compiler probe exposes no Scripture or notes;
the published report contains counts, numeric offsets and book IDs only.

This diagnostic does NOT approve punctuation/whitespace positions, nested
attribute values or visual rendering. It intentionally stays separate from
the independently verified all-start-position and 705728 lexical gates.
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

KINDS=("p", "title", "lg", "q")
_EVENT=re.compile(r"^([+-])(p|title|lg|q):([0-9]+)$")


def source_book_boundary_events(book) -> tuple[int,list[tuple[str,str,int]]]:
    """Read both normal XML containers and SWORD-compatible OSIS milestones."""
    words=0
    events=[]
    for action,element in etree.iterwalk(book, events=("start", "end")):
        if not isinstance(element.tag,str):
            continue
        if element.tag==OSIS+"w" and action=="start":
            words+=1
            continue
        if not element.tag.startswith(OSIS):
            continue
        name=element.tag[len(OSIS):]
        if name=="div" and element.get("type") in ("x-p", "paragraph"):
            name="p"
        if name not in KINDS:
            continue
        sid=element.get("sID")
        eid=element.get("eID")
        if sid is not None and eid is not None:
            raise PilotError("Source layout boundary has both sID and eID")
        if sid is not None or eid is not None:
            if action=="start":
                events.append(("+" if sid is not None else "-",name,words))
        else:
            events.append(("+" if action=="start" else "-",name,words))
    return words,events


def compare_compiled_layout_boundaries(
    candidate:Path, reader_plan:list[tuple[str,str,str]], rows:list[str]
) -> dict:
    books=_books(candidate)
    ids=[book.get("osisID") for book in books]
    if not reader_plan or len(rows)!=len(reader_plan):
        raise PilotError("Stock SWORD layout boundary audit requires every reader entry")
    words_compiled=defaultdict(int)
    events_compiled=defaultdict(list)
    for row,(expected_key,book,_intro) in zip(rows,reader_plan):
        cols=row.split("\t")
        if len(cols)!=4 or cols[:2]!=[book,expected_key] or book not in ids:
            raise PilotError("Unexpected stock SWORD layout boundary reader key")
        try:
            count=int(cols[2])
        except ValueError as exc:
            raise PilotError("Invalid compiled layout boundary word count") from exc
        if count<0 or count>5000:
            raise PilotError("Compiled layout boundary word count outside range")
        prefix=words_compiled[book]
        raw_events=cols[3].split(",") if cols[3] else []
        if len(raw_events)>5000:
            raise PilotError("Excessive layout boundary events in SWORD entry")
        for raw in raw_events:
            match=_EVENT.fullmatch(raw)
            if match is None:
                raise PilotError("Malformed stock SWORD layout boundary event")
            local=int(match.group(3))
            if local>count:
                raise PilotError("Stock SWORD layout boundary event outside word stream")
            events_compiled[book].append((match.group(1),match.group(2),prefix+local))
        words_compiled[book]+=count
    total_source=Counter()
    total_compiled=Counter()
    all_exact=0
    starts_exact=0
    ends_exact=0
    word_differences=[]
    boundary_differences=[]
    for book in books:
        name=book.get("osisID")
        word_count,expected=source_book_boundary_events(book)
        actual=events_compiled[name]
        if word_count!=words_compiled[name] and len(word_differences)<66:
            word_differences.append({
                "book":name,
                "source_word_tags":word_count,
                "compiled_word_tags":words_compiled[name],
            })
        source_starts=[v for v in expected if v[0]=="+"]
        compiled_starts=[v for v in actual if v[0]=="+"]
        source_ends=[v for v in expected if v[0]=="-"]
        compiled_ends=[v for v in actual if v[0]=="-"]
        for sign,kind,_ in expected:
            total_source[sign+kind]+=1
        for sign,kind,_ in actual:
            total_compiled[sign+kind]+=1
        starts_equal=source_starts==compiled_starts
        ends_equal=source_ends==compiled_ends
        starts_exact+=starts_equal
        ends_exact+=ends_equal
        all_exact+=expected==actual and word_count==words_compiled[name]
        if (expected!=actual or word_count!=words_compiled[name]) and len(boundary_differences)<66:
            # The first ordinal is safe to report without exporting XML text.
            ordinal=next((i+1 for i,(a,b) in enumerate(zip(expected,actual))
                          if a!=b),min(len(expected),len(actual))+1)
            end_ordinal=next((i+1 for i,(a,b) in enumerate(zip(source_ends,compiled_ends))
                              if a!=b),min(len(source_ends),len(compiled_ends))+1)
            boundary_differences.append({
                "book":name,
                "source_event_count":len(expected),
                "compiled_event_count":len(actual),
                "source_start_count":len(source_starts),
                "compiled_start_count":len(compiled_starts),
                "source_end_count":len(source_ends),
                "compiled_end_count":len(compiled_ends),
                "first_different_boundary_ordinal":ordinal,
                "first_different_closing_ordinal":end_ordinal,
                "source_end_at_first_difference":(
                    {"kind":source_ends[end_ordinal-1][1],
                     "book_word_offset":source_ends[end_ordinal-1][2]}
                    if end_ordinal<=len(source_ends) else None),
                "compiled_end_at_first_difference":(
                    {"kind":compiled_ends[end_ordinal-1][1],
                     "book_word_offset":compiled_ends[end_ordinal-1][2]}
                    if end_ordinal<=len(compiled_ends) else None),
            })
    exact=all_exact==len(books) and not word_differences
    return {
        "status":("compiled_book_global_layout_boundaries_verified"
                  if exact else "compiled_layout_boundaries_need_review"),
        "books_compared":len(books),
        "books_with_exact_full_boundary_order":all_exact,
        "books_with_exact_all_opening_events":starts_exact,
        "books_with_exact_all_closing_events":ends_exact,
        "source_global_boundary_counts":dict(sorted(total_source.items())),
        "compiled_global_boundary_counts":dict(sorted(total_compiled.items())),
        "first_books_with_word_count_differences":word_differences,
        "first_books_with_boundary_differences":boundary_differences,
        "punctuation_whitespace_and_attribute_placement_verified":False,
        "frontend_rendering_verified":False,
        "source_modified":False,
        "published":False,
    }


def audit_compiled_layout_boundaries(
    candidate:Path, aliases:list[tuple[str,str]], *,
    sword_root:Path,module_id:str,inspector:Path
) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Compiled layout boundary inspector not available")
    plan,_books_in_source_order=ordered_lemma_reader_plan(candidate,aliases)
    with tempfile.TemporaryDirectory(prefix="stock-layout-boundaries-") as tmp:
        root=Path(tmp)
        refs=root/"reader-keys.tsv"
        output=root/"boundary-offsets.tsv"
        refs.write_text("".join("\t".join(item)+"\n" for item in plan),
                        encoding="utf-8")
        try:
            proc=subprocess.run(
                [str(inspector),module_id,str(refs),str(output),
                 "--layout-boundary-word-positions-only"],
                env=dict(os.environ,SWORD_PATH=str(sword_root)),
                capture_output=True,text=True,timeout=200,check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Stable SWORD layout boundary probe timed out") from exc
        if (proc.returncode or proc.stderr or proc.stdout or not output.is_file()
                or output.stat().st_size>8_000_000):
            raise PilotError(
                f"Stable SWORD layout boundary probe rejected entry ({proc.returncode})")
        result=compare_compiled_layout_boundaries(
            candidate,plan,output.read_text(encoding="utf-8").splitlines())
    result["reader_entries_inspected"]=len(plan)
    return result
