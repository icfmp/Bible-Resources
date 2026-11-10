#!/usr/bin/env python3
"""One bounded, read-only Bible audit checkpoint per independent Actions run.

This is an orchestrator for existing tested diagnostics, not an importer,
semantic certifier, edition approver, or publisher. Reports contain NO Bible
text. Missing proofs remain explicit and are never turned into CI success
claims or silently waived.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from bible_intake import ROOT, IntakeError, acquire, load_manifest
from pilot_preflight import inspect_archive
from pilot_runtime import run_reader

STAGES = {
    1:"edition-and-rights",
    2:"pinned-originals",
    3:"authorial-source",
    4:"source-to-native-text",
    5:"editorial-annotations",
    6:"stock-reader-test",
    7:"owner-release-gate",
}
SAFE_CODE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")


def _needs(stage: int) -> tuple[bool, bool]:
    return (stage in (2, 3, 4, 5), stage in (2, 4, 5, 6))


def _status(status: str, *, verified: list[str], missing: list[str], evidence=None) -> dict:
    assert status in {"DONE", "PARTIAL", "BLOCKED", "REVIEW_REQUIRED"}
    return {"status": status, "verified": verified, "missing": missing,
            "evidence": evidence or {}}


def _osis_source(archive: Path, name: str, destination: Path) -> Path:
    from pathlib import PurePosixPath
    pure = PurePosixPath(name)
    if (not name or name.startswith("/") or "\\" in name
            or ".." in pure.parts or pure.is_absolute()):
        raise IntakeError("Unsafe OSIS member path")
    with zipfile.ZipFile(archive) as source:
        if name not in source.namelist():
            raise IntakeError("Declared OSIS member absent from pinned ZIP")
        item = source.getinfo(name)
        if item.file_size < 1 or item.file_size > 128 * 1024 * 1024:
            raise IntakeError("Original OSIS XML member is empty or oversized")
        data = source.read(item)
    destination.write_bytes(data)
    return destination


def _run_source(manifest: dict, archives: dict, work: Path, *, schema: Path | None) -> dict:
    source_format = manifest["source"]["format"]
    if source_format == "USFX":
        from lsg_source_compare import read_source_xml, scan_usfx
        raw, receipt = read_source_xml(archives["source"], source_format="usfx")
        counts, refs = scan_usfx(raw)
        return _status(
            "PARTIAL",
            verified=["Original pinned USFX parsed read-only",
                      "Authorial source verse inventory enumerated"],
            missing=["Official source-to-OSIS conversion and full notes/layout equivalence",
                     "Human edition/revision provenance review"],
            evidence={"source_member_sha256":receipt["sha256"],
                      "original_source_book_count":len(counts.get("original_books", [])),
                      "numbered_source_reference_count":len(refs),
                      "source_format":"USFX"})
    if source_format == "USFM":
        from lsg_source_compare import scan_usfm
        report = scan_usfm(archives["source"])
        return _status("PARTIAL",
            verified=["Original pinned USFM source parsed and inventoried"],
            missing=["Standards-based, lossless USFM-to-OSIS conversion",
                     "Independent source-to-converted editorial and verse parity"],
            evidence={"source_format":"USFM","source_inventory_status":"diagnostic_only",
                      "inventory_keys":sorted(report)[:25]})
    if schema is None or not schema.is_file():
        return _status("BLOCKED",verified=[],
            missing=["Reviewed official OSIS 2.1.1 XSD path is required for stage 3"])
    from guard_osis import inspect as inspect_osis
    from source_osis_inventory import source_inventory
    original = _osis_source(archives["source"], manifest["source"]["member"],
                            work / "source-original.osis.xml")
    proof = inspect_osis(original, schema)
    keys, inventory = source_inventory(original.read_bytes())
    return _status("PARTIAL",
        verified=["Official OSIS schema and reviewed structural allowlist passed",
                  "Original authorial verse-key inventory extracted"],
        missing=["Publisher edition and full original content/annotation identity review",
                 "Native compiled parity is separate stage 4"],
        evidence={"source_format":"OSIS","source_sha256":proof["source_sha256"],
                  "source_verse_key_sha256":sha256(keys.encode()).hexdigest(),
                  "source_numbered_verse_count":inventory["source_verse_count"],
                  "source_book_count":inventory["source_book_count"]})


def _run_fidelity(manifest: dict, archives: dict, work: Path, *,
                  index_binary: Path | None, raw_binary: Path | None,
                  entry_binary: Path | None, schema: Path | None) -> dict:
    if index_binary is None or not index_binary.is_file():
        return _status("BLOCKED",verified=[],missing=["Native SWORD index inspector binary missing"])
    fmt = manifest["source"]["format"]
    if fmt == "USFM":
        return _status("BLOCKED",verified=[],
            missing=["No approved original USFM-to-OSIS conversion and exact source parity"])
    if fmt == "USFX":
        if raw_binary is None or entry_binary is None or not raw_binary.is_file() or not entry_binary.is_file():
            return _status("BLOCKED",verified=[],
                missing=["Native raw corpus and exact-entry inspectors required for full-corpus diagnostics"])
        from source_native_maintext_probe import run_real_usfx_sword_text_probe
        receipt = run_real_usfx_sword_text_probe(
            archives["source"], archives["sword"], ROOT / manifest["crosswalk"],
            index_binary, raw_binary, native_entry_binary=entry_binary)
        rows = receipt["mapped_numbered_text_comparison"]
        counts = rows["classifications"]
        notes = receipt["private_numbered_source_native_note_body_diagnostic"]
        equal = rows["mapped_numbered_maintext_exact_semantic_characters_verified"]
        return _status("PARTIAL" if equal else "BLOCKED",
            verified=["Actual independently read stock-SWORD zText/RawText full native corpus inventoried",
                      "Original USFX mapped main-text compared character-by-character",
                      "Original and compiled note-body/annotation diagnostics collected"],
            missing=([] if equal else ["Mapped indexed main-text has unresolved non-identical entries"])
                    + ["Full publisher edition/canon/extra-book equivalence and original-source conversion",
                       "Full verse-zero structure, Strong, note anchors and resolved reference targets",
                       "Independent legal/editorial acceptance"],
            evidence={"source_format":"USFX","native_driver":receipt["module_native_driver"],
                      "native_versification":receipt["module_versification"],
                      "actual_native_raw_manifest_sha256":
                          receipt["independent_whole_native_raw_manifest_sha256"],
                      "source_archive_sha256":receipt["publisher_original_usfx_zip_sha256"],
                      "stock_archive_sha256":receipt["publisher_compiled_sword_zip_sha256"],
                      "maintext":rows,
                      "notes":notes,
                      "source_scope":receipt["source_book_scope"],
                      "absorbed_verse_groups":receipt["source_only_verse_grouped_native_maintext_witness"]})
    if schema is None or not schema.is_file():
        return _status("BLOCKED",verified=[],
            missing=["Approved OSIS XSD needed to compare an already-authored OSIS source"])
    original = _osis_source(archives["source"],manifest["source"]["member"],
                            work / "source-original.osis.xml")
    from guard_osis import inspect as inspect_osis
    inspect_osis(original,schema)
    from real_second_bible_probe import _safe_single_module
    from source_native_index_audit import audit_source_native_index
    module = work / "isolated-original-sword"
    conf = _safe_single_module(archives["sword"],module)
    if conf["module_id"] != manifest["sword"]["module_id"]:
        raise IntakeError("Independent SWORD identity mismatch")
    diag = audit_source_native_index(original,module,conf["module_id"],index_binary)
    return _status("PARTIAL" if diag["comparison"]["exact_reference_key_parity"] else "BLOCKED",
        verified=["Independent original OSIS and actual stock-SWORD native verse index comparison"],
        missing=["Full OSIS main-text, notes and editorial structure to native binary parity",
                 "Source revision/canon identity and editorial approval"],
        evidence={"source_format":"OSIS","reference_index":diag})


def run_stage(manifest: dict, stage: int, temp: Path, *, opener=None,
              index_binary: Path | None = None, raw_binary: Path | None = None,
              entry_binary: Path | None = None, schema: Path | None = None) -> dict:
    if stage not in STAGES:
        raise IntakeError("Unknown stage")
    if stage == 1:
        return _status("REVIEW_REQUIRED",
            verified=["Manifest schema, approved provider endpoints and exact SHA-256 syntax validated"],
            missing=["Human edition identity and competing upstream baseline",
                     "Rights review for text, notes, derivative enrichments",
                     "Reviewer decision whether to reuse official SWORD or rebuild"])
    if stage == 7:
        return _status("REVIEW_REQUIRED",
            verified=["Publication is disabled in read-only research workflow"],
            missing=["Owner's explicit edition/rights/editorial signoff",
                     "Verified results of all seven independent gates",
                     "Publication PR, release and external Pages delivery proof"])
    want_source,want_sword = _needs(stage)
    receipts, archives = acquire(manifest,temp,source=want_source,sword=want_sword,opener=opener)
    if stage == 2:
        return _status("DONE",
            verified=["Both upstream archives downloaded via provider-allowlisted HTTPS",
                      "Exact pinned SHA-256/size and archive structural limits verified"],
            missing=[],
            evidence={"original_archives":receipts})
    if stage == 3:
        result = _run_source(manifest,archives,temp,schema=schema)
    elif stage in (4,5):
        result = _run_fidelity(manifest,archives,temp,index_binary=index_binary,
                               raw_binary=raw_binary,entry_binary=entry_binary,schema=schema)
        if stage == 5:
            if "notes" in result["evidence"]:
                evidence = result["evidence"]
                result = _status("PARTIAL",
                    verified=["Original/natively compiled numbered-verse note body and raw annotation comparisons executed"],
                    missing=["Exact caller/word-anchor positions, absorbed-verse notes and target resolution",
                             "Full source paragraph, poetry, title, quotation and verse-zero structure",
                             "Strong values/ordinals if the original edition supplies them",
                             "Human editorial acceptance of all differences"],
                    evidence={"original_archives":receipts,
                              "notes":evidence["notes"],
                              "source_scope":evidence["source_scope"]})
            else:
                result = _status("BLOCKED",verified=[],
                    missing=["No source-native note/layout diagnostic for this format yet"],
                    evidence={"original_archives":receipts})
    elif stage == 6:
        pilot = manifest["resource_id"]
        cfg={"pilots":{pilot:{"module_id":manifest["sword"]["module_id"],
                             "category":"bible",
                             "sample_references":manifest["sword"]["sample_references"]}}}
        original = run_reader(pilot,archives["sword"],config=cfg)
        passed = original["status"] == "reader_probe_passed"
        result = _status("PARTIAL" if passed else "BLOCKED",
            verified=["Isolated stock-SWORD/diatheke passage readbacks verified"] if passed else [],
            missing=([] if passed else ["Representative isolated stock SWORD passages unreadable"])
                    + ["Second independent reader/real UI acceptance and standalone/parallel variants",
                       "Candidate package-vs-publisher comparison and editorial release acceptance"],
            evidence={"stock_reader":original})
    else:
        raise IntakeError("Stage not implemented")
    result["evidence"]["original_archives"] = receipts
    return result


def _write_report(report_dir: Path, report: dict) -> None:
    if report_dir.is_symlink() or not report_dir.is_dir():
        raise IntakeError("Report destination must be a pre-existing regular directory")
    destination = report_dir / "stage-report.json"
    summary = report_dir / "stage-summary.md"
    if any(f.exists() or f.is_symlink() for f in (destination,summary)):
        raise IntakeError("Refusing to replace prior stage evidence")
    destination.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    state=report["status"]
    lines=[f"### Bible audit stage {report['stage']}/7 — {state}",
           f"Resource: \`{report['resource_id']}\` — {report['stage_name']}",
           f"GitHub commit: \`{report['git_sha']}\`",
           f"Workflow run: {report['run_url'] or 'local only'}",
           "",
           "**Verified**"]
    lines.extend("- "+v for v in report["verified"])
    if not report["verified"]:
        lines.append("- Nothing proven in this stage")
    lines.extend(["","**Still missing / blocking**"])
    lines.extend("- "+v for v in report["missing"])
    if not report["missing"]:
        lines.append("- None for this stage's narrow technical scope")
    lines.extend(["","No Scripture text, notes or original archives are uploaded.",
                  "**This report is not publication or editorial approval.**"])
    summary.write_text("\n".join(lines)+"\n",encoding="utf-8")


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--stage",type=int,choices=sorted(STAGES),required=True)
    parser.add_argument("--report-dir",type=Path,required=True)
    parser.add_argument("--native-index-binary",type=Path)
    parser.add_argument("--native-raw-binary",type=Path)
    parser.add_argument("--native-entry-binary",type=Path)
    parser.add_argument("--osis-schema",type=Path)
    args=parser.parse_args(argv)
    try:
        manifest=load_manifest(args.resource_id)
        with tempfile.TemporaryDirectory(prefix="bible-research-stage-") as td:
            result=run_stage(manifest,args.stage,Path(td),index_binary=args.native_index_binary,
                             raw_binary=args.native_raw_binary,entry_binary=args.native_entry_binary,
                             schema=args.osis_schema)
        failed=False
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,
            zipfile.BadZipFile, KeyError, TypeError) as exc:
        # Never include original text or raw XML from an exception in public CI.
        result=_status("BLOCKED",verified=[],
            missing=["Run failed: " + type(exc).__name__ + ". Inspect pinned sources and local logs privately."],
            evidence={})
        failed=True
    report={"schema_version":1,"resource_id":args.resource_id,"stage":args.stage,
            "stage_name":STAGES[args.stage],
            "git_sha":os.environ.get("GITHUB_SHA","local"),
            "run_url":os.environ.get("GITHUB_SERVER_URL","")+"/"+
                os.environ.get("GITHUB_REPOSITORY","")+"/actions/runs/"+
                os.environ.get("GITHUB_RUN_ID","") if os.environ.get("GITHUB_RUN_ID") else None,
            "status":result["status"],"gate_completed":result["status"]=="DONE",
            "verified":result["verified"],"missing":result["missing"],
            "evidence":result["evidence"],"reusable_for_pub_approval":False,
            "script_did_not_publish":True}
    try:
        _write_report(args.report_dir,report)
    except (OSError,ValueError) as exc:
        parser.error("Failed to write safe checkpoint report: "+type(exc).__name__)
    print(f"Bible audit {args.resource_id}: stage {args.stage}/7 — {result['status']}")
    return 1 if failed else 0


if __name__=="__main__":
    raise SystemExit(main())
