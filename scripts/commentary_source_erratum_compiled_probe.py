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
from io import BytesIO
from pathlib import Path
import os
import subprocess

from lxml import etree

from commentary_literal_erratum_preflight import (
    preview_exact_reversible_commentary_reference_erratum,
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

MAX_SCAN = 512 * 1024 * 1024
MAX_ADJACENT = 12 * 1024 * 1024


def _read_private_native(root: Path, module_id: str, binary: Path):
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
    parse_native_raw_corpus(BytesIO(run.stdout), on_entry=collect)
    return observed


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
        original_section_control_key: str, original_reviewed_alias_key: str) -> dict:
    """Read real corrected source and untouched controls in actual Xiphos GTK."""
    if any(key not in revised_native_K for key in
           (original_master_key, original_section_control_key, original_reviewed_alias_key)):
        raise ValueError("Missing native corrected/control Xiphos sample")
    bible = verify_and_install_reviewed_bible(install_root)
    if bible["module_id"] != BIBLE_MODULE:
        raise ValueError("Independent vetted Bible not available to real Xiphos")
    comparisons = {}
    for key in (original_master_key, original_section_control_key, original_reviewed_alias_key):
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
            or observed["independent_gui_commentary_excerpt_match_count"] != 3):
        raise ValueError("Xiphos could not show corrected reference and unchanged controls")
    return {
        "status": "PRIVATE_REVISED_ZCOM_REAL_XIPHOS_THREE_PASSAGES_VERIFIED",
        "corrected_reference_sample_key": original_master_key,
        "different_original_section_sample_key": original_section_control_key,
        "index_alias_sample_key": original_reviewed_alias_key,
        "independent_real_reader_sample_count": 3,
        "independent_real_reader_clipboard_matches": 3,
        "actual_xiphos_gui_displayed": True,
        "source_text_or_screenshot_logged": False,
        "published": False,
    }


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
        history_note: str,
        test_with_real_xiphos: bool = True) -> dict:
    """Build and test a second wholly private corrected compiled SWORD ZIP."""
    if (not test_with_real_xiphos or not scratch.is_dir()
            or scratch.is_symlink() or not reviewed_aliases
            or original_master_key.rsplit(".", 1)[0] != first_verse.rsplit(".", 1)[0]
            or not isinstance(original_TOP, list)
            or any(not isinstance(x, bytes) for x in original_TOP)
            or not original_index_only_compiled_root.is_dir()
            or not original_curated_conf):
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
    corrected_root = revised_private_scratch / "complete-original-private-candidate"
    original_compiled = _read_private_native(
        original_index_only_compiled_root, "BRIndexProbe", native_raw_binary
    )
    revised_compiled = _read_private_native(
        corrected_root, "BRIndexProbe", native_raw_binary
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
        delta = classify_native_osis_roundtrip_delta(patched, revised_compiled["K"][key])
        if (delta["word_sequence_relation"] != "EXACT_ORIGINAL_WORD_SEQUENCE"
                or delta["normalized_whitespace_visible_unicode_equal"] is not True
                or delta["non_div_element_order_and_exact_attribute_values_preserved"] is not True
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
    actual_install = _read_private_native(
        install_root, curated_module_id, native_raw_binary
    )
    if actual_install != revised_compiled:
        raise ValueError("New curated SWORD ZIP lost complete corrected native source parity")
    # Select a neutral original distinct section and an actually proposed
    # navigation alias as controls. This is not a test hardcoded to Ezekiel.
    review_control_key = first_verse
    alias_key = sorted(reviewed_aliases)[0]
    xiphos = _private_changed_reference_xiphos(
        install_root, curated_module_id, revised_compiled["K"],
        original_master_key, review_control_key, alias_key
    )
    return {
        "status": "PRIVATE_SOURCE_EDITED_SWORD_ZCOM_CANDIDATE_FULL_PARITY_NOT_PUBLICATION",
        "original_source_chapter_key": original_master_key,
        "source_linked_original_verse_keys_changed": len(modified_original_keys),
        "only_original_linked_source_group_changed": True,
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
        "real_xiphos_three_passage_proof": xiphos,
        "original_and_public_module_unchanged": True,
        "corrected_package_uploaded_or_distributed": False,
        "source_words_or_xml_logged": False,
        "owner_publication_authorized": False,
    }
