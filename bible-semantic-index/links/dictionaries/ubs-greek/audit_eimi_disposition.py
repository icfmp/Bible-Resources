#!/usr/bin/env python3
"""Audit the original Greek εἰμί source disposition, without creating UBS senses.

This is a deterministic, read-only report about an authentic UBS dictionary
entry with no independently attested LEXMeanings in the pinned Greek v1.0.
It never changes an original Strong annotation, headword map or source token.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path

LEMMA = "εἰμί"
ORIGINAL_STRONG = "G2258"
EXPECTED_STATUS = "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release"


def nfc(value):
    return unicodedata.normalize("NFC", value)


def audit(report, english, french):
    if report.get("status") != EXPECTED_STATUS:
        raise ValueError("Unapproved Greek source report status drift")
    if report.get("methods", {}).get("contextual_ubs_sense_ids_inferred") != 0:
        raise ValueError("Source has unauthorized contextual sense claim")
    entries_en = [e for e in english if nfc(e.get("Lemma", "")) == LEMMA]
    entries_fr = [e for e in french if nfc(e.get("Lemma", "")) == LEMMA]
    if len(entries_en) != 1 or len(entries_fr) != 1:
        raise ValueError("Greek εἰμί UBS v1.0 headword inventory ambiguous")
    en, fr = entries_en[0], entries_fr[0]
    if (en["MainId"] != fr["MainId"]
        or ORIGINAL_STRONG not in (en.get("StrongCodes") or [])
        or ORIGINAL_STRONG not in (fr.get("StrongCodes") or [])):
        raise ValueError("Greek εἰμί original UBS bilingual Strong or MainId mismatch")
    senses_en = [m for form in en.get("BaseForms") or []
                 for m in form.get("LEXMeanings") or []]
    senses_fr = [m for form in fr.get("BaseForms") or []
                 for m in form.get("LEXMeanings") or []]
    if senses_en or senses_fr:
        raise ValueError("Greek εἰμί now has independently attested meanings: review required")
    families = [row for row in report["unmatched_families"]
                if nfc(row["nfc_only_comparison_key"]) == LEMMA]
    if not families:
        raise ValueError("Greek εἰμί original source unmatched family missing")
    reasons = Counter()
    strongs = Counter()
    for family in families:
        if (set(family["ubs_nfc_equal_headword_candidates"]) != {en["MainId"]}
            or not family["original_source_occurrences"]
            or not family["original_word_ids_sample"]):
            raise ValueError("Greek εἰμί original source family/word witnesses drift")
        reasons.update(family["reason_counts"])
        strongs[family["original_strong"]] += family["original_source_occurrences"]
    if set(reasons) != {"nfc_lemma_only_no_attested_ubs_ln"}:
        raise ValueError("Greek εἰμί unexpected candidate evidence or sense code")
    return {
        "status": "PRIVATE_original_eimi_source_disposition_no_inferred_senses",
        "source_editions": report["source_editions"],
        "lemma_nfc_for_comparison_only": LEMMA,
        "original_ubs_main_id": en["MainId"],
        "original_ubs_strong_code": ORIGINAL_STRONG,
        "ubs_original_bilingual_lexmeanings_count": {"en": 0, "fr": 0},
        "original_missing_word_occurrences": sum(strongs.values()),
        "original_word_strong_distribution": dict(sorted(strongs.items())),
        "original_source_reason_counts": dict(sorted(reasons.items())),
        "original_family_evidence": families,
        "editorial_disposition": "NO_CONTEXTUAL_SENSE_CANDIDATE; lexical-headword-only requires a separate explicitly reviewed per-original-word decision",
        "original_strong_or_greek_modified": False,
        "new_source_word_links_approved": 0,
        "new_ubs_lexid_inferred": 0,
        "publication_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "english", "french", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8-sig"))
    result = audit(read(args.report), read(args.english), read(args.french))
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_EIMI_SOURCE_DISPOSITION", json.dumps({
        "unmatched_original_words": result["original_missing_word_occurrences"],
        "strongs": result["original_word_strong_distribution"],
        "source_reasons": result["original_source_reason_counts"],
        "ubs_senses": 0, "newly_approved": 0, "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
