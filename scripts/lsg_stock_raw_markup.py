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
    # A verse-milestoned OSIS document can legitimately put <w> or <l>
    # outside a verse's current sID/eID span (titles, linked poetry lines).
    # Record independent *whole-book* source counts instead of pretending
    # all original tags belong to the nearest verse.
    source_global={}
    for book in tree.iter(OSIS+"div"):
        if book.get("type")!="book":
            continue
        book_id=book.get("osisID")
        source_global[book_id]=Counter({
            "w":sum(1 for _ in book.iter(OSIS+"w")),
            "note":sum(1 for _ in book.iter(OSIS+"note")),
            "l":sum(1 for _ in book.iter(OSIS+"l")),
            "q":sum(1 for _ in book.iter(OSIS+"q")),
            "reference":sum(1 for _ in book.iter(OSIS+"reference")),
        })
    if set(source_global)!=set(book_ids):
        raise PilotError("Cannot independently count every source OSIS book")
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
    return aliases,compiled_expected,source_global

def compare_raw_rows(rows: list[str], ordered_refs: list[tuple[str,str]],
                     expected: dict, source_global_by_book: dict) -> dict:
    """Count each actual reader key and conservatively classify interverse tags."""
    if not ordered_refs or len(rows)!=len(ordered_refs):
        raise PilotError("Compiled raw SWORD inspector skipped or inserted reader keys")
    differences=[]
    poetry_diagnostics=[]
    poetry_asymmetric_entry_count=0
    poetry_source_start_deficit_entry_count=0
    expected_inside=Counter()
    compiled_counts=Counter()
    compiled_by_book=defaultdict(Counter)
    expected_inside_by_book=defaultdict(Counter)
    checked=0
    per_verse_notes_equal=0
    per_verse_words_at_least=0
    per_verse_words_exact=0
    for line,(osis_ref,query) in zip(rows,ordered_refs):
        cols=line.split("\t")
        if len(cols)!=7 or cols[0]!=query:
            raise PilotError("Raw compiled SWORD row does not match requested key")
        try:
            w,n,xref,poetry,poetry_end,q=map(int,cols[1:])
        except (TypeError,ValueError) as exc:
            raise PilotError("Malformed unfiltered SWORD markup counter") from exc
        if any(v<0 or v>5000 for v in (w,n,xref,poetry,poetry_end,q)):
            raise PilotError("Out-of-range unfiltered SWORD markup counter")
        book=osis_ref.split(".")[0]
        inside=expected[osis_ref]
        expected_inside.update({"w":inside["w"],"note":inside["note"],"l":inside["l"]})
        expected_inside_by_book[book].update({"w":inside["w"],"note":inside["note"],
                                               "l":inside["l"]})
        compiled_counts.update({"w":w,"note":n,"l":poetry,"l_end":poetry_end,
                                "q":q,"reference":xref})
        compiled_by_book[book].update({"w":w,"note":n,"l":poetry,
                                        "l_end":poetry_end,"q":q,"reference":xref})
        per_verse_notes_equal+=n==inside["note"]
        per_verse_words_at_least+=w>=inside["w"]
        per_verse_words_exact+=w==inside["w"]
        if poetry!=poetry_end or poetry<inside["l"]:
            if poetry!=poetry_end:
                poetry_asymmetric_entry_count+=1
            if poetry<inside["l"]:
                poetry_source_start_deficit_entry_count+=1
            if len(poetry_diagnostics)<160:
                poetry_diagnostics.append({
                    "osis_ref":osis_ref,
                    "source_lines_opened_inside_verse":inside["l"],
                    "compiled_line_start_markers":poetry,
                    "compiled_line_end_markers":poetry_end,
                })
        if (w!=inside["w"] or n!=inside["note"]) and len(differences)<50:
            differences.append({
                "osis_ref":osis_ref,
                "inside_original_word_tags":inside["w"],
                "compiled_raw_word_tags":w,
                "source_note_tags":inside["note"],
                "compiled_raw_note_tags":n,
                "possible_interverse_word_tags":max(0,w-inside["w"]),
            })
        checked+=1
    by_book=[]
    books=set(source_global_by_book)|set(compiled_by_book)
    all_book_tags_equal=True
    only_documented_relocations=True
    for book in sorted(books):
        source=source_global_by_book.get(book,Counter())
        raw=compiled_by_book.get(book,Counter())
        inside=expected_inside_by_book.get(book,Counter())
        # The compiler may attach <w> tags occurring *outside* verse milestones
        # to neighboring entries. Their source authorial words remain in
        # scope; a missing or newly created tag would break global parity.
        total_equal=all(source[k]==raw[k] for k in ("w","note","l"))
        outside=max(0,source["w"]-inside["w"])
        attached=raw["w"]-inside["w"]
        only_documented_relocations &= (attached==outside and outside>=0)
        all_book_tags_equal &= total_equal
        if not total_equal or outside or attached:
            by_book.append({
                "book":book,
                "source_whole_book_word_tags":source["w"],
                "compiled_word_tags":raw["w"],
                "word_tags_outside_source_verse_milestones":outside,
                "word_tags_attached_during_compilation":attached,
                "source_whole_book_note_tags":source["note"],
                "compiled_note_tags":raw["note"],
                "source_whole_book_poetry_line_tags":source["l"],
                "compiled_poetry_line_tags":raw["l"],
                "compiled_poetry_end_milestones":raw["l_end"],
                "compiled_poetry_end_minus_start":raw["l_end"]-raw["l"],
                "word_note_poetry_totals_equal":total_equal,
            })
    verified=(all_book_tags_equal and only_documented_relocations
              and per_verse_words_at_least==checked
              and per_verse_notes_equal==checked)
    global_expected=Counter()
    for counts in source_global_by_book.values():
        global_expected.update(counts)
    return {
        "status":("raw_stock_sword_global_markers_verified_with_interverse_diagnostics"
                  if verified else "blocked_compiled_raw_markup_mismatch"),
        "checked_reader_entries":checked,
        "source_global_word_tags":global_expected["w"],
        "compiled_raw_word_tags":compiled_counts["w"],
        "source_global_note_tags":global_expected["note"],
        "compiled_raw_note_tags":compiled_counts["note"],
        "source_global_poetry_line_tags":global_expected["l"],
        "compiled_raw_poetry_line_tags":compiled_counts["l"],
        "compiled_raw_poetry_line_end_milestones":compiled_counts["l_end"],
        "poetry_end_milestones_match_source_line_count":(
            compiled_counts["l_end"]==global_expected["l"]),
        "poetry_start_end_milestones_balanced":(
            compiled_counts["l"]==compiled_counts["l_end"]),
        "poetry_asymmetric_reader_entry_count":poetry_asymmetric_entry_count,
        "poetry_reader_entries_with_fewer_start_markers_than_source_inside":
            poetry_source_start_deficit_entry_count,
        "first_poetry_marker_location_diagnostics":poetry_diagnostics,
        "words_matching_exact_source_verse_milestone_counts":per_verse_words_exact,
        "verses_with_no_source_word_tag_loss":per_verse_words_at_least,
        "per_verse_note_tag_matches":per_verse_notes_equal,
        "books_compared":len(books),
        "books_with_matching_full_word_note_poetry_tag_counts":sum(
            all(source_global_by_book[b][k]==compiled_by_book[b][k]
                for k in ("w","note","l"))
            for b in books if b in source_global_by_book and b in compiled_by_book),
        "source_global_raw_markup_counts_match_compiled":all_book_tags_equal,
        "all_outside_verse_word_markers_accounted_for":only_documented_relocations,
        "first_interverse_word_relocations_or_mismatches":differences,
        "book_level_diagnostics":by_book[:66],
        "compiled_cross_reference_tag_count":compiled_counts["reference"],
        "compiled_quote_tag_count":compiled_counts["q"],
        "compiled_note_text_targets_verified":False,
        "compiled_lemma_id_values_verified":False,
        "interverse_marker_placement_editorially_approved":False,
        "source_modified":False,
        "published":False,
    }

def audit_stock_raw_markup(publisher_usfx: bytes,candidate: Path,
                           decisions: list[dict], *, sword_root: Path,
                           module_id: str, inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Stock SWORD raw verifier executable not found")
    aliases,expected,source_global=build_stock_markup_plan(
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
        report=compare_raw_rows(proc.stdout.splitlines(),aliases,expected,source_global)
    report["source_reader_merge_count"]=len(decisions)
    report["compiled_module_id"]=module_id
    return report
