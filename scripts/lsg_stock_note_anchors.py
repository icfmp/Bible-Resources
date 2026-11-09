#!/usr/bin/env python3
"""Verify SWORD note word offsets, conservatively separating interverse markup.

The original OSIS note source/word index is compared to actual stock SWORD
raw <note> and <w> positions. Entries with compiler-attached interverse words
or explicitly merged verse IDs are never auto-approved as exact anchors.
No Scripture or note text enters the diagnostic output.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import os
import subprocess
import tempfile

from lxml import etree

from lsg_note_parity import _collect_osis
from lsg_osis_parity import OSIS
from lsg_stock_lemma_parity import ordered_lemma_reader_plan
from pilot_preflight import PilotError


def read_anchor_rows(rows: list[str], reader_plan: list[tuple[str,str,str]]) -> dict:
    if len(rows)!=len(reader_plan):
        raise PilotError("Stock SWORD note anchor reader traversal incomplete")
    found={}
    for line,(query,book,_is_intro) in zip(rows,reader_plan):
        parts=line.split("\t")
        if len(parts)!=4 or parts[0]!=book or parts[1]!=query:
            raise PilotError("Stock note offsets were returned for wrong reader key")
        try:
            words=int(parts[2])
            anchors=[int(x) for x in parts[3].split(",")] if parts[3] else []
        except ValueError as exc:
            raise PilotError("Malformed stock SWORD note word offset") from exc
        if (words<0 or words>5000 or any(a<0 or a>words for a in anchors)
            or len(anchors)>100):
            raise PilotError("Out-of-range note or word offsets in reader entry")
        if (book,query) in found:
            raise PilotError("Repeated compiled SWORD note anchor entry")
        found[(book,query)]=(words,anchors)
    return found


def compare_note_anchors(candidate: Path, aliases: list[tuple[str,str]],
                         decisions: list[dict], expected: dict,
                         rows: list[str]) -> dict:
    plan,books=ordered_lemma_reader_plan(candidate,aliases)
    compiled=read_anchor_rows(rows,plan)
    doc=etree.parse(str(candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    source,outside=_collect_osis(doc)
    aliases_by_ref=dict(aliases)
    reassign={}
    for decision in decisions:
        origin=decision["osis_source_key"]
        reader=decision["osis_reader_key"]
        if origin in reassign or reader not in aliases_by_ref:
            raise PilotError("Unsupported note anchor remapping")
        reassign[origin]=reader
    expected_anchors=defaultdict(list)
    for osis_ref,notes in source.items():
        target=reassign.get(osis_ref,osis_ref)
        if target not in aliases_by_ref:
            raise PilotError("Unmapped source note anchor reference")
        key=(target.split(".",1)[0],aliases_by_ref[target])
        expected_anchors[key].extend(n["word_index"] for n in notes)
    source_note_count=sum(len(v) for v in expected_anchors.values())
    verified=unresolved=hard_mismatch=0
    unresolved_cases=[]
    violations=[]
    checked_entries=0
    grouped_with_notes=0
    merged_reader_keys={(dst.split(".",1)[0],aliases_by_ref[dst])
                        for dst in reassign.values()}
    for osis_ref,query in aliases:
        key=(osis_ref.split(".",1)[0],query)
        if key not in compiled:
            raise PilotError("SWORD lexical anchor reader key unavailable")
        reader_words,reader_notes=compiled[key]
        source_words=expected[osis_ref]["w"]
        if source_words<0:
            raise PilotError("Invalid expected word-tag count for anchor")
        external=reader_words-source_words
        if external<0:
            raise PilotError("SWORD note anchor reader dropped original word tags")
        original_notes=expected_anchors.get(key,[])
        checked_entries+=1
        if len(original_notes)!=len(reader_notes):
            hard_mismatch+=max(len(original_notes),len(reader_notes))
            if len(violations)<60:
                violations.append({
                    "reader_ref":osis_ref,
                    "issue":"note_count_or_reader_key_mismatch",
                    "source_notes":len(original_notes),
                    "compiled_notes":len(reader_notes)})
            continue
        if original_notes:
            grouped_with_notes+=1
        for ordinal,(s,t) in enumerate(zip(original_notes,reader_notes),1):
            if external or key in merged_reader_keys:
                unresolved+=1
                if len(unresolved_cases)<60:
                    unresolved_cases.append({
                        "reader_ref":osis_ref,
                        "note_ordinal":ordinal,
                        "source_word_offset":s,
                        "compiled_word_offset":t,
                        "interverse_word_tags_in_reader":external,
                        "owner_approved_merged_reader_key":key in merged_reader_keys,
                    })
            elif s==t:
                verified+=1
            else:
                hard_mismatch+=1
                if len(violations)<60:
                    violations.append({
                        "reader_ref":osis_ref,
                        "note_ordinal":ordinal,
                        "source_word_offset":s,
                        "compiled_word_offset":t,
                        "issue":"unexpected_note_word_position_change"})
    ordinary_reader_locations={
        (ref.split(".",1)[0],q) for ref,q in aliases}
    extra_notes=sum(len(anchors) for location,(_words,anchors)
                    in compiled.items() if location not in ordinary_reader_locations)
    if outside or extra_notes:
        hard_mismatch+=outside+extra_notes
    complete=(hard_mismatch==0 and verified+unresolved==source_note_count)
    return {
        "status":("ordinary_reader_note_word_anchors_verified_with_reviewed_exceptions"
                  if complete else "blocked_unexplained_note_word_anchor_shift"),
        "ordinary_reader_entries_checked":checked_entries,
        "source_note_count":source_note_count,
        "notes_with_verified_exact_intra_verse_word_offset":verified,
        "notes_in_interverse_or_explicitly_merged_keys_needing_review":unresolved,
        "unexpected_note_anchor_or_count_mismatches":hard_mismatch,
        "first_unresolved_note_word_offsets":unresolved_cases,
        "first_unexplained_note_word_offsets":violations,
        "source_notes_outside_verses":outside,
        "note_rich_markup_placement_verified":False,
        "published":False,
    }


def audit_compiled_note_anchors(candidate: Path, aliases: list[tuple[str,str]],
                                decisions: list[dict], expected: dict, *,
                                sword_root: Path, module_id: str,
                                inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Compiled SWORD note-word-offset tool is missing")
    plan,_=ordered_lemma_reader_plan(candidate,aliases)
    with tempfile.TemporaryDirectory(prefix="note-anchors-") as tmp:
        root=Path(tmp)
        refs=root/"refs.tsv"
        records=root/"offsets.tsv"
        refs.write_text("".join("\t".join(row)+"\n" for row in plan),
                        encoding="utf-8")
        try:
            proc=subprocess.run([str(inspector),module_id,str(refs),
                                 str(records),"--note-word-anchors-only"],
                                env=dict(os.environ,SWORD_PATH=str(sword_root)),
                                capture_output=True,text=True,timeout=180,check=False)
        except subprocess.TimeoutExpired:
            return {"status":"note_anchor_probe_timeout","published":False}
        if proc.returncode or proc.stderr or proc.stdout or not records.is_file():
            return {"status":"note_anchor_probe_failed","exit_code":proc.returncode,
                    "stderr_bytes":len(proc.stderr),"published":False}
        if records.stat().st_size>4_000_000:
            raise PilotError("SWORD note word-offset diagnostic exceeds maximum size")
        rows=records.read_text(encoding="utf-8").splitlines()
        report=compare_note_anchors(candidate,aliases,decisions,expected,rows)
    report["reader_entries_inspected"]=len(plan)
    return report
