#!/usr/bin/env python3
"""Source-witnessed read-only audit of the last 25+1 UBS WLC nonlinks.

The existing 16 sole-candidate families are *not* identity decisions:
inspect every original WLC token, source morphology and all original
candidate UBS headword glosses before applying any word-specific link.
No source content, generated candidate index, or original annotation
is modified by this report. All spellings remain source-original.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from pathlib import Path

CLASSES = {"noun", "verb", "adj", "adv", "num"}


def key(lang, lemma, strong):
    return (lang, unicodedata.normalize("NFC", lemma), strong)


def glosses(entry):
    return sorted({
        word
        for form in entry.get("BaseForms") or []
        for meaning in form.get("LEXMeanings") or []
        for translation in meaning.get("LEXSenses") or []
        for word in translation.get("Glosses") or []
        if isinstance(word, str) and word
    })


def run(ledger, additional, english, french, macula, base=None):
    entries_en = {e["MainId"]: e for e in english}
    entries_fr = {e["MainId"]: e for e in french}
    if len(entries_en) != len(english) or set(entries_en) != set(entries_fr):
        raise ValueError("Changed original UBS bilingual entry inventory")
    original = {}
    for d in ledger["dispositions"]:
        k = key(d["lang"], d["lemma"], d["original_strong"])
        if k in original:
            raise ValueError("Repeated original WLC candidate family")
        original[k] = d
    if len(original) != 16 or sum(d["original_occurrences"] for d in original.values()) != 25:
        raise ValueError("Original sole-candidate family/word population changed")

    prior = additional["unresolved_source_word_abstentions"]
    if len(prior) != 1:
        raise ValueError("Expected one independently source-reviewed residual word")
    hold = prior[0]
    hold_id = hold["word_id"]
    if not isinstance(hold_id, str) or hold_id[:1] != "o":
        raise ValueError("Malformed original residual word identifier")

    source = []
    previously_linked_words_excluded = 0
    lookup_word = runpy.run_path(str(Path(__file__).with_name("build_index.py")))["lookup_word"]
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            k = key(row["lang"], row["lemma"], row["strongnumberx"])
            if k not in original and row["xml:id"] != hold_id:
                continue
            if row["class"] not in CLASSES:
                raise ValueError("Missing original lexical word classification")
            if base:
                old = lookup_word(base, row["xml:id"], row["sdbh"],
                                  row["strongnumberx"], row["lang"], row["lemma"])
                if old["entry_ids"]:
                    if row["xml:id"] == hold_id:
                        raise ValueError("Source-held Raphah word already has a headword")
                    previously_linked_words_excluded += 1
                    continue
            data = {
                "word_id": row["xml:id"],
                "reference": row["ref"],
                "lemma_original": row["lemma"],
                "lang": row["lang"],
                "strong_original": row["strongnumberx"],
                "sdbh_original": row["sdbh"],
                "class_original": row["class"],
                "pos_original": row["pos"],
                "morph_original": row["morph"],
                "english_original": row["english"],
                "gloss_original": row.get("gloss", ""),
                "source_family": ("sole_candidate_identity_unverified"
                                  if k in original else "giant_or_named_rapha_unverified"),
            }
            if row["xml:id"] == hold_id:
                if row["ref"] != hold["reference"] or row["english"] != hold["original_english"]:
                    raise ValueError("Original giant/Raphah source witness changed")
                data["abstention_reason"] = hold["reason"]
            else:
                d = original[k]
                data["candidate_id"] = d["ubs_candidate"]["main_id"]
                data["uncertainty_category"] = d["uncertainty_category"]
            source.append(data)

    if len(source) != 26 or len({r["word_id"] for r in source}) != 26:
        cases = {str(k): sum(key(r["lang"], r["lemma_original"], r["strong_original"]) == k for r in source) for k in original}
        raise ValueError(f"Original residual lexical source inventory not exactly 26: found {len(source)} words; giant present: {any(r['word_id'] == hold_id for r in source)}; source family counts: {cases}")
    for d in original.values():
        tokens = [r for r in source
                  if key(r["lang"], r["lemma_original"], r["strong_original"]) ==
                  key(d["lang"], d["lemma"], d["original_strong"])]
        if len(tokens) != d["original_occurrences"]:
            raise ValueError("Source family occurrence drift")
        first = d["source_first_word"]
        first_token = next((t for t in tokens if t["word_id"] == first["word_id"]), None)
        if first_token is None or any(first_token[k] != first[v] for k, v in (
            ("english_original", "english"), ("pos_original", "pos"),
            ("class_original", "class"))):
            raise ValueError("Original first word witness changed")

    candidate = []
    for d in original.values():
        mid = d["ubs_candidate"]["main_id"]
        en, fr = entries_en[mid], entries_fr[mid]
        if (en["Lemma"] != d["ubs_candidate"]["lemma"]
                or en["StrongCodes"] != d["ubs_candidate"]["strong_codes"]):
            raise ValueError("Original UBS dictionary headword drift")
        candidate.append({
            "family": {"lang": d["lang"], "lemma": d["lemma"],
                       "strong": d["original_strong"]},
            "main_id": mid,
            "headword_original": en["Lemma"],
            "strong_codes_original": en["StrongCodes"],
            "english_headword_glosses_original": glosses(en),
            "french_headword_glosses_original": glosses(fr),
            "uncertainty_category": d["uncertainty_category"],
            "rationale": d["rationale"],
        })

    return {
        "schema_version": 1,
        "status": "original_source_read_only_evidence_not_editorial_acceptance",
        "source_editions": ledger["source_editions"],
        "summary": {
            "sole_candidate_families": len(original),
            "same_lexical_family_source_words_already_linked": previously_linked_words_excluded,
            "sole_candidate_words": len(source) - 1,
            "individually_unlinked_rapha_words": 1,
            "original_word_records_verified": len(source),
            "inferred_contextual_senses": 0,
        },
        "source_words": sorted(source, key=lambda x: x["word_id"]),
        "ubs_headword_candidates": sorted(candidate, key=lambda x: x["main_id"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("single", "additional", "english", "french", "macula", "index", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = run(
        json.loads(args.single.read_text(encoding="utf-8")),
        json.loads(args.additional.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        json.loads(args.french.read_text(encoding="utf-8")),
        args.macula,
        json.loads(args.index.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False,
                                      sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("UBS_LAST_26_SOURCE_WITNESSES", result["summary"])
    for rec in result["source_words"]:
        print("UBS_LAST_WORD", json.dumps({
            key: rec.get(key) for key in (
                "word_id", "reference", "lemma_original", "strong_original",
                "class_original", "pos_original", "english_original",
                "gloss_original", "candidate_id")
        }, ensure_ascii=False, sort_keys=True))
    for entry in result["ubs_headword_candidates"]:
        print("UBS_LAST_HEADWORD", json.dumps({
            "main_id": entry["main_id"], "family": entry["family"],
            "glosses": entry["english_headword_glosses_original"],
        }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

