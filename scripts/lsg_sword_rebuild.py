#!/usr/bin/env python3
"""Disposable real eBible OSIS -> SWORD candidate compiler (no publication).

Input is already independently XSD/structure-validated by the caller.
Never writes to the user's installed SWORD modules, public repositories,
or releases. Returns only text-free metadata; original OSIS remains unchanged.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

from pilot_preflight import PilotError
from pilot_subprocess import query,present_key
from lsg_sword_compare import chapter_plan,parse_sword_chapter,usfx_text_by_verse,plain
from lsg_source_compare import scan_usfx

MAX_COMPILER_LOG=6*1024*1024
MAX_COMPILE_SECONDS=180
SAMPLES=[
    ("Genesis 1:1","Genesis 1:1:"),
    ("Exodus 7:26","Exodus 7:26:"),
    ("Exodus 7:29","Exodus 7:29:"),
    ("Psalms 3:9","Psalms 3:9:"),
    ("Psalms 23:1","Psalms 23:1:"),
    ("John 3:16","John 3:16:"),
]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def full_index_roundtrip(source: bytes, *, root: Path, reader: str) -> dict:
    """Read all source chapters in rebuilt module; never export their text."""
    from collections import Counter
    usfx,keys=scan_usfx(source)
    plan=chapter_plan(keys,full=True)
    source_verses,_=usfx_text_by_verse(source,filter_books=set(plan))
    totals=Counter()
    examples=[]
    index_key_mismatches=[]
    books=[]
    for code,(book_name,chapters) in plan.items():
        book_checks=Counter()
        source_continuous=[]
        sword_continuous=[]
        for chapter in chapters:
            ref=f"{book_name} {chapter}"
            exit_code,body=query("fraLSG1910eb",ref,
                fmt="plain",root=root,exe=reader,limit=4*1024*1024,timeout=30)
            if not present_key(ref,body,exit_code):
                raise PilotError(f"Full SWORD index has no readable chapter: {ref}")
            actual=parse_sword_chapter(body,chapter,"fraLSG1910eb")
            expected={v:text for (b,c,v),text in source_verses.items()
                      if b==code and c==chapter}
            source_only=set(expected)-set(actual)
            sword_only=set(actual)-set(expected)
            same=set(expected)&set(actual)
            exact=sum(expected[v]==actual[v] for v in same)
            no_spaces=sum("".join(expected[v].split())=="".join(actual[v].split())
                          for v in same)
            book_checks.update({
                "chapters":1,"source_verses":len(expected),"sword_verses":len(actual),
                "source_keys_missing":len(source_only),"sword_keys_unexpected":len(sword_only),
                "exact_normalized_text_matches":exact,
                "content_matches_ignoring_whitespace":no_spaces,
            })
            if (source_only or sword_only) and len(index_key_mismatches)<60:
                index_key_mismatches.append({
                    "book":code,"chapter":chapter,
                    "source_only_reference_keys":sorted(source_only)[:25],
                    "sword_only_reference_keys":sorted(sword_only)[:25],
                })
            if len(examples)<75 and (source_only or sword_only or exact!=len(same)):
                examples.append({
                    "book":code,"chapter":chapter,
                    "missing_source_keys":sorted(source_only)[:15],
                    "unexpected_sword_keys":sorted(sword_only)[:15],
                    "same_reference_text_differences":len(same)-exact,
                })
            source_continuous.extend(expected[v] for v in sorted(expected))
            sword_continuous.extend(actual[v] for v in sorted(actual))
        totals.update(book_checks)
        books.append({
            "book":code,**book_checks,
            "continuous_source_vs_compiled_scripture_exact":
               plain(" ".join(source_continuous))==plain(" ".join(sword_continuous)),
            "continuous_source_vs_compiled_scripture_without_whitespace":
               "".join("".join(v.split()) for v in source_continuous)==
               "".join("".join(v.split()) for v in sword_continuous),
        })
    return {
        "status":"all_canonical_source_chapters_read_for_diagnostics",
        "expected_chapters":1189,
        "total_source_verse_keys":len(keys),
        "totals":dict(totals),
        "books":books,
        "first_diagnostic_chapters":examples,
        "all_index_key_mismatch_chapters":index_key_mismatches,
        "source_key_count_matches":totals["source_keys_missing"]==0
          and totals["sword_keys_unexpected"]==0
          and totals["source_verses"]==len(keys)
          and totals["sword_verses"]==len(keys),
        "complete_text_and_note_parity_verified":False,
        "module_not_published":True,
    }


def compile_candidate(osis: Path, *, compiler="osis2mod", reader="diatheke", source_usfx: bytes | None=None) -> dict:
    before=osis.read_bytes()
    report={
        "status":"rebuild_probe_not_approved",
        "original_osis_sha256":_sha(before),
        "source_file_unchanged":True,
        "published":False,
        "approved_for_publication":False,
        "versification":"Segond",
        "module_id":"fraLSG1910eb",
        "real_module_rebuilt_in_temporary_directory":False,
        "all_source_verses_and_annotations_checked":False,
    }
    with tempfile.TemporaryDirectory(prefix="bible-lsg-segond-real-") as home:
        root=Path(home)
        data=root/"modules/texts/rawtext/fralsg1910eb"
        data.mkdir(parents=True)
        result=subprocess.run(
            [compiler,str(data),str(osis),"-v","Segond"],
            capture_output=True,check=False,timeout=MAX_COMPILE_SECONDS,
        )
        logs=result.stdout+result.stderr
        report["compiler_exit_code"]=result.returncode
        report["compiler_output_sha256"]=_sha(logs)
        report["compiler_output_bytes"]=len(logs)
        # Record only canonical source references in compiler messages;
        # never upload raw compiler logs that may contain Bible text.
        known_refs=sorted(set(m.decode("ascii") for m in re.findall(
            rb"\b(?:Gen|Exod|Lev|Num|Deut|Josh|Judg|Ruth|1Sam|2Sam|"
            rb"1Kgs|2Kgs|1Chr|2Chr|Ezra|Neh|Esth|Job|Ps|Prov|Eccl|Song|"
            rb"Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|"
            rb"Nah|Hab|Zeph|Hag|Zech|Mal|Matt|Mark|Luke|John|Acts|"
            rb"Rom|1Cor|2Cor|Gal|Eph|Phil|Col|1Thess|2Thess|"
            rb"1Tim|2Tim|Titus|Phlm|Heb|Jas|1Pet|2Pet|1John|"
            rb"2John|3John|Jude|Rev)\.\d+\.\d+\b",
            logs,
        )))
        report["compiler_source_ref_mentions"]=known_refs[:70]
        report["compiler_diagnostics_count"]={
            "fatal":len(re.findall(rb"(?m)(?:^|\n)FATAL\(",logs)),
            "error":len(re.findall(rb"(?m)(?:^|\n)ERROR\(",logs)),
            "warning":len(re.findall(rb"(?m)(?:^|\n)WARNING\(",logs)),
            "v11n_outside":len(re.findall(rb"not in the Segond versification",logs)),
        }
        files=[p for p in data.rglob("*") if p.is_file()]
        report["module_file_count"]=len(files)
        report["module_total_bytes"]=sum(p.stat().st_size for p in files)
        report["real_module_rebuilt_in_temporary_directory"]=(
            result.returncode==0 and bool(files)
        )
        if len(logs)>MAX_COMPILER_LOG or result.returncode or not files:
            report["status"]="blocked_compiler_or_unbounded_diagnostics"
            return report
        conf=root/"mods.d/fralsg1910eb.conf"
        conf.parent.mkdir(parents=True)
        conf.write_text(
            "[fraLSG1910eb]\n"
            "Description=Nonpublished eBible Louis Segond conversion trial\n"
            "Version=0.0\n"
            "DataPath=./modules/texts/rawtext/fralsg1910eb/\n"
            "ModDrv=RawText\n"
            "Encoding=UTF-8\n"
            "Lang=fr\n"
            "SourceType=OSIS\n"
            # SWORD cannot hide OSIS apparatus or Strong labels in plain
            # reader output unless the module advertises its option filters.
            # They change display only; the compiled source stays intact.
            "GlobalOptionFilter=OSISLemma\n"
            "GlobalOptionFilter=OSISStrongs\n"
            "GlobalOptionFilter=OSISFootnotes\n"
            "GlobalOptionFilter=OSISScripref\n"
            "GlobalOptionFilter=OSISHeadings\n"
            "Versification=Segond\n"
            "DistributionLicense=Public Domain\n",
            encoding="utf-8",
        )
        probes=[]
        for key,header in SAMPLES:
            code,body=query("fraLSG1910eb",key,fmt="plain",root=root,exe=reader,
                            limit=256*1024,timeout=30)
            decoded=body.decode("utf-8",errors="replace")
            heading=decoded.splitlines()[0] if decoded.splitlines() else ""
            matched=heading.startswith(header)
            # A nonempty chapter/verse heading with zero actual content must
            # NEVER be taken as a successful reader round trip.
            content=decoded[len(heading):] if matched else decoded
            has_text=bool(content.strip()) or bool(heading[len(header):].strip())
            # Distinguish real OSIS markup from rendered canonical text.
            # These diagnostics contain no original Scripture words.
            if os.getenv("LSG_SAMPLE_DEBUG")=="1" and key in (
                "Genesis 1:1","Exodus 7:26","Psalms 23:1","John 3:16"
            ):
                # Public-domain LSG, tiny samples in ephemeral CI logs for
                # converter analysis; never include full modules in artifacts.
                print("READBACK_SAMPLE",key,repr(decoded[:480]))
            xml_tags=re.findall(r"<(/?)([A-Za-z][A-Za-z0-9]*)\\b",decoded)
            tag_counts={name:sum(tag==name for _,tag in xml_tags)
                        for name in ("w","note","reference","hi","l","lg","p","verse")}
            mark_bodies=re.findall(r"(?:strong|lemma|morph)(?:=|:)",decoded,re.I)
            probes.append({
                "requested":key,
                "reader_return_code":code,
                "reference_header_preserved":matched,
                "has_nonempty_verse_body":has_text and present_key(key,body,code),
                "output_sha256":_sha(body),
                "output_bytes":len(body),
                "visible_xml_tag_counts":tag_counts,
                "morph_or_lemma_markup_markers":len(mark_bodies),
            })
        report["reader_probes"]=probes
        report["all_sample_keys_have_text"]=all(
            q["reference_header_preserved"] and q["has_nonempty_verse_body"]
            for q in probes
        )
        report["status"]=(
            "actual_text_module_compiled_and_samples_read_not_approved"
            if report["all_sample_keys_have_text"] and not any(
               report["compiler_diagnostics_count"][x] for x in ("fatal","error","v11n_outside")
            )
            else "compiled_but_sample_or_v11n_errors_block"
        )
        if source_usfx is not None and report["all_sample_keys_have_text"]:
            try:
                report["full_source_verse_roundtrip"]=full_index_roundtrip(
                    source_usfx,root=root,reader=reader
                )
            except (OSError,ValueError) as exc:
                report["full_source_verse_roundtrip"]={
                    "status":"blocked",
                    "error_type":type(exc).__name__,
                    "error":str(exc)[:180],
                    "full_source_parity_unverified":True,
                }
            if (report["full_source_verse_roundtrip"].get("source_key_count_matches")
                    is not True):
                report["status"]="compiled_but_full_reference_index_mismatch"
        report["source_file_unchanged"]=_sha(osis.read_bytes())==report["original_osis_sha256"]
        if not report["source_file_unchanged"]:
            raise PilotError("Original OSIS source modified during compiler trial")
    return report
