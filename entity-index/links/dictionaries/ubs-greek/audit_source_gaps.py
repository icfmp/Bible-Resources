#!/usr/bin/env python3
"""Audit every missing UBS 1.0 / Macula SBLGNT Greek lexical headword.

Read only exact, independent original upstream source witnesses. This script
does not edit the existing lexical index, the Greek corpus or UBS dictionaries.
The candidate words it emits are NOT editorially accepted correspondence
decisions or inferred contextual Louw–Nida senses.

Greek accents composed with different canonically equivalent Unicode code
points (for example ώ and ώ) may compare equal with NFC; originals are
always preserved exactly. Similar spelling after accent *stripping* is NOT
an acceptable lemma identity and is not used.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import runpy
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_index.py"))
NUMERIC = re.compile(r"[0-9]+\Z")
ORIGINAL_WORD_ID = re.compile(r"n[0-9]{11}\Z")
CODE = re.compile(r"[0-9]+\.[0-9]+[a-z]?\Z")
NAMES = ("dual_source_lemma_and_ln_candidate_unapproved",
         "nfc_lemma_only_no_attested_ubs_ln",
         "no_nfc_identical_ubs_lemma",
         "multiple_nfc_identical_ubs_headwords_unresolved",
         "unsupported_original_compound_strong")
COUNTS = {
    "original_macula_words": 137741,
    "existing_ubs_entry_words": 128090,
    "missing_original_word_entry": 9651,
    "dual_source_lemma_and_ln_candidate_unapproved": 5938,
    "nfc_lemma_only_no_attested_ubs_ln": 3249,
    "no_nfc_identical_ubs_lemma": 459,
    "multiple_nfc_identical_ubs_headwords_unresolved": 0,
    "unsupported_original_compound_strong": 5,
    "original_missing_families": 238,
}


def norm(lemma: str) -> str:
    return unicodedata.normalize("NFC", lemma)


def source_lexicon(english: list, french: list, baseline: dict):
    built = MOD["build"](english, french)
    if any(built[key] != baseline[key] for key in (
            "by_strong", "by_ln", "format", "schema_version", "dictionary",
            "macula", "statistics", "languages", "license")):
        raise ValueError("Frozen UBS Greek source inventory and existing index changed")
    entries = defaultdict(list)
    domains = {}
    for entry in english:
        if not entry.get("Lemma") or not entry.get("MainId"):
            raise ValueError("UBS lexical entry missing original lemma or ID")
        entries[norm(entry["Lemma"])].append(entry)
        codes = set()
        for sense in MOD["sense_records"](entry):
            value = sense.get("LEXEntryCode")
            if isinstance(value, str) and CODE.fullmatch(value):
                codes.add(value)
        domains[entry["MainId"]] = codes
    for value in entries.values():
        value.sort(key=lambda row: row["MainId"])
    return entries, domains


def classify(row, index, by_lemma, entry_ln):
    """Conservative classification; never creates an approved lexical link."""
    original_strong = row["strong"]
    existing = MOD["lookup"](index, original_strong, row["ln"])
    if existing["entry_ids"]:
        return "existing_ubs_entry_word", None, ()
    if existing["status"] == "unsupported_strong_structure":
        return "unsupported_original_compound_strong", None, ()
    candidates = by_lemma.get(norm(row["lemma"]), [])
    if not candidates:
        return "no_nfc_identical_ubs_lemma", None, ()
    if len(candidates) != 1:
        return "multiple_nfc_identical_ubs_headwords_unresolved", None, ()
    entry = candidates[0]
    verified_codes = tuple(sorted(
        {c for c in row["ln"].split()
         if CODE.fullmatch(c) and c in entry_ln[entry["MainId"]]}
    ))
    if verified_codes:
        return "dual_source_lemma_and_ln_candidate_unapproved", entry, verified_codes
    return "nfc_lemma_only_no_attested_ubs_ln", entry, ()


def audit(baseline, english, french, macula_tsv: Path):
    by_lemma, entry_ln = source_lexicon(english, french, baseline)
    summary = Counter()
    family_register = {}
    potential = {}
    observed_word_ids = set()
    raw_examples = defaultdict(list)
    with macula_tsv.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"xml:id", "ref", "class", "type", "lemma",
                    "strong", "ln", "morph"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError("Pinned Macula SBLGNT source columns have drifted")
        for row in reader:
            wid = row["xml:id"]
            if not ORIGINAL_WORD_ID.fullmatch(wid) or wid in observed_word_ids:
                raise ValueError("Original SBLGNT word ID malformed/duplicate: " + wid)
            observed_word_ids.add(wid)
            summary["original_macula_words"] += 1
            reason, entry, verified_codes = classify(
                row, baseline, by_lemma, entry_ln)
            if reason == "existing_ubs_entry_word":
                summary["existing_ubs_entry_words"] += 1
                continue
            summary["missing_original_word_entry"] += 1
            summary[reason] += 1
            k = (row["strong"], norm(row["lemma"]))
            if k not in family_register:
                family_register[k] = {
                    "original_strong": row["strong"],
                    "original_lemmas": set(),
                    "nfc_only_comparison_key": norm(row["lemma"]),
                    "original_source_occurrences": 0,
                    "reason_counts": Counter(),
                    "original_word_ids_sample": [],
                    "original_reference_samples": [],
                    "original_classes": Counter(),
                    "original_types": Counter(),
                    "source_ln_counts": Counter(),
                    "ubs_nfc_equal_headword_candidates": sorted({
                        e["MainId"] for e in by_lemma.get(norm(row["lemma"]), [])
                    }),
                    "candidate_ubs_source_strong_codes": {
                        e["MainId"]: e.get("StrongCodes") or []
                        for e in by_lemma.get(norm(row["lemma"]), [])
                    },
                    "single_ubs_candidate_original_lemma": (
                        entry["Lemma"] if entry is not None else None
                    ),
                }
            g = family_register[k]
            g["original_lemmas"].add(row["lemma"])
            g["original_source_occurrences"] += 1
            g["reason_counts"][reason] += 1
            g["original_classes"][row["class"]] += 1
            g["original_types"][row["type"]] += 1
            g["source_ln_counts"].update(row["ln"].split())
            if len(g["original_word_ids_sample"]) < 4:
                g["original_word_ids_sample"].append(wid)
                g["original_reference_samples"].append(row["ref"])
            if len(raw_examples[reason]) < 8:
                raw_examples[reason].append({
                    "original_word_id": wid,
                    "reference": row["ref"],
                    "original_strong": row["strong"],
                    "original_lemma": row["lemma"],
                    "original_ln": row["ln"],
                    "original_morph": row["morph"],
                    "candidate_main_id": entry["MainId"] if entry else None,
                    "corroborating_original_ln": list(verified_codes),
                })
            if reason == "dual_source_lemma_and_ln_candidate_unapproved":
                # Original source keys unchanged, and no contextual UBS LEXID.
                potential[wid] = {
                    "status": "source_candidate_NOT_editorially_approved",
                    "original_word_id": wid,
                    "original_reference": row["ref"],
                    "original_lemma": row["lemma"],
                    "original_strong": row["strong"],
                    "original_ln": row["ln"],
                    "original_class": row["class"],
                    "original_morph": row["morph"],
                    "ubs_main_id": entry["MainId"],
                    "ubs_original_lemma": entry["Lemma"],
                    "shared_attested_ln_codes": list(verified_codes),
                    "contextual_ubs_sense_id": None,
                }
    summary["original_missing_families"] = len(family_register)
    if any(summary[name] != value for name, value in COUNTS.items()):
        raise ValueError(
            "Pinned UBS Greek original-source census changed: " +
            json.dumps({k: [summary[k], v] for k, v in COUNTS.items()
                        if summary[k] != v}, sort_keys=True)
        )
    if sum(summary[name] for name in NAMES) != summary["missing_original_word_entry"]:
        raise ValueError("Greek missing-source family reason partition is incomplete")
    if len(potential) != summary[NAMES[0]]:
        raise ValueError("Unapproved source-word preview inventory drift")
    serial = []
    for (strong, lemma), g in family_register.items():
        serial.append({
            **g,
            "original_lemmas": sorted(g["original_lemmas"]),
            "reason_counts": dict(sorted(g["reason_counts"].items())),
            "original_classes": dict(sorted(g["original_classes"].items())),
            "original_types": dict(sorted(g["original_types"].items())),
            "source_ln_counts": dict(sorted(g["source_ln_counts"].items())),
        })
    serial.sort(key=lambda x: (
        -x["original_source_occurrences"], x["original_strong"],
        x["nfc_only_comparison_key"]))
    return {
        "schema_version": 1,
        "status": "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release",
        "source_editions": {
            "ubs_greek_edition": "1.0",
            "ubs_revision": MOD["UBS_REVISION"],
            "macula_sblgnt_revision": MOD["MACULA_REVISION"],
        },
        "methods": {
            "source_lemma_comparison": "Unicode_NFC_only_preserve_original",
            "strong_lookup": "existing_exact_numeric_only_no_guess",
            "ubs_headword_match": "exactly_one_NFC_equal_lemma",
            "source_ln": "at_least_one_exact_code_within_that_UBS_headword",
            "source_word_links_accepted": False,
            "contextual_ubs_sense_ids_inferred": 0,
            "source_text_or_annotations_modified": False,
        },
        "summary": dict(sorted(summary.items())),
        "reason_examples": dict(sorted(raw_examples.items())),
        "unmatched_families": serial,
        "unapproved_source_word_headword_preview": dict(sorted(potential.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("index", "english", "french", "macula", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    en = json.loads(args.english.read_text(encoding="utf-8-sig"))
    fr = json.loads(args.french.read_text(encoding="utf-8-sig"))
    report = audit(index, en, fr, args.macula)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True,
                   indent=2) + "\n", encoding="utf-8"
    )
    print("UBS_GREEK_SOURCE_GAP_REVIEW",
          json.dumps(report["summary"], sort_keys=True))
    for family in report["unmatched_families"][:25]:
        print("UBS_GREEK_ORIGINAL_FAMILY", json.dumps({
            "lemma": family["original_lemmas"],
            "strong": family["original_strong"],
            "occurrences": family["original_source_occurrences"],
            "reasons": family["reason_counts"],
            "ubs_headword_ids": family["ubs_nfc_equal_headword_candidates"],
        }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

