#!/usr/bin/env python3
"""Verify an immutable, already-approved source→stock-SWORD index audit.

This is a backward-compatible evidence adapter for releases whose exhaustive
stock-reader audit predates the newer SWORD_COMPATIBILITY.json format.
It never re-runs the original experiment or turns its assertions into new facts.
New editions should use the independently generated stable_sword_refs proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from stable_sword_refs import load_approved_merge_policy

SHA = re.compile(r"^[0-9a-f]{64}$")
OSIS_KEY = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$")


def _read_object(path: Path, limit: int = 4 * 1024 * 1024) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"{path}: missing, linked or oversized evidence")
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data, raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def archived_release_errors(module: Path, root: Path, manifest_name: str,
                            metadata: dict, validated_source_sha: str) -> list[str]:
    """Fail closed on the entire pinned original audit, approved merge and payload.

    The checked manifest, audit and recorded authorial/reader differences are
    from the *same immutable release*. This checks preservation of that proof,
    not a fresh, independently executed inventory of every SWORD reader slot.
    """
    errors = []
    try:
        pure = PurePosixPath(manifest_name)
        if (not isinstance(manifest_name, str) or pure.is_absolute()
                or ".." in pure.parts or len(pure.parts) != 2
                or pure.parts[0] != "config" or not pure.name.endswith(".json")):
            raise ValueError("Manifest must be a safe config/*.json path")
        manifest, _ = _read_object(root / manifest_name, 256_000)
        audit, raw_audit = _read_object(module / "SOURCE_AUDIT.json")
        source, _ = _read_object(module / "SOURCE_VALIDATION.json", 256_000)

        if (not SHA.fullmatch(manifest.get("release_audit_sha256", ""))
                or _sha(raw_audit) != manifest["release_audit_sha256"]
                or source.get("provenance_audit_sha256") != manifest["release_audit_sha256"]):
            raise ValueError("Publisher/compiled audit differs from pinned release audit")
        if (manifest.get("module_id") != metadata["sword_id"]
                or manifest.get("metadata_path") != (module.relative_to(root) / "metadata.json").as_posix()
                or metadata["quality"]["status"] != "approved"
                or not SHA.fullmatch(manifest.get("release_zip_sha256", ""))
                or manifest.get("editorial_approval", {}).get("approved_by") !=
                    "Bible Resources project owner"):
            raise ValueError("Release/module identity or editorial approval mismatch")
        if (source.get("source_sha256") != validated_source_sha
                or source["source_sha256"] != manifest["provenance"]["final_candidate_osis_sha256"]):
            raise ValueError("Source identity differs from source validation")

        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("No release payload file inventory")
        payload_root = module / "payload"
        if payload_root.is_symlink() or not payload_root.is_dir():
            raise ValueError("Invalid release payload")
        actual = {}
        for item in payload_root.rglob("*"):
            if item.is_symlink():
                raise ValueError("Linked release payload member")
            if item.is_file():
                actual[item.relative_to(payload_root).as_posix()] = item
        if set(files) != set(actual):
            raise ValueError("Release payload differs from complete pinned inventory")
        for relative, expected in files.items():
            p = PurePosixPath(relative)
            if (p.is_absolute() or ".." in p.parts or not SHA.fullmatch(expected)
                    or _sha(actual[relative].read_bytes()) != expected):
                raise ValueError("Release file has invalid path or SHA-256: " + relative)
        if (audit.get("versification") != metadata.get("versification")
                or audit.get("experimental_runtime_needed") is not False
                or audit.get("original_usfm_archive_sha256") != manifest["source_usfm_zip_sha256"]
                or audit.get("original_usfx_archive_sha256") != manifest["source_usfx_zip_sha256"]
                or audit.get("original_usfx_sha256") is None):
            raise ValueError("Original edition/stock SWORD registry evidence mismatched")

        trial = audit["stock_sword_compiled_candidate"]["full_source_verse_roundtrip"]
        assessment = audit["stock_sword_reference_assessment"]
        totals = trial["totals"]
        count = trial["total_source_verse_keys"]
        chapters = trial["expected_chapters"]
        books = trial["books"]
        if (type(count) is not int or count <= 0 or type(chapters) is not int or chapters <= 0
                or not isinstance(books, list) or not books
                or sum(b["source_verses"] for b in books) != count
                or sum(b["chapters"] for b in books) != chapters
                or totals["source_verses"] != count or totals["chapters"] != chapters
                or assessment["source_verse_count"] != count
                or assessment["engine"] != "stock_released_sword"
                or assessment["compiler_versification"] != metadata["versification"]
                or assessment["all_reference_differences_explained"] is not True
                or assessment["all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks"] is not True
                or assessment["original_source_modified"] is not False
                or assessment["unclassified_verse_keys"] != []):
            raise ValueError("Incomplete original full-corpus source/reader inventory")

        missing, empty, appended = set(), set(), set()
        mismatches = trial["unmatched_verse_slot_classification"]
        if not isinstance(mismatches, list):
            raise ValueError("Missing original per-chapter discrepancy classifications")
        for chapter in mismatches:
            if chapter.get("complete_chapter_character_stream_equal_ignoring_whitespace") is not True:
                raise ValueError("Unexplained text change in mismatched chapter")
            book, ch = chapter["book"], chapter["chapter"]
            source_only, reader_only = chapter["source_only_verses"], chapter["reader_only_verses"]
            classified = chapter["diagnostic_slot_classes"]
            if len(classified) != len(source_only) + len(reader_only):
                raise ValueError("Unclassified individual reader/source key")
            for entry in classified:
                key = (book, ch, entry["verse"])
                if entry.get("no_reversification_applied") is not True:
                    raise ValueError("Reversified result masquerades as native index")
                if (entry.get("side") == "source_only"
                        and entry.get("classification") == "readback_preceding_slot_contains_both_verse_character_streams"
                        and entry.get("preceding_slot_compared") is True
                        and entry["verse"] in source_only):
                    if key in missing:
                        raise ValueError("Duplicate source-only key")
                    missing.add(key)
                    appended.add((key, (book, ch, entry["verse"] - 1)))
                elif (entry.get("side") == "reader_only"
                        and entry.get("classification") == "empty_readback_verse_slot"
                        and entry["verse"] in reader_only):
                    if key in empty:
                        raise ValueError("Duplicate reader-only empty key")
                    empty.add(key)
                else:
                    raise ValueError("Unexpected source/reader slot classification")
        if (len(missing) != totals["source_keys_missing"]
                or len(empty) != totals["sword_keys_unexpected"]
                or len(missing) != assessment["source_only_verse_count"]
                or len(empty) != assessment["unoccupied_compiled_verse_count"]):
            raise ValueError("Original inventory discrepancy counters disagree")

        observed = {
            ((a["book"], a["chapter"], a["source_verse"]),
             (a["book"], a["chapter"], a["compiled_verse"]))
            for a in assessment["appended_source_keys"]
            if a.get("distinct_original_reference_unavailable") is True
        }
        if observed != appended or len(observed) != len(assessment["appended_source_keys"]):
            raise ValueError("Actual compiler append differs from classified source keys")

        if missing:
            decisions = audit["authorized_editorial_index_compromise"]
            if (decisions["status"] != "source_bound_owner_authorized_index_compromise"
                    or decisions["observed_source_to_reader_keys_exactly_match_authorization"] is not True
                    or decisions["source_scripture_modified"] is not False
                    or decisions["authorized_merge_count"] != len(missing)):
                raise ValueError("Missing original explicit owner-approved merge")
            policy_path = module / "SOURCE_REFERENCE_MERGES.json"
            decisions_from_policy, digest = load_approved_merge_policy(
                policy_path,
                publisher_digest=audit["original_usfx_sha256"],
                versification=metadata["versification"])
            if digest != decisions["policy_sha256"]:
                raise ValueError("Approved merge policy differs from original audited policy")
            if len(decisions_from_policy) != len(missing):
                raise ValueError("Approved merge count does not match actual source loss")
            approved = {
                (e["authorial_source_key"], e["reader_source_key"],
                 e["osis_source_key"], e["osis_reader_key"])
                for e in decisions["reviewed_merges"]
                if e.get("source_verse_content_preserved") is True
            }
            policy_refs = {
                (e["authorial_source_key"], e["reader_source_key"],
                 e["osis_source_key"], e["osis_reader_key"])
                for e in json.loads(policy_path.read_text(encoding="utf-8"))["allowed_merges"]
            }
            if approved != policy_refs or len(approved) != len(missing):
                raise ValueError("Reviewed authorial/OSIS references changed")
            observed_authorial = {
                (src[0] + "." + str(src[1]) + "." + str(src[2]),
                 dst[0] + "." + str(dst[1]) + "." + str(dst[2]))
                for src, dst in appended
            }
            if {(src, dst) for src, dst, _, _ in approved} != observed_authorial:
                raise ValueError("Approved merge does not match observed source/reader slots")
            if {(src, dst) for src, dst in decisions_from_policy} != {
                    (src, dst) for _, _, src, dst in approved}:
                raise ValueError("Approved OSIS indexes do not match policy")
        elif (assessment.get("exact_source_index_preserved") is not True
              or (module / "SOURCE_REFERENCE_MERGES.json").exists()):
            raise ValueError("Unnecessary merged-index exception in exact-parity module")

        preview = audit["xiphos_test_preview_package"]
        if (preview.get("status") != "private_stock_sword_zip_reinstall_readback_verified"
                or preview.get("text_payload_files_byte_identical_to_verified_module") is not True
                or preview.get("publisher_original_usfx_sha256") != audit["original_usfx_sha256"]):
            raise ValueError("Released file chain lacks original independently reinstalled reader evidence")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
        errors.append(f"{module}/SOURCE_AUDIT.json: [PUBLISHED_SWORD_INDEX_UNVERIFIED] {exc}")
    return errors
