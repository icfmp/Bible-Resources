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

from bible_intake import ROOT, IntakeError, SHA, acquire, load_manifest
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


def _run_source(manifest: dict, archives: dict, work: Path, *, schema: Path | None,
                usfx_schema: Path | None = None) -> dict:
    source_format = manifest["source"]["format"]
    if source_format == "USFX":
        from lsg_source_compare import read_source_xml, scan_usfx
        from source_usfx_structure import audit_source_usfx
        raw, receipt = read_source_xml(archives["source"], source_format="usfx")
        counts, refs = scan_usfx(raw)
        inventory = audit_source_usfx(raw)
        # Independent source-native scanners must not silently disagree about
        # the same original books or numbered references. No text is output.
        if (inventory["source_book_count"] != len(counts["original_books"])
                or inventory["numbered_source_reference_count"] != len(refs)
                or [b["code"] for b in inventory["all_original_books"]]
                   != counts["original_books"]):
            return _status("BLOCKED", verified=[],
                missing=["Independent original USFX verse/book inventory disagreement"],
                evidence={"source_member_sha256":receipt["sha256"]})
        findings = inventory["source_structural_issues"]
        if counts["duplicate_verse_ids"] or counts["nonstandard_verse_identifiers"]:
            return _status("BLOCKED", verified=[],
                missing=["Original source has duplicate or unrecognized verse IDs"],
                evidence={"source_member_sha256":receipt["sha256"],
                          "source_inventory": inventory})
        verified = ["Original pinned USFX parsed read-only",
                    "Independent authorial book/verse inventories agree",
                    "All source elements, notes, heading, poetry and paragraph events inventoried"]
        missing = ["Original source structure does not itself prove native SWORD text, notes or layout fidelity",
                   "Publisher edition/revision human evidence review",
                   "Conversion not performed; N/A for exact stock-SWORD reuse only after review"]
        evidence = {"source_member_sha256":receipt["sha256"],
                    "source_format":"USFX", "source_inventory":inventory,
                    "conversion_performed":False,
                    "conversion_applicability_reviewed":False}
        if findings:
            missing.insert(0, "Original source structural findings require investigation")
            return _status("BLOCKED", verified=verified, missing=missing, evidence=evidence)
        if usfx_schema is None or not usfx_schema.is_file():
            missing.insert(0, "Independently SHA-pinned official USFX XSD required")
            return _status("BLOCKED", verified=verified, missing=missing, evidence=evidence)
        from usfx_schema_gate import validate_source_with_pinned_schema
        policy = json.loads((ROOT / "config/usfx-schema-policy.json").read_text(encoding="utf-8"))
        xsd_report = validate_source_with_pinned_schema(raw, usfx_schema.read_bytes(), policy)
        evidence["official_usfx_xsd"] = xsd_report
        if not xsd_report["official_usfx_schema_validated"]:
            return _status("BLOCKED", verified=verified,
                missing=["Original XML failed official independently SHA-pinned USFX XSD validation"] + missing,
                evidence=evidence)
        verified.append("Exact official pinned USFX XSD validated the complete original source")
        return _status("PARTIAL", verified=verified,
                       missing=missing, evidence=evidence)
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
        from maintext_fidelity_classification import classify_compiled_numbered_maintext
        witness = classify_compiled_numbered_maintext(
            rows, receipt["source_book_scope"],
            receipt["source_only_verse_grouped_native_maintext_witness"],
            full_native_scan_verified=receipt["independent_native_whole_corpus_scan_completed"],
            exact_entry_spotcheck_verified=receipt["independent_native_exact_key_raw_spotcheck_verified"])
        text_preserved = witness[
            "all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding"]
        verified = ["Actual independently read stock-SWORD zText/RawText full native corpus inventoried",
                    "Original USFX mapped main-text compared character-by-character",
                    "Original and compiled note-body/annotation diagnostics collected"]
        if text_preserved:
            verified.append("All mapped numbered words/case/punctuation preserved in exact source order after whitespace folding")
        missing = ([] if text_preserved else [
            "Mapped indexed main-text has unresolved non-whitespace word/punctuation or reference differences"])
        if witness["source_verses_with_whitespace_only_changes"]:
            missing.append("Original main-text whitespace differs; verse/poetry/paragraph layout preservation not yet verified")

        # Stage 4d must not regard apparently identical Scripture as a
        # reusable stock module when authorial note callers/targets were lost.
        from stock_reuse_preflight import preflight_stock_reuse
        stock_preflight = preflight_stock_reuse(
            native_scan_complete=receipt["independent_native_whole_corpus_scan_completed"],
            main_text_preserved=text_preserved,
            notes=notes,
            note_positions=receipt[
                "private_numbered_source_native_note_anchor_position_diagnostic"],
            original_note_scope=receipt["original_source_note_scope"])
        if stock_preflight["proven_material_stock_loss"]:
            missing.insert(0,
                "Stock SWORD reuse BLOCKED by source/native material loss; "
                "inspect preflight categories before researching whitespace")
        else:
            verified.append(
                "Stock reuse material-loss screen found no demonstrated numbered "
                "annotation loss; editorial reuse is NOT approved")
        boundary_screen = rows.get("source_native_body_boundary_word_position_screen", {})
        if boundary_screen.get("all_mapped_book_p_q_start_end_word_ordinals_match") is True:
            verified.append("Source/native body p/q OPEN and CLOSE word ordinals match per book (NOT whitespace/punctuation positions)")
        elif boundary_screen:
            missing.append("Source/native paragraph/poetry opening or closing word ordinals remain different or unverified; see private-structure diagnostic")
        else:
            missing.append("No independent source/native paragraph/poetry start-and-end word position result")
        scope_triage = rows.get("source_native_body_record_scope_triage", {})
        if scope_triage.get("status") == "record_scope_candidate_classification_requires_editorial_review":
            verified.append("All source/native record-scope shifts classified at original word/verse boundaries as candidates only")
            missing.append("Candidate source/native prior/next verse and intro serialization rules require editorial verification; no layout equivalence signoff")
        elif scope_triage.get("status") == "some_record_scope_shifts_remain_unclassified":
            missing.append("Some source/native paragraph/poetry record-scope shifts are nonadjacent or ambiguous despite matching word ordinals")
        else:
            missing.append("Source/native p/q record-scope classification could not run; prerequisite/source mapping unverified")
        punctuation_screen = rows.get(
            "source_native_nonwhitespace_codepoint_boundary_screen", {})
        if punctuation_screen.get(
            "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match") is True:
            verified.append("Original/compiled p/q OPEN and CLOSE punctuation-relative non-whitespace character positions match (NOT source whitespace/newline proof)")
        elif punctuation_screen:
            missing.append("Source-native punctuation-sensitive paragraph/poetry boundary positions differ or remain unverified")
        else:
            missing.append("No independent source-native punctuation-relative p/q boundary audit")
        whitespace_gaps = rows.get("source_native_structural_whitespace_gap_triage", {})
        if whitespace_gaps.get("status") == "whitespace_differences_classified_not_editorially_approved":
            verified.append("Source/native main-text whitespace differences classified by original p/q boundaries and source newline presence (not editorial layout approval)")
            missing.append("Original whitespace/newline runs differ; p/q layout semantics and actual reader presentation need review")
        elif whitespace_gaps:
            missing.append("Original/native whitespace provenance triage blocked or incomplete; do not infer layout parity")
        else:
            missing.append("No independent original/native p/q-aware whitespace gap classification")
        if whitespace_gaps and whitespace_gaps.get(
            "source_xml_fragment_newline_gap_coverage_verified") is True:
            verified.append("Original USFX numbered newline gaps independently mapped to XML node.text/child.tail fragment origins (NOT editorial intent)")
            missing.append("Original XML text/tail provenance does not establish intentional poetry/paragraph linebreaks or native reader layout")
        elif whitespace_gaps:
            missing.append("Original USFX newline XML fragment provenance is incomplete or unavailable")
        body_order = rows.get("source_native_ordered_body_kind_screen", {})
        if body_order.get("status") == "blocked_original_authorial_source_scope_or_structure":
            missing.append("Source-native p/q ordered event check explicitly BLOCKED by original book/structure scope; do not infer matching order")
        elif body_order and body_order.get("same_order_and_kind_in_every_mapped_book") is False:
            missing.append("Original p/q versus native x-p/l body event order or counts differ; structural correspondence requires review")
        elif body_order.get("same_order_and_kind_in_every_mapped_book") is True:
            verified.append("Original p/q vs compiled x-p/l opening kind order matched per book (NOT exact word-position parity)")
        missing += ["Exact publisher edition identity and original book/intro order not independently signed off",
                    "Original note callers, word anchors, resolved reference targets and verse-zero/poetry structure unverified",
                    "Rights/editorial publication approval remains separate"]
        return _status("BLOCKED" if stock_preflight["proven_material_stock_loss"] or not text_preserved else "PARTIAL",
            verified=verified, missing=missing,
            evidence={"source_format":"USFX","native_driver":receipt["module_native_driver"],
                      "native_versification":receipt["module_versification"],
                      "actual_native_raw_manifest_sha256":
                          receipt["independent_whole_native_raw_manifest_sha256"],
                      "source_archive_sha256":receipt["publisher_original_usfx_zip_sha256"],
                      "stock_archive_sha256":receipt["publisher_compiled_sword_zip_sha256"],
                      "maintext":rows,
                      "maintext_scope_classification":witness,
                      "notes":notes,
                      "stock_reuse_preflight":stock_preflight,
                      "note_anchor_positions":receipt[
                          "private_numbered_source_native_note_anchor_position_diagnostic"],
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


def _stage5_from_fidelity(fidelity: dict, receipts: dict) -> dict:
    """Reuse one independent full-corpus receipt for stage-5 machine evidence.

    This intentionally does not approve notes, links, typography or publication.
    Stage 4 and stage 5 can share the same *immutable original/native scan*
    without inventing a second independently observed source.
    """
    evidence = fidelity.get("evidence", {})
    if "notes" not in evidence:
        return _status("BLOCKED", verified=[],
            missing=["No source-native note/layout diagnostic for this format yet"],
            evidence={"original_archives": receipts})
    note_positions = evidence.get("note_anchor_positions", {})
    position_match = (note_positions.get(
        "all_numbered_note_nonspace_anchor_positions_match") is True)
    verified = [
        "Original/natively compiled numbered-verse note body and raw annotation comparisons executed"]
    missing = [
        "Exact caller labels, original reference targets and resolved navigation",
        "Absorbed/non-numbered note ownership and note body typography",
        "Full original paragraph, poetry, title, quotation and verse-zero structure",
        "Strong values/ordinals if the original edition supplies them",
        "Human editorial acceptance of all differences",
    ]
    if position_match:
        verified.append(
            "All original numbered-note caller nonspace codepoint positions match actual stock SWORD")
    else:
        missing.insert(0, "Original/native numbered-note caller positional parity failed or unverified")
    stock_preflight = evidence.get("stock_reuse_preflight", {})
    if stock_preflight.get("proven_material_stock_loss"):
        missing.insert(0, "Stock reuse BLOCKED: original numbered annotation data lost")
    return _status(
        "BLOCKED" if stock_preflight.get("proven_material_stock_loss") else "PARTIAL",
        verified=verified, missing=missing,
        evidence={"original_archives": receipts,
                  "stock_reuse_preflight": stock_preflight,
                  "notes": evidence["notes"],
                  "note_anchor_positions": note_positions,
                  "source_scope": evidence.get("source_scope", {})})


def run_stage_four_and_five(manifest: dict, temp: Path, *, opener=None,
                            index_binary: Path | None = None,
                            raw_binary: Path | None = None,
                            entry_binary: Path | None = None,
                            schema: Path | None = None) -> tuple[dict, dict]:
    """Acquire SHA-pinned originals and scan real native SWORD exactly ONCE.

    The two results are *separate machine receipts*, never editorial approvals.
    The ordinary single-stage 4 and 5 entrypoints remain backward compatible.
    """
    stage4 = run_stage(manifest, 4, temp, opener=opener,
                       index_binary=index_binary, raw_binary=raw_binary,
                       entry_binary=entry_binary, schema=schema)
    stage5 = _stage5_from_fidelity(
        stage4, stage4.get("evidence", {}).get("original_archives", {}))
    return stage4, stage5


def run_stage(manifest: dict, stage: int, temp: Path, *, opener=None,
              index_binary: Path | None = None, raw_binary: Path | None = None,
              entry_binary: Path | None = None, schema: Path | None = None,
              usfx_schema: Path | None = None) -> dict:
    if stage not in STAGES:
        raise IntakeError("Unknown stage")
    if stage == 1:
        pending = [
            f"{kind} original archive SHA-256 not yet independently pinned"
            for kind in ("source", "sword")
            if not isinstance(manifest[kind].get("sha256"), str)
        ]
        if manifest["sword"].get("module_id") is None:
            pending.append("Original SWORD module ID not yet independently inspected")
        if manifest["sword"].get("driver") is None:
            pending.append("Original SWORD driver not yet independently inspected")
        return _status("REVIEW_REQUIRED",
            verified=["Manifest schema and approved provider HTTPS endpoints validated",
                      "Supplied SHA-256 syntax validated where a pin is present",
                      "Stage 1 performed no download or content publication"],
            missing=["Human edition identity and competing upstream baseline",
                     "Rights review for text, notes, derivative enrichments",
                     "Reviewer decision whether to reuse official SWORD or rebuild"] + pending)
    if stage == 7:
        return _status("REVIEW_REQUIRED",
            verified=["Publication is disabled in read-only research workflow"],
            missing=["Owner's explicit edition/rights/editorial signoff",
                     "Verified results of all seven independent gates",
                     "Publication PR, release and external Pages delivery proof"])
    # Stage-one manifests may explicitly record unknown original identities.
    # Never permit those provisional manifests to acquire remote archives.
    missing_pins = []
    for kind in ("source", "sword"):
        pin = manifest[kind].get("sha256")
        if not isinstance(pin, str) or not SHA.fullmatch(pin):
            missing_pins.append(f"Original {kind} archive SHA-256 is not pinned")
    if not isinstance(manifest["sword"].get("module_id"), str):
        missing_pins.append("Original SWORD module ID is not verified")
    if manifest["sword"].get("driver") not in ("RawText", "zText"):
        missing_pins.append("Original SWORD driver is not verified")
    if missing_pins:
        return _status("BLOCKED", verified=[],
                       missing=missing_pins +
                       ["A stage-one research manifest cannot acquire original archives"])

    want_source,want_sword = _needs(stage)
    receipts, archives = acquire(manifest,temp,source=want_source,sword=want_sword,opener=opener)
    if stage == 2:
        return _status("DONE",
            verified=["Both upstream archives downloaded via provider-allowlisted HTTPS",
                      "Exact pinned SHA-256/size and archive structural limits verified"],
            missing=[],
            evidence={"original_archives":receipts})
    if stage == 3:
        result = _run_source(manifest,archives,temp,schema=schema,usfx_schema=usfx_schema)
    elif stage in (4,5):
        result = _run_fidelity(manifest,archives,temp,index_binary=index_binary,
                               raw_binary=raw_binary,entry_binary=entry_binary,schema=schema)
        if stage == 5:
            result = _stage5_from_fidelity(result, receipts)
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
           f"Resource: `{report['resource_id']}` — {report['stage_name']}",
           f"GitHub commit: `{report['git_sha']}`",
           f"Workflow run: {report['run_url'] or 'local only'}",
           "",
           "**Verified**"]
    lines.extend("- "+v for v in report["verified"])
    if not report["verified"]:
        lines.append("- Nothing proven in this stage")
    # Expose a bounded reference/ordinal queue in the permanent issue
    # checkpoint. This lets reviewers resume without downloading a large
    # short-retention artifact; the data never include original verse text.
    if report["stage"] == 4:
        from stable_sword_refs import KEY
        from source_usfx_newline_provenance import SOURCE_NEWLINE_ORIGIN_LABELS
        rows = (report.get("evidence", {}).get("maintext", {})
                .get("source_native_structural_whitespace_gap_triage", {})
                .get("first_unmarked_internal_newline_xml_origin_references_only", []))
        safe = []
        for row in rows[:16]:
            ref = row.get("reference")
            origin = row.get("source_xml_fragment_origin")
            gap = row.get("original_verse_nonspace_codepoint_gap")
            distance = row.get(
                "nearest_explicit_authorial_p_q_boundary_distance_codepoints")
            if (isinstance(ref, str) and KEY.fullmatch(ref)
                    and origin in SOURCE_NEWLINE_ORIGIN_LABELS
                    and type(gap) is int and gap >= 0
                    and type(distance) is int and distance >= 0
                    and row.get("editorial_linebreak_intent_unverified") is True):
                safe.append((ref, origin, gap, distance))
        if safe:
            lines.extend(["", "**Bounded original-newline review coordinates**",
                          "Distances are Unicode non-whitespace codepoints to "
                          "the nearest explicit source p/q start/end. "
                          "These do NOT prove layout equivalence."])
            for ref, origin, gap, distance in safe:
                lines.append(
                    f"- `{ref}` — `{origin}`, source gap {gap}, "
                    f"nearest p/q boundary {distance} codepoints away")

    if report["stage"] in (4, 5):
        preflight = report.get("evidence", {}).get("stock_reuse_preflight", {})
        if preflight:
            lines.extend(["", "**Stock reuse material-loss preflight**",
                          "Machine status: `" + preflight["status"] + "` "
                          "(never reuse/editorial approval)"])
            for code, count in sorted(
                    preflight.get("material_loss_categories", {}).items()):
                # Fixed tool-authored category tokens and numeric counts only:
                # no source/reader strings or private XML leave the runner.
                if SAFE_CODE.fullmatch(code) and type(count) is int:
                    lines.append("- " + code + ": " + str(count))
    lines.extend(["","**Still missing / blocking**"])
    lines.extend("- "+v for v in report["missing"])
    if not report["missing"]:
        lines.append("- None for this stage's narrow technical scope")
    lines.extend(["", "**Next action**", report["next_action"], "",
                  "No Scripture text, notes or original archives are uploaded.",
                  "**This report is not publication or editorial approval.**"])
    summary.write_text("\n".join(lines)+"\n",encoding="utf-8")


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--stage",choices=[*(str(x) for x in sorted(STAGES)), "4-5"],
                        required=True,
                        help="Single audit stage 1–7 or shared machine audit of stages 4-5")
    parser.add_argument("--report-dir",type=Path,required=True)
    parser.add_argument("--native-index-binary",type=Path)
    parser.add_argument("--native-raw-binary",type=Path)
    parser.add_argument("--native-entry-binary",type=Path)
    parser.add_argument("--osis-schema",type=Path)
    parser.add_argument("--usfx-schema",type=Path)
    args=parser.parse_args(argv)
    try:
        manifest=load_manifest(args.resource_id)
        with tempfile.TemporaryDirectory(prefix="bible-research-stage-") as td:
            if args.stage == "4-5":
                stage4, stage5 = run_stage_four_and_five(
                    manifest, Path(td), index_binary=args.native_index_binary,
                    raw_binary=args.native_raw_binary,
                    entry_binary=args.native_entry_binary, schema=args.osis_schema)
                # One underlying scan, but independent 4/7 and 5/7 receipts.
                # A successful workflow is not an editorial signoff for either.
                statuses = (stage4["status"], stage5["status"])
                scan_completed = bool(stage4.get("evidence", {}).get(
                    "actual_native_raw_manifest_sha256"))
                result = _status(
                    "BLOCKED" if "BLOCKED" in statuses else "PARTIAL",
                    verified=(["One verified full native source/SWORD scan supports "
                               "both stage-4 and stage-5 machine receipts"]
                              if scan_completed else
                              ["One stage-4 evaluation reused without a second "
                               "stage-5 source fetch or scan"]) +
                             ["4/7 machine evidence: " + statuses[0],
                              "5/7 machine evidence: " + statuses[1]],
                    missing=(["4/7: " + stage4["missing"][0]]
                             if stage4["missing"] else []) +
                            (["5/7: " + stage5["missing"][0]]
                             if stage5["missing"] else []) +
                            ([] if scan_completed else
                             ["Full native corpus scan not independently evidenced"]) +
                            ["Human editorial/rights/reader decisions are not automated"],
                    evidence={
                        "input_manifest_sha256": sha256(
                            json.dumps(manifest, sort_keys=True,
                                       separators=(",", ":")).encode("utf-8")).hexdigest(),
                        "shared_fidelity_invocations": 1,
                        "full_native_corpus_scan_completed": scan_completed,
                        "stage_machine_receipts": {"4": stage4, "5": stage5},
                        "not_publication_or_editorial_approval": True})
            else:
                result=run_stage(manifest,int(args.stage),Path(td),
                                 index_binary=args.native_index_binary,
                                 raw_binary=args.native_raw_binary,
                                 entry_binary=args.native_entry_binary,
                                 schema=args.osis_schema,usfx_schema=args.usfx_schema)
        failed=False
    except Exception as exc:
        # Third-party parser error strings may contain actual text.
        # Only our own fixed IntakeError message can appear in public logs.
        reason = (str(exc)[:180] if isinstance(exc, IntakeError)
                  else type(exc).__name__ + " (review pinned input privately)")
        result=_status("BLOCKED",verified=[],
            missing=["Run failed: " + reason], evidence={})
        failed=True
    if args.stage == "4-5":
        next_action = ("Review distinct stage 4 and 5 machine receipts and resolve "
                       "remaining editorial issues; neither stage is automatically DONE")
    elif result["status"] == "DONE" and int(args.stage) < 7:
        next_action = f"Review this evidence and proceed to stage {int(args.stage)+1}/7 only when the full gate is documented"
    else:
        next_action = f"Resolve the first missing gate, then repeat stage {args.stage}/7"
    report={"schema_version":2 if args.stage == "4-5" else 1,
            "resource_id":args.resource_id,
            "stage":"4-5" if args.stage == "4-5" else int(args.stage),
            "stage_name":("shared-source-native-4-5" if args.stage == "4-5"
                          else STAGES[int(args.stage)]),
            "git_sha":os.environ.get("GITHUB_SHA","local"),
            "run_url":os.environ.get("GITHUB_SERVER_URL","")+"/"+
                os.environ.get("GITHUB_REPOSITORY","")+"/actions/runs/"+
                os.environ.get("GITHUB_RUN_ID","") if os.environ.get("GITHUB_RUN_ID") else None,
            "status":result["status"],"gate_completed":(
                args.stage != "4-5" and result["status"]=="DONE"),
            "next_action":next_action,
            "verified":result["verified"],"missing":result["missing"],
            "evidence":result["evidence"],"reusable_for_pub_approval":False,
            "script_did_not_publish":True}
    try:
        _write_report(args.report_dir,report)
    except (OSError,ValueError) as exc:
        parser.error("Failed to write safe checkpoint report: "+type(exc).__name__)
    print(f"Bible audit {args.resource_id}: stage {args.stage}/7 — {result['status']}")
    if result["status"] == "BLOCKED":
        for item in result["missing"][:3]:
            print("BLOCKED:", item)
    return 1 if failed else 0


if __name__=="__main__":
    raise SystemExit(main())
