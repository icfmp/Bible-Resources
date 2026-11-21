#!/usr/bin/env python3
"""Produce a source-attested, non-promoting evidence register for the remaining Greek headwords.

This report classifies existing private original-word candidates; it never
authorizes an entry or contextual sense and never edits original source data.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

APPROVED = "source_reviewed_original_greek_pronoun_headword_only"
UNAPPROVED = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
SOURCE_REVISIONS = {
    "ubs_greek_edition": "1.0",
    "ubs_revision": "a15a96cfaa4ca18a6c0339016645ba1e534db3c8",
    "macula_sblgnt_revision": "8423afe47b9e8f24b7772e808af45c7159a6fe7e",
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def prepare(candidate, english, french):
    meta = candidate["editorial_candidate"]
    if (meta.get("source_editions") != SOURCE_REVISIONS
            or meta.get("publication_approved") is not False
            or meta.get("source_pronoun_headword_approvals") != 5033
            or meta.get("other_original_words_still_unapproved") != 905):
        raise ValueError("Private source-reviewed candidate metadata drift")
    by_en = {e["MainId"]: e for e in english}
    by_fr = {e["MainId"]: e for e in french}
    if len(by_en) != len(english) or len(by_fr) != len(french) or set(by_en) != set(by_fr):
        raise ValueError("Pinned UBS bilingual headword identity drift")
    families = defaultdict(list)
    count = Counter()
    ids = set()
    for wid, rec in sorted(candidate["by_macula_word"].items()):
        if wid in ids:
            raise ValueError("Duplicate original Greek word ID")
        ids.add(wid)
        match = rec["match_type"]
        if match not in (APPROVED, UNAPPROVED):
            raise ValueError("Unknown original-word editorial status: " + match)
        count[match] += 1
        if match == APPROVED:
            continue
        mid = rec["entry_id"]
        en, fr = by_en.get(mid), by_fr.get(mid)
        if not en or not fr or nfc(rec["original_lemma"]) != nfc(en["Lemma"]) or nfc(en["Lemma"]) != nfc(fr["Lemma"]):
            raise ValueError("Unattested bilingual source headword at " + wid)
        codes = {
            item.get("LEXEntryCode")
            for form in en.get("BaseForms") or []
            for item in form.get("LEXMeanings") or []
        }
        codes_fr = {
            item.get("LEXEntryCode")
            for form in fr.get("BaseForms") or []
            for item in form.get("LEXMeanings") or []
        }
        attested = set(rec["corroborating_ubs_ln_codes"])
        if not attested or not attested.issubset(codes & codes_fr) or not attested.issubset(set(rec["original_ln"].split())):
            raise ValueError("Original bilingual LN corroboration drift at " + wid)
        if not rec["original_strong"].isdigit() or not rec["original_reference"] or not rec["original_morph"]:
            raise ValueError("Original Greek source witness incomplete at " + wid)
        families[(nfc(rec["original_lemma"]), mid)].append({
            "word_id": wid,
            "reference": rec["original_reference"],
            "original_lemma": rec["original_lemma"],
            "original_strong": rec["original_strong"],
            "original_ln": rec["original_ln"],
            "original_class": rec["original_class"],
            "original_morph": rec["original_morph"],
            "attested_headword_ln_codes": sorted(attested),
        })
    if len(ids) != 5938 or count != {APPROVED: 5033, UNAPPROVED: 905}:
        raise ValueError("Source-reviewed/unapproved token inventory drift")
    records = []
    for (lemma, mid), words in families.items():
        en = by_en[mid]
        parts = sorted({
            p for form in en.get("BaseForms") or []
            for p in form.get("PartsOfSpeech") or []
        })
        records.append({
            "lemma_nfc": lemma,
            "ubs_main_id": mid,
            "ubs_original_lemma": en["Lemma"],
            "ubs_original_pos": parts,
            "original_word_count": len(words),
            "original_classes": dict(sorted(Counter(w["original_class"] for w in words).items())),
            "original_strong_counts": dict(sorted(Counter(w["original_strong"] for w in words).items())),
            "all_original_word_witnesses": words,
            "editorial_status": "UNAPPROVED_requires_separate_lexical_family_review",
            "contextual_sense_ids_selected": [],
        })
    records.sort(key=lambda r: (-r["original_word_count"], r["lemma_nfc"], r["ubs_main_id"]))
    return {
        "status": "PRIVATE_original_word_evidence_ONLY_no_editorial_promotion_no_publication",
        "source_editions": SOURCE_REVISIONS,
        "already_reviewed_pronoun_words_unchanged": 5033,
        "unapproved_words": 905,
        "unapproved_families": len(records),
        "contextual_ubs_sense_ids_inferred": 0,
        "publication_approved": False,
        "families": records,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "english", "french", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8-sig"))
    report = prepare(read(args.candidate), read(args.english), read(args.french))
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_REMAINING_905_SOURCE_EVIDENCE", json.dumps({
        "families": report["unapproved_families"],
        "words": report["unapproved_words"],
        "top_families": [
            {"lemma": r["lemma_nfc"], "main_id": r["ubs_main_id"], "words": r["original_word_count"],
             "parts_of_speech": r["ubs_original_pos"],
             "source_classes": r["original_classes"],
             "source_strong_counts": r["original_strong_counts"]}
            for r in report["families"][:30]
        ],
        "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
