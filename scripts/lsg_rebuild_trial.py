#!/usr/bin/env python3
"""First *real* eBible USFM->OSIS candidate reconstruction, without publication.

Run only with explicitly pinned u2o.py and the exact eBible source archives.
No text or compiled modules are put in GitHub artifacts, only a provenance
and structure report. Any source, markup or verse mismatch blocks approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

from lxml import etree

from guard_osis import ROOT, _schema, inspect as inspect_osis, StructureFailure
from lsg_source_compare import (
    read_source_xml, scan_usfm, scan_osis, scan_usfx, compare_usfm_usfx,
)
from pilot_preflight import PilotError, inspect_archive
from pilot_subprocess import MAX_OUTPUT
from lsg_osis_parity import compare as compare_osis
from lsg_sword_rebuild import compile_candidate


CONVERTER_COMMIT = "dde28bc545e8d8697fa5496c243187847ec55d31"
MAX_CONVERTER_SECONDS = 180
MAX_COMPILED_BYTES = 128 * 1024 * 1024


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_files(usfm_zip: Path, destination: Path) -> list[Path]:
    inspected = inspect_archive(usfm_zip, source_kind="authored")
    files = []
    with zipfile.ZipFile(usfm_zip) as archive:
        for member in inspected["members"]:
            name=member["name"]
            if not name.lower().endswith((".usfm", ".sfm")):
                continue
            info=archive.getinfo(name)
            if info.is_dir():
                continue
            # Names have been safety-checked by the ZIP preflight.
            target=destination/PurePosixPath(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("xb") as output:
                while chunk:=source.read(262144):
                    output.write(chunk)
            files.append(target)
    if len(files)!=66:
        raise PilotError(f"Source USFM must contain exactly 66 books, found {len(files)}")
    return sorted(files)



def _debug_usfm_verse_markers(files: list[Path]) -> None:
    """Emit a few bounded public-domain authoring snippets to CI logs only.

    No raw USFM is included in the JSON report, artifacts or repository.
    Match chapters and verse openings rather than guessing from content.
    """
    targets={("MAT",9,6),("MRK",8,19),("LUK",8,8),
             ("JHN",5,8),("REV",1,8)}
    for file in files:
        content=file.read_text(encoding="utf-8-sig")
        match=re.search(r"(?m)^\\id\s+([A-Z0-9]{3})\b",content)
        if match is None:
            continue
        book=match.group(1)
        if not any(item[0]==book for item in targets):
            continue
        chapter=None
        for marker in re.finditer(r"(?m)^[ \t]*\\(c|v)\s+(\d+)\b",content):
            if marker.group(1)=="c":
                chapter=int(marker.group(2))
            elif chapter is not None:
                key=(book,chapter,int(marker.group(2)))
                if key in targets:
                    snippet=content[max(0,marker.start()-75):marker.start()+260]
                    print("USFM_SOURCE_MARKER_SAMPLE",f"{book}.{chapter}.{key[2]}",repr(snippet))



def _debug_converted_verse_markup(path: Path) -> None:
    """Show bounded, opt-in OSIS fragments only in temporary CI logs.

    These are public-domain pilot excerpts to explain verse boundaries; no
    XML or biblical text is written to GitHub artifacts or source control.
    """
    xml=path.read_text(encoding="utf-8")
    for reference in ("Matt.9.6","Mark.8.19","Luke.8.8",
                      "John.5.8","Rev.1.8"):
        marker=f'sID="{reference}"'
        index=xml.find(marker)
        if index<0:
            print("OSIS_VERSE_MARKUP_SAMPLE",reference,"missing_opening_marker")
            continue
        opening=xml.rfind("<verse",0,index)
        start=max(0,opening-440)
        excerpt=xml[start:min(len(xml),index+700)]
        print("OSIS_VERSE_MARKUP_SAMPLE",reference,repr(excerpt))
        closing=xml.find(f'eID="{reference}"',index)
        if closing>=0:
            print("OSIS_VERSE_END_SAMPLE",reference,
                  repr(xml[max(0,closing-240):min(len(xml),closing+300)]))


def _original_usfm_intro_markers(archive: Path, target_id: str) -> dict:
    """Find introductory source markers without exposing their text."""
    with zipfile.ZipFile(archive) as source:
        matches=[]
        for record in source.infolist():
            if not record.filename.casefold().endswith((".usfm",".sfm")):
                continue
            sample=source.read(record).decode("utf-8-sig")
            found=re.search(r"(?m)^\\id\s+(\S+)",sample)
            if found and found.group(1)==target_id:
                matches.append((record.filename,sample))
        if len(matches)!=1:
            raise PilotError(f"Expected unique source USFM book ID {target_id}")
        path,content=matches[0]
    intro=re.split(r"(?m)^\\c\s+1\b",content,maxsplit=1)[0]
    marker_events=[]
    totals=Counter()
    for i,line in enumerate(intro.splitlines(),1):
        marks=re.findall(r"\\([A-Za-z][A-Za-z0-9_+-]*)(?:\*|\b)",line)
        totals.update(marks)
        if marks:
            marker_events.append({"line":i,"markers":marks[:30]})
    return {
        "source_file_name":path,
        "source_sha256":_sha(content.encode("utf-8-sig")),
        "lines_before_first_chapter":len(intro.splitlines()),
        "marker_counts":dict(sorted(totals.items())),
        "last_intro_markers":marker_events[-60:],
        "source_content_not_published":True,
    }


def _malformed_xml_diagnostic(path: Path, exc: etree.XMLSyntaxError) -> dict:
    """Only report local markup skeleton; never include actual biblical text."""
    line=max(1,int(exc.position[0]))
    # Read through the source once; no raw lines or attribute values leave
    # the temporary runner.
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    near=[]
    # Diagnose a structural converter problem without copying any Scripture.
    # This is a simple tag-stack *diagnostic* only; never repairs XML.
    div_events=[]
    stack=[]
    orphan=[]
    for n, raw_line in enumerate(lines[:line+1],1):
        for match in re.finditer(r"<(/?)div\b([^>]*)>",raw_line):
            closing, raw_attrs=match.groups()
            if closing:
                before=len(stack)
                prior=stack.pop() if stack else None
                div_events.append({"line":n,"event":"close",
                                   "opens_before":before,"matching_open":prior})
                if not prior:
                    orphan.append(n)
            else:
                kind=re.search(r'\btype="([^"]{1,60})"',raw_attrs)
                osis_id=re.search(r'\bosisID="([^"]{1,50})"',raw_attrs)
                record={"line":n,"type":kind[1] if kind else "",
                        "osis_id":osis_id[1] if osis_id else ""}
                stack.append(record)
                div_events.append({"line":n,"event":"open","node":record,
                                   "opens_after":len(stack)})
        if len(div_events)>25:
            div_events=div_events[-25:]
    suspect=next((event["line"] for event in reversed(div_events)
                  if event["event"]=="close"
                  and (event.get("matching_open") or {}).get("type")=="book"),None)
    if suspect and suspect < line-30:
        for n in range(max(1,suspect-18),min(len(lines),suspect+18)+1):
            tags=re.findall(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9:_-]*)\b",lines[n-1])
            if tags:
                near.append({"line":n,"section":"last_book_close",
                             "tags":[("/" if closed else "")+tag for closed,tag in tags[:45]]})
    for n in range(max(1,line-12),min(len(lines),line+12)+1):
        tags=re.findall(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9:_-]*)\b",lines[n-1])
        if tags:
            near.append({"line":n,"tags":[("/" if closed else "")+tag for closed,tag in tags[:30]]})
    return {
        "line":line,"column":int(exc.position[1]),
        "error_kind":"misnested_or_malformed_XML",
        "nearby_element_names_only":near,
        "last_div_events":div_events[-25:],
        "first_orphan_div_close":orphan[0] if orphan else None,
        "current_div_stack_tail":stack[-10:],
        "source_xml_sha256":_sha(path.read_bytes()),
        "corrective_action":"review_converter_and_original_USFM_not_silent_XML_recovery",
    }


def _osis_summary(output: Path, original_usfx: bytes, expected_books: list[str]) -> dict:
    size=output.stat().st_size if output.exists() else 0
    if not size or size>MAX_COMPILED_BYTES:
        raise PilotError("Converted source missing or exceeds 128MiB")
    raw=output.read_bytes()
    structure,ids=scan_osis(raw)
    usfx,original_keys=scan_usfx(original_usfx)
    if len(ids)!=len(set(ids)):
        raise PilotError("Duplicate converted opening verse IDs")
    root=etree.fromstring(raw,parser=etree.XMLParser(resolve_entities=False,
              load_dtd=False,no_network=True,recover=False,huge_tree=False))
    canonical=[n.get("osisID") for n in root.iter()
               if isinstance(n.tag,str) and n.tag.endswith("}div")
               and n.get("type")=="book"]
    original=[n.get("id") for n in etree.fromstring(original_usfx).iter("book")]
    if len(canonical)!=66 or len(original)!=66 or len(set(canonical))!=66:
        raise PilotError("Unexpected original/converted book count or duplicate book")
    mapped={source:target for source,target in zip(original,canonical)}
    if len(mapped)!=66:
        raise PilotError("Nonunique source IDs in original USFX")
    expected={f"{mapped[b]}.{c}.{v}" for b,c,v in original_keys}
    converted=set(ids)
    missing=sorted(expected-converted)
    extra=sorted(converted-expected)
    structure["original_source_book_to_osis_id"]=mapped
    return {
        "source_xml_sha256":_sha(raw),
        "source_xml_bytes":size,
        "tag_counts":structure["source_elements"],
        "source_book_count":len(canonical),
        "converted_verse_openings":len(ids),
        "converted_unique_verse_keys":len(converted),
        "publisher_source_verse_keys":len(expected),
        "verse_keys_missing_from_converted":len(missing),
        "verse_keys_unexpected_in_converted":len(extra),
        "missing_first_30":missing[:30],
        "unexpected_first_30":extra[:30],
        "book_id_mapping":mapped,
        "generated_xml_is_original_source":False,
        "source_text_equivalent":False,
        "notes_verified":False,
        "references_verified":False,
        "candidate_xml_schema_validated":False,
        "candidate_structural_policy_validated":False,
    }


def _schema_proof(output: Path, schema: Path) -> dict:
    policy_path=ROOT/"config/osis-policy.json"
    policy=json.loads(policy_path.read_text(encoding="utf-8"))
    validator, pinned=_schema(policy, schema)
    doc=etree.parse(str(output),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,huge_tree=False))
    if not validator.validate(doc):
        issue=validator.error_log[0]
        return {
            "xsd_status":"blocked",
            "xsd_error":str(issue.message)[:260],
            "xsd_line":issue.line,
            "xsd_sha256":pinned,
            "policy_status":"not_run_due_invalid_xsd",
        }
    proof={"xsd_status":"validated","xsd_sha256":pinned}
    try:
        detail=inspect_osis(output,schema)
    except StructureFailure as e:
        proof.update({"policy_status":"blocked","policy_code":e.code,
                      "policy_line":e.line,"policy_reason":e.detail[:240]})
    else:
        proof.update({"policy_status":"validated",
                      "policy_sha256":detail["policy_sha256"]})
    return proof



def _marker_evidence(parity: dict) -> dict:
    """Separate obsolete at-line-opening counts from verified verse ownership.

    A <l>/<q> can span multiple sID/eID milestones and Selah is an inline
    character style rather than a poetic line. The old opener counter remains
    reported but cannot itself veto independently verified source structure.
    """
    expected=parity["total_source_verse_keys"]
    poetry=parity["source_to_candidate_poetry_verse_owned_audit"]
    lexical_and_notes=(
        parity["exact_normalized_word_sequences"]==expected
        and parity["matching_verse_note_counts"]==expected
        and parity["unconverted_usfm_markup_diagnostic"]["no_unconverted_usfm_markup"]
    )
    lyric=poetry["all_poetry_segments_and_levels_verified"]
    selah=poetry["all_selah_text_and_verse_positions_verified"]
    return {
        "legacy_poetry_opening_position_counts_equal":
            parity["matching_verse_poetry_line_counts"]==expected,
        "source_owned_poetry_segments_and_levels_equal":lyric,
        "source_selah_marker_text_and_verse_equal":selah,
        "source_marker_counts_parity":lexical_and_notes and lyric and selah,
        "full_poetry_editorial_layout_approved":False,
    }

def run(usfm_zip: Path, usfx_zip: Path, converter: Path, schema: Path) -> dict:
    source=scan_usfm(usfm_zip)
    original_xml,original_meta=read_source_xml(usfx_zip,source_format="usfx")
    original,original_keys=scan_usfx(original_xml)
    same=compare_usfm_usfx(source,original,original_keys)
    if (same.get("status")!="verse_key_sets_equal" or
            source["summary"]["verse_keys"]!=31170 or
            original["book_count"]!=66):
        raise PilotError("Publisher original USFM/USFX reference sets are not exactly aligned")
    report={
        "schema_version":1,
        "status":"candidate_conversion_inspected_not_approved",
        "converter":"adyeths/u2o.py",
        "converter_pinned_commit":CONVERTER_COMMIT,
        "converter_sha256":_sha(Path(converter).read_bytes()),
        "source_usfm_archive_sha256":source["archive_sha256"],
        "source_usfx_archive_sha256":original_meta["archive_sha256"],
        "source_usfx_document_sha256":original_meta["sha256"],
        "source_to_source_verse_key_status":same["status"],
        "source_verse_keys":source["summary"]["verse_keys"],
        "source_poetry_markers":source["summary"]["poetry_markers"],
        "source_paragraph_markers":source["summary"]["paragraph_markers"],
        "source_text_modified":False,
        "candidate_published":False,
        "all_verse_text_fidelity_verified":False,
        "notes_and_cross_references_verified":False,
    }
    with tempfile.TemporaryDirectory(prefix="bible-lsg-real-import-") as tmp:
        root=Path(tmp)
        usfm_files=_safe_files(usfm_zip,root/"usfm")
        if os.getenv("LSG_SAMPLE_DEBUG")=="1":
            _debug_usfm_verse_markers(usfm_files)
        candidate=root/"candidate.osis.xml"
        command=[sys.executable,str(converter),"Bible.fraLSG1910eb",
                 "-l","fr","-x","-o",str(candidate),*map(str,usfm_files)]
        proc=subprocess.run(command,capture_output=True,timeout=MAX_CONVERTER_SECONDS,
                            check=False,cwd=root)
        if len(proc.stdout)+len(proc.stderr)>MAX_OUTPUT:
            raise PilotError("Converter stdout/stderr exceeded bounded audit limit")
        report["conversion_command_completed"]=proc.returncode==0
        report["converter_return_code"]=proc.returncode
        report["converter_diagnostics_sha256"]=_sha(proc.stdout+b"\0"+proc.stderr)
        if proc.returncode!=0 or not candidate.is_file():
            report["status"]="blocked_converter_failure"
            report["converter_diagnostics_last_line"]="(omitted: original text may be present)"
            return report
        try:
            report["osis_candidate"]=_osis_summary(candidate,original_xml,source["_book_order"])
        except etree.XMLSyntaxError as exc:
            report["status"]="blocked_malformed_converted_osis"
            report["conversion_xml_diagnostic"]=_malformed_xml_diagnostic(candidate,exc)
            report["jhn_source_intro_diagnostic"]=_original_usfm_intro_markers(usfm_zip,"JHN")
            return report
        report["osis_schema"]=_schema_proof(candidate,schema)
        if os.getenv("LSG_SAMPLE_DEBUG")=="1":
            _debug_converted_verse_markup(candidate)
        report["source_to_generated_osis"]=compare_osis(candidate,original_xml)
        note_audit=report["source_to_generated_osis"]["source_to_candidate_note_content_audit"]
        report["note_content_and_reference_text_parity"]=note_audit[
            "textual_target_references_verified"]
        report["note_editorial_metadata_parity"]=note_audit[
            "all_note_contents_metadata_and_positions_verified"]
        # Real, disposable diagnostic compilation is allowed only after the
        # full original OSIS document passes both the official pinned XSD
        # and the separately reviewed structural policy.
        if (report["osis_schema"]["xsd_status"]=="validated"
                and report["osis_schema"]["policy_status"]=="validated"):
            report["real_segond_sword_trial"]=compile_candidate(candidate,source_usfx=original_xml)
        report["structure_key_sets_equal"]=(
           report["osis_candidate"]["verse_keys_missing_from_converted"]==0
           and report["osis_candidate"]["verse_keys_unexpected_in_converted"]==0
        )
        # Keep the entire candidate private. No temporary OSIS source or
        # third-party data is uploaded, even if XSD or content check fails.
        parity=report["source_to_generated_osis"]
        report["canonical_verse_text_parity"]=(
            parity["exact_normalized_verse_text_matches"]==parity["total_source_verse_keys"]
        )
        report.update(_marker_evidence(parity))
        report["status"]=(
            "candidate_verse_text_and_marker_parity_checked_not_approved"
            if report["structure_key_sets_equal"]
               and report["osis_schema"]["xsd_status"]=="validated"
               and report["osis_schema"]["policy_status"]=="validated"
               and report["canonical_verse_text_parity"]
               and report["source_marker_counts_parity"]
            else "candidate_parity_mismatch_or_schema_blocked"
        )
    return report


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--usfm-zip",type=Path,required=True)
    ap.add_argument("--usfx-zip",type=Path,required=True)
    ap.add_argument("--converter",type=Path,required=True)
    ap.add_argument("--schema",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    args=ap.parse_args(argv)
    try:
        result=run(args.usfm_zip,args.usfx_zip,args.converter,args.schema)
        code=0 if result["status"]=="candidate_verse_text_and_marker_parity_checked_not_approved" else 1
    except (OSError,ValueError,StructureFailure,etree.XMLSyntaxError,
            subprocess.TimeoutExpired,zipfile.BadZipFile) as exc:
        result={"status":"blocked","category":type(exc).__name__,
                "detail":str(exc)[:250],"source_text_modified":False}
        code=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"LSG converter trial: {result['status']}")
    return code


if __name__=="__main__":
    raise SystemExit(main())
