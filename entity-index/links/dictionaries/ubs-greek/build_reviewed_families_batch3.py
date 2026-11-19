#!/usr/bin/env python3
"""Review specific original Greek headwords from the exact 328-word source register.

Do not change the baseline index, original lexical annotations or contextual
meaning. The resulting complete word-ID overlay is a private review artifact.
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
RESIDUAL = runpy.run_path(str(HERE / "audit_remaining_328.py"))
OLD = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
NEW = "source_reviewed_original_greek_headword_batch3_only"
GRAMMAR = {
    "adj": {"adjc", "adj", "adjective"},
    "verb": {"verb"},
    "noun": {"noun", "noun-name"},
}
POLICY = {
    "exact_original_word_ids": True,
    "original_nfc_lemma_and_bilingual_ln": True,
    "original_macula_class_and_ubs_pos": True,
    "original_strong_unchanged": True,
    "no_contextual_ubs_sense": True,
    "no_global_strong_aliases": True,
    "no_publication": True,
}


def nfc(v):
    return unicodedata.normalize("NFC", v)


def canonical(v):
    return (json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def select(ledger, residual):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "source_verified_greek_lexical_headword_batch3_private_not_published"
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("source_editions") != residual["source_editions"]
        or ledger.get("previous_reviewed_original_words") != 7641
        or ledger.get("new_reviewed_original_words") != 155
        or ledger.get("remaining_strict_unapproved_words") != 173):
        raise ValueError("Unapproved Greek editorial batch3 scope or source revision")
    decisions = {}
    for x in ledger["reviewed_families"]:
        key = (x["lemma_nfc"], x["ubs_main_id"])
        if (key in decisions or x["lemma_nfc"] != nfc(x["lemma_nfc"])
            or x["macula_class"] not in GRAMMAR or
            not isinstance(x["source_word_count"], int)
            or x["source_word_count"] < 1 or
            len(x.get("editorial_basis", "")) < 180):
            raise ValueError("Unattested Greek batch3 family decision")
        decisions[key] = x
    if len(decisions) != 19 or sum(x["source_word_count"] for x in decisions.values()) != 155:
        raise ValueError("Greek batch3 explicit family inventory drift")
    return decisions


def pos_compatible(source_class, parts):
    parts = {str(p).lower().rstrip(".").split(",", 1)[0].strip() for p in parts}
    return bool(parts & GRAMMAR[source_class])


def build(candidate, original_905, batch2, residual, ledger, english, french):
    independently_audited = RESIDUAL["build"](original_905, batch2)
    if residual != independently_audited:
        raise ValueError("Residual exact Greek source evidence modified")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 7641
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 328
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0):
        raise ValueError("Previous Greek lexical editorial batch drift")
    decisions = select(ledger, residual)
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Pinned UBS bilingual source entry identities drift")
    approved_ids = set()
    counts = Counter()
    for f in residual["families"]:
        key = (f["lemma_nfc"], f["ubs_main_id"])
        decision = decisions.get(key)
        if decision is None:
            continue
        mid = f["ubs_main_id"]
        if (f["original_word_count"] != decision["source_word_count"] or
            f["original_classes"] != {decision["macula_class"]: f["original_word_count"]} or
            mid not in en or mid not in fr or
            nfc(en[mid]["Lemma"]) != f["lemma_nfc"] or
            nfc(fr[mid]["Lemma"]) != f["lemma_nfc"] or
            not pos_compatible(decision["macula_class"], f["ubs_original_pos"])):
            raise ValueError("Pinned Greek lexical family source POS or headword discrepancy: " + repr(key))
        for word in f["all_original_word_witnesses"]:
            wid = word["word_id"]
            original = candidate["by_macula_word"].get(wid)
            if (wid in approved_ids or original is None or original["match_type"] != OLD or
                original["entry_id"] != mid or
                original["original_lemma"] != word["original_lemma"] or
                original["original_strong"] != word["original_strong"] or
                original["original_ln"] != word["original_ln"] or
                original["original_reference"] != word["reference"] or
                original["original_class"] != word["original_class"] or
                original["original_morph"] != word["original_morph"] or
                original["corroborating_ubs_ln_codes"] != word["attested_headword_ln_codes"]):
                raise ValueError("Greek original word-ID source witness drift: " + wid)
            approved_ids.add(wid)
        counts[key[0]] += f["original_word_count"]
    if set(counts) != {x[0] for x in decisions} or len(approved_ids) != 155:
        raise ValueError("Greek batch3 155 original-word source attestations incomplete")
    out = copy.deepcopy(candidate)
    for wid in approved_ids:
        out["by_macula_word"][wid]["match_type"] = NEW
    if Counter(x["match_type"] for x in out["by_macula_word"].values()) != {
        "source_reviewed_original_greek_pronoun_headword_only": 5033,
        "source_reviewed_original_greek_headword_batch2_only": 577,
        "source_reviewed_original_greek_entry_only_without_ubs_ln": 2031,
        NEW: 155, OLD: 173,
    }:
        raise ValueError("Greek reviewed/unreviewed original-word partition changed")
    for wid, row in candidate["by_macula_word"].items():
        old = {k: v for k, v in row.items() if k != "match_type"}
        new = {k: v for k, v in out["by_macula_word"][wid].items() if k != "match_type"}
        if old != new or (wid not in approved_ids and row != out["by_macula_word"][wid]):
            raise ValueError("Greek original lexical annotation or earlier editorial decision mutated")
    for k in candidate:
        if k not in ("by_macula_word", "word_aware_coverage", "editorial_candidate") and out[k] != candidate[k]:
            raise ValueError("Historical UBS Greek bridge mutated: " + k)
    out["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_19_Greek_families_headword_review_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 7796,
        "strict_original_words_still_unapproved": 173,
        "other_original_words_still_unapproved": 173,
        "new_original_word_lexical_batch3_approvals": 155,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "editorial_source_batch3": "v1_reviewed_families_batch3.json",
        "publication_approved": False,
    }
    out["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 7796,
        "other_unapproved_word_headword_candidates": 173,
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("candidate", "evidence", "batch2", "residual", "ledger", "english", "french", "output"):
        p.add_argument("--" + field, type=Path, required=True)
    args = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    result = build(read(args.candidate), read(args.evidence), read(args.batch2),
                   read(args.residual), read(args.ledger), read(args.english), read(args.french))
    args.output.write_bytes(canonical(result))
    print("UBS_GREEK_BATCH3_SOURCE_REVIEW", json.dumps({
        "approved_original_words_batch3": 155,
        "reviewed_additional_original_words_total": 7796,
        "strict_unapproved_original_words_remaining": 173,
        "editorially_reviewed_headword_candidate_words": 135886,
        "source_words": 137741,
        "contextual_sense_ids_inferred": 0,
        "published": False,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
