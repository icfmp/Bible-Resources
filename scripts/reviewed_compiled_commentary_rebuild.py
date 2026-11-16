#!/usr/bin/env python3
"""Offline, fail-closed binding of a reviewed SWORD commentary rebuild.

The recorded native comparison MUST be generated independently from the
complete original source and the actual libSWORD-installed rebuilt module.
This checker authenticates the exact source manifest, review contract,
native-audit receipt and every shipped byte. It does not manufacture or
reperform a source-text comparison from self-reported booleans.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


def zcom_member_suffixes(block_type: str) -> tuple[str, ...]:
    """Native zCom members follow SWORD compression block granularity."""
    prefix = {"BOOK": "b", "CHAPTER": "c", "VERSE": "v"}.get(block_type)
    if prefix is None:
        raise ValueError("Unsupported standard zCom compression block type")
    return tuple(
        f"{testament}.{prefix}z{suffix}"
        for testament in ("nt", "ot")
        for suffix in ("s", "v", "z")
    )

SHA = re.compile(r"[0-9a-f]{64}\Z")
ORIGINAL = re.compile(r"config/commentary-intake/[a-z0-9-]+\.json\Z")
REVIEW = re.compile(r"config/commentary-rebuilds/[a-z0-9-]+\.json\Z")
KEY = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")
GITHUB_ISSUE = re.compile(
    r"https://github\.com/[^/]+/[^/]+/issues/[1-9][0-9]*\Z"
)


def _object(path: Path, size_limit: int) -> tuple[dict, str]:
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size > size_limit):
        raise ValueError("Missing, linked or oversized attestation input")
    data = path.read_bytes()
    object_ = json.loads(data)
    if not isinstance(object_, dict):
        raise ValueError("Attestation is not an object")
    return object_, sha256(data).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def _counts(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == {"K", "I", "TOP"}
            and all(type(value[k]) is int and 0 <= value[k] <= 200000
                    for k in ("K", "I", "TOP")) and value["K"] > 0)


def _review_deltas(edits: object, links: object, original: dict,
                   candidate: dict) -> None:
    if (not isinstance(edits, list) or not isinstance(links, list)
            or len(edits) > 500 or len(links) > 50000
            or not edits and not links):
        raise ValueError("Unbounded or empty rebuilt source-delta declaration")
    changed = set()
    seen_orig_digests = set()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {
            "master_key", "original_sha256", "revised_sha256",
            "affected_original_keys"
        }:
            raise ValueError("Malformed reviewed authorial source correction")
        master = edit["master_key"]
        keys = edit["affected_original_keys"]
        if (not isinstance(master, str) or not KEY.fullmatch(master)
                or not _digest(edit["original_sha256"])
                or not _digest(edit["revised_sha256"])
                or edit["original_sha256"] == edit["revised_sha256"]
                or edit["original_sha256"] in seen_orig_digests
                or not isinstance(keys, list) or not 1 <= len(keys) <= original["K"]
                or keys != sorted(set(keys)) or master not in keys
                or any(not isinstance(key, str) or not KEY.fullmatch(key)
                       for key in keys)
                or changed.intersection(keys)):
            raise ValueError("Unreviewed, overlapping or inconsistent source correction")
        seen_orig_digests.add(edit["original_sha256"])
        changed.update(keys)
    added = set()
    for link in links:
        if (not isinstance(link, dict)
                or set(link) != {"new_key", "master_key"}
                or not isinstance(link["new_key"], str)
                or not isinstance(link["master_key"], str)
                or not KEY.fullmatch(link["new_key"])
                or not KEY.fullmatch(link["master_key"])
                or link["new_key"] == link["master_key"]
                or link["new_key"] in added
                or link["new_key"] in changed):
            raise ValueError("Unreviewed or duplicate rebuilt navigation alias")
        added.add(link["new_key"])
    if (candidate["K"] != original["K"] + len(added)
            or candidate["I"] != original["I"]
            or candidate["TOP"] != original["TOP"]):
        raise ValueError("Native I/K/TOP counts do not reconcile with link deltas")
    if any(link["master_key"] in added for link in links):
        raise ValueError("An added key cannot masquerade as an original master")
    if len(changed) > original["K"]:
        raise ValueError("Too many changed original native addresses")


def reviewed_rebuilt_commentary_errors(
        module_dir: Path, root: Path, metadata: dict,
        conf: dict) -> list[str]:
    """Validate an independently attested rebuilt SWORD zCom release.

    A passing synthetic fixture tests this contract, NOT authorial fidelity;
    the real native comparison and explicit project-owner approval must be
    reviewed and pinned before an actual module uses this route.
    """
    prefix = f"{module_dir.name}: [REBUILT_COMMENTARY_PROOF_INVALID] "
    try:
        if metadata.get("category") != "commentary":
            raise ValueError("Only commentaries may use the rebuild route")
        index = metadata.get("index_audit", {})
        review_name = index.get("manifest")
        if (index.get("mode") != "reviewed_compiled_commentary_rebuild"
                or not isinstance(review_name, str)
                or not REVIEW.fullmatch(review_name)):
            raise ValueError("Unreviewed rebuilt-commentary manifest path")
        review, _ = _object(root / review_name, 1_000_000)
        original_name = review.get("original_manifest")
        if not isinstance(original_name, str) or not ORIGINAL.fullmatch(original_name):
            raise ValueError("Original-source manifest path not pinned")
        original, original_manifest_sha = _object(root / original_name, 256_000)
        proof, _ = _object(module_dir / "SOURCE_VALIDATION.json", 256_000)
        audit, audit_sha = _object(module_dir / "SOURCE_AUDIT.json", 1_000_000)
        if (review.get("schema_version") != 1
                or review.get("status") != "owner_authorized_for_release"
                or review.get("module_id") != metadata["id"]
                or review.get("sword_id") != metadata["sword_id"]
                or review.get("version") != metadata["version"]
                or review.get("versification") != metadata["versification"]
                or review.get("original_manifest_sha256") != original_manifest_sha
                or review.get("original_archive_sha256") != original.get("archive_sha256")
                or review.get("original_native_corpus_sha256")
                   != original.get("native_raw_corpus_sha256")
                or review.get("original_module_id") != original.get("module_id")
                or original.get("category") != "commentary"
                or original.get("source_page_url") != metadata["origin"]["url"]
                or not _digest(review.get("candidate_native_corpus_sha256"))
                or not _digest(review.get("index_only_rebuild_native_corpus_sha256"))
                or review["index_only_rebuild_native_corpus_sha256"]
                   == review["candidate_native_corpus_sha256"]
                or review.get("source_audit_sha256") != audit_sha):
            raise ValueError("Original, version or source-audit identity differs")
        upstreams = metadata.get("upstreams")
        if (not isinstance(upstreams, list) or len(upstreams) != 1
                or upstreams[0].get("module_id") != original["module_id"]
                or upstreams[0].get("provider") != original.get("provider")
                or upstreams[0].get("last_integrated_version") != original.get("version")
                or upstreams[0].get("last_integrated_conf_sha256")
                   != original.get("stock_conf_sha256")):
            raise ValueError("Curated upstream identity is inconsistent")
        if (metadata.get("rights", {}).get("redistribution_allowed") is not True
                or metadata["rights"].get("derivatives_allowed") is not True
                or metadata["rights"].get("license") != conf.get("DistributionLicense")
                or metadata.get("quality", {}).get("status") != "approved"):
            raise ValueError("Derived source rights or editorial status unapproved")
        authorization = review.get("authorization")
        if (not isinstance(authorization, dict)
                or authorization.get("approved_by") != "Bible Resources project owner"
                or not isinstance(authorization.get("scope"), str)
                or len(authorization["scope"].strip()) < 20
                or not isinstance(authorization.get("evidence_url"), str)
                or not GITHUB_ISSUE.fullmatch(authorization["evidence_url"])):
            raise ValueError("Explicit per-edition owner review unavailable")
        expected_proof = {
            "schema_version": 1,
            "status": "validated",
            "source_kind": "reviewed_compiled_commentary_rebuild",
            "review_manifest": review_name,
            "source_audit_sha256": audit_sha,
            "original_archive_sha256": original["archive_sha256"],
            "candidate_native_corpus_sha256": review["candidate_native_corpus_sha256"],
            "curated_module_id": metadata["sword_id"],
            "curated_version": metadata["version"],
        }
        if any(proof.get(field) != value for field, value in expected_proof.items()):
            raise ValueError("Source validation proof is incomplete or inconsistent")
        if any(proof.get(field) is True for field in (
                "all_original_compressed_files_byte_identical",
                "all_native_original_keys_byte_identical",
                "no_original_source_text_edited")):
            raise ValueError("Rebuilt commentary must not impersonate stock identity")
        counts_original = review.get("original_native_counts")
        counts_candidate = review.get("candidate_native_counts")
        if not _counts(counts_original) or not _counts(counts_candidate):
            raise ValueError("Incomplete native I/K/TOP census")
        edits = review.get("source_edits")
        links = review.get("added_links")
        _review_deltas(edits, links, counts_original, counts_candidate)
        expected_audit = {
            "schema_version": 1,
            "status": "complete_native_rebuild_comparison",
            "source_kind": "reviewed_compiled_commentary_rebuild",
            "original_archive_sha256": review["original_archive_sha256"],
            "original_native_corpus_sha256": review["original_native_corpus_sha256"],
            "index_only_rebuild_native_corpus_sha256":
                review["index_only_rebuild_native_corpus_sha256"],
            "candidate_native_corpus_sha256": review["candidate_native_corpus_sha256"],
            "original_native_counts": counts_original,
            "candidate_native_counts": counts_candidate,
            "source_edits": edits,
            "added_links": links,
            "versification": metadata["versification"],
            "compiler": "osis2mod",
            "reader": "libSWORD",
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
        if any(audit.get(field) != value for field, value in expected_audit.items()):
            raise ValueError("Native comparison lacks a required verified invariant")
        if (conf.get("ModDrv") != "zCom"
                or conf.get("SourceType") != "OSIS"
                or conf.get("Versification") != metadata["versification"]
                or conf.get("Version") != metadata["version"]
                or conf.get("BlockType") not in {"BOOK", "CHAPTER", "VERSE"}
                or conf.get("BlockType") != review.get("block_type")):
            raise ValueError("Compiled zCom format or metadata does not match review")
        folder = metadata["sword_id"].lower()
        paths = {
            "mods.d/" + folder + ".conf",
            *("modules/comments/zcom/" + folder + "/" + name
              for name in zcom_member_suffixes(conf.get("BlockType"))),
        }
        expected_files = review.get("payload_sha256")
        if (not isinstance(expected_files, dict)
                or set(expected_files) != paths
                or not all(_digest(value) for value in expected_files.values())):
            raise ValueError("Incomplete exact compiled payload file inventory")
        payload = module_dir / "payload"
        if payload.is_symlink() or not payload.is_dir():
            raise ValueError("Missing original-safe payload directory")
        actual = {}
        for path in payload.rglob("*"):
            if path.is_symlink():
                raise ValueError("Symlink in rebuilt SWORD payload")
            if path.is_file():
                actual[path.relative_to(payload).as_posix()] = path
        if set(actual) != paths:
            raise ValueError("Added or omitted compiled commentary files")
        for relative in sorted(paths):
            if sha256(actual[relative].read_bytes()).hexdigest() != expected_files[relative]:
                raise ValueError("Compiled commentary payload checksum mismatch: " + relative)
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError) as exc:
        return [prefix + str(exc)]
    return []
