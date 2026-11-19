#!/usr/bin/env python3
"""Review exactly three original Greek Ἄλφα word IDs without changing capitalization.

The original UBS v1.0 headword has case-only spelling ἄλφα and is a uniquely
attested Greek letter-name. Independent source Louw–Nida identity and
grammatical class are required, not a speculative casefold alias.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path

STATUS = "source_reviewed_original_greek_Alpha_case_only_lexical_headword_only"
POLICY = {
    "only_attested_original_word_ids": True,
    "source_greek_spelling_preserved": True,
    "casefold_diagnostic_only_until_corrobated_by_original_ln": True,
    "require_unique_original_ubs_en_fr_headword": True,
    "require_original_ubs_en_fr_lexical_ln_code": True,
    "require_source_lexical_noun_class": True,
    "original_source_strong_preserved": True,
    "no_global_strong_alias": True,
    "no_contextual_lexid": True,
    "historical_strong_index_unchanged": True,
    "publication_approved": False,
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def pos(entry):
    return {str(p).lower().rstrip(".").split(",", 1)[0]
            for f in entry.get("BaseForms") or []
            for p in f.get("PartsOfSpeech") or []}


def ln(entry):
    return {str(m["LEXEntryCode"])
            for f in entry.get("BaseForms") or []
            for m in f.get("LEXMeanings") or []
            if isinstance(m.get("LEXEntryCode"), str)}


def validate(ledger, source, english, french):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "PRIVATE_original_word_specific_greek_case_only_alpha_lexical_headword_review"
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("source_editions") != source.get("source_editions")
        or ledger.get("previous_source_word_headword_reviews") != 9186
        or ledger.get("new_original_word_headword_reviews") != 3
        or ledger.get("other_original_ubs_no_exact_lemma_words_still_unapproved") != 456
        or ledger.get("remaining_strict_unapproved_source_words") != 1):
        raise ValueError("Greek Alpha source case-review editorial authorization or version drift")
    decision = ledger["reviewed_original_lexeme"]
    if (decision.get("macula_lemma_original") != "Ἄλφα"
        or decision.get("ubs_original_lemma_case_only") != "ἄλφα"
        or decision.get("ubs_main_id") != "000253000000000"
        or decision.get("macula_original_strong") != "1"
        or decision.get("macula_original_class") != "noun"
        or decision.get("macula_original_louw_nida") != "61.7"
        or decision.get("original_word_count") != 3
        or len(decision.get("editorial_basis", "")) < 250):
        raise ValueError("Greek Alpha word-specific original lexical editorial decision altered")
    if nfc("Ἄλφα") == nfc("ἄλφα") or nfc("Ἄλφα").casefold() != nfc("ἄλφα").casefold():
        raise ValueError("Greek Alpha capitalization is not a case-only original spelling variant")
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Original UBS bilingual Greek headword inventory changed")
    mid = decision["ubs_main_id"]
    if (mid not in en or mid not in fr
        or nfc(en[mid]["Lemma"]) != decision["ubs_original_lemma_case_only"]
        or nfc(fr[mid]["Lemma"]) != decision["ubs_original_lemma_case_only"]):
        raise ValueError("Original UBS bilingual Greek lowercase Alpha lexeme missing")
    # The UBS grammatical metadata are native-source labels, not source edits.
    en_pos, fr_pos = pos(en[mid]), pos(fr[mid])
    if not ("noun" in en_pos or "noun-name" in en_pos) or "nom" not in fr_pos:
        raise ValueError("Original UBS Greek Alpha EN/FR noun POS not independently attested")
    if not (ln(en[mid]) == ln(fr[mid]) and "61.7" in ln(en[mid])):
        raise ValueError("Pinned original UBS Greek bilingual Alpha lexical LN witness missing")
    return decision, mid


def review(candidate, source, ledger, english, french):
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 9186
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved") != 1
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or len(candidate.get("by_macula_ambiguous_word", {})) != 220):
        raise ValueError("Previous Greek original source-word headword candidate changed")
    decision, mid = validate(ledger, source, english, french)
    case_groups = [f for f in source["source_word_families"]
                   if f["ubs_case_only_spelling_main_ids"]]
    if len(case_groups) != 1:
        raise ValueError("Greek original source case-only lemma group inventory drift")
    family = case_groups[0]
    if (family["original_greek_lemma_nfc_for_comparison"] != "Ἄλφα"
        or family["original_source_strong"] != "1"
        or family["original_word_count"] != 3
        or family["original_source_classes"] != {"noun": 3}
        or family["ubs_case_only_spelling_main_ids"] != [mid]
        or family["original_ln_code_counts"] != {"61.7": 3}
        or family["ubs_exact_original_strong_main_ids_other_lemma"]
        or len(family["source_original_word_witnesses"]) != 3):
        raise ValueError("Original Greek Alpha source word-ID or lexicographic casefold drift")
    output = copy.deepcopy(candidate)
    new_ids = set()
    for row in family["source_original_word_witnesses"]:
        wid = row["original_word_id"]
        if (wid in candidate["by_macula_word"]
            or wid in candidate.get("by_macula_ambiguous_word", {})
            or wid in new_ids
            or row["original_lemma"] != decision["macula_lemma_original"]
            or row["original_strong"] != decision["macula_original_strong"]
            or row["original_class"] != "noun"
            or row["original_ln"] != "61.7"
            or not row["original_reference"] or not row["original_morph"]):
            raise ValueError("Greek original Alpha word-ID, Greek, Strong, LN or morphology drift")
        new_ids.add(wid)
        output["by_macula_word"][wid] = {
            "entry_id": mid,
            "match_type": STATUS,
            "original_lemma": row["original_lemma"],
            "original_strong": row["original_strong"],
            "original_ln": row["original_ln"],
            "original_reference": row["original_reference"],
            "original_class": row["original_class"],
            "original_morph": row["original_morph"],
            "corroborating_ubs_ln_codes": ["61.7"],
            "original_ubs_lexeme": decision["ubs_original_lemma_case_only"],
            "source_comparison": "original_Greek_case_only_lemma_and_bilingual_lexical_LN",
        }
    if len(new_ids) != 3 or len(output["by_macula_word"]) != 9190:
        raise ValueError("Greek exactly three original Alpha words not individually source-reviewed")
    output["by_macula_word"] = dict(sorted(output["by_macula_word"].items()))
    if any(output[k] != v for k,v in candidate.items()
           if k not in ("by_macula_word", "editorial_candidate", "word_aware_coverage")):
        raise ValueError("Frozen Greek lexical Strong/ambiguity candidate unexpectedly mutated")
    for wid, item in candidate["by_macula_word"].items():
        if output["by_macula_word"][wid] != item:
            raise ValueError("Earlier Greek original source-word headword review mutated")
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_three_Greek_Alpha_original_word_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total": 9189,
        "new_original_Greek_alpha_letter_name_headwords": 3,
        "other_original_words_still_unapproved": 1,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "editorial_source_letter_name_capitalization": "v1_reviewed_case_only_alpha.json",
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 9189,
        "word_aware_entry_candidate_words": 137280,
        "remaining_no_ubs_headword_candidate_original_words": 461,
        "new_source_ubs_case_only_original_word_lexical_headwords": 3,
        "other_unapproved_word_headword_candidates": 1,
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("candidate", "source", "ledger", "english", "french", "output"):
        p.add_argument("--"+key, type=Path, required=True)
    a=p.parse_args()
    read=lambda f: json.loads(f.read_text(encoding="utf-8-sig"))
    r=review(read(a.candidate), read(a.source), read(a.ledger),
             read(a.english), read(a.french))
    a.output.write_bytes((json.dumps(r, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"))+"\n").encode("utf-8"))
    print("GREEK_ALPHA_ORIGINAL_WORD_HEADWORD_REVIEWED", json.dumps({
        "reviewed_original_word_ids": 3,
        "source_spelling_preserved": True,
        "original_strong_preserved": "1",
        "reviewed_headwords_above_baseline": 9189,
        "source_reviewed_lexical_word_coverage": 137279,
        "lexical_original_word_ids_remaining_unapproved": 462,
        "new_contextual_senses": 0,
        "published": False,
        "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
