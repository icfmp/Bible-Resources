#!/usr/bin/env python3
"""Review 101 individually source-attested Greek headword families (138 words).

This is an original-word-ID-specific lexeme/headword approval only. Original
Greek, Strong, LN, morphology, references, legacy links and all prior
source-reviewed headwords are immutable; no contextual UBS meaning is chosen.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = runpy.run_path(str(HERE / "audit_remaining_173.py"))
NEW = "source_reviewed_original_greek_headword_batch4_only"
OLD = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
GRAMMAR = {
    "noun": {"noun", "noun-name"},
    "verb": {"verb"},
    "adj": {"adjc", "adj", "adjective"},
    "adv": {"advb", "adv"},
    "prep": {"prep"},
    "conj": {"conj"},
}
POLICY = {
    "original_word_ids_only": True,
    "original_lemma_nfc_exact": True,
    "require_original_ubs_en_fr_ln": True,
    "require_matching_source_grammatical_class": True,
    "require_attested_nonzero_original_strong": True,
    "no_contextual_lexid": True,
    "no_global_strong_alias": True,
    "legacy_index_unchanged": True,
    "publication_approved": False,
}


def nfc(v):
    return unicodedata.normalize("NFC", v)


def normalized_pos(source_parts):
    return {str(p).lower().replace(".", "").split(",", 1)[0].split(" ", 1)[0]
            for p in source_parts}


def canonical(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_ledger(ledger, residual):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "individual_original_greek_word_headword_review_batch4_private"
        or ledger.get("source_editions") != residual.get("source_editions")
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("previously_reviewed_original_words") != 7796
        or ledger.get("source_word_approvals_batch4") != 138
        or ledger.get("remaining_strict_source_word_unapproved") != 35):
        raise ValueError("Greek fourth source-lexical editorial scope drift")
    reviewed = {}
    for row in ledger["reviewed_families"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if (key in reviewed or row["lemma_nfc"] != nfc(row["lemma_nfc"])
            or row["macula_class"] not in GRAMMAR
            or not isinstance(row["source_word_count"], int)
            or row["source_word_count"] < 1 or
            len(row.get("editorial_basis", "")) < 180):
            raise ValueError("Original Greek batch4 entry decision malformed")
        reviewed[key] = row
    if len(reviewed) != 101 or sum(x["source_word_count"] for x in reviewed.values()) != 138:
        raise ValueError("Greek fourth reviewed source family count drift")
    deferred = {}
    for row in ledger["deferred_families"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if key in reviewed or key in deferred:
            raise ValueError("Duplicate approved/deferred original Greek family")
        deferred[key] = row
    if len(deferred) != 7 or sum(x["source_word_count"] for x in deferred.values()) != 35:
        raise ValueError("Greek explicitly deferred original source inventory drift")
    return reviewed, deferred


def build(candidate, residual328, third_ledger, residual173, ledger, english, french):
    trusted = SOURCE["triage"](residual328, third_ledger)
    if trusted != residual173:
        raise ValueError("Original Greek 173-word source witness register drift")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 7796
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 173
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0):
        raise ValueError("Previously reviewed original Greek source-word candidate drift")
    approved, deferred = validate_ledger(ledger, residual173)
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("UBS bilingual Greek lexical inventory drift")
    newly_reviewed = set()
    observed_approved, observed_deferred = set(), set()
    for f in residual173["families"]:
        key = (f["lemma_nfc"], f["ubs_main_id"])
        decision = approved.get(key)
        if decision is None:
            d = deferred.get(key)
            if d is None or (d["source_word_count"] != f["original_word_count"]
                              or d["original_strong_counts"] != f["original_strong_counts"]
                              or d["ubs_original_pos"] != f["ubs_original_pos"]):
                raise ValueError("Unreviewed Greek original-family classification changed")
            observed_deferred.add(key)
            continue
        if (decision["source_word_count"] != f["original_word_count"]
            or f["original_classes"] != {decision["macula_class"]: f["original_word_count"]}
            or decision["original_strong_counts"] != f["original_strong_counts"]
            or decision["original_ubs_parts_of_speech"] != f["ubs_original_pos"]
            or not (GRAMMAR[decision["macula_class"]] & normalized_pos(f["ubs_original_pos"]))
            or any(s == "0" or not s.isdigit() for s in f["original_strong_counts"])
            or f["ubs_main_id"] not in en or f["ubs_main_id"] not in fr
            or nfc(en[key[1]]["Lemma"]) != key[0]
            or nfc(fr[key[1]]["Lemma"]) != key[0]):
            raise ValueError("Greek batch4 dictionary/source headword POS or Strong evidence drift")
        observed_approved.add(key)
        for word in f["all_original_word_witnesses"]:
            wid = word["word_id"]
            original = candidate["by_macula_word"].get(wid)
            if (wid in newly_reviewed or original is None
                or original["match_type"] != OLD
                or original["entry_id"] != key[1]
                or original["original_lemma"] != word["original_lemma"]
                or original["original_strong"] != word["original_strong"]
                or original["original_ln"] != word["original_ln"]
                or original["original_reference"] != word["reference"]
                or original["original_class"] != word["original_class"]
                or original["original_morph"] != word["original_morph"]
                or original["corroborating_ubs_ln_codes"] != word["attested_headword_ln_codes"]):
                raise ValueError("Unattested exact original Greek word-ID headword evidence: " + wid)
            newly_reviewed.add(wid)
    if (observed_approved != set(approved) or observed_deferred != set(deferred)
        or len(newly_reviewed) != 138):
        raise ValueError("Source-original Greek fourth review ledger not exhaustively matched")
    output = copy.deepcopy(candidate)
    for wid in newly_reviewed:
        output["by_macula_word"][wid]["match_type"] = NEW
    kinds = Counter(x["match_type"] for x in output["by_macula_word"].values())
    if kinds != {
        "source_reviewed_original_greek_pronoun_headword_only": 5033,
        "source_reviewed_original_greek_headword_batch2_only": 577,
        "source_reviewed_original_greek_entry_only_without_ubs_ln": 2031,
        "source_reviewed_original_greek_headword_batch3_only": 155,
        NEW: 138,
        OLD: 35,
    }:
        raise ValueError("Greek original word headword review partition changed")
    for wid, original in candidate["by_macula_word"].items():
        updated = output["by_macula_word"][wid]
        if ({k: v for k, v in original.items() if k != "match_type"} !=
                {k: v for k, v in updated.items() if k != "match_type"}
            or (wid not in newly_reviewed and original != updated)):
            raise ValueError("Greek original source annotation or earlier approval mutated")
    for key in candidate:
        if key not in ("by_macula_word", "editorial_candidate", "word_aware_coverage") and candidate[key] != output[key]:
            raise ValueError("Frozen original UBS Greek lexical map modified")
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_source-reviewed_138_Greek_original_word_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 7934,
        "other_original_words_still_unapproved": 35,
        "new_original_word_lexical_batch4_approvals": 138,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
        "editorial_source_batch4": "v1_reviewed_families_batch4.json",
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 7934,
        "other_unapproved_word_headword_candidates": 35,
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("candidate", "residual328", "third_ledger", "residual173",
                "ledger", "english", "french", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    output = build(read(a.candidate), read(a.residual328), read(a.third_ledger),
                   read(a.residual173), read(a.ledger),
                   read(a.english), read(a.french))
    a.output.write_bytes(canonical(output))
    print("UBS_GREEK_BATCH4_REVIEW", json.dumps({
        "new_original_word_headwords": 138,
        "previous_source_word_headwords_reviewed": 7796,
        "total_new_source_word_headwords_reviewed": 7934,
        "strict_unapproved_word_ids": 35,
        "lexical_candidate_words": 136024,
        "original_macula_words": 137741,
        "contextual_sense_ids_inferred": 0,
        "published": False,
        "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
