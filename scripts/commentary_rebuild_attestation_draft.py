#!/usr/bin/env python3
"""Produce a text-free, NEVER-APPROVED draft from a real private SWORD rebuild.

The caller must independently compare complete original/index-only/rebuilt
native maps, all linked-section boundaries, and the real installed candidate.
This function checks the exact scoped differences and packages the resulting
native and source fingerprints for a *future* owner-reviewed attestation.
It never modifies the original, exposes source words, or authorizes release.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from compiled_stock_commentary_proof import SUFFIXES
from reviewed_compiled_commentary_rebuild import _review_deltas

# These messages are fixed, source-neutral and intentionally contain no
# original text, citation labels, XML or user-controlled value interpolation.
PUBLIC_REBUILD_ATTESTATION_ERROR_CODES = frozenset({
    "Private native evidence or original manifest unavailable",
    "Source witness manifest absent, linked or oversized",
    "Real original source fingerprint does not match pin",
    "Malformed or duplicated original native source bodies",
    "Complete original/index-only/candidate K-I-TOP parity failed",
    "Actual native raw stream corpus digest/count not independently confirmed",
    "Incomplete real native SWORD corpus scan",
    "Source-delta receipt lacks exact reversible original native keys",
    "Source-delta master does not belong to edited original group",
    "Unpinned or mis-scoped original source-body correction",
    "Unreviewed compiled original K bytes changed",
    "Corrected original source-byte evidence is incomplete",
    "Corrected source hash not tied to reviewed native edit",
    "Added SWORD key does not equal reviewed original master",
    "Missing or unsafe actually installed candidate payload",
})

SHA = re.compile(r"[0-9a-f]{64}\Z")
ORIGINAL_PATH = re.compile(r"config/commentary-intake/[a-z0-9-]+\.json\Z")


def _counts(data: dict) -> dict:
    return {"K": len(data["K"]), "I": len(data["I"]), "TOP": len(data["U"])}


def _receipt_counts(receipt: dict) -> dict:
    return {
        "K": receipt["actual_occupied_numbered_entry_count"],
        "I": receipt["actual_occupied_intro_entry_count"],
        "TOP": receipt["actual_occupied_anonymous_top_entry_count"],
    }


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def private_rebuild_attestation_draft(
        *, repo_root: Path, original_manifest: str, module_id: str,
        version: str, versification: str,
        original_native_corpus_sha256: str,
        original_source_numbered: dict[str, list[tuple[str, bytes]]],
        original_source_intros: dict[str, bytes],
        original_source_top: list[bytes],
        original_index_compiled: dict,
        revised_compiled: dict,
        installed_compiled: dict,
        index_receipt: dict, revised_receipt: dict, installed_receipt: dict,
        source_edit_receipts: list[dict],
        source_edit_affected_keys: list[list[str]],
        corrected_source_by_original_key: dict[str, bytes],
        aliases: dict[str, dict],
        installed_candidate_root: Path,
        existing_links_preserved: bool,
        full_source_semantic_and_structure_parity_verified: bool,
        all_new_native_aliases_linked: bool,
        real_reader_passage_matches: int) -> dict:
    """Build only a metadata review draft after strict in-memory comparisons.

    Native receipts MUST originate from the full libSWORD raw stream, not
    synthesized from the reconstructed dictionaries. Their ordered digest
    follows the source inventory's collision-resistant length framing.
    """
    if (not ORIGINAL_PATH.fullmatch(original_manifest)
            or repo_root.is_symlink()
            or not SHA.fullmatch(original_native_corpus_sha256)
            or not isinstance(source_edit_receipts, list)
            or len(source_edit_receipts) != len(source_edit_affected_keys)
            or not source_edit_receipts
            or not isinstance(aliases, dict) or not aliases
            or existing_links_preserved is not True
            or full_source_semantic_and_structure_parity_verified is not True
            or all_new_native_aliases_linked is not True
            or type(real_reader_passage_matches) is not int
            or not 1 <= real_reader_passage_matches <= 8):
        raise ValueError("Private native evidence or original manifest unavailable")
    original_path = repo_root / original_manifest
    if (original_path.is_symlink() or not original_path.is_file()
            or original_path.stat().st_size > 256_000):
        raise ValueError("Source witness manifest absent, linked or oversized")
    original_bytes = original_path.read_bytes()
    original = json.loads(original_bytes)
    if (original.get("category") != "commentary"
            or original.get("native_raw_corpus_sha256") != original_native_corpus_sha256
            or not SHA.fullmatch(original.get("archive_sha256", ""))
            or not SHA.fullmatch(original.get("stock_conf_sha256", ""))):
        raise ValueError("Real original source fingerprint does not match pin")
    source_k = {key: raw for chapter in original_source_numbered.values()
                for key, raw in chapter}
    original_counts = {
        "K": len(source_k), "I": len(original_source_intros),
        "TOP": len(original_source_top),
    }
    original_expected_keys = set(source_k)
    if (sum(len(chapter) for chapter in original_source_numbered.values())
            != len(source_k)
            or any(not isinstance(raw, bytes) for raw in source_k.values())
            or any(not isinstance(raw, bytes) for raw in original_source_intros.values())
            or any(not isinstance(raw, bytes) for raw in original_source_top)
            or not original_counts["K"] or not original_counts["I"]):
        raise ValueError("Malformed or duplicated original native source bodies")
    alias_keys = set(aliases)
    if (alias_keys & original_expected_keys
            or set(original_index_compiled["K"]) != original_expected_keys | alias_keys
            or set(revised_compiled["K"]) != original_expected_keys | alias_keys
            or installed_compiled != revised_compiled
            or original_index_compiled["I"] != revised_compiled["I"]
            or original_index_compiled["U"] != revised_compiled["U"]
            or len(original_index_compiled["I"]) != original_counts["I"]
            or len(original_index_compiled["U"]) != original_counts["TOP"]):
        raise ValueError("Complete original/index-only/candidate K-I-TOP parity failed")
    index_counts = _counts(original_index_compiled)
    revised_counts = _counts(revised_compiled)
    installed_counts = _counts(installed_compiled)
    if (any(_receipt_counts(receipt) != counts
            for receipt, counts in (
                (index_receipt, index_counts),
                (revised_receipt, revised_counts),
                (installed_receipt, installed_counts)))
            or revised_receipt["all_native_raw_entries_ordered_sha256"]
               != installed_receipt["all_native_raw_entries_ordered_sha256"]):
        raise ValueError("Actual native raw stream corpus digest/count not independently confirmed")
    for receipt in (index_receipt, revised_receipt, installed_receipt):
        if (receipt["status"]
                != "actual_full_native_raw_corpus_hashed_not_source_parity_approved"
                or not SHA.fullmatch(receipt["all_native_raw_entries_ordered_sha256"])):
            raise ValueError("Incomplete real native SWORD corpus scan")
    modifications = {
        key for key in original_expected_keys
        if original_index_compiled["K"][key] != revised_compiled["K"][key]
    }
    declared_edits = []
    declared_changed = set()
    for receipt, keys in zip(source_edit_receipts, source_edit_affected_keys):
        if (not isinstance(receipt, dict)
                or not isinstance(keys, list) or not keys
                or keys != sorted(set(keys))
                or not set(keys) <= original_expected_keys
                or declared_changed.intersection(keys)
                or receipt.get("reverse_restores_exact_original_raw_bytes") is not True):
            raise ValueError("Source-delta receipt lacks exact reversible original native keys")
        master = receipt.get("original_native_entry")
        if not isinstance(master, str) or master not in keys:
            raise ValueError("Source-delta master does not belong to edited original group")
        original_hash = receipt.get("original_raw_sha256")
        corrected_hash = receipt.get("proposed_raw_sha256")
        if (not isinstance(original_hash, str)
                or not isinstance(corrected_hash, str)
                or not SHA.fullmatch(original_hash)
                or not SHA.fullmatch(corrected_hash)
                or original_hash == corrected_hash
                or _sha(source_k[master]) != original_hash
                or {key for key in original_expected_keys
                    if _sha(source_k[key]) == original_hash} != set(keys)):
            raise ValueError("Unpinned or mis-scoped original source-body correction")
        declared_changed.update(keys)
        declared_edits.append({
            "master_key": master, "original_sha256": original_hash,
            "revised_sha256": corrected_hash,
            "affected_original_keys": keys,
        })
    if modifications != declared_changed:
        raise ValueError("Unreviewed compiled original K bytes changed")
    if (not isinstance(corrected_source_by_original_key, dict)
            or set(corrected_source_by_original_key) != declared_changed
            or any(not isinstance(raw, bytes)
                   for raw in corrected_source_by_original_key.values())):
        raise ValueError("Corrected original source-byte evidence is incomplete")
    for edit in declared_edits:
        if any(_sha(corrected_source_by_original_key[key]) != edit["revised_sha256"]
               for key in edit["affected_original_keys"]):
            raise ValueError("Corrected source hash not tied to reviewed native edit")
    links = []
    for key, claim in sorted(aliases.items()):
        master = claim.get("link_to") if isinstance(claim, dict) else None
        if (master not in original_expected_keys
                or claim.get("source_raw_sha256") != _sha(source_k[master])
                or revised_compiled["K"][key] != revised_compiled["K"][master]
                or original_index_compiled["K"][key]
                   != original_index_compiled["K"][master]):
            raise ValueError("Added SWORD key does not equal reviewed original master")
        links.append({"new_key": key, "master_key": master})
    _review_deltas(declared_edits, links, original_counts, revised_counts)
    folder = module_id.lower()
    paths = [
        "mods.d/" + folder + ".conf",
        *("modules/comments/zcom/" + folder + "/" + suffix
          for suffix in SUFFIXES),
    ]
    package_hashes = {}
    for rel in paths:
        path = installed_candidate_root / rel
        if (path.is_symlink() or not path.is_file()
                or path.stat().st_size > 20 * 1024 * 1024):
            raise ValueError("Missing or unsafe actually installed candidate payload")
        package_hashes[rel] = _sha(path.read_bytes())
    audit = {
        "schema_version": 1,
        "status": "complete_native_rebuild_comparison",
        "source_kind": "reviewed_compiled_commentary_rebuild",
        "original_archive_sha256": original["archive_sha256"],
        "original_native_corpus_sha256": original_native_corpus_sha256,
        "index_only_rebuild_native_corpus_sha256":
            index_receipt["all_native_raw_entries_ordered_sha256"],
        "candidate_native_corpus_sha256":
            installed_receipt["all_native_raw_entries_ordered_sha256"],
        "original_native_counts": original_counts,
        "candidate_native_counts": revised_counts,
        "source_edits": declared_edits,
        "added_links": links,
        "versification": versification,
        "compiler": "osis2mod", "reader": "libSWORD",
        "full_original_and_rebuilt_native_inventory_compared": True,
        "all_other_original_K_bytes_identical": True,
        "all_original_I_bytes_identical": True,
        "all_original_TOP_bytes_identical": True,
        "all_original_linked_section_boundaries_preserved": True,
        "all_added_K_keys_link_to_reviewed_original_master": True,
        "all_edited_source_structure_and_unedited_content_preserved": True,
        "no_unreviewed_original_native_keys_changed": True,
        "no_source_prose_exported": True,
    }
    # Deliberately not owner-approved. Future production must regenerate
    # this proof against the final committed, fully reviewed SWORD payload.
    review = {
        "schema_version": 1,
        "status": "private_draft_not_owner_authorized_for_release",
        "module_id": original_manifest.split("/")[-1].removesuffix(".json"),
        "sword_id": module_id,
        "version": version, "versification": versification,
        "original_manifest": original_manifest,
        "original_manifest_sha256": _sha(original_bytes),
        "original_archive_sha256": original["archive_sha256"],
        "original_module_id": original["module_id"],
        "original_native_corpus_sha256": original_native_corpus_sha256,
        "index_only_rebuild_native_corpus_sha256":
            index_receipt["all_native_raw_entries_ordered_sha256"],
        "candidate_native_corpus_sha256":
            installed_receipt["all_native_raw_entries_ordered_sha256"],
        "original_native_counts": original_counts,
        "candidate_native_counts": revised_counts,
        "source_edits": declared_edits, "added_links": links,
        "block_type": "CHAPTER",
        "payload_sha256": package_hashes,
        "authorization": {
            "approved_by": "PENDING — project owner decision required",
            "scope": "Private complete-source and native SWORD verification; not a public release",
            "evidence_url": "",
        },
    }
    audit_raw = (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode()
    review["source_audit_sha256"] = _sha(audit_raw)
    source_validation = {
        "schema_version": 1, "status": "private_draft_not_release_validated",
        "source_kind": "reviewed_compiled_commentary_rebuild",
        "review_manifest": "config/commentary-rebuilds/"
                           + review["module_id"] + ".json",
        "source_audit_sha256": _sha(audit_raw),
        "original_archive_sha256": original["archive_sha256"],
        "candidate_native_corpus_sha256":
            installed_receipt["all_native_raw_entries_ordered_sha256"],
        "curated_module_id": module_id, "curated_version": version,
    }
    return {
        "status": "PRIVATE_REAL_NATIVE_ATTESTATION_DRAFT_NOT_RELEASE",
        "release_authorized": False,
        "data_text_exported": False,
        "source_audit": audit,
        "source_audit_sha256": _sha(audit_raw),
        "review_manifest": review,
        "source_validation": source_validation,
        "original_native_K_count": original_counts["K"],
        "added_native_K_count": len(links),
        "original_K_keys_edited": len(modifications),
        "original_native_linked_section_boundaries_preserved": True,
        "real_reader_sample_count": real_reader_passage_matches,
        "actual_installed_candidate_payload_hashed": True,
    }
