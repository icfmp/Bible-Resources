#!/usr/bin/env python3
"""Verify no-link decisions for original MACULA Hebrew source morphemes.

This checks exact source witnesses, original UBS headword inventories, and
source pins. An inherited composite Strong code never establishes identity
between a grammatical segment and the larger dictionary headword.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

UBS_STRONG = re.compile(r"^([HA])0*([0-9]+)[a-z]?$")
SOURCE_STRONG = re.compile(r"^([0-9]+)[a-z]?$")
DECISION = "retain_unlinked_source_morpheme_not_candidate_headword"


def nfc(text):
    return unicodedata.normalize("NFC", text)


def consonants(text):
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed
                   if not unicodedata.combining(c) or c in ("\u05c1", "\u05c2"))


def family_key(row):
    return row["lang"], nfc(row["lemma"]), row["original_strong"]


def verify_register(ledger, register):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported source morpheme ledger version")
    if ledger.get("source_editions") != register["source_editions"]:
        raise ValueError("Pinned source revision differs")
    family = {family_key(f): f for f in register["families"]}
    checked = set()
    word_ids = {}
    occurrences = 0
    for d in ledger["decisions"]:
        key = family_key(d)
        if key in checked:
            raise ValueError("Duplicate source morpheme family")
        checked.add(key)
        f = family.get(key)
        if f is None or f["reason"] != "same_strong_family_unresolved":
            raise ValueError("Unregistered or incompatible source morpheme family")
        if (len(f["ubs_candidate_entries"]) != 1
                or f["ubs_candidate_entries"][0] != d["ubs_candidate_entry_id"]
                or f["occurrences"] != d["original_occurrences"]
                or f["source_classes"] != d["source_classes"]
                or f["source_witnesses"] != d["source_word_witnesses"]):
            raise ValueError("Original WLC family or UBS candidate changed")
        if (d.get("decision") != DECISION
                or d.get("lexical_identity_approved") is not False
                or d.get("contextual_sense_approved") is not False
                or d.get("source_data_modified") is not False
                or not d.get("grammatical_role")
                or not d.get("rationale")):
            raise ValueError("Unjustified or unsafe original morpheme decision")
        occurrences += d["original_occurrences"]
        for witness in d["source_word_witnesses"]:
            wid = witness["original_word_id"]
            if wid in word_ids:
                raise ValueError("Original WLC word ID used in multiple decisions")
            word_ids[wid] = (d, witness)
    return {"families": len(checked), "occurrences": occurrences, "word_ids": word_ids}


def verify_ubs(ledger, entries):
    by_id = {e["MainId"]: e for e in entries}
    for d in ledger["decisions"]:
        e = by_id.get(d["ubs_candidate_entry_id"])
        if e is None:
            raise ValueError("Original UBS candidate no longer exists")
        source = SOURCE_STRONG.fullmatch(d["original_strong"])
        if source is None:
            raise ValueError("Unsupported source Strong syntax")
        number = int(source.group(1))
        if not any((m := UBS_STRONG.fullmatch(str(s)))
                   and m.group(1) == d["lang"]
                   and int(m.group(2)) == number
                   for s in (e.get("StrongCodes") or [])):
            raise ValueError("UBS candidate original Strong family changed")
        canonical_and_alternates = [e["Lemma"], *(e.get("AlternateLemmas") or [])]
        if any(isinstance(lemma, str) and
               consonants(lemma) == consonants(d["lemma"])
               for lemma in canonical_and_alternates):
            raise ValueError("Lexical surface now matches original morpheme")


def verify_macula(review, macula):
    pending = dict(review["word_ids"])
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            pair = pending.pop(row["xml:id"], None)
            if pair is None:
                continue
            d, witness = pair
            if (row["lang"] != d["lang"]
                    or nfc(row["lemma"]) != nfc(d["lemma"])
                    or row["strongnumberx"] != d["original_strong"]
                    or row["ref"] != witness["reference"]
                    or row["sdbh"] != witness["original_sdbh"]
                    or row["class"] not in d["source_classes"]):
                raise ValueError("Original MACULA word changed: " + row["xml:id"])
    if pending:
        raise ValueError("Missing original source morpheme witness: " + str(sorted(pending)))


def verify(ledger, register, entries, macula):
    result = verify_register(ledger, register)
    verify_ubs(ledger, entries)
    verify_macula(result, macula)
    return {"families": result["families"], "occurrences": result["occurrences"],
            "word_witnesses": len(result["word_ids"])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("register", "decisions", "english", "macula"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    result = verify(
        json.loads(args.decisions.read_text(encoding="utf-8")),
        json.loads(args.register.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        args.macula,
    )
    if result != {"families": 10, "occurrences": 27, "word_witnesses": 19}:
        raise ValueError("Pinned source morpheme batch coverage changed")
    print("UBS_SOURCE_SEGMENT_ABSTENTIONS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

