#!/usr/bin/env python3
"""Versioned, content-free source/native Bible stage-4 subcheck receipts.

The metadata receipts allow later exact-input/tool-bound review and cautious
reuse. They do NOT mean that a subcheck ran in its own job or that human
editorial gates passed. Only fixed machine codes, integers, SHA digests and
bounded canonical verse references may leave private runner memory.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

HEX = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
RESOURCE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
VERSE = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$")
SUBCHECKS = ("4a", "4b", "4c", "4d")
DEPENDENCIES = {"4a": (), "4b": ("4a",), "4c": ("4b",),
                "4d": ("4a", "4b", "4c")}
STATUS = {"DONE", "PARTIAL", "BLOCKED", "REVIEW_REQUIRED"}
METRICS = {"exact_native_verse_probes", "original_numbered_note_inventory_count",
           "matching_indexed_keys_checked"}
MAX_NUMBER = 300_000
MAX_REFS = 8


class Stage4ReceiptError(ValueError):
    """Unpinned, unknown or potentially source-leaking machine evidence."""


def _canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(data: object) -> str:
    return sha256(_canonical(data)).hexdigest()


def _check_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict) or not RESOURCE.fullmatch(
            manifest.get("resource_id", "")):
        raise Stage4ReceiptError("Invalid reviewed resource ID")
    for kind in ("source", "sword"):
        value = manifest.get(kind, {}).get("sha256")
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise Stage4ReceiptError("Source or SWORD original not exactly pinned")


def _metrics(evidence: dict) -> dict:
    fast = evidence.get("fast_stock_note_preflight", {})
    rows = evidence.get("maintext", {}).get("classifications", {})
    if not isinstance(fast, dict) or not isinstance(rows, dict):
        raise Stage4ReceiptError("Unexpected source/native evidence type")
    candidates = {
        "exact_native_verse_probes": fast.get("independent_exact_native_verse_probes"),
        "original_numbered_note_inventory_count":
            fast.get("original_numbered_note_inventory_count"),
        "matching_indexed_keys_checked": rows.get("matching_indexed_keys_checked"),
    }
    out = {}
    for key in sorted(METRICS):
        number = candidates[key]
        if number is None:
            continue
        if type(number) is not int or not 0 <= number <= MAX_NUMBER:
            raise Stage4ReceiptError("Invalid original/native machine count")
        out[key] = number
    return out


def _samples(evidence: dict) -> list[str]:
    fast = evidence.get("fast_stock_note_preflight", {})
    if not isinstance(fast, dict):
        raise Stage4ReceiptError("Unexpected early source/native evidence")
    ref = fast.get("sampled_exact_source_reference")
    if ref is None:
        return []
    if not isinstance(ref, str) or not VERSE.fullmatch(ref):
        raise Stage4ReceiptError("Unsafe sampled source reference")
    return [ref]


def _scope(evidence: dict) -> dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """Conservative statuses limited to independently evidenced facts."""
    fast = evidence.get("fast_stock_note_preflight", {})
    main = evidence.get("maintext", {})
    witness = evidence.get("maintext_scope_classification", {})
    stock = evidence.get("stock_reuse_preflight", {})
    index = evidence.get("reference_index", {})
    for value in (fast, main, witness, stock, index):
        if not isinstance(value, dict):
            raise Stage4ReceiptError("Malformed source/native audit evidence")
    full = isinstance(evidence.get("actual_native_raw_manifest_sha256"), str) and bool(
        HEX.fullmatch(evidence["actual_native_raw_manifest_sha256"]))
    early_loss = fast.get("fast_stock_reuse_disqualified") is True
    material_loss = stock.get("proven_material_stock_loss") is True
    index_equal = index.get("comparison", {}).get(
        "exact_reference_key_parity") is True if isinstance(index.get(
            "comparison", {}), dict) else False
    main_equal = witness.get(
        "all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding"
    ) is True
    rows = main
    word = rows.get("source_native_body_boundary_word_position_screen", {})
    punctuation = rows.get("source_native_nonwhitespace_codepoint_boundary_screen", {})
    order = rows.get("source_native_ordered_body_kind_screen", {})
    topology = rows.get("source_native_p_q_event_topology_diagnostic", {})
    for value in (word, punctuation, order, topology):
        if not isinstance(value, dict):
            raise Stage4ReceiptError("Invalid structural evidence")
    if early_loss:
        reason = (
            "unmodified_stock_proven_note_loss",
            "index_not_examined_after_early_stock_rejection",
        )
        return {
            "4a": ("BLOCKED", (), reason),
            "4b": ("BLOCKED", (), ("full_main_text_scan_not_executed",)),
            "4c": ("BLOCKED", (), ("structural_audit_not_executed",)),
            "4d": ("BLOCKED", ("stock_note_loss_proven_in_native_entry",), (
                "replacement_module_requires_independent_audit",)),
        }
    index_ready = index_equal
    main_ready = bool(full and main_equal)
    word_ok = word.get("all_mapped_book_p_q_start_end_word_ordinals_match") is True
    punctuation_ok = punctuation.get(
        "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match") is True
    order_ok = order.get("same_order_and_kind_in_every_mapped_book") is True
    structure_difference = (
        topology.get("status") == "source_native_structural_topology_differs"
        or word.get("all_mapped_book_p_q_start_end_word_ordinals_match") is False
        or punctuation.get(
            "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match") is False
        or order.get("same_order_and_kind_in_every_mapped_book") is False
    )
    if index_ready:
        a = ("DONE", ("source_native_occupied_reference_keys_match",), ())
    elif index:
        a = ("BLOCKED", (), ("source_native_reference_index_not_equal_or_unproven",))
    else:
        a = ("PARTIAL", (), ("independent_source_native_index_not_verified",))
    if main_ready:
        b = ("PARTIAL", ("full_native_scan_and_mapped_words_punctuation_match",), (
            "complete_original_to_native_index_and_versification_still_separate",
            "source_whitespace_not_asserted_identical"))
    elif full or witness:
        b = ("BLOCKED", (), ("mapped_main_text_parity_failed_or_not_proven",))
    else:
        b = ("BLOCKED", (), ("full_main_text_scan_not_executed",))
    if structure_difference:
        c = ("BLOCKED", (), ("source_native_p_q_boundary_or_kind_difference",))
    elif (full and word_ok and punctuation_ok and order_ok
          and topology.get("all_source_native_p_q_open_close_event_topology_match") is True):
        c = ("PARTIAL", (
            "p_q_open_close_word_and_codepoint_boundaries_match",
            "p_q_open_close_pairing_and_topology_machine_positions_match",
        ), (
            "whitespace_verse_zero_and_non_p_q_styles_unverified",
            "source_native_representation_equivalence_not_editorially_approved"))
    else:
        c = ("PARTIAL" if full else "BLOCKED", (),
             ("cross_verse_verse_zero_and_structural_positions_unverified",))
    if material_loss:
        d = ("BLOCKED", ("material_original_native_stock_loss_proven",), (
            "replacement_requires_separate_source_native_proof",))
    else:
        d = ("REVIEW_REQUIRED", (), (
            "no_approval_of_stock_reuse_from_negative_sample",
            "editorial_source_identity_and_rights_review_not_automated"))
    return {"4a": a, "4b": b, "4c": c, "4d": d}


def create_subcheck_receipts(
    manifest: dict, fidelity: dict, *, commit_sha: str, run_url: str | None
) -> dict:
    """Produce self-checksummed facts about four *distinct* machine questions.

    Does not perform an additional audit or claim that a source-native scan
    was completed when the fast loss gate correctly stopped it early.
    """
    _check_manifest(manifest)
    if not isinstance(fidelity, dict) or not isinstance(
            fidelity.get("evidence"), dict):
        raise Stage4ReceiptError("Missing machine evidence")
    if not isinstance(commit_sha, str) or (commit_sha != "local-unpinned"
                                          and not COMMIT.fullmatch(commit_sha)):
        raise Stage4ReceiptError("Unpinned or invalid audit tool commit")
    if run_url is not None and (not isinstance(run_url, str)
                                or not re.fullmatch(
                                    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[1-9][0-9]*",
                                    run_url)):
        raise Stage4ReceiptError("Unsafe workflow run reference")
    evidence = fidelity["evidence"]
    exact = evidence.get("original_archives", {})
    if not isinstance(exact, dict):
        raise Stage4ReceiptError("Original input receipts malformed")
    # A failed-before-acquire run is not a source-attested certificate.
    acquired = all(
        isinstance(exact.get(k), dict) and
        exact[k].get("sha256") == manifest[k]["sha256"]
        for k in ("source", "sword"))
    scoped = _scope(evidence)
    result = {
        "schema_version": 1,
        "resource_id": manifest["resource_id"],
        "input_source_archive_sha256": manifest["source"]["sha256"],
        "input_sword_archive_sha256": manifest["sword"]["sha256"],
        "input_manifest_sha256": _sha(manifest),
        "audit_tool_commit": commit_sha,
        "run_url": run_url,
        "verified_exact_original_archives_in_this_run": acquired,
        "only_metadata_no_bible_or_note_text": True,
        "editorial_or_publication_approved": False,
        "subchecks": {},
    }
    metrics = _metrics(evidence)
    samples = _samples(evidence)
    for name in SUBCHECKS:
        state, proven, gaps = scoped[name]
        if not acquired:
            state = "BLOCKED"
            proven = ()
            gaps = ("sha_pinned_original_archives_not_independently_reacquired",)
        deps = {dep: result["subchecks"][dep]["digest_sha256"]
                for dep in DEPENDENCIES[name]}
        row = {
            "name": name,
            "status": state,
            "verified_machine_codes": list(proven),
            "unverified_machine_codes": list(gaps),
            "dependencies": deps,
            "counts": metrics if name == "4d" else {},
            "sampled_original_reference_ids": samples if name == "4d" else [],
            "completed_full_native_corpus_scan": bool(
                evidence.get("actual_native_raw_manifest_sha256"))
                if name in ("4b", "4c") else False,
        }
        row["digest_sha256"] = _sha(row)
        result["subchecks"][name] = row
    return result


def verify_receipts_for_reuse(
    candidate: dict, manifest: dict, *, commit_sha: str,
    subcheck: str
) -> dict:
    """Fail closed on any lineage, dependency, structure or pin mismatch.

    Returns *only* the exact prior machine status, never editorial approval.
    No full audit is made by this function; a prior valid BLOCKED stays BLOCKED.
    """
    _check_manifest(manifest)
    if subcheck not in SUBCHECKS:
        raise Stage4ReceiptError("Unsupported requested subcheck")
    if not isinstance(candidate, dict) or set(candidate) != {
            "schema_version", "resource_id", "input_source_archive_sha256",
            "input_sword_archive_sha256", "input_manifest_sha256",
            "audit_tool_commit", "run_url",
            "verified_exact_original_archives_in_this_run",
            "only_metadata_no_bible_or_note_text",
            "editorial_or_publication_approved", "subchecks"}:
        raise Stage4ReceiptError("Unexpected or incomplete reusable evidence")
    if (candidate["schema_version"] != 1 or
        candidate["resource_id"] != manifest["resource_id"] or
        candidate["input_source_archive_sha256"] != manifest["source"]["sha256"] or
        candidate["input_sword_archive_sha256"] != manifest["sword"]["sha256"] or
        candidate["input_manifest_sha256"] != _sha(manifest) or
        not COMMIT.fullmatch(commit_sha) or
        candidate["audit_tool_commit"] != commit_sha or
        candidate["verified_exact_original_archives_in_this_run"] is not True or
        candidate["only_metadata_no_bible_or_note_text"] is not True or
        candidate["editorial_or_publication_approved"] is not False or
        not isinstance(candidate["run_url"], str) or
        not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[1-9][0-9]*",
            candidate["run_url"])):
        raise Stage4ReceiptError("Source, tool, runner or manifest identity drift")
    allrows = candidate.get("subchecks")
    if not isinstance(allrows, dict) or set(allrows) != set(SUBCHECKS):
        raise Stage4ReceiptError("Incomplete stage-4 lineage graph")
    for name in SUBCHECKS:
        row = allrows[name]
        if not isinstance(row, dict) or set(row) != {
            "name", "status", "verified_machine_codes", "unverified_machine_codes",
            "dependencies", "counts", "sampled_original_reference_ids",
            "completed_full_native_corpus_scan", "digest_sha256"
        } or row["name"] != name or row["status"] not in STATUS:
            raise Stage4ReceiptError("Malformed subcheck result")
        if not isinstance(row["dependencies"], dict) or set(
                row["dependencies"]) != set(DEPENDENCIES[name]):
            raise Stage4ReceiptError("Malformed source/native dependencies")
        for dep in DEPENDENCIES[name]:
            if row["dependencies"][dep] != allrows[dep]["digest_sha256"]:
                raise Stage4ReceiptError("Stale dependent subcheck")
        if row["digest_sha256"] != _sha({k:v for k,v in row.items()
                                       if k != "digest_sha256"}):
            raise Stage4ReceiptError("Untrusted subcheck machine checksum")
        for key in ("verified_machine_codes", "unverified_machine_codes"):
            codes = row[key]
            if (not isinstance(codes, list) or len(codes)>12 or
                    any(not isinstance(v, str) or
                        not re.fullmatch(r"[a-z][a-z0-9_]{1,95}", v)
                        for v in codes)):
                raise Stage4ReceiptError("Unsafe machine finding code")
        if not isinstance(row["counts"], dict) or not set(
                row["counts"]).issubset(METRICS):
            raise Stage4ReceiptError("Unsafe source/native count")
        for value in row["counts"].values():
            if type(value) is not int or not 0 <= value <= MAX_NUMBER:
                raise Stage4ReceiptError("Unbounded finding count")
        refs = row["sampled_original_reference_ids"]
        if (not isinstance(refs, list) or len(refs) > MAX_REFS
                or any(not isinstance(v, str) or not VERSE.fullmatch(v)
                       for v in refs)
                or type(row["completed_full_native_corpus_scan"]) is not bool):
            raise Stage4ReceiptError("Unsafe note or Scripture sample")
        if row["status"] == "DONE" and row["unverified_machine_codes"]:
            raise Stage4ReceiptError("Complete check has unverified mandatory facts")
    return dict(allrows[subcheck], editorial_or_publication_approved=False,
                machine_receipt_reused_only=True)
