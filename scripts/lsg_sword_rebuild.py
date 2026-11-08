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
from lsg_sword_compare import chapter_plan,parse_sword_chapter,usfx_text_by_verse,plain,explain_wrapper
from lsg_source_compare import scan_usfx

MAX_COMPILER_LOG=6*1024*1024
MAX_COMPILE_SECONDS=180
# The publisher's original eBible module declares NRSV, but a direct
# osis2mod -v NRSV import of the authored verse IDs reports 112 out-of-v11n
# references. Segond permits a broader *diagnostic* readback (it still has
# mismatched verse slots). Neither choice is publication-approved.
PUBLISHER_DECLARED_V11N="NRSV"
PROBE_V11N="Segond"
ALTERNATE_PROBE_V11N="Calvin"
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



def _no_whitespace(value: str) -> str:
    """Diagnostic character equality; never permission to reassign a verse."""
    return "".join(value.split())


def classify_chapter_slot_differences(expected: dict[int,str],
                                      actual: dict[int,str]) -> dict:
    """Distinguish empty v11n reader slots and possible adjacent verse merges.

    Compare existing real strings only. No synthetic verse is fabricated and
    all proposed associations remain unapproved until publisher v11n review.
    """
    source_only=sorted(set(expected)-set(actual))
    reader_only=sorted(set(actual)-set(expected))
    classes=[]
    for v in source_only:
        prev=v-1
        can_compare=prev in expected and prev in actual
        adjacent_merged=(
            _no_whitespace(actual[prev])
            ==_no_whitespace(expected[prev])+_no_whitespace(expected[v])
            if can_compare else False
        )
        classes.append({
            "verse":v,
            "side":"source_only",
            "classification":(
                "readback_preceding_slot_contains_both_verse_character_streams"
                if adjacent_merged else "unresolved_missing_verse_index"
            ),
            "preceding_slot_compared":can_compare,
            "no_reversification_applied":True,
        })
    for v in reader_only:
        classes.append({
            "verse":v,
            "side":"reader_only",
            "classification":(
                "empty_readback_verse_slot"
                if not actual[v].strip() else "unexpected_populated_reader_slot"
            ),
            "no_reversification_applied":True,
        })
    source_stream=_no_whitespace("".join(expected[k] for k in sorted(expected)))
    reader_stream=_no_whitespace("".join(actual[k] for k in sorted(actual)))
    return {
        "source_only_verses":source_only,
        "reader_only_verses":reader_only,
        "complete_chapter_character_stream_equal_ignoring_whitespace":
            source_stream==reader_stream,
        "source_characters_excluding_whitespace":len(source_stream),
        "reader_characters_excluding_whitespace":len(reader_stream),
        "diagnostic_slot_classes":classes,
        "all_verse_reference_slots_verified":not source_only and not reader_only,
        "editorial_and_versification_approved":False,
    }




def count_reader_only_asterisks(source: str, rendered: str) -> int | None:
    """Conservatively count only inserted literal '*' codepoints.

    The original entire source character stream must be a left-to-right
    subsequence of reader output. Missing/altered source punctuation, digits
    or letters cannot pass. Does not infer a safe transformation.
    """
    i=j=0
    extra=0
    while j<len(rendered):
        if i<len(source) and source[i]==rendered[j]:
            i+=1
            j+=1
        elif rendered[j]=="*":
            extra+=1
            j+=1
        else:
            return None
    return extra if i==len(source) else None


def classify_chapter_readback_wrappers(expected: dict[int,str],
                                       actual: dict[int,str]) -> dict:
    """Check known whole-verse diatheke emphasis wrappers without editing text.

    Only an exact balanced '* <verse> *' wrapper, around a verse without
    source asterisks, can be diagnosed as *visual*. Other changes stay red.
    """
    source=_no_whitespace("".join(expected[v] for v in sorted(expected)))
    raw=_no_whitespace("".join(actual[v] for v in sorted(actual)))
    corrected=[]
    count=0
    for v in sorted(actual):
        rendered=actual[v]
        if v in expected and explain_wrapper(expected[v],rendered):
            rendered=expected[v]
            count+=1
        corrected.append(rendered)
    stripped=_no_whitespace("".join(corrected))
    residual_stars=count_reader_only_asterisks(source,stripped)
    return {
        "source_and_reader_character_stream_equal":source==raw,
        "character_stream_equal_after_exact_display_wrappers":source==stripped,
        "exact_whole_verse_visual_wrappers":count,
        "remaining_changes_consist_only_of_added_reader_asterisks":
            residual_stars is not None,
        "reader_only_residual_asterisk_count":residual_stars,
        "source_non_whitespace_characters":len(source),
        "reader_non_whitespace_characters":len(raw),
        "source_sha256":_sha(source.encode("utf-8")),
        "reader_sha256":_sha(raw.encode("utf-8")),
        "approved_for_publication":False,
    }


def full_index_roundtrip(source: bytes, *, root: Path, reader: str,
                         module_id: str="fraLSG1910eb") -> dict:
    """Read all source chapters in rebuilt module; never export their text."""
    from collections import Counter
    usfx,keys=scan_usfx(source)
    plan=chapter_plan(keys,full=True)
    source_verses,_=usfx_text_by_verse(source,filter_books=set(plan))
    totals=Counter()
    examples=[]
    index_key_mismatches=[]
    unmatched_slot_classes=[]
    chapter_stream_parity=0
    wrapper_stream_parity=0
    verified_visual_wrappers=0
    chapters_matching_after_asterisk_only_diagnostic=0
    first_unexplained_chapter_streams=[]
    books=[]
    for code,(book_name,chapters) in plan.items():
        book_checks=Counter()
        source_continuous=[]
        sword_continuous=[]
        for chapter in chapters:
            ref=f"{book_name} {chapter}"
            exit_code,body=query(module_id,ref,
                fmt="plain",root=root,exe=reader,limit=4*1024*1024,timeout=30)
            if not present_key(ref,body,exit_code):
                raise PilotError(f"Full SWORD index has no readable chapter: {ref}")
            actual=parse_sword_chapter(body,chapter,module_id)
            expected={v:text for (b,c,v),text in source_verses.items()
                      if b==code and c==chapter}
            source_only=set(expected)-set(actual)
            sword_only=set(actual)-set(expected)
            chapter_slot_audit=classify_chapter_slot_differences(expected,actual)
            chapter_stream_parity+=chapter_slot_audit[
                "complete_chapter_character_stream_equal_ignoring_whitespace"]
            display_audit=classify_chapter_readback_wrappers(expected,actual)
            wrapper_stream_parity+=display_audit[
                "character_stream_equal_after_exact_display_wrappers"]
            verified_visual_wrappers+=display_audit[
                "exact_whole_verse_visual_wrappers"]
            chapters_matching_after_asterisk_only_diagnostic+=display_audit[
                "remaining_changes_consist_only_of_added_reader_asterisks"]
            if (not display_audit[
                    "character_stream_equal_after_exact_display_wrappers"]
                    and len(first_unexplained_chapter_streams)<50):
                first_unexplained_chapter_streams.append({
                    "book":code,"chapter":chapter,**display_audit,
                })
            if (source_only or sword_only) and len(unmatched_slot_classes)<70:
                unmatched_slot_classes.append({
                    "book":code,"chapter":chapter,**chapter_slot_audit,
                })
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
        "unmatched_verse_slot_classification":unmatched_slot_classes,
        "chapters_with_equal_continuous_text_ignoring_whitespace":chapter_stream_parity,
        "all_chapter_content_preserved_without_spaces":chapter_stream_parity==1189,
        "chapters_matching_after_exact_visual_wrappers":wrapper_stream_parity,
        "recognized_whole_verse_reader_emphasis_wrappers":verified_visual_wrappers,
        "chapters_where_every_residual_difference_is_added_asterisk_only":
            chapters_matching_after_asterisk_only_diagnostic,
        "first_unexplained_chapter_character_streams":first_unexplained_chapter_streams,
        "source_key_count_matches":totals["source_keys_missing"]==0
          and totals["sword_keys_unexpected"]==0
          and totals["source_verses"]==len(keys)
          and totals["sword_verses"]==len(keys),
        "complete_text_and_note_parity_verified":False,
        "module_not_published":True,
    }


def compile_candidate(osis: Path, *, compiler="osis2mod", reader="diatheke",
                      source_usfx: bytes | None=None, versification: str=PROBE_V11N) -> dict:
    # Explicit, reviewed registry allowlist: this is diagnostic, not a
    # request to rewrite source IDs or to publish a second edition.
    if versification not in {PROBE_V11N, ALTERNATE_PROBE_V11N}:
        raise PilotError("Unreviewed SWORD versification in LSG trial")
    before=osis.read_bytes()
    report={
        "status":"rebuild_probe_not_approved",
        "original_osis_sha256":_sha(before),
        "source_file_unchanged":True,
        "published":False,
        "approved_for_publication":False,
        "versification":versification,
        "publisher_declared_versification":PUBLISHER_DECLARED_V11N,
        "publisher_v11n_matches_diagnostic_probe":versification==PUBLISHER_DECLARED_V11N,
        "versification_approved":False,
        "module_id":"fraLSG1910eb",
        "real_module_rebuilt_in_temporary_directory":False,
        "all_source_verses_and_annotations_checked":False,
    }
    with tempfile.TemporaryDirectory(prefix="bible-lsg-segond-real-") as home:
        root=Path(home)
        data=root/"modules/texts/rawtext/fralsg1910eb"
        data.mkdir(parents=True)
        result=subprocess.run(
            [compiler,str(data),str(osis),"-v",versification],
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
            "v11n_outside":len(re.findall(
                rb"not in the "+versification.encode("ascii")+rb" versification",logs)),
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
            f"Versification={versification}\n"
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
        # A failed spot-check must not suppress a full index diagnostic:
        # alternate French registries can expose different verse maxima.
        if source_usfx is not None and report["real_module_rebuilt_in_temporary_directory"]:
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
