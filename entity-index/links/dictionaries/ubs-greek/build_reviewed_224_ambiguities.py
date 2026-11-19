#!/usr/bin/env python3
"""Source-review 220 original Greek word-specific lexical heads under ambiguous Strong.

The legacy original Strong index is NEVER narrowed. A separate private
source-word-ID overlay records which original UBS lexical headword is uniquely
attested by the original Greek lemma AND original UBS LN-domain evidence.
No contextual semantic sense / LEXID is selected.
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
AUDIT = runpy.run_path(str(HERE / "audit_224_ambiguities.py"))
STATUS = "source_reviewed_ambiguous_original_greek_word_lexical_headword_only"
REASON = "unique_original_nfc_lemma_and_ln_headword_witness"
POLICY = {
    "original_word_id_required": True,
    "preserve_all_original_ubs_strong_candidates": True,
    "require_unique_greek_nfc_headword_and_original_ln": True,
    "require_compatible_original_source_word_class": True,
    "no_global_strong_alias": True,
    "no_contextual_semantic_lexid": True,
    "no_original_source_mutation": True,
    "no_publication": True,
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def canonical(v):
    return (json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def original_parts(entry):
    return {str(p).lower().split(",", 1)[0].rstrip(".")
            for form in entry.get("BaseForms") or []
            for p in form.get("PartsOfSpeech") or []}


def plan(ledger, report):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "source_reviewed_original_word_specific_greek_ambiguous_Strong_headwords_private"
        or ledger.get("source_editions") != report["source_editions"]
        or ledger.get("editorial_policy") != POLICY
        or ledger.get("source_reviewed_ambiguous_original_word_headwords") != 220
        or ledger.get("original_words_still_ambiguous_unreviewed") != 4):
        raise ValueError("Greek 220-word ambiguity editorial source authorization drift")
    choices = {}
    for r in ledger["source_verified_unique_headword_families"]:
        key = (r["lemma_nfc"], r["source_strong"], r["ubs_main_id"])
        if (key in choices or nfc(r["lemma_nfc"]) != r["lemma_nfc"]
            or r["macula_class"] not in ("noun", "verb")
            or not r["source_strong"].isdigit()
            or len(r.get("editorial_basis", "")) < 180
            or not isinstance(r["original_word_count"], int)):
            raise ValueError("Unattested Greek ambiguous lexical headword editorial decision")
        choices[key] = r
    if len(choices) != 5 or sum(r["original_word_count"] for r in choices.values()) != 220:
        raise ValueError("Greek five-family original lexical evidence inventory drift")
    return choices


def build(candidate, source, classified, ledger, english, french):
    independently_checked = AUDIT["classify"](source)
    if independently_checked != classified:
        raise ValueError("Original 224 Greek ambiguity evidence register drift")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total") != 9152
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["editorial_candidate"].get("new_inferred_contextual_lexical_sense_ids") != 0):
        raise ValueError("Previously reviewed Greek candidate source/metadata drift")
    choices = plan(ledger, classified)
    en = {x["MainId"]: x for x in english}
    fr = {x["MainId"]: x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Original UBS Greek EN/FR headword identities drift")
    reviewed = {}
    totals = Counter()
    for word in classified["reason_witnesses"].get(REASON, []):
        mid_list = word["original_same_lemma_and_ln_ubs_main_ids"]
        if len(mid_list) != 1:
            raise ValueError("Unattested unique original Greek LN/lemma headword witness")
        mid = mid_list[0]
        key = (nfc(word["original_lemma"]), word["original_strong"], mid)
        decision = choices.get(key)
        wid = word["original_word_id"]
        if (not decision or wid in reviewed or wid in candidate["by_macula_word"]
            or word["original_class"] != decision["macula_class"]
            or word["original_lemma_matching_ubs_main_ids"] != [mid]
            or mid not in word["existing_original_ubs_main_ids"]
            or len(word["existing_original_ubs_main_ids"]) < 2
            or not word["matching_original_ubs_ln_codes_by_main_id"].get(mid)
            or not word["original_reference"] or not word["original_morph"]
            or nfc(en[mid]["Lemma"]) != key[0]
            or nfc(fr[mid]["Lemma"]) != key[0]):
            raise ValueError("Uncorroborated Greek original word-ID lexical headword: " + wid)
        expected_grammar = "noun" if decision["macula_class"] == "noun" else "verb"
        if not any(p.startswith(expected_grammar) for p in original_parts(en[mid])):
            raise ValueError("Original UBS Greek lexical headword POS contradicts source: " + mid)
        source_ln = set(word["original_ln"].split())
        en_ln = {
            x.get("LEXEntryCode")
            for form in en[mid].get("BaseForms") or []
            for x in form.get("LEXMeanings") or []
        }
        fr_ln = {
            x.get("LEXEntryCode")
            for form in fr[mid].get("BaseForms") or []
            for x in form.get("LEXMeanings") or []
        }
        matched = sorted(source_ln & en_ln & fr_ln)
        if not matched or matched != word["matching_original_ubs_ln_codes_by_main_id"][mid]:
            raise ValueError("Original Greek ambiguous lemma/LN corroboration differs from bilingual source")
        reviewed[wid] = {
            "entry_id": mid,
            "match_type": STATUS,
            "original_lemma": word["original_lemma"],
            "original_strong": word["original_strong"],
            "original_ln": word["original_ln"],
            "original_reference": word["original_reference"],
            "original_class": word["original_class"],
            "original_morph": word["original_morph"],
            "original_strong_ubs_main_ids_preserved": word["existing_original_ubs_main_ids"],
            "original_headword_ln_corroboration": matched,
        }
        totals[key] += 1
    if (len(reviewed) != 220 or set(totals) != set(choices)
        or any(totals[k] != choices[k]["original_word_count"] for k in choices)):
        raise ValueError("Original Greek 220-word-specific ambiguity review inventory incomplete")
    output = copy.deepcopy(candidate)
    output["by_macula_ambiguous_word"] = dict(sorted(reviewed.items()))
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "PRIVATE_220_source_reviewed_ambiguous_Strong_word_headwords_NOT_PUBLISHED",
        "original_strong_ambiguous_word_population_unchanged": 224,
        "reviewed_unique_original_ambiguity_word_headwords": 220,
        "remaining_original_word_headword_ambiguities": 4,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "editorial_source_original_ambiguities": "v1_reviewed_ambiguous_headwords.json",
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "preexisting_ambiguous_strong_entry_words_unchanged": 224,
        "reviewed_original_word_specific_ambiguous_strong_headwords": 220,
        "remaining_original_word_ambiguities": 4,
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    if (any(output[k] != candidate[k] for k in candidate
            if k not in ("editorial_candidate", "word_aware_coverage"))
        or output["by_macula_word"] != candidate["by_macula_word"]):
        raise ValueError("Greek original source or historical Strong maps mutated")
    return output


def lookup_reviewed_ambiguity(candidate, wid, reference, lemma, strong, ln, morph):
    row = (candidate.get("by_macula_ambiguous_word") or {}).get(wid)
    if not row:
        return {"status": "no_source_reviewed_ambiguity_entry", "entry_ids": [], "sense_ids": []}
    if any((row["original_reference"] != reference, row["original_lemma"] != lemma,
            row["original_strong"] != strong, row["original_ln"] != ln,
            row["original_morph"] != morph)):
        return {"status": "source_original_word_annotation_mismatch",
                "entry_ids": [], "sense_ids": []}
    if row["match_type"] != STATUS:
        return {"status": "unrecognized_ambiguity_review_status",
                "entry_ids": [], "sense_ids": []}
    return {"status": "source_reviewed_original_word_lexical_headword_only",
            "entry_ids": [row["entry_id"]], "sense_ids": [],
            "original_legacy_Strong_entry_ids_preserved":
                row["original_strong_ubs_main_ids_preserved"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "source", "classified", "ledger",
                 "english", "french", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8-sig"))
    out = build(read(a.candidate), read(a.source), read(a.classified),
                read(a.ledger), read(a.english), read(a.french))
    a.output.write_bytes(canonical(out))
    print("GREEK_220_ORIGINAL_WORD_LEXICAL_AMBIGUITY_HEADWORDS", json.dumps({
        "source_word_ambiguity_headwords_reviewed": 220,
        "preexisting_original_strong_ambiguity_candidates_preserved": 224,
        "unreviewed_original_word_ambiguities": 4,
        "new_source_unmatched_word_coverage": 0,
        "new_contextual_senses_inferred": 0,
        "published": False,
        "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
