#!/usr/bin/env python3
"""Privately rebuild an authorized-to-test, never-to-publish SWORD source erratum.

The original and previously accepted index-only candidate are preserved. This
probe constructs a second, isolated compiler candidate using one separately
source-corroborated byte-reversible reference+label edit and the existing
reviewed *index-only* alias set. It checks every I/K/TOP original and linked
entry against the first compiled index-only candidate, then tests the newly
staged corrected ZIP with an independent actual Xiphos reader.

This is a generic verification transport, NOT an editorial authority, not a
source replacement, not an upstream import and not a release mechanism.
"""
from __future__ import annotations

from hashlib import sha256
from datetime import date, timedelta
from io import BytesIO
import json
from pathlib import Path
import os
import subprocess

from lxml import etree

from commentary_literal_erratum_preflight import (
    preview_exact_reversible_commentary_reference_erratum,
    preview_exact_reversible_commentary_prose_erratum,
)
from commentary_public_metadata_preflight import (
    prepare_provisional_public_commentary_conf, _exact_conf_value,
)
from commentary_reference_registry_triage import (
    SINGLE_VERSE, _unambiguous_verse_range_endpoints,
)
from commentary_osis_mixed_transport_probe import (
    probe_complete_original_transport, privately_stage_versioned_zcom_zip,
)
from commentary_osis_transport_probe import classify_native_osis_roundtrip_delta
from commentary_xiphos_dual_reader import (
    BIBLE_MODULE, _run_real_gui, verify_and_install_reviewed_bible,
)
from pilot_subprocess import present_key, query
from sword_native_raw_corpus_inventory import parse_native_raw_corpus
from commentary_rebuild_attestation_draft import private_rebuild_attestation_draft, _native_map_digest

MAX_SCAN = 512 * 1024 * 1024
MAX_ADJACENT = 12 * 1024 * 1024


def _read_private_native(root: Path, module_id: str, binary: Path, *, with_receipt: bool = False):
    if not root.is_dir() or root.is_symlink() or not binary.is_file():
        raise ValueError("Untrusted compiled original SWORD comparison roots")
    run = subprocess.run(
        [str(binary), module_id],
        env=dict(os.environ, SWORD_PATH=str(root)),
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=300, check=False
    )
    if run.returncode or len(run.stdout) > MAX_SCAN:
        raise ValueError("Independent compiled commentary readback unavailable")
    observed = {"K": {}, "I": {}, "U": []}
    def collect(kind, key, raw):
        if kind == "U":
            observed["U"].append(raw)
        else:
            observed[kind][key] = raw
    receipt, _, _, _ = parse_native_raw_corpus(BytesIO(run.stdout), on_entry=collect)
    receipt["native_identity_map_sha256"] = _native_map_digest(observed)
    return (observed, receipt) if with_receipt else observed


def _read_original_native_link_topology(root: Path, module_id: str, binary: Path):
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("Native linked-index binary missing")
    run = subprocess.run(
        [str(binary), module_id, "--adjacent-links"],
        env=dict(os.environ, SWORD_PATH=str(root)),
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=180, check=False,
    )
    if run.returncode or not 3 < len(run.stdout) <= MAX_ADJACENT:
        raise ValueError("Original linked topology unavailable")
    return run.stdout


def _original_citation_endpoints(raw: bytes, *, first: str,
                                 expected_end: str) -> int:
    """Count exact canonical endpoints, not substrings or ambiguous suffixes.

    A substring check can accidentally match e.g. Gen.1.3 in Gen.1.30;
    a suffix check alone can silently accept an unrelated first verse.
    This must compare the parsed *entire* reference to the two canonical
    identities, preserving source bytes and rejecting exotic link grammar.
    """
    if (not isinstance(first, str) or not isinstance(expected_end, str)
            or not SINGLE_VERSE.fullmatch(first)
            or not SINGLE_VERSE.fullmatch(expected_end)):
        raise ValueError("Expected canonical section endpoint identifiers")
    try:
        root = etree.fromstring(
            b"<entry>" + raw + b"</entry>",
            parser=etree.XMLParser(resolve_entities=False, no_network=True,
                                   load_dtd=False, recover=False,
                                   huge_tree=False, remove_blank_text=False)
        )
    except (etree.XMLSyntaxError, ValueError):
        raise ValueError("Source erratum candidate no longer strictly parseable") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError("Unresolved source entity in commentary reference")
    return sum(
        _unambiguous_verse_range_endpoints(el.get("osisRef", ""))
        == (first, expected_end)
        for el in root.iter()
        if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "reference"
    )


def _private_changed_reference_xiphos(
        install_root: Path, module_id: str,
        revised_native_K: dict[str, bytes], original_master_key: str,
        original_section_control_key: str, original_reviewed_alias_key: str,
        additional_sample_keys: tuple[str, ...] = ()) -> dict:
    """Read real corrected source and untouched controls in actual Xiphos GTK."""
    if any(key not in revised_native_K for key in
           (original_master_key, original_section_control_key, original_reviewed_alias_key)):
        raise ValueError("Missing native corrected/control Xiphos sample")
    bible = verify_and_install_reviewed_bible(install_root)
    if bible["module_id"] != BIBLE_MODULE:
        raise ValueError("Independent vetted Bible not available to real Xiphos")
    comparisons = {}
    required = tuple(dict.fromkeys((
        original_master_key, original_section_control_key,
        original_reviewed_alias_key, *additional_sample_keys
    )))
    if len(required) > 8:
        raise ValueError("Unbounded private source-change Xiphos examples")
    for key in required:
        book, chapter, verse = key.split(".")
        passage = f"{book} {chapter}:{verse}"
        result, commentary_plain = query(
            module_id, passage, fmt="plain", root=install_root,
            limit=256 * 1024, timeout=30,
        )
        bible_code, bible_plain = query(
            BIBLE_MODULE, passage, fmt="plain", root=install_root,
            limit=256 * 1024, timeout=30,
        )
        if (not present_key(passage, commentary_plain, result)
                or not present_key(passage, bible_plain, bible_code)
                or len(commentary_plain) < 64):
            raise ValueError("Real reader could not navigate corrected/control original verse")
        comparisons[passage] = {
            "commentary": commentary_plain,
            "bible": bible_plain,
            "commentary_internal": revised_native_K[key],
        }
    observed = _run_real_gui(
        install_root, comparisons, seconds=6, commentary_module_id=module_id)
    if (not observed["real_xiphos_executable_started_and_visible"]
            or not observed["actual_passage_commands_accepted"]
            or observed["independent_gui_commentary_excerpt_match_count"] != len(required)):
        raise ValueError("Xiphos could not show corrected reference and unchanged controls")
    return {
        "status": "PRIVATE_REVISED_ZCOM_REAL_XIPHOS_THREE_PASSAGES_VERIFIED",
        "corrected_reference_sample_key": original_master_key,
        "different_original_section_sample_key": original_section_control_key,
        "index_alias_sample_key": original_reviewed_alias_key,
        "independent_real_reader_sample_count": len(required),
        "independent_real_reader_clipboard_matches": len(required),
        "additional_prose_source_sample_keys": list(additional_sample_keys),
        "actual_xiphos_gui_displayed": True,
        "source_text_or_screenshot_logged": False,
        "published": False,
    }



def _apply_private_reviewed_prose_changes(
        originals: dict[str, list[tuple[str, bytes]]],
        already_edited: dict[str, list[tuple[str, bytes]]],
        plans: list[dict]) -> tuple[dict[str, list[tuple[str, bytes]]],
                                    dict[str, bytes], list[dict]]:
    """Apply only independently pinned, byte-reversible edits to source bodies.

    One authorial body can occupy several original native addresses. A
    generic correction follows that same raw body, never restructures it.
    No text/markup/attributes/rights are emitted in the receipt.
    """
    if not isinstance(plans, list) or len(plans) > 16:
        raise ValueError("Unbounded private source correction plans")
    original_lookup = {key: raw for rows in originals.values()
                       for key, raw in rows}
    modified = dict(already_edited)
    source_by_key: dict[str, bytes] = {}
    receipts: list[dict] = []
    seen_hashes = set()
    for plan in plans:
        if not isinstance(plan, dict):
            raise ValueError("Invalid private source correction plan")
        key = plan.get("original_native_entry")
        expected = plan.get("original_raw_sha256")
        expected_count = plan.get("expected_original_linked_native_K_count")
        if (not isinstance(key, str) or key not in original_lookup
                or not isinstance(expected, str) or len(expected) != 64
                or any(c not in "0123456789abcdef" for c in expected)
                or type(expected_count) is not int or not 1 <= expected_count <= 250):
            raise ValueError("Private source correction requires pinned original body and keys")
        original = original_lookup[key]
        digest = sha256(original).hexdigest()
        if digest != expected or digest in seen_hashes:
            raise ValueError("Stale or duplicated native original source correction")
        seen_hashes.add(digest)
        patched, proof = preview_exact_reversible_commentary_prose_erratum(
            original, original_phrase=plan.get("original_phrase"),
            corrected_phrase=plan.get("corrected_phrase"),
        )
        chapter = key.rsplit(".", 1)[0]
        matched: set[str] = set()
        for current_chapter, rows in modified.items():
            next_rows = []
            for existing_key, raw in rows:
                if sha256(raw).hexdigest() == digest:
                    if current_chapter != chapter:
                        raise ValueError("Prose source body unexpectedly reused across chapters")
                    if existing_key in source_by_key:
                        raise ValueError("Overlapping private source correction plans")
                    next_rows.append((existing_key, patched))
                    source_by_key[existing_key] = patched
                    matched.add(existing_key)
                else:
                    next_rows.append((existing_key, raw))
            modified[current_chapter] = next_rows
        if key not in matched or len(matched) != expected_count:
            raise ValueError("Unexpected linked native verse occupancy for prose correction")
        receipts.append({
            "original_native_entry": key,
            "affected_original_K_count": len(matched),
            "affected_original_K_keys": sorted(matched),
            **proof,
        })
    return modified, source_by_key, receipts

def probe_private_compiled_source_erratum(
        *, original_intros: dict[str, bytes],
        original_numbered: dict[str, list[tuple[str, bytes]]],
        original_TOP: list[bytes],
        original_master_key: str, first_verse: str,
        original_end_verse: str, proposed_end_verse: str,
        original_index_only_compiled_root: Path,
        reviewed_aliases: dict[str, dict],
        curated_module_id: str,
        curated_previous_version: str,
        curated_proposed_version: str,
        original_curated_conf: bytes,
        scratch: Path, native_raw_binary: Path,
        native_index_binary: Path,
        history_note: str, source_provider: str,
        test_with_real_xiphos: bool = True,
        additional_original_source_edits: list[dict] | None = None,
        original_source_manifest: str | None = None,
        original_native_corpus_sha256: str | None = None) -> dict:
    """Build and test a second wholly private corrected compiled SWORD ZIP."""
    if (not test_with_real_xiphos or not scratch.is_dir()
            or scratch.is_symlink() or not reviewed_aliases
            or original_master_key.rsplit(".", 1)[0] != first_verse.rsplit(".", 1)[0]
            or not isinstance(original_TOP, list)
            or any(not isinstance(x, bytes) for x in original_TOP)
            or not original_index_only_compiled_root.is_dir()
            or not original_curated_conf
            or not isinstance(source_provider, str) or not source_provider.strip()):
        raise ValueError("Missing source-verified candidate/review baseline")
    chapter = original_master_key.rsplit(".", 1)[0]
    native_original_chapter = original_numbered.get(chapter, [])
    original_body = next((raw for key, raw in native_original_chapter
                          if key == original_master_key), None)
    if original_body is None:
        raise ValueError("Original source-correction master missing")
    patched, byte_receipt = preview_exact_reversible_commentary_reference_erratum(
        original_body, first_verse=first_verse,
        original_end_verse=original_end_verse,
        proposed_end_verse=proposed_end_verse
    )
    original_digest = sha256(original_body).digest()
    revised = {}
    modified_original_keys = set()
    for original_chapter, rows in original_numbered.items():
        current = []
        for key, raw in rows:
            if sha256(raw).digest() == original_digest:
                if original_chapter != chapter:
                    raise ValueError("Source erratum body reused in a different original chapter")
                current.append((key, patched))
                modified_original_keys.add(key)
            else:
                current.append((key, raw))
        revised[original_chapter] = current
    if (original_master_key not in modified_original_keys
            or not 1 <= len(modified_original_keys) <= 250):
        raise ValueError("Original source group cardinality unreviewed")
    reference_changed_original_keys = set(modified_original_keys)
    edited_raw_for_original_key = {
        key: patched for key in reference_changed_original_keys
    }
    revised, prose_edited_by_key, prose_receipts = _apply_private_reviewed_prose_changes(
        original_numbered, revised, additional_original_source_edits or []
    )
    if set(prose_edited_by_key) & modified_original_keys:
        raise ValueError("A source citation and prose correction overlap one original body")
    modified_original_keys.update(prose_edited_by_key)
    edited_raw_for_original_key.update(prose_edited_by_key)
    revised_private_scratch = scratch / "corrected-standard-compiler"
    revised_private_scratch.mkdir()
    full = probe_complete_original_transport(
        original_intros, revised, original_TOP,
        scratch=revised_private_scratch, native_raw_binary=native_raw_binary,
        provisional_index_aliases=reviewed_aliases,
        test_preview_in_xiphos=False,
        native_index_binary=native_index_binary
    )
    if (not full.get("full_original_K_I_U_native_entry_parity_proven")
            or full["extra_K_count"] != len(reviewed_aliases)
            or full["planned_extra_index_keys"] != len(reviewed_aliases)
            or full["original_indexed_I_K_text_markup_reference_checks_passed"] is not True
            or full["all_original_TOP_positions_exact_raw_bytes"] is not True
            or full["all_proposed_new_aliases_same_compiled_raw_as_original_master"] is not True):
        raise ValueError("Original commentary corrected private OSIS does not preserve edited-source parity")
    linked = full.get("private_native_original_and_provisional_alias_link_identity")
    if (not isinstance(linked, dict)
            or linked.get("status") != "REAL_LIBSWORD_NATIVE_NONADJACENT_LINK_IDENTITY"
            or linked.get("proposed_key_count") != len(reviewed_aliases)
            or linked.get("native_linked_alias_count") != len(reviewed_aliases)
            or linked.get("all_original_master_to_proposed_target_pairs_are_native_linked") is not True
            or linked.get("all_independently_distinct_section_controls_unlinked") is not True
            or linked.get("non_linked_proposed_pairs") != []):
        raise ValueError("Actual libSWORD reviewed native alias identities were not proven")
    corrected_root = revised_private_scratch / "complete-original-private-candidate"
    original_compiled, original_index_receipt = _read_private_native(
        original_index_only_compiled_root, "BRIndexProbe", native_raw_binary,
        with_receipt=True,
    )
    revised_compiled, revised_receipt = _read_private_native(
        corrected_root, "BRIndexProbe", native_raw_binary,
        with_receipt=True,
    )
    if (original_compiled["I"] != revised_compiled["I"]
            or original_compiled["U"] != revised_compiled["U"]
            or set(original_compiled["K"]) != set(revised_compiled["K"])):
        raise ValueError("Source edit altered original introductions TOP or K address set")
    original_native_differences = {
        key for key in original_compiled["K"]
        if original_compiled["K"][key] != revised_compiled["K"][key]
    }
    if original_native_differences != modified_original_keys:
        raise ValueError("Private source-edit changed K keys outside one original linked section")
    for key in modified_original_keys:
        delta = classify_native_osis_roundtrip_delta(
            edited_raw_for_original_key[key], revised_compiled["K"][key]
        )
        if (delta["word_sequence_relation"] != "EXACT_ORIGINAL_WORD_SEQUENCE"
                or delta["normalized_whitespace_visible_unicode_equal"] is not True
                or delta["non_div_element_order_and_exact_attribute_values_preserved"] is not True
                or delta["original_nondiv_text_and_tail_ownership_preserved"] is not True
                or delta["reference_attribute_values_in_original_document_order_preserved"] is not True):
            raise ValueError("Corrected original linked entry lost modified-source XML/text")
    if _original_citation_endpoints(revised_compiled["K"][original_master_key],
                                    first=first_verse, expected_end=proposed_end_verse) != 1:
        raise ValueError("Corrected original native link target not visible in compiled SWORD")
    adjacency_a = _read_original_native_link_topology(
        original_index_only_compiled_root, "BRIndexProbe", native_index_binary)
    adjacency_b = _read_original_native_link_topology(
        corrected_root, "BRIndexProbe", native_index_binary)
    if adjacency_a != adjacency_b:
        raise ValueError("Source-only erratum unexpectedly changed any native SWORD linked boundary")
    staged_scratch = scratch / "corrected-versioned-private-zip"
    staged_scratch.mkdir()
    staged = privately_stage_versioned_zcom_zip(
        compiler_root=corrected_root,
        compiled_module_id="BRIndexProbe",
        package_module_id=curated_module_id,
        previous_version=curated_previous_version,
        proposed_version=curated_proposed_version,
        published_conf_template=original_curated_conf,
        scratch=staged_scratch,
        native_raw_binary=native_raw_binary,
        provisional_index_aliases=reviewed_aliases,
        test_with_real_xiphos=False,
        history_note=history_note,
        source_reference_change_verified=True,
    )
    if (staged["source_annotations_and_words_modified"] is not True
            or staged["private_conf_metadata_exact_delta_receipt"][
                "private_source_reference_change_verified"] is not True
            or staged["installed_package_I_K_U_raw_bytes_equal_to_private_compiled_source"] is not True
            or staged["package_saved_as_public_artifact"] is not False
            or staged["published"] is not False):
        raise ValueError("Revised private candidate source and versioned metadata unverifiable")
    install_root = (staged_scratch / "curated-package-stage"
                    / "isolated-package-install")
    actual_install, actual_install_receipt = _read_private_native(
        install_root, curated_module_id, native_raw_binary,
        with_receipt=True,
    )
    if actual_install != revised_compiled:
        raise ValueError("New curated SWORD ZIP lost complete corrected native source parity")
    # A generic *public-metadata proposal* must also work against the
    # real privately compiled ZIP, not merely synthetic .conf test fixtures.
    # Use the day immediately after the actual original source date solely
    # as a reproducible dummy input; NEVER treat it as a release calendar day.
    installed_conf = (
        install_root / "mods.d" / (curated_module_id.lower() + ".conf")
    ).read_bytes()
    source_date = _exact_conf_value(
        installed_conf.decode("utf-8"), "SwordVersionDate")
    dummy_day = (date.fromisoformat(source_date) + timedelta(days=1)).isoformat()
    _, metadata_proposal = prepare_provisional_public_commentary_conf(
        installed_conf,
        expected_module_id=curated_module_id,
        expected_module_version=curated_proposed_version,
        source_provider=source_provider,
        original_sword_version_date=source_date,
        proposed_public_revision_day=dummy_day,
        revision_summary=history_note,
    )
    if (metadata_proposal["publication_authorized"] is not False
            or metadata_proposal["public_asset_generated"] is not False
            or metadata_proposal["exact_changed_fields"]
               != ["About", "SwordVersionDate"]
            or metadata_proposal["all_other_fields_comments_license_textsource_and_history_exact"]
               is not True):
        raise ValueError("Actual private ZIP .conf cannot yield a safe metadata draft")
    # Select a neutral original distinct section and an actually proposed
    # navigation alias as controls. This is not a test hardcoded to Ezekiel.
    review_control_key = first_verse
    alias_key = sorted(reviewed_aliases)[0]
    xiphos = _private_changed_reference_xiphos(
        install_root, curated_module_id, revised_compiled["K"],
        original_master_key, review_control_key, alias_key,
        additional_sample_keys=tuple(
            receipt["original_native_entry"] for receipt in prose_receipts
        )
    )
    if (original_source_manifest is None or original_native_corpus_sha256 is None):
        raise ValueError("Private source attestation needs the independently pinned original")
    attestation = private_rebuild_attestation_draft(
        repo_root=Path(__file__).resolve().parents[1],
        original_manifest=original_source_manifest,
        module_id=curated_module_id, version=curated_proposed_version,
        versification=_exact_conf_value(installed_conf.decode("utf-8"), "Versification"),
        compiled_block_type=_exact_conf_value(installed_conf.decode("utf-8"), "BlockType"),
        original_native_corpus_sha256=original_native_corpus_sha256,
        original_source_numbered=original_numbered,
        original_source_intros=original_intros, original_source_top=original_TOP,
        original_index_compiled=original_compiled,
        revised_compiled=revised_compiled,
        installed_compiled=actual_install,
        index_receipt=original_index_receipt, revised_receipt=revised_receipt,
        installed_receipt=actual_install_receipt,
        source_edit_receipts=[
            {"original_native_entry": original_master_key, **byte_receipt},
            *prose_receipts,
        ],
        source_edit_affected_keys=[
            sorted(reference_changed_original_keys),
            *[r["affected_original_K_keys"] for r in prose_receipts],
        ],
        corrected_source_by_original_key=edited_raw_for_original_key,
        aliases=reviewed_aliases, installed_candidate_root=install_root,
        existing_links_preserved=adjacency_a == adjacency_b,
        full_source_semantic_and_structure_parity_verified=(
            full["original_indexed_I_K_text_markup_reference_checks_passed"] is True
        ),
        all_new_native_aliases_linked=(
            linked["all_original_master_to_proposed_target_pairs_are_native_linked"] is True
            and linked["native_linked_alias_count"] == len(reviewed_aliases)
            and linked["all_independently_distinct_section_controls_unlinked"] is True
        ),
        real_reader_passage_matches=xiphos["independent_real_reader_clipboard_matches"],
    )
    if (attestation["release_authorized"] or attestation["data_text_exported"]
            or attestation["original_K_keys_edited"] != len(modified_original_keys)
            or attestation["real_reader_sample_count"] != len(
                xiphos["additional_prose_source_sample_keys"]
            ) + 3):
        raise ValueError("Private source attestation claims an unreviewed release or native edit")
    return {
        "status": "PRIVATE_SOURCE_EDITED_SWORD_ZCOM_CANDIDATE_FULL_PARITY_NOT_PUBLICATION",
        "original_source_chapter_key": original_master_key,
        "source_linked_original_verse_keys_changed": len(reference_changed_original_keys),
        "additional_prose_original_verse_keys_changed": len(prose_edited_by_key),
        "all_source_linked_original_verse_keys_changed": len(modified_original_keys),
        "additional_prose_original_source_change_receipts": prose_receipts,
        "only_original_linked_source_group_changed": len(prose_receipts) == 0,
        "only_exactly_reviewed_original_source_groups_changed": True,
        "exact_original_K_keys_changed": sorted(modified_original_keys),
        "all_other_original_and_alias_K_bytes_identical_to_index_only_compilation": True,
        "all_original_I_and_TOP_bytes_identical_to_index_only_compilation": True,
        "all_original_compiled_native_adjacent_links_identical": True,
        "complete_corrected_source_semantic_and_xml_parity_passed": True,
        "corrected_reference_native_target_present_once": True,
        "original_raw_source_checksum": byte_receipt["original_raw_sha256"],
        "edited_raw_source_checksum": byte_receipt["proposed_raw_sha256"],
        "reverse_restores_exact_original_raw": byte_receipt[
            "reverse_restores_exact_original_raw_bytes"],
        "original_numbered_key_count": len(original_compiled["K"]) - len(reviewed_aliases),
        "revised_numbered_key_count": len(revised_compiled["K"]),
        "original_intro_key_count": len(revised_compiled["I"]),
        "original_TOP_slot_count": len(revised_compiled["U"]),
        "package_zip_sha256": staged["staged_package_zip_sha256"],
        "package_isolated_install_exact_compiled_parity": True,
        "corrected_metadata_guard": staged["private_conf_metadata_exact_delta_receipt"],
        "private_real_native_rebuild_attestation_draft": attestation,
        "private_package_real_conf_public_metadata_dry_run": {
            **metadata_proposal,
            "test_date_only_no_actual_release_day_selected": True,
        },
        "real_xiphos_three_passage_proof": xiphos,
        "original_and_public_module_unchanged": True,
        "corrected_package_uploaded_or_distributed": False,
        "source_words_or_xml_logged": False,
        "owner_publication_authorized": False,
    }
