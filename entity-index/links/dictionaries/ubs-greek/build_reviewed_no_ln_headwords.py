#!/usr/bin/env python3
"""Review a source-attested UBS Greek headword with no published LEXMeanings.

Only exact, individually verified original MACULA Greek word IDs are accepted.
Original Strong, morphology, Greek text, verse and Louw–Nida annotations remain
unchanged. No contextual UBS sense, global Strong alias, SWORD or release.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import runpy
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = runpy.run_path(str(HERE / "audit_eimi_disposition.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))
NEW = "source_reviewed_original_greek_entry_only_without_ubs_ln"
REV = "source_reviewed_original_greek_headword_batch2_only"
PRON = "source_reviewed_original_greek_pronoun_headword_only"
PENDING = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
EXPECTED_POLICY = {
    "require_exact_original_word_id": True,
    "require_nfc_original_lemma_identity": True,
    "require_original_source_morphology_and_class": True,
    "require_unique_bilingual_ubs_headword": True,
    "require_original_ubs_headword_no_lexmeanings": True,
    "preserve_original_strong_codes": True,
    "never_infer_contextual_ubs_lexid": True,
    "no_global_strong_aliases": True,
    "publication_approved": False,
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def review_ledger(ledger, report, english, french):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "source_attested_entry_only_without_ubs_ln_private_not_published"
        or ledger.get("editorial_policy") != EXPECTED_POLICY
        or ledger.get("source_editions") != report.get("source_editions")
        or ledger.get("previously_source_reviewed_headword_words") != 5610
        or ledger.get("additional_source_reviewed_entry_only_words") != 2031
        or len(ledger.get("reviewed_headword_families", [])) != 1):
        raise ValueError("Greek entry-only editorial approval or edition drift")
    review = ledger["reviewed_headword_families"][0]
    if (review.get("lemma_nfc") != "εἰμί"
        or review.get("original_ubs_strong") != "G2258"
        or review.get("original_macula_class") != "verb"
        or review.get("original_ubs_pos") != "verb"
        or review.get("original_source_unmatched_words") != 2031
        or len(review.get("rationale", "")) < 170):
        raise ValueError("Greek entry-only source/headword decision is not explicitly approved")
    disposition = AUDIT["audit"](report, english, french)
    if disposition["original_missing_word_occurrences"] != 2031:
        raise ValueError("Original Greek source gap population differs from review ledger")
    mid = disposition["original_ubs_main_id"]
    en = next(e for e in english if e["MainId"] == mid)
    fr = next(e for e in french if e["MainId"] == mid)
    for e, expected in ((en, "verb"), (fr, "verbe")):
        pos = {str(p).lower().rstrip(".") for form in e.get("BaseForms") or []
               for p in form.get("PartsOfSpeech") or []}
        if expected not in pos:
            raise ValueError("Original UBS Greek lexical POS not attested in source language: " + repr(sorted(pos)))
    return review, mid, disposition


def validate_original_word(row, mid, review, baseline, source_strongs):
    if (nfc(row["lemma"]) != review["lemma_nfc"]
        or row["class"] != review["original_macula_class"]
        or not row["morph"] or not row["ref"] or not row["xml:id"]
        or not row["strong"].isdigit()
        or row["strong"] not in source_strongs
        or BUILD["lookup"](baseline, row["strong"], row["ln"])["entry_ids"]):
        raise ValueError("Unattested original Greek entry-only source word: " + repr(row.get("xml:id")))
    return {
        "entry_id": mid,
        "match_type": NEW,
        "original_lemma": row["lemma"],
        "original_strong": row["strong"],
        "original_ln": row["ln"],
        "original_reference": row["ref"],
        "original_class": row["class"],
        "original_morph": row["morph"],
        "corroborating_ubs_ln_codes": [],
    }


def review(original, baseline, report, english, french, ledger, macula):
    if (original["editorial_candidate"].get("reviewed_original_headword_words_total") != 5610
        or original["editorial_candidate"].get("other_original_words_still_unapproved") != 328
        or original["editorial_candidate"].get("publication_approved") is not False
        or original["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0):
        raise ValueError("Previous Greek original-source editorial approval drift")
    policy, mid, disposition = review_ledger(ledger, report, english, french)
    expected_strongs = disposition["original_word_strong_distribution"]
    words = {}
    counts = Counter()
    seen = set()
    inventory = 0
    with macula.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            wid = row["xml:id"]
            if wid in seen:
                raise ValueError("Duplicate original Greek MACULA word ID")
            seen.add(wid)
            inventory += 1
            if nfc(row["lemma"]) != policy["lemma_nfc"]:
                continue
            if BUILD["lookup"](baseline, row["strong"], row["ln"])["entry_ids"]:
                continue
            item = validate_original_word(row, mid, policy, baseline, expected_strongs)
            if wid in original["by_macula_word"]:
                raise ValueError("Original Greek εἰμί entry-only source overlaps reviewed or pending LN candidate")
            words[wid] = item
            counts[row["strong"]] += 1
    if inventory != 137741 or len(words) != 2031 or dict(sorted(counts.items())) != expected_strongs:
        raise ValueError("Full original Greek source word IDs / εἰμί Strong distribution drift")
    output = copy.deepcopy(original)
    output["by_macula_word"].update(words)
    output["by_macula_word"] = dict(sorted(output["by_macula_word"].items()))
    kinds = Counter(x["match_type"] for x in output["by_macula_word"].values())
    if kinds != {PRON: 5033, REV: 577, PENDING: 328, NEW: 2031}:
        raise ValueError("Original Greek source word candidate classification drift")
    if any(output[k] != original[k] for k in baseline):
        raise ValueError("Existing UBS Greek baseline/index was mutated")
    if any(output["by_macula_word"][wid] != rec for wid, rec in original["by_macula_word"].items()):
        raise ValueError("Original Greek earlier editorial approval mutated")
    output["editorial_candidate"] = {
        **original["editorial_candidate"],
        "status": "PRIVATE_original_source_reviewed_without_ubs_ln_NOT_PUBLISHED",
        "editorial_acceptance": "exact_original_word_ids_with_headword_evidence_only",
        "new_original_entry_only_no_ln_approvals": 2031,
        "reviewed_original_headword_words_total": 7641,
        "other_original_words_still_unapproved": 328,
        "original_source_remaining_no_ln_words": 1218,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
        "editorial_source_entry_only": "v1_reviewed_no_ln_headwords.json",
    }
    output["word_aware_coverage"] = {
        **original["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 7641,
        "existing_strong_entry_candidate_words_unchanged": 128090,
        "word_aware_entry_candidate_words": 136059,
        "remaining_no_ubs_headword_candidate_original_words": 1682,
        "new_source_original_word_entry_only_without_ln": 2031,
        "original_gap_classes_still_unlinked": {
            "nfc_lemma_only_no_attested_ubs_ln": 1218,
            "no_nfc_identical_ubs_lemma": 459,
            "unsupported_original_compound_strong": 5,
        },
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "index", "report", "english", "french", "ledger", "macula", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    output = review(read(args.candidate), read(args.index), read(args.report),
                    read(args.english), read(args.french), read(args.ledger), args.macula)
    args.output.write_bytes(canonical(output))
    print("UBS_GREEK_VERIFIED_ENTRY_ONLY_NO_LN", json.dumps({
        "new_original_word_id_headwords": 2031,
        "total_extra_editorially_reviewed_original_words": 7641,
        "reviewed_lexical_headword_coverage": 135731,
        "source_words_total": 137741,
        "original_source_lemma_only_no_ln_still_unlinked": 1218,
        "strict_ln_candidate_words_unapproved": 328,
        "new_contextual_sense_ids": 0,
        "published": False,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
