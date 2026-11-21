#!/usr/bin/env python3
"""Review individual original Greek word headwords across attested POS taxonomies.

MACULA and UBS source grammatical taxonomies can classify the same lexeme
differently. This source-word-ID only ledger requires exact original Greek
NFC headword and original UBS EN/FR Louw–Nida witnesses, preserves the
source labels, Strong and morphology, and never assigns contextual LEXID.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

PREVIOUS = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
REVIEWED = "source_reviewed_original_greek_headword_grammatical_taxonomy_only"
POLICY = {
    "explicit_original_word_ids_only": True,
    "retain_original_macula_and_ubs_pos": True,
    "require_original_greek_nfc_lemma": True,
    "require_attested_original_ln_in_both_ubs_languages": True,
    "require_attested_nonzero_original_strong": True,
    "source_pos_taxonomy_not_contextual_pos": True,
    "preserve_historical_strong_aliases": True,
    "no_contextual_lexid": True,
    "no_source_edit": True,
    "no_publication": True,
}
ALLOWED_TAXONOMIES = {("num", "adjc"), ("pron", "prel"), ("det", "artc")}


def nfc(value):
    return unicodedata.normalize("NFC", value)


def parts_of_speech(entry):
    return {str(p).lower().rstrip(".").split(",", 1)[0] for form in entry.get("BaseForms") or []
            for p in form.get("PartsOfSpeech") or []}


def original_lexical_codes(entry):
    return {str(m["LEXEntryCode"]) for form in entry.get("BaseForms") or []
            for m in form.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"), str)}


def validate_ledger(ledger, remaining):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "PRIVATE_original_grammatical_taxonomy_crosswalk_lexical_headword_review_NOT_PUBLISHED"
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("source_editions") != remaining.get("source_editions")
        or ledger.get("previous_word_headword_reviews") != 9152
        or ledger.get("new_source_reviewed_original_words") != 32
        or ledger.get("remaining_strict_original_words") != 3):
        raise ValueError("Original Greek lexical taxonomy editorial approval or pinned source drift")
    taxonomy = {(x["macula"], x["ubs"]) for x in ledger["grammatical_class_crosswalk"]}
    if len(ledger["grammatical_class_crosswalk"]) != 3 or taxonomy != ALLOWED_TAXONOMIES or any(
            len(x["basis"]) < 110 for x in ledger["grammatical_class_crosswalk"]):
        raise ValueError("Unsupported or undocumented original Greek lexicographic POS taxonomy")
    reviewed = {}
    for row in ledger["reviewed_families"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if (key in reviewed or row["lemma_nfc"] != nfc(row["lemma_nfc"])
            or (row["macula_class"], row["original_ubs_pos"].rstrip(".")) not in taxonomy
            or not isinstance(row["original_word_count"], int)
            or row["original_word_count"] < 1
            or any(not key.isdigit() or key == "0" for key in row["original_strong_counts"])
            or "HEADWORD only" not in row["decision"]):
            raise ValueError("Unattested Greek taxonomy headword review decision")
        reviewed[key] = row
    deferred = {}
    for row in ledger["deferred_families"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if key in reviewed or key in deferred or len(row["reason"]) < 60:
            raise ValueError("Incomplete Greek editorial deferred lexical family")
        deferred[key] = row
    if (len(reviewed) != 4 or sum(x["original_word_count"] for x in reviewed.values()) != 32
        or len(deferred) != 3 or sum(x["original_word_count"] for x in deferred.values()) != 3):
        raise ValueError("Original Greek 35-word lexical taxonomy review incomplete")
    return reviewed, deferred


def build(candidate, previous_ledger, residual, taxonomy_ledger, english, french):
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 9152
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 35
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0
        or len(candidate.get("by_macula_ambiguous_word", {})) != 220):
        raise ValueError("Existing Greek source-reviewed lexeme/ambiguity overlay drift")
    reviewed, deferred = validate_ledger(taxonomy_ledger, residual)
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Original UBS bilingual dictionary inventory drift")
    from_prior = {
        (row["lemma_nfc"], row["ubs_main_id"]): row
        for row in previous_ledger["deferred_families"]
    }
    if set(from_prior) != set(reviewed) | set(deferred) or len(from_prior) != 7:
        raise ValueError("Earlier unreviewed Greek source family dispositions differ")
    output = copy.deepcopy(candidate)
    selected_ids = set()
    approved_keys = set()
    deferred_keys = set()
    for family in residual["families"]:
        key = (family["lemma_nfc"], family["ubs_main_id"])
        if key not in from_prior:
            continue  # The other 101 families were already approved in batch 4.
        decision = reviewed.get(key)
        if decision is None:
            d = deferred.get(key)
            if d is None or family["original_word_count"] != d["original_word_count"]:
                raise ValueError("Unapproved Greek source grammar or Strong family modified")
            deferred_keys.add(key)
            continue
        mid = key[1]
        if (mid not in en or mid not in fr or
            nfc(en[mid]["Lemma"]) != key[0] or nfc(fr[mid]["Lemma"]) != key[0] or
            family["original_word_count"] != decision["original_word_count"] or
            family["original_classes"] != {decision["macula_class"]: family["original_word_count"]} or
            family["original_strong_counts"] != decision["original_strong_counts"] or
            family["ubs_original_pos"] != [decision["original_ubs_pos"]] or
            decision["original_ubs_pos"].rstrip(".") not in parts_of_speech(en[mid]) or
            decision["original_ubs_pos"].rstrip(".") not in parts_of_speech(fr[mid])):
            raise ValueError("Greek original source taxonomy, lexeme or UBS bilingual POS mismatch")
        en_ln = original_lexical_codes(en[mid])
        fr_ln = original_lexical_codes(fr[mid])
        if not en_ln or en_ln != fr_ln:
            raise ValueError("Pinned UBS Greek bilingual lexical-domain evidence mismatch")
        if len(family["all_original_word_witnesses"]) != family["original_word_count"]:
            raise ValueError("Missing Greek original source per-word witness")
        approved_keys.add(key)
        for word in family["all_original_word_witnesses"]:
            wid = word["word_id"]
            old = candidate["by_macula_word"].get(wid)
            if (wid in selected_ids or old is None or old["match_type"] != PREVIOUS
                or old["entry_id"] != mid
                or old["original_lemma"] != word["original_lemma"]
                or old["original_strong"] != word["original_strong"]
                or old["original_ln"] != word["original_ln"]
                or old["original_class"] != word["original_class"]
                or old["original_morph"] != word["original_morph"]
                or old["original_reference"] != word["reference"]
                or old["corroborating_ubs_ln_codes"] != word["attested_headword_ln_codes"]):
                raise ValueError("Unverified Greek original word-ID lexical headword witness: " + wid)
            shared = sorted(set(old["original_ln"].split()) & en_ln & fr_ln)
            if not shared or shared != old["corroborating_ubs_ln_codes"]:
                raise ValueError("Missing independent bilingual Greek Louw–Nida lexical evidence")
            if old["original_strong"] == "0" or not old["original_strong"].isdigit():
                raise ValueError("Greek original Strong 0 / unsupported annotation not eligible")
            output["by_macula_word"][wid]["match_type"] = REVIEWED
            selected_ids.add(wid)
    if (approved_keys != set(reviewed) or deferred_keys != set(deferred)
        or len(selected_ids) != 32):
        raise ValueError("Unaccounted original Greek taxonomy family/word evidence")
    counts = Counter(x["match_type"] for x in output["by_macula_word"].values())
    if counts[REVIEWED] != 32 or counts[PREVIOUS] != 3 or len(output["by_macula_word"]) != 9187:
        raise ValueError("Greek 32 reviewed / 3 deferred original-word partition drift")
    for wid, item in candidate["by_macula_word"].items():
        new = output["by_macula_word"][wid]
        if ({k:v for k,v in item.items() if k != "match_type"} !=
            {k:v for k,v in new.items() if k != "match_type"}
            or (wid not in selected_ids and item != new)):
            raise ValueError("Original Greek Strong/LN/text/morphology/source review was modified")
    for key in candidate:
        if key not in ("by_macula_word", "editorial_candidate", "word_aware_coverage") and candidate[key] != output[key]:
            raise ValueError("Existing Greek baseline Strong bridge/ambiguities modified")
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_32_original_Greek_word_headwords_taxonomy_review_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 9184,
        "other_original_words_still_unapproved": 3,
        "new_source_taxonomy_lexical_headword_approvals": 32,
        "editorial_source_taxonomy_review": "v1_reviewed_taxonomy_headwords.json",
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 9184,
        "other_unapproved_word_headword_candidates": 3,
        "word_aware_entry_candidate_words": candidate["word_aware_coverage"]["word_aware_entry_candidate_words"],
        "remaining_no_ubs_headword_candidate_original_words": candidate["word_aware_coverage"]["remaining_no_ubs_headword_candidate_original_words"],
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "previous_ledger", "residual", "taxonomy_ledger", "english", "french", "output"):
        p.add_argument("--"+name, required=True, type=Path)
    a = p.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    result = build(read(a.candidate), read(a.previous_ledger),
                   read(a.residual), read(a.taxonomy_ledger), read(a.english), read(a.french))
    a.output.write_bytes((json.dumps(result, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"))+"\n").encode("utf-8"))
    print("GREEK_TAXONOMY_32_WORD_ID_HEADWORDS", json.dumps({
        "new_word_headwords": 32,
        "previous_extra_word_headwords": 9152,
        "extra_word_headwords_reviewed_total": 9184,
        "lexical_entry_candidate_word_coverage": 137274,
        "strict_source_pos_or_strong_pending_words": 3,
        "contextual_lexids_inferred": 0,
        "published": False,
        "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
