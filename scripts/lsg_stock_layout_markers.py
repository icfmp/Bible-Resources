#!/usr/bin/env python3
"""Observe original OSIS and compiled SWORD structural layout markers.

The compiler may turn container elements into sID/eID milestones or attach
interverse layout material to verse-zero introductions. Count actual
structural *starts* and explicit end milestones, per canonical book.
This is a read-only diagnostic, not pixel-level or editorial approval.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import os
import subprocess
import tempfile

from lsg_osis_parity import OSIS
from lsg_stock_lemma_parity import _books, ordered_lemma_reader_plan
from pilot_preflight import PilotError


MARKERS=("p","title","lg","q")
FIELDS=tuple(field for tag in MARKERS
             for field in (tag+"_starts", tag+"_ends"))


def compare_compiled_layout_marker_rows(
    candidate: Path, reader_plan: list[tuple[str,str,str]], rows: list[str]
) -> dict:
    """Compare authored structure after accounting for SWORD intro entries."""
    books=_books(candidate)
    book_ids=[node.get("osisID") for node in books]
    if not reader_plan or len(rows)!=len(reader_plan):
        raise PilotError("Incomplete stock SWORD layout entry inventory")
    source_totals={}
    for book in books:
        counts=Counter()
        for node in book.iter():
            if not isinstance(node.tag,str) or not node.tag.startswith(OSIS):
                continue
            name=node.tag[len(OSIS):]
            if name not in MARKERS:
                continue
            if node.get("sID") is not None and node.get("eID") is not None:
                raise PilotError("Malformed source OSIS layout milestone")
            counts[name+("_ends" if node.get("eID") is not None else "_starts")]+=1
        source_totals[book.get("osisID")]=counts
    compiled=defaultdict(Counter)
    for line,(expected_key,book,intro) in zip(rows,reader_plan):
        parts=line.split("\t")
        if len(parts)!=10 or parts[0]!=book or parts[1]!=expected_key:
            raise PilotError("SWORD layout inspector returned wrong canonical entry")
        if book not in source_totals:
            raise PilotError("Unexpected compiled layout book ID")
        try:
            values=[int(v) for v in parts[2:]]
        except ValueError as exc:
            raise PilotError("Malformed compiled SWORD layout count") from exc
        if any(n<0 or n>5000 for n in values):
            raise PilotError("Out-of-bounds compiled SWORD layout count")
        compiled[book].update(dict(zip(FIELDS,values)))
    diffs=[]
    exact_starts=0
    exact_end_milestones=0
    source_summary=Counter()
    compiled_summary=Counter()
    for book in book_ids:
        src=source_totals[book]
        target=compiled[book]
        source_summary.update(src)
        compiled_summary.update(target)
        starts_ok=all(src[t+"_starts"]==target[t+"_starts"] for t in MARKERS)
        ends_ok=all(src[t+"_ends"]==target[t+"_ends"] for t in MARKERS)
        exact_starts+=starts_ok
        exact_end_milestones+=ends_ok
        if not (starts_ok and ends_ok) and len(diffs)<66:
            diffs.append({
                "book":book,
                "source_layout_marker_counts":{k:int(src[k]) for k in FIELDS},
                "compiled_layout_marker_counts":{k:int(target[k]) for k in FIELDS},
            })
    return {
        "status":("compiled_source_layout_start_marker_counts_match"
                  if exact_starts==len(book_ids) else
                  "compiled_source_layout_start_markers_need_review"),
        "books_compared":len(book_ids),
        "books_matching_all_logical_layout_starts":exact_starts,
        "books_matching_all_explicit_end_milestones":exact_end_milestones,
        "source_global_layout_marker_counts":{k:int(source_summary[k]) for k in FIELDS},
        "compiled_global_layout_marker_counts":{k:int(compiled_summary[k]) for k in FIELDS},
        "first_books_with_layout_marker_differences":diffs,
        "actual_paragraph_content_and_boundaries_verified":False,
        "actual_poetry_group_semantic_placement_verified":False,
        "frontend_visual_rendering_verified":False,
        "source_modified":False,
        "published":False,
    }


def audit_compiled_layout_markers(
    candidate: Path, aliases: list[tuple[str,str]], *,
    sword_root: Path, module_id: str, inspector: Path
) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Stable SWORD layout inspector executable missing")
    plan,_books_in_source_order=ordered_lemma_reader_plan(candidate,aliases)
    with tempfile.TemporaryDirectory(prefix="stock-layout-markers-") as tmp:
        root=Path(tmp)
        refs=root/"reader-entries.tsv"
        output=root/"layout-counts.tsv"
        refs.write_text("".join("\t".join(row)+"\n" for row in plan),
                        encoding="utf-8")
        try:
            process=subprocess.run(
                [str(inspector),module_id,str(refs),str(output),
                 "--layout-markers-only"],
                env=dict(os.environ,SWORD_PATH=str(sword_root)),
                capture_output=True,text=True,timeout=180,check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Stock SWORD layout marker inspection timed out") from exc
        if (process.returncode or process.stderr or process.stdout
                or not output.is_file()
                or output.stat().st_size>5_000_000):
            raise PilotError(
                f"Stock SWORD layout marker inspector failed (exit {process.returncode})")
        rows=output.read_text(encoding="utf-8").splitlines()
        result=compare_compiled_layout_marker_rows(candidate,plan,rows)
    result["reader_entries_inspected"]=len(plan)
    return result
