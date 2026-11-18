#!/usr/bin/env python3
"""Generate a deterministic UBS Hebrew (EN/FR) to pinned Macula WLC bridge.

Links exact SDBH lexical sense IDs first, with a separate entry-only Strong
fallback. It never supplies dictionary prose or guesses a contextual sense.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

UBS_REVISION = "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"
MACULA_REVISION = "47db250bd55d0d8577f2a94fba114ef16c35b23c"
UBS_FILES = {
    "en": "dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-en.JSON",
    "fr": "dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-fr.JSON",
}
STRONG = re.compile(r"^([HA])0*([0-9]+)$")
MACULA_STRONG = re.compile(r"^[0-9]+$")
LEX_ID = re.compile(r"^[0-9]{15}$")


def senses(entry):
    for form in entry.get("BaseForms") or []:
        for sense in form.get("LEXMeanings") or []:
            yield sense


def signature(entry):
    """Compare identifiers, not independently translated explanatory fields."""
    return (
        entry["Lemma"],
        tuple(entry.get("StrongCodes") or []),
        tuple(sorted((str(s["LEXID"]), str(s.get("LEXEntryCode") or ""))
                     for s in senses(entry))),
    )


def build(english, french):
    if not isinstance(english, list) or not isinstance(french, list):
        raise ValueError("Expected UBS array of dictionary records")
    en = {e["MainId"]: e for e in english}
    fr = {e["MainId"]: e for e in french}
    if len(en) != len(english) or len(fr) != len(french):
        raise ValueError("Duplicate UBS MainId")
    if en.keys() != fr.keys():
        raise ValueError("Bilingual MainId inventories differ")
    drift = [key for key in en if signature(en[key]) != signature(fr[key])]
    if drift:
        raise ValueError(f"EN/FR lexical ID drift; refusing to infer bilingual identity: {drift[:10]} (total {len(drift)})")
    by_strong = defaultdict(set)
    by_sdbh = defaultdict(set)
    skipped = set()
    sense_assignments = 0
    for mid, entry in en.items():
        for raw in entry.get("StrongCodes") or []:
            m = STRONG.fullmatch(str(raw))
            if not m:
                skipped.add(str(raw))
                continue
            by_strong[f"{m.group(1)}{int(m.group(2))}"].add(mid)
        for sense in senses(entry):
            sid = str(sense["LEXID"])
            if not LEX_ID.fullmatch(sid):
                raise ValueError(f"Malformed UBS lexical sense identifier: {mid} {sid}")
            by_sdbh[sid].add(mid)
            sense_assignments += 1
    return {
        "format": "bsi-ubs-hebrew-lexical-crosswalk",
        "schema_version": 1,
        "languages": ["en", "fr"],
        "license": "CC BY-SA 4.0",
        "dictionary": {
            "name": "UBS Dictionary of Biblical Hebrew",
            "repository": "https://github.com/ubsicap/ubs-open-license",
            "revision": UBS_REVISION,
            "edition": "0.9.4",
            "paths": UBS_FILES,
        },
        "macula": {
            "repository": "https://github.com/Clear-Bible/macula-hebrew",
            "revision": MACULA_REVISION,
            "corpus": "wlc",
            "lookup": ["sdbh", "strongnumberx", "lang"],
        },
        "policy": {
            "sdbh": "exact_15_digit_original_source_sense_id",
            "strong": "entry_only_exact_language_specific_numeric_code",
            "unresolved": "return_all_candidates_never_guess_contextual_sense",
            "definitions": "not_redistributed_look_up_UBS_original_edition",
        },
        "statistics": {
            "shared_entries": len(en),
            "shared_senses": sense_assignments,
            "unique_sdbh_ids": len(by_sdbh),
            "indexed_strong_numbers": len(by_strong),
            "excluded_non_numeric_strong_codes": len(skipped),
        },
        "by_sdbh": {k: sorted(v) for k, v in sorted(by_sdbh.items())},
        "by_strong": {k: sorted(v) for k, v in sorted(by_strong.items())},
    }


def lookup(index, sdbh, strongnumberx, lang):
    """A sense ID is authoritative only on exact match; Strong is entry-only."""
    sdbh = str(sdbh or "").strip()
    raw_strong = str(strongnumberx or "").strip()
    lang = str(lang or "").strip()
    if sdbh and LEX_ID.fullmatch(sdbh):
        direct = index["by_sdbh"].get(sdbh, [])
        if direct:
            return {
                "status": "direct_sense_candidates" if len(direct) > 1 else "direct_sense",
                "entry_ids": list(direct),
                "sense_ids": [sdbh],
                "evidence": "macula_sdbh_exact",
            }
    if lang not in ("H", "A") or not MACULA_STRONG.fullmatch(raw_strong):
        return {"status": "no_verified_lexical_link", "entry_ids": [],
                "sense_ids": [], "evidence": "none"}
    key = f"{lang}{int(raw_strong)}"
    candidates = index["by_strong"].get(key, [])
    return {
        "status": ("no_entry_match" if not candidates else
                   "ambiguous_entry_only" if len(candidates) > 1 else
                   "entry_only"),
        "entry_ids": list(candidates),
        "sense_ids": [],
        "evidence": "macula_strong_exact_only" if candidates else "none",
    }


def audit(index, macula):
    count = Counter()
    sample = {"direct_sense": None, "entry_only": None, "no_entry_match": None}
    with macula.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        required = {"xml:id", "sdbh", "strongnumberx", "lang"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Macula WLC TSV lacks columns {sorted(required)}")
        for row in reader:
            if not row["xml:id"].startswith("o") or len(row["xml:id"]) != 13:
                raise ValueError(f"Malformed pinned original word: {row['xml:id']}")
            count["macula_words"] += 1
            if row["sdbh"].strip():
                count["macula_with_sdbh"] += 1
            outcome = lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])
            count[outcome["status"]] += 1
            if outcome["entry_ids"]:
                count["with_ubs_entry_candidates"] += 1
            if outcome["sense_ids"]:
                count["with_exact_ubs_sense_candidates"] += 1
            if len(outcome["entry_ids"]) > 1:
                count["ambiguous_ubs_entry_candidates"] += 1
            if len(outcome["sense_ids"]) > 1:
                count["multiple_lexical_sense_candidates"] += 1
            if outcome["status"] in sample and sample[outcome["status"]] is None:
                sample[outcome["status"]] = {
                    "word_id": row["xml:id"],
                    "sdbh": row["sdbh"], "lang": row["lang"],
                    "strongnumberx": row["strongnumberx"],
                    **outcome,
                }
    return dict(sorted(count.items())), sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--french", type=Path, required=True)
    parser.add_argument("--macula", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    en = json.loads(args.english.read_text(encoding="utf-8"))
    fr = json.loads(args.french.read_text(encoding="utf-8"))
    index = build(en, fr)
    coverage, sample = audit(index, args.macula)
    index["coverage"] = coverage
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n", encoding="utf-8")
    print("BSI_UBS_HEBREW_BUILD", json.dumps(index["statistics"], sort_keys=True))
    print("BSI_UBS_HEBREW_COVERAGE", json.dumps(coverage, sort_keys=True))
    print("BSI_UBS_HEBREW_SAMPLES", json.dumps(sample, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
