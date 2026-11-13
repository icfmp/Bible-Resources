#!/usr/bin/env python3
"""Read a byte-identical, privately repackaged MHCC inside real Xiphos.

The stock CrossWire module and a candidate containing exactly the same
compressed bytes (with only private SWORD ID/DataPath metadata relabelled)
are independently compared across ALL native occupied keys *before* this
reader is invoked. Our published, SHA-256-attested BRLSG1910 Bible is
installed alongside the PRIVATE candidate. Original material stays solely
inside a disposable runner and the only durable record is metadata.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from commentary_stock_candidate import make_private_candidate
from commentary_xiphos_dual_reader import (
    _original_stock_reference_bearing_samples,
    _run_real_gui,
    prepare_original_and_candidate_gui_samples,
    verify_and_install_reviewed_bible,
)
from commentary_xiphos_heading_probe import (
    pinned_source_intro_witness,
    probe_real_xiphos_commentary_heading_menu,
)
from pilot_preflight import PilotError

PRIVATE_ID = "BRMHCCReview"
SHA = re.compile(r"[a-f0-9]{64}\Z")


def _gate_real_candidate_gui(receipt: dict) -> None:
    """Do not confuse executable startup with full selected GUI acceptance."""
    if receipt.get("selected_private_commentary_module_id") != PRIVATE_ID:
        raise PilotError("Xiphos did not select the expected private module")
    bible = receipt.get("installed_reviewed_bible", {})
    if (bible.get("module_id") != "BRLSG1910"
            or bible.get("all_five_published_bible_files_sha256_attested") is not True):
        raise PilotError("Private Xiphos reader has no attested published Bible")
    if receipt.get("original_source_corpus_hash_reconfirmed") is not True:
        raise PilotError("Private reader original source digest was not confirmed")
    refs = receipt.get("actual_substantive_sample_references", [])
    baseline = receipt.get("actual_baseline_commentary_samples", [])
    linked = receipt.get("actual_source_link_samples", [])
    if (baseline != ["Gen 1:1", "Ps 23:1", "Matt 5:1"]
            or len(linked) != 2 or len(refs) != 5
            or len(set(refs)) != 5 or set(refs) != set(baseline + linked)):
        raise PilotError("Not five independent original stock samples")
    matched = receipt.get("commentary_clipboard_match_by_passage", {})
    markup = receipt.get("real_markup_rendering_observation_by_passage", {})
    if (set(matched) != set(refs) or any(v is not True for v in matched.values())
            or receipt.get("independent_gui_commentary_excerpt_match_count") != 5
            or receipt.get("actual_passage_commands_accepted") is not True
            or receipt.get("real_main_reader_window_found") is not True
            or set(markup) != set(refs)):
        raise PilotError("Private Xiphos commentary GUI prose did not match 5 original entries")
    for ref in linked:
        data = markup[ref]
        if (data.get("original_internal_reference_elements_found", 0) < 1
                or data.get("source_reference_labels_observed_as_real_gui_HTML_anchors", 0) < 1
                or data.get("exact_native_source_osisref_encoded_in_real_gui_HTML_link_destinations", 0) < 1):
            raise PilotError("Private Xiphos GUI did not preserve original link label/OSIS target")
    if (receipt.get("xiphos_reference_mouse_click_navigation_verified") is not False
            or receipt.get("all_authorial_source_edition_differences_resolved") is not False
            or receipt.get("published") is not False):
        raise PilotError("Private candidate reader exceeded its approval scope")


def private_candidate_xiphos_review(
    resource_id: str, *, native_full_corpus_binary: Path,
    native_single_key_binary: Path, seconds: int = 12,
) -> dict:
    if (resource_id != "mhcc-crosswire" or not 6 <= seconds <= 25
            or native_full_corpus_binary.is_symlink()
            or not native_full_corpus_binary.is_file()
            or native_single_key_binary.is_symlink()
            or not native_single_key_binary.is_file()):
        raise PilotError("Unreviewed original commentary/candidate reader inputs")

    def verify_candidate(original_root: Path, candidate_root: Path, manifest: dict) -> dict:
        # The callback runs ONLY after both complete 29,975-entry inventories,
        # compressed member bytes and stock->candidate diatheke were proven.
        bible = verify_and_install_reviewed_bible(candidate_root)
        cases = _original_stock_reference_bearing_samples(
            original_root, manifest["module_id"], native_full_corpus_binary,
            expected_corpus_sha256=manifest["native_raw_corpus_sha256"],
        )
        comparisons, baseline, links, sparse = prepare_original_and_candidate_gui_samples(
            manifest,
            original_root=original_root,
            reader_root=candidate_root,
            selected_module_id=PRIVATE_ID,
            source_reference_cases=cases,
            native_raw_key_binary=native_single_key_binary,
        )
        authentic_intros = pinned_source_intro_witness(
            original_root, manifest["module_id"], native_full_corpus_binary,
            expected_raw_corpus_sha256=manifest["native_raw_corpus_sha256"],
        )
        real_gui = _run_real_gui(
            candidate_root, comparisons, seconds=seconds,
            commentary_module_id=PRIVATE_ID,
            on_gui_ready=lambda env: {
                "real_Xiphos_commentary_book_chapter_heading_context_menu":
                probe_real_xiphos_commentary_heading_menu(
                    env, authentic_intros,
                    ordinary_first_verse=comparisons["Gen 1:1"]["commentary"],
                ),
            },
        )
        result = {
            "status": "byte_exact_private_candidate_real_Xiphos_GUI_observation",
            "selected_private_commentary_module_id": PRIVATE_ID,
            "installed_reviewed_bible": bible,
            "original_source_corpus_hash_reconfirmed": cases[
                "full_pinned_raw_corpus_sha256_reconfirmed"
            ],
            "authentic_original_reference_bearing_keys_count": cases[
                "original_occupied_numbered_keys_with_reference_markup"
            ],
            "actual_baseline_commentary_samples": baseline,
            "actual_source_link_samples": links,
            "actual_substantive_sample_references": list(comparisons),
            "original_stock_sparse_slots_preserved": sparse,
            **real_gui,
            "xiphos_reference_mouse_click_navigation_verified": False,
            "all_authorial_source_edition_differences_resolved": False,
            "published": False,
            "original_words_links_screenshots_or_SWORD_archives_uploaded": False,
        }
        _gate_real_candidate_gui(result)
        return result

    result = make_private_candidate(
        resource_id,
        native_raw_binary=native_full_corpus_binary,
        reader="diatheke",
        candidate_id=PRIVATE_ID,
        on_verified_private_candidate=verify_candidate,
    )
    receipt = result.get("independent_private_candidate_gui_receipt")
    if not isinstance(receipt, dict):
        raise PilotError("Actual candidate GUI evidence not produced")
    _gate_real_candidate_gui(receipt)
    if (result["private_candidate_module_id"] != PRIVATE_ID
            or result["total_native_keys"] != 29975
            or result["complete_stock_and_candidate_native_raw_corpus_sha256_equal"] is not True
            or result["all_original_SWORD_compressed_files_byte_preserved"] is not True
            or result["private_candidate_archive_destroyed_without_upload"] is not True
            or result["published"] is not False
            or result["editorial_acceptance"] is not False):
        raise PilotError("Original MHCC/private candidate inventory was not proven unchanged")
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--native-full-corpus-binary", required=True, type=Path)
    p.add_argument("--native-single-key-binary", required=True, type=Path)
    p.add_argument("--seconds", type=int, default=12)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args(argv)
    if (args.report.is_symlink() or args.report.exists()
            or not args.report.parent.is_dir()):
        raise PilotError("Refusing preexisting or unsafe private Xiphos metadata destination")
    record = private_candidate_xiphos_review(
        args.resource_id,
        native_full_corpus_binary=args.native_full_corpus_binary,
        native_single_key_binary=args.native_single_key_binary,
        seconds=args.seconds,
    )
    args.report.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Real isolated Xiphos: exact private candidate + attested Bible, five original commentary entries and two source link hrefs verified; never published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
