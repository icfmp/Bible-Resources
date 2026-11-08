#!/usr/bin/env python3
"""Verify unfiltered raw SWORD word/note/poetry markers after reviewed merges.

The input and output are original-source verse IDs, tag counts, and hashes,
never Scripture words. This is separate from authorial content/text parity,
note semantic target parity, edition identity, and visual UI checks.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import os
import subprocess
import tempfile

from lxml import etree

from pilot_preflight import PilotError
from lsg_source_compare import scan_usfx
from lsg_sword_compare import chapter_plan
from lsg_osis_parity import _osis_verses, OSIS

def build_stock_markup_plan(source: bytes, candidate: Path,
                            decisions: list[dict]) -> tuple[list[tuple[str, str]],dict,dict]:
    """Return unique *reader* keys and merged expected source tag counts."""
    original,authorial_keys=scan_usfx(source)
    plan=chapter_plan(authorial_keys,full=True)
    tree=etree.parse(str(candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    book_ids=[n.get("osisID") for n in tree.iter(OSIS+"div")
              if n.get("type")=="book"]
    codes=original["original_books"]
    if (len(codes)!=66 or len(book_ids)!=66
        or len(set(codes))!=66 or len(set(book_ids))!=66):
        raise PilotError("Cannot independently align original and OSIS book IDs")
    mapping=dict(zip(codes,book_ids))
    _body,word_entries,notes,lines=_osis_verses(candidate)
    original_keys={f"{mapping[c]}.{ch}.{v}" for c,ch,v in authorial_keys}
    remap={}
    for d in decisions:
        source_ref=d["osis_source_key"]
        dest_ref=d["osis_reader_key"]
        if (source_ref not in original_keys or dest_ref not in original_keys
            or source_ref in remap or source_ref==dest_ref):
            raise PilotError("Invalid approved raw-markup reference merger")
        remap[source_ref]=dest_ref
    compiled_expected=defaultdict(Counter)
    reader_names={}
    for code,ch,verse in authorial_keys:
        original_ref=f"{mapping[code]}.{ch}.{verse}"
        reader_ref=remap.get(original_ref,original_ref)
        target_parts=reader_ref.split(".")
        if target_parts[0]!=mapping[code] or int(target_parts[1])!=ch:
            raise PilotError("Source merger crosses book or chapter in raw audit")
        target_verse=int(target_parts[2])
        query=f"{plan[code][0]} {ch}:{target_verse}"
        prior=reader_names.setdefault(reader_ref,query)
        if prior!=query:
            raise PilotError("Ambiguous SWORD reader alias")
        counts=compiled_expected[reader_ref]
        counts["w"]+=len(word_entries.get(original_ref,()))
        counts["note"]+=notes.get(original_ref,0)
        counts["l"]+=lines.get(original_ref,0)
        counts["verses"]+=1
    if (len(compiled_expected)!=len(original_keys)-len(decisions)
        or any(len([x for x in decisions if x["osis_reader_key"]==k])>1
               for k in compiled_expected)):
        raise PilotError("Compiled reader index does not match authorized merged slots")
    aliases=[(reader_ref,reader_names[reader_ref])
             for reader_ref in sorted(compiled_expected)]
    expected_poetry=Counter()
    for ref,counts in compiled_expected.items():
        expected_poetry[ref.split(".")[0]]+=counts["l"]
    return aliases,compiled_expected,expected_poetry

def compare_raw_rows(rows: list[str], ordered_refs: list[tuple[str,str]],
                     expected: dict, poetry_by_book: dict) -> dict:
    if not ordered_refs or len(rows)!=len(ordered_refs):
        raise PilotError("Compiled raw SWORD inspector skipped or inserted reader keys")
    differences=[]
    source_count=Counter()
    compiled_count=Counter()
    compiled_lines=Counter()
    checked=0
    for line,(osis_ref,query) in zip(rows,ordered_refs):
        cols=line.split("\t")
        if len(cols)!=6 or cols[0]!=query:
            raise PilotError("Raw compiled SWORD row ref does not match requested key")
        try:
            w,n,xref,poetry,q=map(int,cols[1:])
        except (TypeError,ValueError) as exc:
            raise PilotError("Malformed raw SWORD markup counter") from exc
        if any(val<0 or val>5000 for val in (w,n,xref,poetry,q)):
            raise PilotError("Unexpected unfiltered SWORD counter")
        e=expected[osis_ref]
        source_count.update({"word":e["w"],"note":e["note"],"poetry":e["l"]})
        compiled_count.update({"word":w,"note":n,"poetry":poetry,"reference":xref,"q":q})
        compiled_lines[osis_ref.split(".")[0]]+=poetry
        if (w,n)!=(e["w"],e["note"]) and len(differences)<50:
            differences.append({
                "osis_ref":osis_ref,
                "expected_word_tags":e["w"],"compiled_word_tags":w,
                "expected_note_tags":e["note"],"compiled_note_tags":n})
        checked+=1
    # Count every verse by itself, not merely global tag totals.
    per_verse_words_equal=sum(
        1 for line,(osis_ref,_) in zip(rows,ordered_refs)
        if int(line.split("\t")[1])==expected[osis_ref]["w"])
    per_verse_notes_equal=sum(
        1 for line,(osis_ref,_) in zip(rows,ordered_refs)
        if int(line.split("\t")[2])==expected[osis_ref]["note"])
    all_book_names=set(poetry_by_book)|set(compiled_lines)
    poetry_equal=all(compiled_lines[b]==poetry_by_book.get(b,0)
                     for b in all_book_names)
    return {
        "status": ("raw_stock_sword_word_note_poetry_counts_verified"
                   if (per_verse_words_equal==checked and
                       per_verse_notes_equal==checked and poetry_equal)
                   else "blocked_compiled_raw_markup_mismatch"),
        "checked_reader_entries":checked,
        "expected_source_word_tags":source_count["word"],
        "compiled_word_tags":compiled_count["word"],
        "expected_source_note_tags":source_count["note"],
        "compiled_note_tags":compiled_count["note"],
        "expected_source_poetry_line_tags":source_count["poetry"],
        "compiled_poetry_line_tags":compiled_count["poetry"],
        "per_verse_word_tag_matches":per_verse_words_equal,
        "per_verse_note_tag_matches":per_verse_notes_equal,
        "books_with_matching_poetry_line_tags":sum(
            compiled_lines[b]==poetry_by_book.get(b,0) for b in all_book_names),
        "books_compared":len(all_book_names),
        "source_to_compiled_word_tag_counts_verified":per_verse_words_equal==checked,
        "source_to_compiled_note_tag_counts_verified":per_verse_notes_equal==checked,
        "source_to_compiled_poetry_line_counts_verified":poetry_equal,
        "compiled_cross_reference_tag_count":compiled_count["reference"],
        "compiled_q_tag_count":compiled_count["q"],
        "first_mismatches":differences,
        "compiled_note_text_targets_verified":False,
        "compiled_lemma_id_values_verified":False,
        "original_source_modified":False,
        "published":False,
    }

def audit_stock_raw_markup(publisher_usfx: bytes,candidate: Path,
                           decisions: list[dict], *, sword_root: Path,
                           module_id: str, inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Stock SWORD raw verifier executable not found")
    aliases,expected,expected_poetry=build_stock_markup_plan(
        publisher_usfx,candidate,decisions)
    with tempfile.TemporaryDirectory(prefix="stock-sword-raw-") as temp:
        refs=Path(temp)/"reader-keys.txt"
        refs.write_text("\n".join(k for _,k in aliases)+"\n",encoding="utf-8")
        env=dict(os.environ,SWORD_PATH=str(sword_root))
        try:
            proc=subprocess.run([str(inspector),module_id,str(refs)],
                env=env,capture_output=True,text=True,timeout=180,check=False)
        except subprocess.TimeoutExpired as exc:
            raise PilotError("Stock SWORD raw markup inspection timed out") from exc
        if (proc.returncode or proc.stderr.strip()
            or len(proc.stdout)>8_000_000):
            raise PilotError("Stock SWORD raw markup inspection failed")
        report=compare_raw_rows(proc.stdout.splitlines(),aliases,expected,expected_poetry)
    report["source_reader_merge_count"]=len(decisions)
    report["compiled_module_id"]=module_id
    return report
