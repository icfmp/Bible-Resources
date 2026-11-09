#!/usr/bin/env python3
"""Rebuild real Segond 1910 in *stock* SWORD with documented index limits.

All original source files and generated Bible content remain private in
temporary storage; only text-free diagnostics are uploaded. Publication is
never implied by successful compilation or faithful continuous text.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from lxml import etree

from pilot_preflight import PilotError
from pilot_subprocess import MAX_OUTPUT
from lsg_source_compare import scan_usfm, scan_usfx, read_source_xml, compare_usfm_usfx
from lsg_rebuild_trial import (_safe_files, _osis_summary, _schema_proof,
                               CONVERTER_COMMIT, MAX_CONVERTER_SECONDS)
from lsg_ephemeral_osis_candidate import prepare_ephemeral_source_spaced_osis
from lsg_sword_rebuild import compile_candidate
from lsg_stock_raw_markup import audit_stock_raw_markup
import os
from reviewed_reference_merges import (load_reviewed_merges, assess_reviewed_merges,
                                       annotate_editorial_label)

APPEND = "readback_preceding_slot_contains_both_verse_character_streams"
EMPTY = "empty_readback_verse_slot"

def assess_stock_readback(roundtrip: dict) -> dict:
    """Classify *observed* official SWORD append/blank behavior, not edits."""
    chapters = roundtrip.get("expected_chapters")
    totals = roundtrip.get("totals", {})
    problems = roundtrip.get("unmatched_verse_slot_classification", [])
    source_count = roundtrip.get("total_source_verse_keys")
    if (type(chapters) is not int or chapters < 1
            or type(source_count) is not int or source_count < 1
            or not isinstance(totals, dict) or not isinstance(problems, list)):
        raise PilotError("Incomplete SWORD index readback")
    missing = totals.get("source_keys_missing")
    unexpected = totals.get("sword_keys_unexpected")
    if (type(missing) is not int or type(unexpected) is not int
            or missing < 0 or unexpected < 0):
        raise PilotError("Incomplete SWORD index difference counters")
    source_only = reader_only = 0
    appended = []
    unclassified = []
    for chapter in problems:
        if not isinstance(chapter, dict):
            raise PilotError("Malformed SWORD chapter diagnostic")
        original = chapter.get("source_only_verses")
        extra = chapter.get("reader_only_verses")
        classes = chapter.get("diagnostic_slot_classes")
        if not all(isinstance(part, list) for part in (original, extra, classes)):
            raise PilotError("Incomplete SWORD chapter diagnostic")
        source_only += len(original)
        reader_only += len(extra)
        if len(classes) != len(original) + len(extra):
            raise PilotError("Incomplete SWORD individual slot classifications")
        for item in classes:
            verse = item.get("verse")
            side = item.get("side")
            kind = item.get("classification")
            valid = (
                type(verse) is int
                and item.get("no_reversification_applied") is True
                and ((side == "source_only" and verse in original and kind == APPEND
                      and item.get("preceding_slot_compared") is True)
                     or (side == "reader_only" and verse in extra and kind == EMPTY))
            )
            if not valid:
                unclassified.append({"book": chapter.get("book"),
                                     "chapter": chapter.get("chapter"),
                                     "verse": verse, "classification": kind})
            elif side == "source_only":
                appended.append({"book": chapter.get("book"),
                                 "chapter": chapter.get("chapter"),
                                 "source_verse": verse, "compiled_verse": verse - 1,
                                 "distinct_original_reference_unavailable": True})
    complete_index_diagnostics = (
        source_only == missing and reader_only == unexpected
        and len(appended) == missing and not unclassified
        and totals.get("source_verses") == source_count
        and totals.get("chapters") == chapters
    )
    # Whole-chapter comparisons are against original USFX, independent
    # of the compiler's selected slot maxima. Asterisks are diagnosed by
    # an existing conservative display-only classifier, never removed.
    residual = roundtrip.get("first_unexplained_chapter_character_streams", [])
    if not isinstance(residual, list):
        raise PilotError("Malformed compiled display-artifact report")
    # The original full-source checker explicitly proves that the only
    # additions are reader-rendered asterisks and that no original letter,
    # digit or punctuation has been removed, changed, or reordered. These
    # additional glyphs are reported, not erased or approved as markup.
    verified_visual_only = all(
        isinstance(item, dict)
        and item.get("remaining_changes_consist_only_of_added_reader_asterisks") is True
        and type(item.get("reader_only_residual_asterisk_count")) is int
        and item["reader_only_residual_asterisk_count"] > 0
        for item in residual
    )
    continuous_text = (
        roundtrip.get(
            "chapters_where_every_residual_difference_is_added_asterisk_only"
        ) == chapters and verified_visual_only
    )
    classified = complete_index_diagnostics and continuous_text
    return {
        "status": ("stock_segond_limitations_classified_not_approved" if classified
                   else "blocked_unexplained_scripture_or_reference_change"),
        "engine": "stock_released_sword",
        "compiler_versification": "Segond",
        "observed_crosswire_behavior": "append_out_of_registry_verse_to_preceding_entry",
        "source_verse_count": source_count,
        "source_only_verse_count": missing,
        "unoccupied_compiled_verse_count": unexpected,
        "appended_source_keys": appended[:70],
        "unclassified_verse_keys": unclassified[:70],
        "all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks":
            continuous_text,
        "all_reference_differences_explained": complete_index_diagnostics,
        "reader_display_asterisk_only_chapters": [
            {"book": item.get("book"), "chapter": item.get("chapter"),
             "added_visual_asterisk_count": item.get("reader_only_residual_asterisk_count")}
            for item in residual if isinstance(item, dict)
        ],
        "visual_artifacts_are_not_approved_as_authorial_text": True,
        "exact_source_index_preserved": missing == 0 and unexpected == 0,
        "source_verse_accessibility_lost": missing > 0,
        "original_source_modified": False,
        "full_compiled_notes_poetry_markup_verified": False,
        "editorial_approval": False,
        "approved_for_publication": False,
        "published": False,
    }

def run_stable(usfm_zip: Path, usfx_zip: Path, converter: Path, schema: Path) -> dict:
    usfm = scan_usfm(usfm_zip)
    original_xml, origin = read_source_xml(usfx_zip, source_format="usfx")
    original, keys = scan_usfx(original_xml)
    if (compare_usfm_usfx(usfm, original, keys).get("status") != "verse_key_sets_equal"
            or original["book_count"] != 66 or len(keys) != 31170):
        raise PilotError("Publisher original reference identities are inconsistent")
    digest = hashlib.sha256(original_xml).hexdigest()
    report = {
        "status": "stock_segond_trial_not_completed",
        "original_usfm_archive_sha256": usfm["archive_sha256"],
        "original_usfx_archive_sha256": origin["archive_sha256"],
        "original_usfx_sha256": digest,
        "converter_pinned_commit": CONVERTER_COMMIT,
        "versification": "Segond",
        "experimental_runtime_needed": False,
        "published": False,
        "approved_for_publication": False,
    }
    with tempfile.TemporaryDirectory(prefix="lsg-stock-sword-pilot-") as location:
        home = Path(location)
        files = _safe_files(usfm_zip, home / "usfm")
        raw = home / "raw.osis.xml"
        command = [sys.executable, str(converter), "Bible.fraLSG1910eb",
                   "-l", "fr", "-x", "-o", str(raw), *map(str, files)]
        proc = subprocess.run(command, cwd=home, capture_output=True,
                              timeout=MAX_CONVERTER_SECONDS, check=False)
        if (proc.returncode or not raw.is_file()
                or len(proc.stdout) + len(proc.stderr) > MAX_OUTPUT):
            raise PilotError("Reviewed USFM-to-OSIS converter did not complete")
        summary = _osis_summary(raw, original_xml, usfm["_book_order"])
        if (summary["verse_keys_missing_from_converted"]
                or summary["verse_keys_unexpected_in_converted"]):
            raise PilotError("Converter changed source verse IDs")
        schema_status = _schema_proof(raw, schema)
        report["raw_osis_schema"] = schema_status
        if (schema_status["xsd_status"] != "validated"
                or schema_status["policy_status"] != "validated"):
            raise PilotError("Converted OSIS failed pinned CrossWire schema/policy")
        improved = home / "attested-display.osis.xml"
        report["source_attested_spacing"] = prepare_ephemeral_source_spaced_osis(
            raw, original_xml, improved, schema)
        # The textual source remains immutable. A separately tracked,
        # exact-source authorization allows the *standard SWORD compiler*
        # to combine adjacent entries when its official v11n has no key.
        policy = Path(__file__).resolve().parents[1] / "config/lsg-reviewed-verse-merges.json"
        decisions, policy_digest = load_reviewed_merges(
            policy, source_digest=digest, source_keys=keys, versification="Segond")
        labeled = home / "editorially-labeled.osis.xml"
        report["osis_editorial_range_label"] = annotate_editorial_label(
            improved, labeled, decisions, schema_proof=lambda p: _schema_proof(p, schema))
        summary_labeled = _osis_summary(labeled, original_xml, usfm["_book_order"])
        if (summary_labeled["verse_keys_missing_from_converted"]
                or summary_labeled["verse_keys_unexpected_in_converted"]):
            raise PilotError("OSIS editorial metadata changed the original verse keys")
        inspector=os.environ.get("LSG_STOCK_RAW_INSPECTOR")
        if not inspector:
            raise PilotError("Unfiltered stable SWORD raw markup audit executable is required")
        lemma_inspector=os.environ.get("LSG_STOCK_LEMMA_INSPECTOR")
        if not lemma_inspector:
            raise PilotError("Stable SWORD compiled word-lemma verification is required")
        note_inspector=os.environ.get("LSG_STOCK_NOTE_INSPECTOR")
        if not note_inspector:
            raise PilotError("Stable SWORD note-entry diagnostic executable is required")
        # Standard SWORD About metadata may be visible in the module details
        # even if frontends render the canonical verse key as plain "52".
        module_notice = "Note de versification : " + "; ".join(
            f"{d['osis_reader_key']} regroupe les versets {d['preferred_display_label']}"
            for d in decisions
        ) + ". Le texte biblique original est intégralement conservé."
        report["stock_sword_compiled_candidate"] = compile_candidate(
            labeled, source_usfx=original_xml, versification="Segond",
            module_info_note=module_notice,
            after_full_readback=lambda root,module_id,roundtrip:
                audit_stock_raw_markup(
                    original_xml,labeled,decisions,sword_root=root,
                    module_id=module_id,inspector=Path(inspector),
                    lemma_inspector=Path(lemma_inspector),
                    note_inspector=Path(note_inspector)))
        compiled = report["stock_sword_compiled_candidate"]
        if (not compiled.get("real_module_rebuilt_in_temporary_directory")
                or "full_source_verse_roundtrip" not in compiled):
            raise PilotError("Stock osis2mod or full diatheke readback failed")
        report["stock_sword_reference_assessment"] = assess_stock_readback(
            compiled["full_source_verse_roundtrip"])
        report["authorized_editorial_index_compromise"] = assess_reviewed_merges(
            decisions, policy_digest, report["stock_sword_reference_assessment"])
        raw_audit=compiled.get("compiled_raw_markup_review")
        if (not isinstance(raw_audit,dict) or
                raw_audit.get("status") != "raw_stock_sword_full_scope_markers_verified_including_intros"):
            report["status"]="blocked_compiled_raw_markup_mismatch"
        else:
            report["status"] = "authorized_stable_sword_index_compromise_not_published"
        if hashlib.sha256(original_xml).hexdigest() != digest:
            raise PilotError("Publisher original source changed during trial")
    return report

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("usfm-zip", "usfx-zip", "converter", "schema", "report"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run_stable(args.usfm_zip, args.usfx_zip,
                            args.converter, args.schema)
    except (PilotError, OSError, ValueError, etree.XMLSyntaxError,
            subprocess.TimeoutExpired) as exc:
        report = {"status": "blocked", "category": type(exc).__name__,
                  "detail": str(exc)[:180],
                  "published": False, "approved_for_publication": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True,
                                      ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("Stock SWORD Segond:", report["status"])
    return int(report["status"] != "authorized_stable_sword_index_compromise_not_published")

if __name__ == "__main__":
    raise SystemExit(main())
