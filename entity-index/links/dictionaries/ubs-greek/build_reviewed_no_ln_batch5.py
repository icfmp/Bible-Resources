#!/usr/bin/env python3
"""Review exact original Greek headwords when source UBS LN codes do not intersect.

Only original-word-ID-specific lexical headword identity is reviewed, never
an individual contextual UBS lexical sense or a global original Strong alias.
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
AUDIT = runpy.run_path(str(HERE / "audit_remaining_no_ln.py"))
NEW = "source_reviewed_original_greek_headword_without_corresponding_ubs_ln_batch5"
PENDING = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
POLICY = {
    "original_macula_word_id_required": True,
    "source_greek_nfc_lemma_identity": True,
    "unique_original_ubs_en_fr_headword": True,
    "original_ubs_part_of_speech_matches_source_class": True,
    "original_strong_morph_ln_preserved": True,
    "allow_entry_only_without_contextual_ln": True,
    "never_infer_contextual_ubs_lexid": True,
    "no_global_strong_alias": True,
    "original_index_unmodified": True,
    "publication_approved": False,
}
PARTS = {
    "pron": ({"pprs", "pdem", "prfl"}, {"pprs", "pdem", "prfl"}),
    "verb": ({"verb"}, {"verbe"}),
    "adj": ({"adjc"}, {"adjc"}),
}


def nfc(v):
    return unicodedata.normalize("NFC", v)


def canonical(v):
    return (json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def pos_value(source):
    return {str(x).lower().rstrip(".") for x in source}


def review_ledger(ledger, report):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "source_verified_original_greek_entry_only_without_lexical_ln_batch5_private"
        or ledger.get("source_editions") != report["source_editions"]
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("previous_new_source_word_approvals") != 7934
        or ledger.get("source_reviewed_entry_only_without_ln_word_count") != 1218
        or ledger.get("remaining_strict_unapproved_words") != 35):
        raise ValueError("Greek no-LN editorial evidence or original edition drift")
    reviewed = {}
    for x in ledger["reviewed_lexical_families"]:
        key = (x["lemma_nfc"], x["ubs_main_id"])
        if (key in reviewed or x["lemma_nfc"] != nfc(x["lemma_nfc"])
            or x["macula_source_class"] not in PARTS
            or not isinstance(x["original_word_count"], int)
            or x["original_word_count"] < 1
            or len(x.get("editorial_basis", "")) < 180):
            raise ValueError("Unattested Greek no-LN lexical headword editorial decision")
        reviewed[key] = x
    if (len(reviewed) != 8
        or sum(x["original_word_count"] for x in reviewed.values()) != 1218):
        raise ValueError("Original Greek no-LN eight-family review scope drift")
    return reviewed


def build(candidate, source_report, baseline, english, french, macula, report, ledger):
    independently_audited = AUDIT["audit"](source_report, baseline, english, french, macula)
    if independently_audited != report:
        raise ValueError("Pinned original Greek no-LN word-ID evidence register modified")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 7934
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 35
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0):
        raise ValueError("Previously reviewed Greek lexical candidate drift")
    selected = review_ledger(ledger, report)
    new_words = {}
    observed = set()
    for family in report["families"]:
        key = (family["lemma_nfc"], family["ubs_main_id"])
        entry = selected.get(key)
        if (not entry or family["original_word_count"] != entry["original_word_count"]
            or family["source_class_counts"] != {
                entry["macula_source_class"]: entry["original_word_count"]}
            or family["original_strong_counts"] != entry["original_strong_counts"]
            or family["ubs_original_parts_of_speech_en"] != entry["original_ubs_pos_en"]
            or family["ubs_original_parts_of_speech_fr"] != entry["original_ubs_pos_fr"]
            or (not pos_value(family["ubs_original_parts_of_speech_en"])
                & PARTS[entry["macula_source_class"]][0])
            or (not pos_value(family["ubs_original_parts_of_speech_fr"])
                & PARTS[entry["macula_source_class"]][1])):
            raise ValueError("Greek original source POS, headword or word-count evidence drift: " + repr(key))
        if family["ubs_source_meanings_missing"]:
            # Missing semantic data is allowed; it is NEVER manufactured.
            pass
        observed.add(key)
        for word in family["original_word_witnesses"]:
            wid = word["original_word_id"]
            if (wid in candidate["by_macula_word"] or wid in new_words
                or nfc(word["original_greek_lemma"]) != key[0]
                or word["ubs_main_id"] != key[1]
                or word["original_class"] != entry["macula_source_class"]
                or not word["original_strong"].isdigit()
                or not word["original_morph"] or not word["original_reference"]
                or word["contextual_ubs_lexid"] is not None):
                raise ValueError("Unattested original Greek word-ID source evidence: " + wid)
            new_words[wid] = {
                "entry_id": key[1],
                "match_type": NEW,
                "original_lemma": word["original_greek_lemma"],
                "original_strong": word["original_strong"],
                "original_ln": word["original_ln"],
                "original_reference": word["original_reference"],
                "original_class": word["original_class"],
                "original_morph": word["original_morph"],
                "corroborating_ubs_ln_codes": [],
            }
    if len(new_words) != 1218 or observed != set(selected):
        raise ValueError("Unreviewed original Greek no-LN words or lexical families")
    result = copy.deepcopy(candidate)
    result["by_macula_word"].update(new_words)
    result["by_macula_word"] = dict(sorted(result["by_macula_word"].items()))
    if Counter(x["match_type"] for x in result["by_macula_word"].values()) != {
        "source_reviewed_original_greek_pronoun_headword_only": 5033,
        "source_reviewed_original_greek_headword_batch2_only": 577,
        "source_reviewed_original_greek_entry_only_without_ubs_ln": 2031,
        "source_reviewed_original_greek_headword_batch3_only": 155,
        "source_reviewed_original_greek_headword_batch4_only": 138,
        NEW: 1218,
        PENDING: 35,
    }:
        raise ValueError("Greek original word-ID reviewed/unapproved inventory drift")
    for key, original in candidate.items():
        if key not in ("by_macula_word", "editorial_candidate", "word_aware_coverage") and result[key] != original:
            raise ValueError("Historical original UBS lexical data mutated: " + key)
    for wid, original in candidate["by_macula_word"].items():
        if result["by_macula_word"][wid] != original:
            raise ValueError("Earlier original Greek lexical review mutated: " + wid)
    result["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_1218_more_source_word_headwords_entry_only_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 9152,
        "other_original_words_still_unapproved": 35,
        "new_entry_only_without_corresponding_ln_word_approvals": 1218,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
        "editorial_source_batch5": "v1_reviewed_no_ln_families_batch5.json",
    }
    result["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 9152,
        "other_unapproved_word_headword_candidates": 35,
        "new_source_original_word_entry_only_without_ln": 3249,
        "word_aware_entry_candidate_words": 137277,
        "remaining_no_ubs_headword_candidate_original_words": 464,
        "original_gap_classes_still_unlinked": {
            "nfc_lemma_only_no_attested_ubs_ln": 0,
            "no_nfc_identical_ubs_lemma": 459,
            "unsupported_original_compound_strong": 5,
        },
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "source_report", "index", "english", "french",
                 "macula", "report", "ledger", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8-sig"))
    out = build(read(a.candidate), read(a.source_report), read(a.index),
                read(a.english), read(a.french), a.macula,
                read(a.report), read(a.ledger))
    a.output.write_bytes(canonical(out))
    print("UBS_GREEK_BATCH5_ENTRY_ONLY_VERIFIED", json.dumps({
        "new_word_ids": 1218,
        "new_source_reviewed_words_total": 9152,
        "editorially_reviewed_headword_candidate_words": 137242,
        "unapproved_strict_candidates": 35,
        "other_unmatched_source_word_ids": 464,
        "new_contextual_lexids": 0,
        "published": False,
        "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
