#!/usr/bin/env python3
"""End-to-end *non-publishing* LSG candidate for SWORD HEAD XML versification.

All authorial verse IDs, notes, lexical word annotations and poetry are kept
in the source OSIS. Only source-attested ASCII display separators are added
to a temporary independently XSD-checked clone. The v11n delta is generated
from original USFX verse keys against a registered SWORD base, never from
an editor's hardcoded exception.
"""
from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from pathlib import Path
import subprocess
import tempfile
from contextlib import contextmanager

from lxml import etree

from pilot_preflight import PilotError
from lsg_source_compare import scan_usfx
from lsg_source_v11n_delta import build_v11n_delta
from lsg_v11n_coverage import parse_ceilings
from lsg_ephemeral_osis_candidate import prepare_ephemeral_source_spaced_osis
from lsg_sword_rebuild import full_index_roundtrip
from pilot_subprocess import query, present_key

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MODULE_ID="BRLSG1910eb"


@contextmanager
def head_sword_library(prefix: Path):
    old=os.environ.get("LD_LIBRARY_PATH")
    path=str(prefix/"lib")
    os.environ["LD_LIBRARY_PATH"]=path+(":"+old if old else "")
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("LD_LIBRARY_PATH",None)
        else:
            os.environ["LD_LIBRARY_PATH"]=old


def summarize_internal_markup(raw: bytes) -> dict:
    """Count OSIS-like opening tags without logging any Scripture text."""
    counts=Counter(
        tag.decode("ascii") for tag in re.findall(
            rb"<([A-Za-z][A-Za-z0-9]*)\b",raw)
    )
    return {
        "tag_counts":{name:counts.get(name,0) for name in (
            "w","note","reference","l","lg","q","hi","title"
        )},
        "returned_bytes":len(raw),
        "returned_sha256":hashlib.sha256(raw).hexdigest(),
    }



def audit_compiled_internal_markup(candidate: Path, source: bytes,
                                   *, sword_root: Path, reader: str) -> dict:
    """Compare *all* compiled note and word tags with original OSIS by verse.

    Internal reader tags are an independent SWORD compiler round-trip, not a
    claim about xref target clickability or exact rendered layout in Xiphos.
    Poetry tag counts are compared by entire book, to avoid milestone split
    ambiguity when <l> spans multiple verses.
    """
    from collections import Counter
    from lsg_osis_parity import _osis_verses
    from lsg_sword_compare import chapter_plan, parse_sword_chapter
    original_text,source_keys=scan_usfx(source)
    plan=chapter_plan(source_keys,full=True)
    original_words=original_text["original_books"]
    osis_root=etree.parse(str(candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    converted_books=[n.get("osisID") for n in osis_root.iter(OSIS+"div")
                     if n.get("type")=="book"]
    if len(original_words)!=len(converted_books) or len(original_words)!=66:
        raise PilotError("Cannot align authorial and converted book order for markup")
    mapping=dict(zip(original_words,converted_books))
    _,words,notes,lines=_osis_verses(candidate)
    expected_words=sum(len(v) for v in words.values())
    expected_notes=sum(notes.values())
    # The XML tag <l> opener may occur in one verse and close in another,
    # so compare by book across the independently compiled output.
    expected_lines_by_book=Counter()
    for k,count in lines.items():
        expected_lines_by_book[k.split(".")[0]]+=count
    found=Counter()
    note_slots_equal=0
    word_slots_equal=0
    differences=[]
    lines_by_book=Counter()
    for code,(book_name,chapters) in plan.items():
        canonical=mapping[code]
        for chapter in chapters:
            ref=f"{book_name} {chapter}"
            rc,content=query(MODULE_ID,ref,fmt="internal",
                             root=sword_root,exe=reader,
                             timeout=30,limit=4*1024*1024,options="sfnhl")
            if not present_key(ref,content,rc):
                raise PilotError("SWORD cannot read source chapter in internal markup audit")
            # The rendered verse-heading parser may normalize whitespace
            # but must never normalize or delete markup opening tags.
            rendered=parse_sword_chapter(content,chapter,MODULE_ID)
            authored={v for (b,c,v) in source_keys if b==code and c==chapter}
            if set(rendered)!=authored:
                raise PilotError("SWORD internal markup readback changed verse keys")
            for verse,fragment in rendered.items():
                reference=f"{canonical}.{chapter}.{verse}"
                tags=Counter(re.findall(r"<([A-Za-z][A-Za-z0-9]*)\b",fragment))
                got_words=tags["w"]
                got_notes=tags["note"]
                got_lines=tags["l"]
                expected_w=len(words.get(reference,[]))
                expected_n=notes.get(reference,0)
                word_slots_equal+=got_words==expected_w
                note_slots_equal+=got_notes==expected_n
                found.update({"reader_word_tags":got_words,
                              "reader_note_tags":got_notes,
                              "reader_line_tags":got_lines,
                              "verses":1})
                lines_by_book[canonical]+=got_lines
                if ((got_words!=expected_w or got_notes!=expected_n)
                        and len(differences)<70):
                    differences.append({
                        "reference":f"{code}.{chapter}.{verse}",
                        "expected_word_tags":expected_w,
                        "compiled_word_tags":got_words,
                        "expected_note_tags":expected_n,
                        "compiled_note_tags":got_notes,
                    })
    poem_equal=sum(
        lines_by_book[book]==expected_lines_by_book.get(book,0)
        for book in mapping.values()
    )
    return {
        "source_verse_count":len(source_keys),
        "verses_checked":found["verses"],
        "expected_ordered_word_tags":expected_words,
        "compiled_word_tags":found["reader_word_tags"],
        "per_verse_word_tag_counts_equal":word_slots_equal,
        "expected_cross_reference_notes":expected_notes,
        "compiled_cross_reference_notes":found["reader_note_tags"],
        "per_verse_note_tag_counts_equal":note_slots_equal,
        "compiled_poetry_line_tag_count":found["reader_line_tags"],
        "original_poetry_line_tag_count":sum(lines.values()),
        "books_with_equal_poetry_line_tag_counts":poem_equal,
        "sample_mismatches":differences,
        "full_compiled_word_count_parity":
            word_slots_equal==len(source_keys) and
            found["reader_word_tags"]==expected_words,
        "full_compiled_note_count_parity":
            note_slots_equal==len(source_keys) and
            found["reader_note_tags"]==expected_notes,
        "full_compiled_poetry_counts_parity":poem_equal==len(mapping),
        "note_reference_targets_and_markers_approved":False,
        "editorial_approval":False,
    }



def audit_sword_unfiltered_raw_verse_entries(
    original_candidate: Path,
    publisher_usfx: bytes,
    *,
    sword_root: Path,
    head_prefix: Path,
    inspector: Path,
    temp_dir: Path,
) -> dict:
    """Compare actual compiled RAW OSIS verse markup without diatheke filters.

    Requires the unfiltered SWORD C++ getRawEntry() API and verified exact
    publisher verse keys. Only numeric tag counters and verse identifiers
    leave the C++ inspector. This still does not prove note text or clickable
    machine destinations.
    """
    from lsg_osis_parity import _osis_verses
    from lsg_sword_compare import chapter_plan

    source,keys=scan_usfx(publisher_usfx)
    plan=chapter_plan(keys,full=True)
    by_book={}
    tree=etree.parse(str(original_candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    source_books=source["original_books"]
    converted_books=[e.get("osisID") for e in tree.iter(OSIS+"div")
                     if e.get("type")=="book"]
    if len(source_books)!=66 or len(converted_books)!=66:
        raise PilotError("Unreviewed book identity for raw compiled-entry audit")
    mapping=dict(zip(source_books,converted_books))
    _,words,notes,lines=_osis_verses(original_candidate)
    input_refs=[]
    osis_refs=[]
    for code,(name,chapters) in plan.items():
        canonical=mapping[code]
        for chapter in chapters:
            for verse in sorted(v for bk,ch,v in keys if bk==code and ch==chapter):
                input_refs.append(f"{name} {chapter}:{verse}")
                osis_refs.append(f"{canonical}.{chapter}.{verse}")
    if len(input_refs)!=len(keys):
        raise PilotError("Raw-reader source reference count differs")
    source_file=temp_dir/"original-verse-queries.txt"
    source_file.write_text("\n".join(input_refs)+"\n",encoding="utf-8")
    with head_sword_library(head_prefix):
        env=dict(os.environ,SWORD_PATH=str(sword_root))
        process=subprocess.run(
            [str(inspector),MODULE_ID,str(source_file)],
            capture_output=True,text=True,env=env,timeout=150,check=False,
        )
    if process.returncode or process.stderr.strip() or len(process.stdout)>8_000_000:
        raise PilotError("Raw SWORD verse inspector failed or returned unbounded data")
    rows=process.stdout.splitlines()
    if len(rows)!=len(input_refs):
        raise PilotError("Raw SWORD verse inspector skipped source keys")
    total=Counter()
    matching_w=0
    matching_notes=0
    note_mismatch=[]
    word_mismatch=[]
    for i,line in enumerate(rows):
        cells=line.split("\t")
        if len(cells)!=6 or cells[0]!=input_refs[i]:
            raise PilotError("Malformed or out-of-order SWORD raw verse counts")
        try:
            w,n,r,l,q=map(int,cells[1:])
        except ValueError as exc:
            raise PilotError("Invalid SWORD raw markup numeric count") from exc
        if any(x<0 or x>5000 for x in (w,n,r,l,q)):
            raise PilotError("SWORD raw markup counter out of allowed range")
        ref=osis_refs[i]
        expected_w=len(words.get(ref,()))
        expected_n=notes.get(ref,0)
        matching_w+=w==expected_w
        matching_notes+=n==expected_n
        if w!=expected_w and len(word_mismatch)<30:
            word_mismatch.append({"source_ref":ref,
                                  "source":expected_w,"compiled_raw":w})
        if n!=expected_n and len(note_mismatch)<30:
            note_mismatch.append({"source_ref":ref,
                                  "source":expected_n,"compiled_raw":n})
        total.update({"w":w,"note":n,"reference":r,"l":l,"q":q})
    return {
        "original_verse_keys":len(keys),
        "compiled_raw_verse_keys_checked":len(rows),
        "source_ordered_word_count":sum(map(len,words.values())),
        "compiled_raw_word_tag_count":total["w"],
        "source_cross_reference_note_count":sum(notes.values()),
        "compiled_raw_note_tag_count":total["note"],
        "word_tag_count_by_verse_matching":matching_w,
        "note_tag_count_by_verse_matching":matching_notes,
        "first_word_marker_mismatches":word_mismatch,
        "first_note_marker_mismatches":note_mismatch,
        "compiled_raw_reference_tag_count":total["reference"],
        "compiled_raw_poetry_line_tag_count":total["l"],
        "all_source_word_counts_preserved":matching_w==len(keys),
        "all_source_note_counts_preserved":matching_notes==len(keys),
        "note_content_targets_and_raw_verse_markup_approved":False,
        "original_candidate_unchanged":True,
        "published":False,
    }


def experiment(publisher_usfx: bytes, raw_candidate: Path, schema: Path,
               *, head_prefix: Path, installed_registry_helper: Path) -> dict:
    """Run entire source-to-SWORD chain in TemporaryDirectory; metadata only."""
    report={
        "status":"experimental_chain_not_started",
        "module_id":MODULE_ID,
        "custom_runtime_required":True,
        "stock_xiphos_compatibility_verified":False,
        "published":False,
        "approved_for_publication":False,
    }
    source,keys=scan_usfx(publisher_usfx)
    book_order=source["original_books"]
    root=etree.parse(str(raw_candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    codes=[node.get("osisID") for node in root.iter(OSIS+"div")
           if node.get("type")=="book"]
    if len(codes)!=len(book_order) or len(set(codes))!=len(codes):
        raise PilotError("Original and converted book structures are not bijective")
    mapping=dict(zip(book_order,codes))
    if not installed_registry_helper.is_file() or installed_registry_helper.is_symlink():
        raise PilotError("Missing trusted stock SWORD registry inspector")
    rows=subprocess.run([str(installed_registry_helper)],
                        capture_output=True,text=True,timeout=30,check=False)
    if rows.returncode or rows.stderr.strip() or len(rows.stdout)>8_000_000:
        raise PilotError("Stock SWORD registry inspector failed")
    installed=parse_ceilings(rows.stdout)
    if "Segond" not in installed:
        raise PilotError("No reviewed Segond base installed")
    xml,delta_proof=build_v11n_delta(
        keys,mapping,installed["Segond"],
        base_name="Segond",edition_id=MODULE_ID,
        book_order=book_order)
    report["source_derived_xml_versification"]=delta_proof
    prefix=Path(head_prefix)
    compiler=prefix/"bin/osis2mod"
    reader=prefix/"bin/diatheke"
    if not (compiler.is_file() and reader.is_file()):
        raise PilotError("The pinned experimental XML-v11n SWORD tools are absent")
    source_hash=hashlib.sha256(raw_candidate.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="brlsg1910-head-nonrelease-") as dirname:
        home=Path(dirname)
        improved=home/"candidate-source-spaces.osis.xml"
        report["source_spacing_candidate"]=prepare_ephemeral_source_spaced_osis(
            raw_candidate,publisher_usfx,improved,schema)
        v11n=home/"candidate-source-v11n.xml"
        v11n.write_bytes(xml)
        sword_root=home/"sword"
        data=sword_root/"modules/texts/rawtext/brlsg1910eb"
        data.mkdir(parents=True)
        conf=sword_root/"mods.d/brlsg1910eb.conf"
        conf.parent.mkdir(parents=True)
        conf.write_text(
            "["+MODULE_ID+"]\n"
            "Description=Unpublished LSG 1910 source-v11n compatibility experiment\n"
            "DataPath=./modules/texts/rawtext/brlsg1910eb/\n"
            "ModDrv=RawText\n"
            "SourceType=OSIS\n"
            "Encoding=UTF-8\n"
            "Lang=fr\n"
            "GlobalOptionFilter=OSISLemma\n"
            "GlobalOptionFilter=OSISStrongs\n"
            "GlobalOptionFilter=OSISFootnotes\n"
            "GlobalOptionFilter=OSISScripref\n"
            "GlobalOptionFilter=OSISHeadings\n"
            "Versification="+MODULE_ID+"\n"
            "DistributionLicense=Public Domain\n",
            encoding="utf-8")
        with head_sword_library(prefix):
            compiled=subprocess.run(
                [str(compiler),str(data),str(improved),"-v",str(v11n)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                timeout=180,check=False)
            logs=compiled.stdout+compiled.stderr
            report["head_osis2mod_exit_code"]=compiled.returncode
            report["head_osis2mod_log_sha256"]=hashlib.sha256(logs).hexdigest()
            report["head_osis2mod_log_bytes"]=len(logs)
            if len(logs)>6_000_000 or compiled.returncode:
                report["status"]="head_compilation_failed"
                return report
            if not any(p.is_file() for p in data.rglob("*")):
                report["status"]="head_compilation_did_not_produce_data"
                return report
            (data/"v11n.xml").write_bytes(xml)
            probes={}
            for ref in ("Mark 10:52","Mark 10:53","Job 34:36"):
                result,body=query(MODULE_ID,ref,fmt="plain",
                                  root=sword_root,exe=str(reader),
                                  timeout=30,limit=128*1024)
                probes[ref]=present_key(ref,body,result) and bool(
                    body.strip())
            report["required_authored_reference_probes"]=probes
            if not all(probes.values()):
                report["status"]="head_cannot_reach_some_authored_reference_slots"
                return report
            # Entire real-source SWORD round-trip. No Scripture is exported;
            # the common verifier uploads only aggregate counters/hashes.
            report["source_to_head_sword_full_roundtrip"]=full_index_roundtrip(
                publisher_usfx,root=sword_root,reader=str(reader),
                module_id=MODULE_ID,
            )
            # Distinguish plain-reader text parity from compiled markup
            # preservation. Internal format may be renderer-specific; this
            # initial bounded probe is *not* full apparatus certification.
            per_verse_internal={}
            for ref in ("Mark 10:53","Job 34:36","John 3:16",
                        "Psalms 23:1","Acts 8:37"):
                rc,body=query(MODULE_ID,ref,fmt="internal",
                              root=sword_root,exe=str(reader),
                              timeout=30,limit=256*1024,options="sfnhl")
                per_verse_internal[ref]={
                    "query_return_code":rc,
                    **summarize_internal_markup(body),
                }
            report["source_to_compiled_internal_markup_samples"]=per_verse_internal
            try:
                report["source_to_compiled_internal_markup_full_audit"]=(
                    audit_compiled_internal_markup(
                        improved,publisher_usfx,sword_root=sword_root,
                        reader=str(reader)))
            except PilotError as exc:
                # The -o flags can change diatheke's headings. This is a
                # *reader* diagnostic; keep the independent raw-entry gate.
                report["source_to_compiled_internal_markup_full_audit"]={
                    "status":"reader_output_not_machine_parsable",
                    "reason":str(exc)[:170],
                    "approved_for_publication":False,
                }
            inspector=os.getenv("LSG_SWORD_RAW_INSPECTOR")
            if inspector:
                report["source_to_compiled_raw_markup_audit"]=(
                    audit_sword_unfiltered_raw_verse_entries(
                        improved,publisher_usfx,sword_root=sword_root,
                        head_prefix=prefix,inspector=Path(inspector),
                        temp_dir=home))
            report["all_compiled_note_text_targets_strongs_poetry_verified"]=False
        report["status"]="complete_private_xml_v11n_head_reader_trial"
        report["generated_module_file_count"]=sum(
            p.is_file() for p in data.rglob("*"))
        report["all_original_verse_reference_slots_preserved"]=report[
            "source_to_head_sword_full_roundtrip"]["source_key_count_matches"]
    if hashlib.sha256(raw_candidate.read_bytes()).hexdigest()!=source_hash:
        raise PilotError("Original OSIS candidate was altered by SWORD experiment")
    report["source_candidate_unmodified"]=True
    report["experimental_module_erased_after_run"]=True
    return report
