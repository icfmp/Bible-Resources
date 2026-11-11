#!/usr/bin/env python3
"""Build two isolated SWORD research candidates from exact official OSIS.

Research-only: compile original bytes via standard osis2mod, inspect with the
*actual* native libSWORD and discard every temporary module. Emit bounded
source-vs-reader evidence, not Bible text, note bodies or a release package.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from lxml import etree

from bible_intake import ROOT
from publisher_osis_observation import read_pinned_publisher_osis
from publisher_osis_usfx_parity import (
    original_osis_verses_and_notes, _nonspace, _fold,
)
from source_native_maintext_probe import native_raw_main_text
from source_native_note_positions import native_note_anchor_positions
from source_osis_inventory import source_inventory
from native_milestone_pair_audit import NativeMilestonePairAudit
from sword_native_inventory import collect_native_inventory
from stable_sword_refs import KEY

MODULE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,48}\Z")
SYSTEM = re.compile(r"[A-Za-z][A-Za-z0-9]{1,31}\Z")
RESOURCE = re.compile(r"[a-z0-9][a-z0-9-]{1,48}\Z")
MAX_SAMPLE = 15
MAX_ENTRY = 2 * 1024 * 1024
MAX_LOG = 32 * 1024 * 1024
MAX_FRAMES = 350_000


class PublisherSWORDResearchError(ValueError):
    """SWORD research candidate is incomplete, contradictory, or unsafe."""


def config_for(resource_id):
    if not RESOURCE.fullmatch(resource_id):
        raise PublisherSWORDResearchError("Invalid source research ID")
    path=ROOT/"config/publisher-sword-research"/f"{resource_id}.json"
    if not path.is_file() or path.is_symlink():
        raise PublisherSWORDResearchError("No reviewed compilation candidate config")
    cfg=json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(cfg,dict) or set(cfg)!={
            "schema_version","resource_id","purpose","publisher_source_manifest",
            "candidate_module_id","candidate_versifications","compression","note"}
            or cfg["schema_version"]!=1 or cfg["resource_id"]!=resource_id
            or cfg["purpose"]!="research_only"
            or cfg["publisher_source_manifest"]!=
                f"config/publisher-osis/{resource_id}.json"
            or cfg["compression"]!="zip"
            or not MODULE.fullmatch(cfg["candidate_module_id"])
            or not isinstance(cfg["candidate_versifications"],list)
            or not 1<=len(cfg["candidate_versifications"])<=4
            or any(not isinstance(v,str) or not SYSTEM.fullmatch(v)
                   for v in cfg["candidate_versifications"])
            or len(set(cfg["candidate_versifications"]))!=len(cfg["candidate_versifications"])
            or not isinstance(cfg["note"],str) or len(cfg["note"])>250):
        raise PublisherSWORDResearchError("Unreviewed compilation candidate settings")
    return cfg


def _create_candidate_layout(folder: Path, module_id: str, system: str):
    """Create separate normal SWORD root and one strict research-only .conf."""
    if not MODULE.fullmatch(module_id) or not SYSTEM.fullmatch(system):
        raise PublisherSWORDResearchError("Unsafe original source candidate module identity")
    name=module_id.lower()
    payload=folder/"payload"
    conf=payload/"mods.d"/f"{name}.conf"
    out=payload/"modules"/"texts"/"ztext"/name
    out.mkdir(parents=True,exist_ok=False)
    conf.parent.mkdir(parents=True,exist_ok=False)
    conf.write_text(
        f"[{module_id}]\n"
        f"DataPath=./modules/texts/ztext/{name}/\n"
        "ModDrv=zText\n"
        "BlockType=BOOK\n"
        "CompressType=ZIP\n"
        "Encoding=UTF-8\n"
        "Lang=fr\n"
        "SourceType=OSIS\n"
        f"Versification={system}\n"
        "Description=Publisher original OSIS research-only unapproved module\n"
        "Version=0.0.0-research\n"
        "GlobalOptionFilter=OSISFootnotes\n"
        "GlobalOptionFilter=OSISXRefs\n",
        encoding="utf-8")
    return payload,out


def _compile_osis(tool: Path, outfile: Path, module_path: Path, system: str,
                  log_path: Path):
    if not tool.is_file() or tool.is_symlink() or not outfile.is_file():
        raise PublisherSWORDResearchError("Missing trusted compiler or original pinned OSIS")
    with log_path.open("xb") as log:
        try:
            cmd=[str(tool.resolve(strict=True)),str(module_path),
                 str(outfile),"-z","z","-b","4","-v",system]
            process=subprocess.run(cmd,stdout=log,stderr=log,check=False,timeout=420)
        except subprocess.TimeoutExpired as exc:
            raise PublisherSWORDResearchError("Official OSIS compiler exceeded bounded timeout") from exc
        except OSError as exc:
            raise PublisherSWORDResearchError("Official OSIS compiler failed to launch") from exc
    if log_path.stat().st_size>MAX_LOG:
        raise PublisherSWORDResearchError("OSIS tool emitted excessive diagnostics")
    # Never print raw compiler stdout/stderr: even diagnostic messages can
    # include quoted Scripture/notes. Keep only bounded category counts.
    lines=log_path.read_text(encoding="utf-8",errors="replace").splitlines()
    categories=Counter()
    first_safe=[]
    for line in lines:
        u=line.upper()
        found=next((k for k in ("FATAL","ERROR","WARNING","INFO")
                    if u.startswith(k+"(")),"unclassified")
        categories[found]+=1
        # Original line and column are safe, body text is not.
        match=re.search(r"\[(\d{1,8}),(\d{1,8})\]",line)
        if found in {"FATAL","ERROR","WARNING"} and match and len(first_safe)<MAX_SAMPLE:
            first_safe.append({"type":found,
                               "source_line":int(match.group(1)),
                               "source_column":int(match.group(2))})
    if process.returncode!=0:
        raise PublisherSWORDResearchError(
            f"OSIS tool returned nonzero exit status {process.returncode}")
    return {"compiler_tool":"osis2mod","tool_sha256":sha256(tool.read_bytes()).hexdigest(),
            "returncode":process.returncode,
            "diagnostic_categories":dict(sorted(categories.items())),
            "first_diagnostic_locations_no_source_text":first_safe,
            "compiler_log_is_private_and_discarded":True}


def _read_native_frames(reader: Path, module_id: str, payload: Path):
    """Generate raw XML in a private pipe, never GitHub stdout or artifacts."""
    env=dict(os.environ,SWORD_PATH=str(payload.resolve(strict=True)))
    command=[str(reader.resolve(strict=True)),module_id]
    try:
        p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env)
    except OSError as exc:
        raise PublisherSWORDResearchError("Trusted native reader cannot execute") from exc
    count=Counter()
    try:
        while True:
            header=p.stdout.readline(192)
            if not header:
                raise PublisherSWORDResearchError("Native raw reader ended without checksum trailer")
            if len(header)>=192 or not header.endswith(b"\n"):
                raise PublisherSWORDResearchError("Unsafe raw native entry frame header")
            line=header.decode("ascii",errors="strict").rstrip("\n")
            cells=line.split("\t")
            if cells[0]=="S":
                if len(cells)!=5:
                    raise PublisherSWORDResearchError("Malformed native frame trailer")
                expected=tuple(map(int,cells[1:]))
                if expected!=(sum(count.values()),count["K"],count["I"],count["U"]):
                    raise PublisherSWORDResearchError("Native frame count mismatch")
                if p.stdout.read(1):
                    raise PublisherSWORDResearchError("Unexpected trailing native raw bytes")
                try:
                    if p.wait(timeout=15)!=0:
                        raise PublisherSWORDResearchError(
                            "Native raw reader returned nonzero after final frame")
                except subprocess.TimeoutExpired as exc:
                    raise PublisherSWORDResearchError(
                        "Native raw reader failed to terminate") from exc
                break
            if len(cells)!=3 or cells[0] not in {"K","I","U"}:
                raise PublisherSWORDResearchError("Invalid native entry frame type")
            kind,ref,number=cells
            if kind=="K" and KEY.fullmatch(ref) is None:
                raise PublisherSWORDResearchError("Unsafe populated native verse reference")
            if not number.isdecimal() or int(number)>MAX_ENTRY:
                raise PublisherSWORDResearchError("Invalid native raw XML fragment size")
            raw=p.stdout.read(int(number))
            if len(raw)!=int(number):
                raise PublisherSWORDResearchError("Truncated native raw XML frame")
            count[kind]+=1
            if sum(count.values())>MAX_FRAMES:
                raise PublisherSWORDResearchError("Native corpus exceeded safe size")
            yield kind,ref,raw
    finally:
        p.stdout.close()
        if p.poll() is None:
            p.kill()
        p.wait(timeout=15)


def _native_notes(raw: bytes):
    try:
        root=etree.fromstring(
            b"<private_root>"+raw+b"</private_root>",
            etree.XMLParser(resolve_entities=False,load_dtd=False,
                            no_network=True,recover=False,huge_tree=False))
    except etree.XMLSyntaxError as exc:
        raise PublisherSWORDResearchError("Invalid native raw XML note structure") from exc
    if any(isinstance(x,etree._Entity) for x in root.iter()):
        raise PublisherSWORDResearchError("Native source contains unresolved entity")
    return [
        {"caller":n.get("n"),"type":n.get("type"),
         "body":"".join(n.itertext()),
         "targets":tuple(x.get("osisRef") for x in n.iterdescendants()
                         if isinstance(x.tag,str)
                         and etree.QName(x).localname=="reference" and x.get("osisRef"))}
        for n in root.iter()
        if isinstance(n.tag,str) and etree.QName(n).localname=="note"
    ]


def _candidate_result(index_binary: Path,raw_binary: Path,
                      candidate_dir: Path,module_id: str,system: str,
                      source: dict,notes: dict):
    native_keys,_,inventory=collect_native_inventory(
        index_binary,candidate_dir,module_id)
    source_set=set(source)
    native_set=set(native_keys.splitlines())
    counts=Counter()
    samples=defaultdict(list)
    def sample(category,ref,**extra):
        if len(samples[category])<MAX_SAMPLE:
            samples[category].append({"reference":ref,"kind":category,**extra})
    for ref in sorted(source_set-native_set):
        sample("authored_source_verse_not_populated",ref)
    for ref in sorted(native_set-source_set):
        sample("unexpected_populated_native_verse",ref)
    counts["official_source_verse_count"]=len(source_set)
    counts["populated_native_verse_count"]=len(native_set)
    counts["source_only_references"]=len(source_set-native_set)
    counts["native_only_references"]=len(native_set-source_set)

    indexed_seen=set()
    milestones=NativeMilestonePairAudit()
    for kind,ref,raw in _read_native_frames(raw_binary,module_id,
                                           candidate_dir/"payload"):
        milestones.observe(kind,ref,raw)
        if kind!="K":
            counts["native_other_"+kind+"_entries"]+=1
            continue
        indexed_seen.add(ref)
        if ref not in source:
            continue
        original=source[ref]
        try:
            native_prose,_discarded=native_raw_main_text(raw)
            matching=_nonspace(original)==_nonspace(native_prose)
        except (ValueError,UnicodeError):
            matching=False
        if matching:
            counts["numbered_verse_nonspace_main_text_equal"]+=1
        else:
            counts["numbered_verse_nonspace_main_text_differs_or_unparseable"]+=1
            sample("numbered_verse_word_or_punctuation_difference",ref)
        expected=notes[ref]
        try:
            native=_native_notes(raw)
        except (ValueError,UnicodeError):
            counts["numbered_verse_note_xml_invalid"]+=1
            sample("numbered_verse_note_xml_invalid",ref)
            continue
        if len(expected)!=len(native):
            counts["numbered_verse_note_count_differs"]+=1
            sample("numbered_verse_note_count_differs",ref,
                   source_count=len(expected),compiled_count=len(native))
            continue
        counts["numbered_verse_note_count_matches"]+=1
        if matching:
            try:
                points=native_note_anchor_positions(raw,original)
            except (ValueError,UnicodeError):
                points=()
            if len(points)!=len(expected):
                counts["numbered_verse_note_positions_unverified"]+=1
            else:
                for i,(old,newpoint) in enumerate(zip(expected,points),1):
                    if old["point"]==newpoint:
                        counts["note_nonspace_anchor_equal"]+=1
                    else:
                        counts["note_nonspace_anchor_moved"]+=1
                        sample("note_nonspace_anchor_moved",ref,one_based_note=i)
        for idx,(old,new) in enumerate(zip(expected,native),1):
            counts["note_pairs_compared"]+=1
            if old["caller"]==new["caller"]:
                counts["note_original_caller_label_equal"]+=1
            else:
                counts["note_original_caller_label_different"]+=1
                sample("note_original_caller_label_different",ref,one_based_note=idx)
            if old["type"]==new["type"]:
                counts["note_original_type_equal"]+=1
            else:
                counts["note_original_type_different"]+=1
            if _fold(old["body"])==_fold(new["body"]):
                counts["note_body_equal_after_whitespace_folding"]+=1
            else:
                counts["note_body_words_or_punctuation_differ"]+=1
                sample("note_body_words_or_punctuation_differ",ref,one_based_note=idx)
            if old["targets"]==new["targets"]:
                counts["note_explicit_target_sequence_equal"]+=1
            else:
                counts["note_explicit_target_sequence_different"]+=1
                sample("note_explicit_target_sequence_different",ref,one_based_note=idx)
    if indexed_seen!=native_set:
        raise PublisherSWORDResearchError("Native index and raw corpus enumerations disagree")
    native_structure=milestones.finish()

    approved_candidate=False
    all_ok=(
        not counts["source_only_references"] and
        not counts["native_only_references"] and
        not counts["numbered_verse_nonspace_main_text_differs_or_unparseable"] and
        not counts["numbered_verse_note_count_differs"] and
        not counts["numbered_verse_note_xml_invalid"] and
        not counts["note_original_caller_label_different"] and
        not counts["note_body_words_or_punctuation_differ"] and
        not counts["note_original_type_different"] and
        not counts["note_explicit_target_sequence_different"] and
        not counts["note_nonspace_anchor_moved"] and
        not counts["numbered_verse_note_positions_unverified"] and
        counts["note_pairs_compared"]==sum(map(len,notes.values()))
    )
    return {
        "candidate_status":("full_numbered_text_and_note_preflight_equal_not_approved"
                            if all_ok else "candidate_source_native_differences_require_review"),
        "candidate_versification":system,
        "candidate_module_id":module_id,
        "compiled_payload_sha256":inventory["module_payload_sha256"],
        "compiled_engine_version":inventory["reader_version"],
        "compiled_native_milestone_closure_metadata_only":native_structure,
        "compiled_native_driver":inventory["module_driver"],
        "source_to_compiled_counts":dict(sorted(counts.items())),
        "first_safe_reference_note_index_findings":[
            x for key in sorted(samples) for x in samples[key]][:MAX_SAMPLE*6],
        "explicit_p_q_and_layout_structure_fidelity_verified":False,
        "publisher_original_note_target_navigation_verified":False,
        "visual_reader_or_parallel_reader_verified":False,
        "usable_for_publication":approved_candidate,
    }


def compiler_output_metrics(output_dir: Path) -> dict:
    """Only counts/byte sizes of the isolated standard compiler's artifacts.

    Do not reveal any generated path, filename, original text, or note.
    This is diagnostics, not proof that the index is readable.
    """
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise PublisherSWORDResearchError("Missing private compiler output directory")
    entries = list(output_dir.rglob("*"))
    if len(entries) > 1000 or any(item.is_symlink() for item in entries):
        raise PublisherSWORDResearchError("Unsafe private compiler output tree")
    files = [item for item in entries if item.is_file()]
    sizes = [item.stat().st_size for item in files]
    return {
        "files": len(files),
        "nonempty_files": sum(size > 0 for size in sizes),
        "total_bytes": sum(sizes),
        "not_reader_or_source_fidelity_approval": True,
    }


def safe_failure_code(exc: Exception) -> str:
    """Stable diagnostics only; never disclose exception strings from source/XML.

    Only messages emitted by this tool or the trusted native-index wrapper
    are recognized. Unknown exceptions are intentionally opaque.
    """
    message = str(exc)
    # Numeric exit is diagnostic metadata from our native inspector, not
    # publisher text. Never echo the remainder of an exception message.
    native_exit = re.match(r"Stock-SWORD native inspector blocked \(exit ([0-9]{1,3})\)", message)
    if native_exit:
        value = int(native_exit.group(1))
        if 1 <= value <= 255:
            return f"native_inspector_exit_{value}"
    known = (
        ("OSIS tool returned nonzero exit status ", "compiler_nonzero_exit"),
        ("Official OSIS compiler exceeded bounded timeout", "compiler_bounded_timeout"),
        ("Official OSIS compiler failed to launch", "compiler_launch_failed"),
        ("Official OSIS compiler failed or timed out", "compiler_launch_or_timeout"),
        ("OSIS tool emitted excessive diagnostics", "compiler_excessive_private_output"),
        ("Missing trusted compiler or original pinned OSIS", "compiler_or_source_missing"),
        ("Stock-SWORD native inspector blocked", "native_inspector_nonzero_exit"),
        ("Stock SWORD module contains no populated Bible verses", "native_zero_populated_verses"),
        ("Missing or symlinked module directory", "native_module_directory_missing"),
        ("Missing or symlinked SWORD configuration directory", "native_mods_directory_missing"),
        ("Missing terminal complete-inventory counts", "native_trailer_missing"),
        ("Missing, empty or implausibly large native inventory", "native_inventory_unavailable"),
        ("Native driver or v11n disagrees", "native_driver_versification_disagreement"),
        ("Native index and raw corpus enumerations disagree", "native_index_raw_mismatch"),
        ("Invalid native raw XML note structure", "native_note_xml_invalid"),
    )
    for prefix,code in known:
        if message.startswith(prefix):
            return code
    return "unclassified_private_failure"


def select_candidate_versifications(cfg: dict, requested: str | None):
    """Never invent or silently switch an unreviewed original source v11n."""
    allowed=cfg["candidate_versifications"]
    if requested is not None and requested not in allowed:
        raise PublisherSWORDResearchError("Unreviewed requested candidate versification")
    return list(allowed) if requested is None else [requested]


def probe(resource_id: str, *, osis2mod:Path,index_binary:Path,
          raw_binary:Path, versification: str | None = None):
    cfg=config_for(resource_id)
    selected=select_candidate_versifications(cfg,versification)
    original=read_pinned_publisher_osis(resource_id)
    source_keys,source_meta=source_inventory(original)
    verses,notes,source_check=original_osis_verses_and_notes(original)
    if (set(verses)!=set(source_keys.splitlines())
            or source_check["publisher_numbered_verse_count"]!=
               source_meta["source_verse_count"]):
        raise PublisherSWORDResearchError("Independent publisher source inventories differ")
    results=[]
    with tempfile.TemporaryDirectory(prefix="bible-official-osis-compile-research-") as root:
        tmp=Path(root)
        sourcefile=tmp/"source-authored-pinned.osis.xml"
        sourcefile.write_bytes(original)
        for system in selected:
            work=tmp/("research-"+system)
            work.mkdir()
            payload,out=_create_candidate_layout(
                work,cfg["candidate_module_id"],system)
            compilation=None
            try:
                compilation=_compile_osis(
                    osis2mod,sourcefile,out,system,work/"osis2mod-private.log")
                compared=_candidate_result(
                    index_binary,raw_binary,work,
                    cfg["candidate_module_id"],system,verses,notes)
                compared["standard_osis_compiler"]=compilation
            except (PublisherSWORDResearchError,ValueError,OSError,
                    subprocess.TimeoutExpired) as exc:
                compared={
                    "candidate_status":"blocked_compilation_or_source_native_evidence",
                    "candidate_versification":system,
                    "reason_category":type(exc).__name__,
                    "safe_failure_code":safe_failure_code(exc),
                    "usable_for_publication":False,
                }
                if compilation is not None:
                    compared["standard_osis_compiler"] = compilation
                compared["compiled_output_metadata"] = compiler_output_metrics(out)
            results.append(compared)
        if sha256(sourcefile.read_bytes()).hexdigest()!=sha256(original).hexdigest():
            raise PublisherSWORDResearchError("Original publisher XML mutated during compilation")
    return {
        "schema_version":1,
        "status":"reviewed_original_standards_sword_compilation_research_only",
        "resource_id":resource_id,
        "original_publisher_osis_sha256":sha256(original).hexdigest(),
        "official_source_verse_count":len(verses),
        "official_source_note_count":sum(map(len,notes.values())),
        "candidate_research_results":results,
        "candidate_source_xml_or_module_uploaded":False,
        "candidate_original_note_letters_reconstructed_from_source_not_guessed":True,
        "source_osis_official_schema_verified":False,
        "original_poetry_paragraph_verse0_presentation_verified":False,
        "not_released_or_approved":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id",required=True)
    p.add_argument("--osis2mod",type=Path,required=True)
    p.add_argument("--native-index",type=Path,required=True)
    p.add_argument("--native-raw",type=Path,required=True)
    p.add_argument("--versification",default=None)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    if a.report.exists() or a.report.is_symlink() or not a.report.parent.is_dir():
        p.error("Use new metadata report in an existing directory")
    result=probe(a.resource_id,osis2mod=a.osis2mod,index_binary=a.native_index,
                 raw_binary=a.native_raw,versification=a.versification)
    a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Official OSIS to SWORD research executed for",a.resource_id)
    for row in result["candidate_research_results"]:
        print(row["candidate_versification"],row["candidate_status"])
    print("No source, compiled candidate, Scripture or note content persisted")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
