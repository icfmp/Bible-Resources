#!/usr/bin/env python3
"""Review two original Greek word-specific headwords without inventing missing Strong.

Original MACULA strong=0 is preserved, not a G0 equivalent. Exact original
word ID, Unicode NFC lemma, morphology, grammatical class and original LN
are crosschecked against the pinned bilingual UBS lexical entry. No
contextual sense/LEXID is inferred and no global alias is generated.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

OLD = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
NEW = "source_reviewed_original_greek_word_without_strong_lemma_ln_headword_only"
POLICY = {
    "original_word_id_required": True,
    "original_macula_strong_zero_must_remain_zero": True,
    "unique_ubs_original_greek_lemma_nfc": True,
    "original_ubs_en_fr_lexical_ln_domain_corroboration": True,
    "require_matching_original_lexical_pos": True,
    "do_not_infer_original_strong_code": True,
    "do_not_infer_contextual_ubs_lexid": True,
    "do_not_create_global_alias": True,
    "original_index_and_text_unchanged": True,
    "publication_approved": False,
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def source_pos(entry):
    return {str(p).lower().rstrip(".").split(",", 1)[0] for f in entry.get("BaseForms") or []
            for p in f.get("PartsOfSpeech") or []}


def source_ln(entry):
    return {str(m["LEXEntryCode"]) for f in entry.get("BaseForms") or []
            for m in f.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"), str)}


def audit_ledger(ledger, residual):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "PRIVATE_review_original_greek_word_specific_lemma_ln_headwords_without_source_strong"
        or ledger.get("source_editions") != residual.get("source_editions")
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("previous_reviewed_original_word_headwords") != 9184
        or ledger.get("new_reviewed_source_word_headwords") != 2
        or ledger.get("strict_source_word_candidates_still_unapproved") != 1):
        raise ValueError("Greek original Strong=0 source-editorial review authorization drift")
    selected = {}
    for row in ledger["reviewed"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if (key in selected or nfc(row["lemma_nfc"]) != row["lemma_nfc"]
            or row["original_strong"] != "0"
            or row["original_macula_class"] != "noun"
            or row["original_word_count"] != 1
            or row["ubs_original_pos_prefix_en"] not in {"noun", "noun-name"}
            or row["ubs_original_pos_prefix_fr"] != "nom"
            or len(row["editorial_basis"]) < 200):
            raise ValueError("Missing original Greek Strong=0 word-specific independent lexical decision")
        selected[key] = row
    deferred = {(row["lemma_nfc"], row["ubs_main_id"]): row for row in ledger["deferred"]}
    if (len(selected) != 2 or len(deferred) != 1 or
        set(deferred) != {("ὁπότε", "003605000000000")}):
        raise ValueError("Greek incomplete zero-Strong original-word editorial partition")
    return selected, deferred


def build(candidate, ledger, residual, english, french):
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 9184
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 3
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0
        or len(candidate.get("by_macula_ambiguous_word", {})) != 220):
        raise ValueError("Previous Greek source-reviewed original word inventory drift")
    selected, deferred = audit_ledger(ledger, residual)
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Greek UBS original English/French lexical inventory changed")
    chosen, declined = set(), set()
    output = copy.deepcopy(candidate)
    for family in residual["families"]:
        key = (family["lemma_nfc"], family["ubs_main_id"])
        if key not in selected and key not in deferred:
            continue
        decision = selected.get(key)
        if decision is None:
            if (family["original_word_count"] != 1 or
                family["original_word_count"] != deferred[key]["original_word_count"]):
                raise ValueError("Original Greek deferred temporal conjunction changed")
            declined.add(key)
            continue
        mid = key[1]
        if (mid not in en or mid not in fr
            or nfc(en[mid]["Lemma"]) != key[0]
            or nfc(fr[mid]["Lemma"]) != key[0]
            or family["original_word_count"] != 1
            or family["original_classes"] != {"noun": 1}
            or family["original_strong_counts"] != {"0": 1}
            or len(family["all_original_word_witnesses"]) != 1
            or decision["ubs_original_pos_prefix_en"] not in source_pos(en[mid])
            or decision["ubs_original_pos_prefix_fr"] not in source_pos(fr[mid])):
            raise ValueError("Original Greek Strong=0 lemma, morphology or UBS bilingual POS mismatch: " + repr({"key": key, "family_count": family["original_word_count"], "classes": family["original_classes"], "strong_counts": family["original_strong_counts"], "en_pos": sorted(source_pos(en[mid])) if mid in en else [], "fr_pos": sorted(source_pos(fr[mid])) if mid in fr else [], "original_word_count": len(family["all_original_word_witnesses"])}))
        en_ln, fr_ln = source_ln(en[mid]), source_ln(fr[mid])
        if not en_ln or en_ln != fr_ln:
            raise ValueError("Original Greek Strong=0 bilingual Louw–Nida source disagreement")
        witness = family["all_original_word_witnesses"][0]
        wid = witness["word_id"]
        old = candidate["by_macula_word"].get(wid)
        if (not old or old["match_type"] != OLD or old["entry_id"] != mid
            or old["original_strong"] != "0"
            or old["original_lemma"] != witness["original_lemma"]
            or old["original_ln"] != witness["original_ln"]
            or old["original_morph"] != witness["original_morph"]
            or old["original_reference"] != witness["reference"]
            or old["original_class"] != "noun"
            or old["corroborating_ubs_ln_codes"] != witness["attested_headword_ln_codes"]):
            raise ValueError("Original Greek Strong=0 word ID or source annotation drift: " + wid)
        if (sorted(set(old["original_ln"].split()) & en_ln & fr_ln)
            != old["corroborating_ubs_ln_codes"]):
            raise ValueError("Original Greek Strong=0 independent lexical LN corroboration missing")
        output["by_macula_word"][wid]["match_type"] = NEW
        chosen.add(key)
    if chosen != set(selected) or declined != set(deferred):
        raise ValueError("Original Greek Strong=0 review did not exhaust explicit ledger")
    parts = Counter(x["match_type"] for x in output["by_macula_word"].values())
    if len(output["by_macula_word"]) != 9187 or parts[NEW] != 2 or parts[OLD] != 1:
        raise ValueError("Greek original source-reviewed headwords / pending cohort drift")
    for wid, row in candidate["by_macula_word"].items():
        new = output["by_macula_word"][wid]
        if ({k:v for k,v in row.items() if k != "match_type"} !=
            {k:v for k,v in new.items() if k != "match_type"}
            or (row["match_type"] != OLD and new != row)):
            raise ValueError("Historical source Strong, LN, Greek, morphology or earlier review mutated")
    for k in candidate:
        if k not in ("by_macula_word", "editorial_candidate", "word_aware_coverage") and output[k] != candidate[k]:
            raise ValueError("Historical Greek lexical Strong maps/ambiguous words modified")
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_original_Greek_two_missing_Strong_lexical_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 9186,
        "other_original_words_still_unapproved": 1,
        "new_original_word_strong_zero_headword_reviews": 2,
        "editorial_source_missing_strong_review": "v1_reviewed_missing_strong_word_headwords.json",
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 9186,
        "other_unapproved_word_headword_candidates": 1,
        "word_aware_entry_candidate_words": candidate["word_aware_coverage"]["word_aware_entry_candidate_words"],
        "remaining_no_ubs_headword_candidate_original_words": candidate["word_aware_coverage"]["remaining_no_ubs_headword_candidate_original_words"],
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("candidate", "ledger", "residual", "english", "french", "output"):
        parser.add_argument("--"+field, type=Path, required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    result = build(read(args.candidate), read(args.ledger), read(args.residual),
                   read(args.english), read(args.french))
    args.output.write_bytes((json.dumps(result, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"))+"\n").encode("utf-8"))
    print("GREEK_STRONG_ZERO_ORIGINAL_WORD_HEADWORDS_SOURCE_REVIEWED", json.dumps({
        "new_headword_id_only_reviews": 2,
        "old_strong_value_preserved": "0",
        "extra_word_headword_reviews_total": 9186,
        "lexical_candidate_original_word_coverage": 137276,
        "strict_unapproved_grammatical_cases": 1,
        "new_contextual_lexids": 0,
        "published": False,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
