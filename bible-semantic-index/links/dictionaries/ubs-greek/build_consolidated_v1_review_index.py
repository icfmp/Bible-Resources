#!/usr/bin/env python3
"""Consolidate all pinned-source UBS Greek v1 lexical and semantic candidates.

PRIVATE review index only. This does not publish dictionary text, certify a
contextual meaning or alter the frozen historical by_strong/by_ln index.

Contract:
* Every original SBLGNT word ID is present exactly once.
* The source-supported UBS lexical headword is returned even when no LEXID
  can be selected. All original sense candidates are retained.
* The five distinct provisional semantic evidence tiers are reported
  separately, and are NEVER mistaken for contextually verified meanings.
* A multi-headword or missing-entry word remains explicitly unresolved.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

TOTAL = 137741
TIERS = (
    ("ln_unique", "word_id_to_provisional_ubs_lexid", 122504,
     "ubs_original_main_id", "ubs_original_lexid"),
    ("single_sense_without_ln", "word_id_to_lower_confidence_provisional_ubs_lexid", 170,
     "original_ubs_main_id", "original_ubs_unique_lexid"),
    ("explicit_ubs_form", "new_word_id_to_source_form_supported_provisional_lexid", 223,
     "ubs_main_id", "editorial_provisional_ubs_lexid"),
    ("ubs_verse_citation", "word_id_to_new_UBS_source_verse_provisional_lexid", 258,
     "ubs_original_main_id", "source_reference_supported_provisional_ubs_lexid"),
    ("calibrated_ubs_word_locator", "word_id_to_source_position_provisional_lexid", 40,
     "ubs_original_main_id", "source_position_provisional_ubs_lexid"),
)
ORIGINAL = ("original_word_id", "original_reference", "original_lemma",
            "original_strong", "original_ln", "original_class", "original_morph")


def build(index, reviewed, high, unresolved, low, forms, verses, positions):
    layers = (high, low, forms, verses, positions)
    editions = high.get("source_editions")
    if not isinstance(editions, dict) or not editions:
        raise ValueError("Pinned original editions unavailable")
    if any(layer.get("source_editions") != editions or layer.get("published") is not False
           for layer in (reviewed, *layers, unresolved) if layer is not reviewed):
        raise ValueError("Source revisions or private candidate status drift")
    if (reviewed.get("editorial_candidate", {}).get("publication_approved") is not False
        or reviewed.get("word_aware_coverage", {}).get("word_aware_entry_candidate_words") != 137694
        or len(reviewed.get("by_macula_word", {})) != 9604
        or len(reviewed.get("by_macula_ambiguous_word", {})) != 220):
        raise ValueError("Source-reviewed UBS lexical headword coverage drift")
    if (index.get("coverage", {}).get("macula_words") != TOTAL
        or unresolved.get("status") != "PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review"
        or unresolved.get("unresolved_original_word_count") != 15237
        or unresolved.get("published") is not False):
        raise ValueError("Original source audit baseline drift")
    for field, old in index.items():
        if reviewed.get(field) != old:
            raise ValueError("Frozen original UBS index is not preserved")
    unsolved = unresolved["word_id_to_unresolved_original_source_evidence"]
    if len(unsolved) != 15237:
        raise ValueError("Incomplete unresolved original-word inventory")

    assigned = {}
    for (tier, key, expected, entry_key, sense_key), layer in zip(TIERS, layers):
        mapping = layer[key]
        if len(mapping) != expected:
            raise ValueError(f"Original word-ID count drift in {tier}")
        if layer.get("publication_approved") is not False and tier != "ln_unique":
            raise ValueError("An unreleased source candidate is flagged as published")
        for wid, witness in mapping.items():
            if wid in assigned or witness["original_word_id"] != wid:
                raise ValueError("Duplicate or inconsistent original word ID: " + wid)
            if not isinstance(witness[entry_key], str) or not isinstance(witness[sense_key], str):
                raise ValueError("Missing source-backed lexical IDs")
            if not witness[entry_key] or not witness[sense_key]:
                raise ValueError("Blank source-backed lexical IDs")
            assigned[wid] = (tier, witness[entry_key], witness[sense_key], witness)
    if len(assigned) != 123195:
        raise ValueError("Five provisional evidence tiers do not partition correctly")
    if len(assigned) + len(set(unsolved) - set(assigned)) != TOTAL:
        raise ValueError("Original source word IDs are not exhaustively represented")
    if set(high["word_id_to_provisional_ubs_lexid"]) & set(unsolved):
        raise ValueError("Original LN-unique words overlap unresolved source register")
    if set(high["word_id_to_provisional_ubs_lexid"]) | set(unsolved) != set(assigned) | set(unsolved):
        raise ValueError("Incorrect original-word lexical ledger union")
    if len(set(high["word_id_to_provisional_ubs_lexid"]) | set(unsolved)) != TOTAL:
        raise ValueError("Full pinned MACULA word-ID census drift")

    by_word = {}
    results = Counter()
    for wid, source in unsolved.items():
        if source["original_word_id"] != wid:
            raise ValueError("Unresolved source word ID mismatch")
        heads = source["source_original_ubs_main_id_candidates"]
        original_pairs = source["source_ubs_lexid_candidate_pairs"]
        sense_candidates = sorted({p["original_ubs_lexid"] for p in original_pairs})
        if len(heads) != len(set(heads)):
            raise ValueError("Duplicate original UBS headword candidate")
        if any(p["original_ubs_main_id"] not in heads for p in original_pairs):
            raise ValueError("Original UBS source LEXID belongs to unrelated entry")
        if not heads:
            status = "missing_ubs_headword"
        elif len(heads) > 1:
            status = "ambiguous_ubs_headwords"
        elif len(sense_candidates) > 1:
            status = "ambiguous_ubs_senses"
        else:
            status = "ubs_entry_only"
        chosen = assigned.get(wid)
        if chosen:
            tier, mid, sid, witness = chosen
            if tier == "ln_unique":
                raise ValueError("LN-unique word incorrectly present in unresolved register")
            if heads != [mid] or sid not in sense_candidates and tier != "single_sense_without_ln":
                # LN-missing single authentic UBS LEXID is confirmed separately
                # in its own source-backed builder, not the original-LN pairs.
                raise ValueError("Chosen sense absent from original source candidates")
            if tier == "single_sense_without_ln" and source["editorial_status"] != "no_original_ln_matching_ubs_lexical_sense":
                raise ValueError("Lower confidence single-sense source category drift")
            if any(source[field] != witness[field] for field in ORIGINAL):
                raise ValueError("Original UBS/MACULA word witness changed")
            status = "provisional_ubs_lexid"
        row = {
            "original_reference": source["original_reference"],
            "original_lemma": source["original_lemma"],
            "original_strong": source["original_strong"],
            "original_ln": source["original_ln"],
            "ubs_main_ids": heads,
            "ubs_lexid_candidates_from_original_ln": sense_candidates,
            "status": status,
            "provisional_ubs_lexid": chosen[2] if chosen else None,
            "evidence_tier": chosen[0] if chosen else None,
            "source_disposition": source["editorial_status"],
        }
        by_word[wid] = row
        results[status] += 1
    for wid, witness in high["word_id_to_provisional_ubs_lexid"].items():
        if wid in by_word:
            raise ValueError("Original LN-backed and unresolved source word overlap")
        chosen = assigned[wid]
        row = {
            "original_reference": witness["original_reference"],
            "original_lemma": witness["original_lemma"],
            "original_strong": witness["original_strong"],
            "original_ln": witness["original_ln"],
            "ubs_main_ids": [chosen[1]],
            "ubs_lexid_candidates_from_original_ln": [chosen[2]],
            "status": "provisional_ubs_lexid",
            "provisional_ubs_lexid": chosen[2],
            "evidence_tier": "ln_unique",
            "source_disposition": "unique_source_attested_ubs_lexid_NOT_contextually_verified",
        }
        by_word[wid] = row
        results["provisional_ubs_lexid"] += 1

    if len(by_word) != TOTAL or results["provisional_ubs_lexid"] != 123195:
        raise ValueError("Consolidated original Greek word-ID/semantic counts drift")
    if (results["ambiguous_ubs_headwords"] != 4
        or results["missing_ubs_headword"] != 47
        or results["ambiguous_ubs_senses"] != 2207
        or results["ubs_entry_only"] != 12288):
        raise ValueError("Original Greek unresolved source dispositions changed: " + repr(results))
    return {
        "schema_version": 1,
        "status": "PRIVATE_REPRODUCIBLE_UBS_Greek_NT_v1_original_word_candidate_INDEX_NOT_PUBLISHED",
        "source_editions": editions,
        "source_licensing": {
            "ubs_greek_dictionary": "CC BY-SA 4.0; United Bible Societies; original pinned Greek dictionary README; dictionary copyright UBS 2023",
            "macula_sblgnt": "CC BY 4.0 dataset; MACULA Greek Linguistic Datasets © 2022–2024 Biblica, Inc.; hosted by Clear-Bible; upstream contains separately originated third-party data",
            "macula_embedded_ubs_annotation_notice": "UBS MARBLE @ln/@domain annotations described by pinned MACULA LICENSE.md as Used with permission; field-level redistribution clearance required",
            "release_rights_status": "NOT_APPROVED; see RELEASE_READINESS.md and issue #431",
            "contains_dictionary_definitions": False,
            "contains_original_biblical_verses": False,
        },
        "original_word_ids": TOTAL,
        "reviewed_source_lexical_headword_words": 137694,
        "missing_supported_lexical_headword_words": 47,
        "provisional_semantic_word_ids": 123195,
        "not_assigned_a_provisional_sense": 14546,
        "provisional_evidence_tiers": {tier: count for tier, _, count, _, _ in TIERS},
        "word_status_counts": dict(sorted(results.items())),
        "semantic_context_independently_verified": 0,
        "publication_approved": False,
        "original_index_and_sources_modified": False,
        "by_original_macula_word_id": dict(sorted(by_word.items())),
    }


def lookup(consolidated, wid):
    row = consolidated["by_original_macula_word_id"].get(wid)
    if row is None:
        return {"status": "unknown_original_word_id", "original_word_id": wid}
    return {"original_word_id": wid, **row}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("index", "reviewed", "high", "unresolved", "low",
                "forms", "verses", "positions", "output"):
        p.add_argument("--" + key, required=True, type=Path)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    output = build(read(a.index), read(a.reviewed), read(a.high), read(a.unresolved),
                   read(a.low), read(a.forms), read(a.verses), read(a.positions))
    a.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")) + "\n", encoding="utf-8")
    print("UBS_GREEK_PRIVATE_CONSOLIDATED_WORD_INDEX", json.dumps({
        "original_word_ids": output["original_word_ids"],
        "lexical_headwords": output["reviewed_source_lexical_headword_words"],
        "provisional_word_senses": output["provisional_semantic_word_ids"],
        "unresolved": output["not_assigned_a_provisional_sense"],
        "statuses": output["word_status_counts"],
        "contextual_verified": 0,
        "published": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
