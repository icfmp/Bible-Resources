#!/usr/bin/env python3
"""Prepare and test a private original-data-preserving zCom SWORD commentary.

Uses the exact upstream pinned archive. Changes ONLY SWORD module identity
and DataPath in configuration, NEVER compressed corpus bytes, verse keys,
original headings, annotations, notes or text. Independent native engine
readback verifies all actual occupied K/I/TOP entries in the source and
candidate, not just a few representative passages.

Both ZIPs remain inside TemporaryDirectory and are never uploaded.
This is a runnable *technical candidate*, not a rights/editorial release.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

from commentary_intake import load_manifest
from commentary_native_raw_inventory import _safe_stock_install
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from pilot_subprocess import present_key, query
from promote_sword_preview import promote
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

SHA = re.compile(r"[a-f0-9]{64}\Z")
MODULE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,39}\Z")
MAX_CONF = 16000
NATIVE_SCAN_TIMEOUT = 360


def private_relabel_config(original: bytes, old_id: str, candidate_id: str) -> bytes:
    """Prove original SWORD conf changes in *exactly two lines*."""
    if (not MODULE.fullmatch(old_id) or not MODULE.fullmatch(candidate_id)
            or old_id == candidate_id or len(original)>MAX_CONF):
        raise PilotError("Unreviewed original SWORD commentary identity or config size")
    try:
        original.decode("utf-8",errors="strict")
    except UnicodeError:
        raise PilotError("Original stock SWORD .conf is not verified UTF-8") from None
    lines=original.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != f"[{old_id}]".encode("ascii"):
        raise PilotError("Actual original stock SWORD .conf section differs")
    source_path=f"DataPath=./modules/comments/zcom/{old_id.lower()}/".encode("ascii")
    destination_path=f"DataPath=./modules/comments/zcom/{candidate_id.lower()}/".encode("ascii")
    matches=[i for i,line in enumerate(lines) if line.rstrip(b"\r\n")==source_path]
    if len(matches)!=1:
        raise PilotError("Actual original compressed commentary DataPath must occur exactly once")
    edited=list(lines)
    edited[0]=edited[0].replace(f"[{old_id}]".encode("ascii"),
                               f"[{candidate_id}]".encode("ascii"),1)
    index=matches[0]
    edited[index]=edited[index].replace(source_path,destination_path,1)
    rebuilt=b"".join(edited)
    if len(rebuilt)>MAX_CONF:
        raise PilotError("Private SWORD metadata rewrite exceeds reviewed bounds")
    # Independently reconstruct exactly those two expected changes.
    expected=original.replace(f"[{old_id}]".encode("ascii"),
                               f"[{candidate_id}]".encode("ascii"),1)
    expected=expected.replace(source_path,destination_path,1)
    if rebuilt!=expected or b"CipherKey=" in rebuilt:
        raise PilotError("Private candidate changed more than its SWORD identity/DataPath")
    return rebuilt


def _native_content(root:Path,module_id:str,native_raw_binary:Path) -> dict:
    process=None
    env=dict(os.environ,SWORD_PATH=str(root))
    try:
        process=subprocess.Popen(
            ["timeout",f"{NATIVE_SCAN_TIMEOUT}s",str(native_raw_binary),module_id],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env
        )
        if process.stdout is None:
            raise PilotError("Independent SWORD native raw reader unavailable")
        full,keys,intros,top=parse_native_raw_corpus(process.stdout)
        process.stdout.close()
        status=process.wait(timeout=15)
        if status!=0:
            raise PilotError("Independent native original/candidate raw stream did not finish")
        return {
            "raw_sha256":full["all_native_raw_entries_ordered_sha256"],
            "count":full["all_actual_raw_entries_scanned"],
            "K":full["actual_occupied_numbered_entry_count"],
            "I":full["actual_occupied_intro_entry_count"],
            "U":full["actual_occupied_anonymous_top_entry_count"],
            "raw_bytes":full["actual_native_unfiltered_raw_bytes_total"],
            "keys":keys,"intros":intros,"top":top,
        }
    except BaseException:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        raise


def make_private_candidate(
    resource_id:str,
    *,native_raw_binary:Path,reader:str="diatheke",
    candidate_id:str="BRMHCCReview",
    directory:Path|None=None,
) -> dict:
    manifest=load_manifest(resource_id,directory=directory)
    old_id=manifest["module_id"]
    if manifest["rights"]["status"]!="research_only" or manifest["rights"]["owner_approved"] is not False:
        raise PilotError("Unexpected original commentary rights workflow state")
    if not MODULE.fullmatch(candidate_id) or candidate_id==old_id:
        raise PilotError("Unreviewed test-only SWORD commentary identity")
    expected_conf=manifest.get("stock_conf_sha256")
    expected_raw=manifest.get("native_raw_corpus_sha256")
    if (not isinstance(expected_conf,str) or not SHA.fullmatch(expected_conf)
            or not isinstance(expected_raw,str) or not SHA.fullmatch(expected_raw)):
        raise PilotError("Reviewed original stock .conf/full native SHA-256 pins required")
    if native_raw_binary.is_symlink() or not native_raw_binary.is_file():
        raise PilotError("Independent original full native raw SWORD reader unavailable")
    with tempfile.TemporaryDirectory(prefix="commentary-private-stock-candidate-") as temporary:
        work=Path(temporary)
        original_zip=work/"original-crosswire.zip"
        observed=fetch(manifest["sword_zip_url"],original_zip,manifest["provider"])
        if observed["sha256"]!=manifest["archive_sha256"]:
            raise PilotError("Original SWORD commentary ZIP SHA-256 changed")
        original_info=inspect_archive(original_zip,source_kind="sword",
                                      expected_module_id=old_id,
                                      expected_category="commentary")
        original_conf=original_info["sword_conf"]
        if (original_conf["driver"]!="zCom" or original_conf["version"]!=manifest["version"]
                or original_conf["language"]!=manifest["language"]
                or (original_conf["versification"] or "KJV")!="KJV"
                or "public domain" not in (original_conf["distribution_license"] or "").lower()):
            raise PilotError("Pinned original public-domain CrossWire commentary metadata differs")
        with ZipFile(original_zip) as archive:
            conf_bytes=archive.read(f"mods.d/{old_id.lower()}.conf")
        if sha256(conf_bytes).hexdigest()!=expected_conf:
            raise PilotError("Original SWORD module .conf is not the independently pinned one")
        reviewed_conf=private_relabel_config(conf_bytes,old_id,candidate_id)
        config=work/"candidate.conf"
        config.write_bytes(reviewed_conf)
        private_zip=work/"candidate-NEVER-PUBLISH.zip"
        promotion=promote(
            original_zip,private_zip,
            expected_source_sha256=manifest["archive_sha256"],
            source_id=old_id,destination_id=candidate_id,
            config=config,driver="zCom",versification="KJV",
        )
        if promotion["data_byte_equal"] is not True or promotion["published"] is not False:
            raise PilotError("Original zCom commentary data preservation failed")
        candidate_info=inspect_archive(private_zip,source_kind="sword",
                                       expected_module_id=candidate_id,
                                       expected_category="commentary")
        if (candidate_info["sword_conf"]["driver"]!="zCom"
                or candidate_info["sword_conf"]["version"]!=original_conf["version"]
                or candidate_info["sword_conf"]["language"]!=original_conf["language"]):
            raise PilotError("Private candidate SWORD original driver/edition changed")
        original_install=work/"original-installed"
        candidate_install=work/"candidate-installed"
        _safe_stock_install(original_zip,original_info["members"],original_install)
        _safe_stock_install(private_zip,candidate_info["members"],candidate_install)
        stock=_native_content(original_install,old_id,native_raw_binary)
        candidate=_native_content(candidate_install,candidate_id,native_raw_binary)
        if (stock["raw_sha256"]!=expected_raw or
                {key:stock[key] for key in stock} !=
                {key:candidate[key] for key in candidate}):
            raise PilotError("Candidate SWORD native content or occupied-key order differs from stock")
        if stock["count"]!=stock["K"]+stock["I"]+stock["U"]:
            raise PilotError("Native original and candidate occupied count mismatch")
        probes=[]
        substantial=0
        for passage in manifest["sample_references"]:
            stock_code,stock_text=query(old_id,passage,fmt="plain",
                                       root=original_install,exe=reader,
                                       limit=256*1024,timeout=30)
            test_code,test_text=query(candidate_id,passage,fmt="plain",
                                      root=candidate_install,exe=reader,
                                      limit=256*1024,timeout=30)
            if (stock_code!=0 or test_code!=0 or
                    stock_text!=test_text or
                    not present_key(passage,stock_text,stock_code)):
                raise PilotError("Independent diatheke readback differs after identity-only candidate packaging")
            if len(stock_text)>64:
                substantial+=1
            probes.append({
                "source_query_SHA256":sha256(passage.encode()).hexdigest(),
                "native_reader_output_sha256":sha256(stock_text).hexdigest(),
                "candidate_plain_readback_byte_equal":True,
                "response_has_substantial_content":len(stock_text)>64,
            })
        if substantial<1:
            raise PilotError("Original commentary test samples did not contain any substantial reader output")
        # The scope of this report is binary preservation, not CCEL digital-edition parity.
        return {
            "schema_version":1,
            "status":"exact_original_zCom_payload_private_candidate_full_native_roundtrip_verified",
            "resource_id":resource_id,
            "upstream_sword_original_archive_sha256":observed["sha256"],
            "upstream_sword_original_conf_sha256":expected_conf,
            "upstream_sword_original_module_id":old_id,
            "private_candidate_module_id":candidate_id,
            "private_candidate_package_sha256":promotion["release_zip_sha256"],
            "private_candidate_package_bytes":promotion["release_zip_bytes"],
            "private_candidate_original_compressed_file_count":
                len(promotion["per_file_sha256"]),
            "all_original_SWORD_compressed_files_byte_preserved":True,
            "original_metadata_only_module_identity_and_data_path_changed":True,
            "full_native_unfiltered_raw_corpus_sha256":stock["raw_sha256"],
            "complete_stock_and_candidate_native_raw_corpus_sha256_equal":True,
            "all_occupied_native_K_I_TOP_keys_and_order_identical":True,
            "numbered_commentary_K_keys":stock["K"],
            "intro_I_keys":stock["I"],
            "opaque_TOP_keys":stock["U"],
            "total_native_keys":stock["count"],
            "complete_native_raw_entry_bytes":stock["raw_bytes"],
            "isolated_stock_diatheke_original_vs_private_candidate":probes,
            "substantial_plain_readback_sample_count":substantial,
            "no_unredacted_authorial_text_or_real_reference_names_in_report":True,
            "private_candidate_archive_destroyed_without_upload":True,
            "independent_Xiphos_AndBible_visual_validation_passed":False,
            "CCEL_source_to_CrossWire_digital_edition_equivalence_proven":False,
            "digital_transcription_rights_separately_approved":False,
            "editorial_acceptance":False,
            "published":False,
        }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--candidate-id",default="BRMHCCReview")
    parser.add_argument("--native-raw-binary",type=Path,required=True)
    parser.add_argument("--reader",default="diatheke")
    parser.add_argument("--report",required=True,type=Path)
    args=parser.parse_args(argv)
    report=make_private_candidate(args.resource_id,candidate_id=args.candidate_id,
                                   native_raw_binary=args.native_raw_binary,
                                   reader=args.reader)
    if args.report.exists() or args.report.is_symlink():
        raise PilotError("Refusing to overwrite an existing private review receipt")
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Private exact-stock zCom candidate built, installed and native corpus crosschecked "
          "(metadata only; no candidate ZIP retained or released)")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
