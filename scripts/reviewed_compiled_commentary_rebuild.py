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

def commentary_payload_paths(sword_id: str, block_type: str,
                             driver: str = "zCom") -> frozenset[str]:
    """Exact seven-member SWORD commentary payload for zCom or zCom4."""
    if (not isinstance(sword_id, str)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,31}", sword_id)):
        raise ValueError("Unsafe SWORD module identifier for native payload")
    if driver not in ("zCom", "zCom4"):
        raise ValueError("Unsupported native SWORD commentary driver")
    folder = sword_id.lower()
    return frozenset({"mods.d/" + folder + ".conf"} | {
        "modules/comments/" + driver.lower() + "/" + folder + "/" + member
        for member in zcom_member_suffixes(block_type)
    })


def zcom_payload_paths(sword_id: str, block_type: str) -> frozenset[str]:
    """Backwards-compatible exact zCom-only layout used by other release gates."""
    return commentary_payload_paths(sword_id, block_type, "zCom")


def checked_commentary_payload_files(payload: Path, sword_id: str,
                                     block_type: str,
                                     driver: str = "zCom") -> dict[str, Path]:
    """Read-only exact inventory gate; no source/owner approval is inferred."""
    expected = commentary_payload_paths(sword_id, block_type, driver)
    if payload.is_symlink() or not payload.is_dir():
        raise ValueError("Missing or unsafe native commentary payload directory")
    found: dict[str, Path] = {}
    for item in payload.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlink in reviewed SWORD payload")
        if item.is_file():
            found[item.relative_to(payload).as_posix()] = item
    if set(found) != expected:
        raise ValueError("Added or omitted native commentary payload inventory files")
    return found


def checked_zcom_payload_files(payload: Path, sword_id: str,
                               block_type: str) -> dict[str, Path]:
    """Backwards-compatible fail-closed zCom inventory gate."""
    return checked_commentary_payload_files(payload, sword_id, block_type, "zCom")


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



def _check_incremental_revision(module_dir: Path, root: Path, metadata: dict,
                                review: dict, audit: dict) -> dict:
    """Bind a source-attested semantic rebuild to its prior immutable review.

    The legacy raw-byte comparison still applies to v1 reviews. A subsequent
    serialization-changing rebuild needs a separate, versioned proof, not
    false byte-identity claims or a resource-specific exemption.
    """
    revision = review.get("incremental_revision")
    if not isinstance(revision, dict):
        raise ValueError("Missing incremental source/reader evidence")
    if not re.fullmatch(r"[a-z0-9-]+", module_dir.name):
        raise ValueError("Unsafe edition identity")
    language = metadata.get("language")
    if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("Unsafe edition language")
    edition = root / "sources/cleaned/commentaries" / language / module_dir.name
    previous_version = revision.get("previous_version")
    version = metadata["version"]
    if not all(isinstance(v, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v)
               for v in (previous_version, version)) or (
                   tuple(map(int, previous_version.split("."))) >= tuple(map(int, version.split(".")))):
        raise ValueError("Previous review must precede the candidate")
    archive = edition / "editorial/evidence" / ("release-" + previous_version)
    previous, previous_sha = _object(archive / "review-manifest.json", 1_000_000)
    previous_audit, previous_audit_sha = _object(archive / "SOURCE_AUDIT.json", 1_000_000)
    if (previous.get("schema_version") != 1 or previous.get("status") != "owner_authorized_for_release"
            or previous.get("version") != previous_version
            or previous.get("module_id") != metadata["id"]
            or previous.get("sword_id") != metadata["sword_id"]
            or previous.get("versification") != metadata["versification"]
            or previous_sha != revision.get("previous_review_sha256")
            or previous_audit_sha != previous.get("source_audit_sha256")
            or previous_audit.get("candidate_native_corpus_sha256") != previous.get("candidate_native_corpus_sha256")
            or previous.get("candidate_native_corpus_sha256") != revision.get("previous_native_corpus_sha256")
            or previous.get("candidate_native_counts") != review["candidate_native_counts"]
            or any(previous.get(key) != review.get(key) for key in (
                "original_manifest", "original_manifest_sha256", "original_archive_sha256",
                "original_native_corpus_sha256", "original_native_counts",
                "index_only_rebuild_native_corpus_sha256", "added_links", "source_edits"))):
        raise ValueError("Prior immutable review does not match revision ancestry")
    previous_cleanup, cleanup_sha = _object(archive / "CLEANUP_MANIFEST.json", 1_000_000)
    if (cleanup_sha != revision.get("previous_cleanup_sha256")
            or previous_cleanup.get("reconstructed_source_sha256") != revision.get("previous_source_sha256")
            or previous_cleanup.get("source_native_corpus_sha256") != revision["previous_native_corpus_sha256"]):
        raise ValueError("Previous cleaned master provenance differs")
    source_name = revision.get("source_name")
    if not isinstance(source_name, str) or not re.fullmatch(r"[a-z0-9-]+\.osis\.xml", source_name):
        raise ValueError("Unsafe canonical OSIS source filename")
    source = edition / source_name
    if (source.is_symlink() or not source.is_file() or source.stat().st_size > 128 * 1024 * 1024
            or sha256(source.read_bytes()).hexdigest() != revision.get("candidate_source_sha256")):
        raise ValueError("Canonical OSIS source checksum mismatch")
    if (not _digest(revision.get("previous_source_sha256"))
            or not _digest(revision.get("candidate_source_sha256"))
            or revision["previous_source_sha256"] == revision["candidate_source_sha256"]):
        raise ValueError("Missing distinct source revision fingerprints")
    evidence, evidence_sha = _object(
        edition / "editorial/evidence" / ("release-" + version) / "incremental-native-reader.json", 1_000_000)
    if (evidence_sha != revision.get("evidence_sha256")
            or evidence.get("schema_version") != 1
            or evidence.get("previous_source_sha256") != revision["previous_source_sha256"]
            or evidence.get("candidate_source_sha256") != revision["candidate_source_sha256"]
            or evidence.get("previous_native_corpus_sha256") != revision["previous_native_corpus_sha256"]
            or evidence.get("candidate_native_corpus_sha256") != review["candidate_native_corpus_sha256"]
            or evidence.get("candidate_native_counts") != review["candidate_native_counts"]
            or evidence.get("payload_sha256") != review["payload_sha256"]
            or evidence.get("semantic_changed_keys") != revision.get("semantic_changed_keys")
            or evidence.get("reference_changed_keys") != revision.get("reference_changed_keys")
            or evidence.get("missing_keys") != [] or evidence.get("extra_keys") != []
            or evidence.get("changed_alias_links") != []
            or evidence.get("parse_failures") != 0 or evidence.get("brnp_findings") != 0
            or evidence.get("official_osis_schema_validated") is not True
            or evidence.get("native_link_topology_equal") is not True
            or evidence.get("opaque_top_bytes_equal") is not True
            or evidence.get("source_reversible") is not True
            or evidence.get("source_idempotent_normalization") is not True
            or evidence.get("remaining_source_text_and_markup_equal") is not True
            or evidence.get("all_native_entries_compared") is not True
            or evidence.get("reader_checks_passed") is not True):
        raise ValueError("Incremental native/source/reader proof differs")
    changes = revision.get("semantic_changed_keys")
    ref_changes = revision.get("reference_changed_keys")
    if (not isinstance(changes, list) or changes != sorted(set(changes))
            or not all(isinstance(key, str) and KEY.fullmatch(key) for key in changes)
            or not isinstance(ref_changes, list) or ref_changes != sorted(set(ref_changes))
            or not set(ref_changes).issubset(changes)):
        raise ValueError("Unbounded or invalid incremental source correction scope")
    if audit.get("incremental_revision") != revision:
        raise ValueError("Native audit does not bind the exact incremental review")
    return {"candidate_source_sha256": revision["candidate_source_sha256"],
            "incremental_evidence_sha256": evidence_sha}



def metadata_promotion_inputs(module_dir, root, metadata, review, proof, audit_sha):
    """Reuse the exact prior content review for a reversible display-only release.

    No new native/content attestations are fabricated. All previous review
    fields and data member hashes remain identical, and the old config hash
    is reconstructed from the current config by reversing the allowed edits.
    """
    promotion = review["metadata_promotion"]
    version = metadata["version"]
    previous_version = promotion["previous_version"]
    if not all(isinstance(v, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v)
               for v in (previous_version, version)) or tuple(map(int, previous_version.split("."))) >= tuple(map(int, version.split("."))):
        raise ValueError("Invalid metadata promotion version sequence")
    if not re.fullmatch(r"[a-z0-9-]+", module_dir.name) or not re.fullmatch(r"[a-z]{2,3}", metadata["language"]):
        raise ValueError("Unsafe metadata promotion identity")
    archive = root / "sources/cleaned/commentaries" / metadata["language"] / module_dir.name / "editorial/evidence" / ("release-" + previous_version)
    prior, prior_sha = _object(archive/"review-manifest.json", 1_000_000)
    prior_meta, meta_sha = _object(archive/"metadata.json", 256_000)
    prior_proof, proof_sha = _object(archive/"SOURCE_VALIDATION.json", 256_000)
    if (prior_sha != promotion["previous_review_sha256"]
            or meta_sha != promotion["previous_metadata_sha256"]
            or proof_sha != promotion["previous_proof_sha256"]
            or prior.get("metadata_promotion") is not None
            or prior.get("version") != previous_version
            or prior_meta.get("version") != previous_version
            or prior.get("source_audit_sha256") != audit_sha
            or prior.get("status") != "owner_authorized_for_release"
            or prior.get("schema_version") != 2):
        raise ValueError("Unverified prior content review")
    conf_key = "mods.d/" + metadata["sword_id"].lower() + ".conf"
    permitted = dict(prior, version=version, authorization=review["authorization"],
                     metadata_promotion=promotion,
                     payload_sha256=dict(prior["payload_sha256"]))
    permitted["payload_sha256"][conf_key] = review["payload_sha256"][conf_key]
    if permitted != review:
        raise ValueError("Promotion changed original content proof or binary member hashes")
    expected_meta = dict(prior_meta, version=version, title=dict(prior_meta["title"]))
    expected_meta["title"]["en"] = promotion["new_display_name"]
    if metadata != expected_meta:
        raise ValueError("Promotion changed unrelated catalogue metadata")
    if proof != dict(prior_proof, curated_version=version, metadata_promotion=promotion):
        raise ValueError("Promotion changed historical source validation")
    old_conf = archive/"module.conf"
    if old_conf.is_symlink() or not old_conf.is_file() or old_conf.stat().st_size > 256_000:
        raise ValueError("Missing prior native configuration")
    old_bytes = old_conf.read_bytes()
    if sha256(old_bytes).hexdigest() != prior["payload_sha256"][conf_key]:
        raise ValueError("Prior native configuration differs from reviewed hash")
    old_name = promotion["old_display_name"]
    new_name = promotion["new_display_name"]
    if old_name != prior_meta["title"]["en"] or not isinstance(new_name, str) or not new_name.strip() or any(c in new_name for c in "\r\n"):
        raise ValueError("Unreviewed display name")
    expected = old_bytes
    for before, after in (
        (("Version="+previous_version+"\n").encode(), ("Version="+version+"\n").encode()),
        (("Description="+old_name+"\n").encode(), ("Description="+new_name+"\n").encode()),
        ((" version "+previous_version+".").encode(), (" version "+version+".").encode()),
    ):
        if expected.count(before) != 1:
            raise ValueError("Ambiguous version/display config change")
        expected = expected.replace(before, after, 1)
    current = module_dir/"payload"/conf_key
    if current.is_symlink() or current.read_bytes() != expected or sha256(expected).hexdigest() != review["payload_sha256"][conf_key]:
        raise ValueError("Unexpected configuration changes during metadata promotion")
    return prior_meta, prior


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
        if (review.get("schema_version") not in (1, 2)
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
        incremental = review["schema_version"] == 2
        content_meta, content_review = (metadata, review)
        if "metadata_promotion" in review:
            content_meta, content_review = metadata_promotion_inputs(module_dir, root, metadata, review, proof, audit_sha)
        extra_proof = (_check_incremental_revision(module_dir, root, content_meta, content_review, audit)
                       if incremental else {})
        expected_proof = {
            "schema_version": review["schema_version"],
            **extra_proof,
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
        if incremental:
            expected_audit.update(schema_version=2, status="complete_native_semantic_rebuild_comparison")
            # v1 raw identity holds only for its named historical transport baseline.
            for field in ("all_other_original_K_bytes_identical", "all_original_I_bytes_identical"):
                expected_audit.pop(field)
                if field in audit:
                    raise ValueError("Incremental semantic proof must not claim historical raw-byte identity")
        if any(audit.get(field) != value for field, value in expected_audit.items()):
            raise ValueError("Native comparison lacks a required verified invariant")
        if (conf.get("ModDrv") != "zCom"
                or conf.get("SourceType") != "OSIS"
                or conf.get("Versification") != metadata["versification"]
                or conf.get("Version") != metadata["version"]
                or conf.get("BlockType") not in {"BOOK", "CHAPTER", "VERSE"}
                or conf.get("BlockType") != review.get("block_type")):
            raise ValueError("Compiled zCom format or metadata does not match review")
        paths = zcom_payload_paths(metadata["sword_id"], conf["BlockType"])
        expected_files = review.get("payload_sha256")
        if (not isinstance(expected_files, dict)
                or set(expected_files) != paths
                or not all(_digest(value) for value in expected_files.values())):
            raise ValueError("Incomplete exact compiled payload file inventory")
        actual = checked_zcom_payload_files(
            module_dir / "payload", metadata["sword_id"], conf["BlockType"])
        for relative in sorted(paths):
            if sha256(actual[relative].read_bytes()).hexdigest() != expected_files[relative]:
                raise ValueError("Compiled commentary payload checksum mismatch: " + relative)
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError) as exc:
        return [prefix + str(exc)]
    return []
