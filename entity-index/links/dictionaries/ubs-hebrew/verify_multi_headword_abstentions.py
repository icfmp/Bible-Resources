#!/usr/bin/env python3
"""Verify editorial abstentions for multi-headword UBS Hebrew lexical families.

Abstaining does not accept a lexical identity or contextual sense. Keep the
generated family register unchanged and check the exact original witnesses.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

UBS_STRONG = re.compile(r"([HA])0*([0-9]+)[a-z]?$")
SOURCE_STRONG = re.compile(r"([0-9]+)[a-z]?$")
DISPOSITION = "retain_unlinked_ambiguous_headword_choice"
RELATIONS = {
    "same_strong_family_unresolved": "same_strong_numeric_family",
    "different_strong_same_consonants": "same_consonants_different_strong_family",
}


def consonants(value):
    """Compare Hebrew consonants without conflating shin and sin letters."""
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(
        char for char in decomposed
        if not unicodedata.combining(char) or char in ("\u05c1", "\u05c2")
    )


def key(row):
    return (row["lang"], unicodedata.normalize("NFC", row["lemma"]),
            row["original_strong"])


def verify_register(ledger, register):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported multi-headword abstention schema")
    if ledger.get("source_editions") != register["source_editions"]:
        raise ValueError("Original source editions changed")
    expected = {
        key(f): f for f in register["families"]
        if f["reason"] in RELATIONS
        and len(f["ubs_candidate_entries"]) > 1
    }
    decisions = ledger["dispositions"]
    if len(decisions) != len(expected):
        raise ValueError("Missing or additional multi-headword abstentions")
    seen = set()
    word_ids = set()
    total = 0
    for d in decisions:
        k = key(d)
        if k in seen or k not in expected:
            raise ValueError("Duplicate or unexpected original family key")
        seen.add(k)
        f = expected[k]
        if (d["original_occurrences"] != f["occurrences"]
                or d["ubs_candidate_entries"] != f["ubs_candidate_entries"]
                or d["source_classes"] != f["source_classes"]
                or d.get("candidate_relation") != RELATIONS[f["reason"]]):
            raise ValueError("Candidate set or original source counts changed")
        if d["original_word_witness"] not in f["source_witnesses"]:
            raise ValueError("Original MACULA witness changed")
        if (d.get("disposition") != DISPOSITION
                or d.get("lexical_identity_approved") is not False
                or d.get("contextual_sense_approved") is not False
                or d.get("source_data_modified") is not False
                or not d.get("rationale")):
            raise ValueError("Unjustified or unsafe lexical approval")
        word_id = d["original_word_witness"]["original_word_id"]
        if word_id in word_ids:
            raise ValueError("Original source word assigned twice")
        word_ids.add(word_id)
        total += d["original_occurrences"]
    if seen != set(expected):
        raise ValueError("Unrecorded multi-headword family")
    return {"families": len(seen), "occurrences": total, "word_ids": word_ids}


def verify_ubs(ledger, entries):
    by_id = {e["MainId"]: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate pinned UBS MainId")
    for d in ledger["dispositions"]:
        match = SOURCE_STRONG.fullmatch(d["original_strong"])
        if match is None:
            raise ValueError("Invalid original Strong syntax")
        numeric = int(match.group(1))
        for candidate_id in d["ubs_candidate_entries"]:
            entry = by_id.get(candidate_id)
            if entry is None:
                raise ValueError("UBS candidate not in pinned dictionary")
            codes = entry.get("StrongCodes") or []
            matches_numeric = any(
                (m := UBS_STRONG.fullmatch(str(raw)))
                and m.group(1) == d["lang"]
                and int(m.group(2)) == numeric for raw in codes
            )
            if d["candidate_relation"] == "same_strong_numeric_family":
                if not matches_numeric:
                    raise ValueError("UBS candidate no longer shares original Strong family")
            else:
                if matches_numeric:
                    raise ValueError("Cross-Strong UBS candidate unexpectedly shares source family")
                forms = [entry["Lemma"], *(entry.get("AlternateLemmas") or [])]
                if not any(isinstance(form, str)
                           and consonants(form) == consonants(d["lemma"])
                           for form in forms):
                    raise ValueError("UBS candidate original consonants no longer match")


def verify_macula(ledger, macula):
    pending = {
        d["original_word_witness"]["original_word_id"]: d
        for d in ledger["dispositions"]
    }
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            d = pending.pop(row["xml:id"], None)
            if d is None:
                continue
            w = d["original_word_witness"]
            actual = (row["lang"], unicodedata.normalize("NFC", row["lemma"]),
                      row["strongnumberx"], row["ref"], row["sdbh"])
            expected = (d["lang"], unicodedata.normalize("NFC", d["lemma"]),
                        d["original_strong"], w["reference"], w["original_sdbh"])
            if actual != expected or row["class"] not in d["source_classes"]:
                raise ValueError("Original MACULA word witness differs: " + row["xml:id"])
    if pending:
        raise ValueError("Missing original MACULA witnesses: " + str(sorted(pending)))


def verify(ledger, register, entries, macula):
    result = verify_register(ledger, register)
    verify_ubs(ledger, entries)
    verify_macula(ledger, macula)
    return {k: v for k, v in result.items() if k != "word_ids"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("register", "decisions", "english", "macula"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    result = verify(
        json.loads(args.decisions.read_text(encoding="utf-8")),
        json.loads(args.register.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        args.macula,
    )
    if result != {"families": 48, "occurrences": 458}:
        raise ValueError("Pinned multi-headword abstention count changed")
    print("UBS_SOURCE_PINNED_AMBIGUOUS_ABSTENTIONS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

