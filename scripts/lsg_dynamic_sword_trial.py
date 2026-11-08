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
    _,keys=scan_usfx(publisher_usfx)
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
