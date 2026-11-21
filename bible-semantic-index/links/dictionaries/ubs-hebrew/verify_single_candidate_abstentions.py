#!/usr/bin/env python3
"""Verify independently documented, deliberately unlinked UBS sole candidates.

A lexical abstention is a source-bound review outcome, not a positive UBS
headword identity, a proof of nonidentity, or a contextual sense decision.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

UBS_STRONG = re.compile(r"^([HA])0*([0-9]+)([a-z]?)$")
SOURCE_STRONG = re.compile(r"^([0-9]+)([a-z]?)$")
RELATIONS = {
    "same_strong_family_unresolved",
    "different_strong_exact_attested_lemma",
    "different_strong_same_consonants",
}
OUTCOME = "reversible_single_candidate_identity_abstention"


def norm(text):
    return unicodedata.normalize("NFC", text)


def consonants(text):
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(char) or char in ("\u05c1", "\u05c2")
    )


def key(item):
    return item["lang"], norm(item["lemma"]), item["original_strong"]


def candidate_parts(entry):
    found = []
    for form in entry.get("BaseForms") or []:
        for part in form.get("PartsOfSpeech") or []:
            if part not in found:
                found.append(part)
    return found


def source_glosses(entry):
    return {
        gloss
        for form in entry.get("BaseForms") or []
        for sense in form.get("LEXMeanings") or []
        for translation in sense.get("LEXSenses") or []
        for gloss in translation.get("Glosses") or []
    }


def verify_register(ledger, register):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported lexical abstention format")
    if ledger.get("source_editions") != register["source_editions"]:
        raise ValueError("Pinned original source revisions changed")
    family = {key(item): item for item in register["families"]}
    seen = set()
    witnesses = {}
    occurrence_count = 0
    for decision in ledger["dispositions"]:
        k = key(decision)
        if k in seen:
            raise ValueError("Repeated lexical abstention family")
        seen.add(k)
        f = family.get(k)
        if (f is None or f["reason"] not in RELATIONS
                or f["ubs_candidate_entries"]
                != [decision["ubs_candidate"]["main_id"]]
                or decision.get("candidate_relation") != f["reason"]):
            raise ValueError("Unknown or changed sole UBS lexical candidate")
        if (decision["original_occurrences"] != f["occurrences"]
                or decision["original_source_classes"] != f["source_classes"]
                or decision["original_word_witnesses"] != f["source_witnesses"]):
            raise ValueError("Original source lexical family changed")
        first = decision["source_first_word"]
        if (first["word_id"] != f["source_witnesses"][0]["original_word_id"]
                or first["class"] not in f["source_classes"]
                or not isinstance(first["pos"], str)
                or not first["pos"]
                or not isinstance(first["english"], str)):
            raise ValueError("Original word source evidence invalid")
        if (decision.get("disposition") != OUTCOME
                or decision.get("lexical_identity_approved") is not False
                or decision.get("contextual_sense_approved") is not False
                or decision.get("index_word_links_applied") is not False
                or decision.get("source_data_modified") is not False
                or not decision.get("uncertainty_category")
                or len(decision.get("rationale") or "") < 60):
            raise ValueError("Unsafe or unexplained source lexical abstention")
        occurrence_count += f["occurrences"]
        for w in f["source_witnesses"]:
            wid = w["original_word_id"]
            if wid in witnesses:
                raise ValueError("Repeated original MACULA word ID")
            witnesses[wid] = (decision, w)

    return {
        "families": len(seen),
        "occurrences": occurrence_count,
        "word_witnesses": witnesses,
    }


def verify_ubs(ledger, entries):
    by_id = {entry["MainId"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Repeated source UBS MainId")
    for decision in ledger["dispositions"]:
        candidate = decision["ubs_candidate"]
        entry = by_id.get(candidate["main_id"])
        if entry is None:
            raise ValueError("Original UBS candidate disappeared")
        if (norm(entry["Lemma"]) != norm(candidate["lemma"])
                or entry["StrongCodes"] != candidate["strong_codes"]
                or candidate_parts(entry) != candidate["parts_of_speech"]
                or candidate["attested_gloss"] not in source_glosses(entry)):
            raise ValueError("Original UBS candidate metadata or meaning changed")
        source_code = SOURCE_STRONG.fullmatch(decision["original_strong"])
        if source_code is None or decision["lang"] not in ("H", "A"):
            raise ValueError("Unsupported original source Strong or language")
        numeric_family = any(
            (m := UBS_STRONG.fullmatch(str(raw)))
            and m.group(1) == decision["lang"]
            and int(m.group(2)) == int(source_code.group(1))
            for raw in entry.get("StrongCodes") or []
        )
        relation = decision["candidate_relation"]
        if relation == "same_strong_family_unresolved":
            if not numeric_family:
                raise ValueError("Original source Strong family no longer attested")
        else:
            if numeric_family:
                raise ValueError("Previously different-Strong candidate now shares source family")
            forms = [
                entry["Lemma"],
                *(entry.get("AlternateLemmas") or ()),
            ]
            if relation == "different_strong_exact_attested_lemma":
                if norm(decision["lemma"]) not in {norm(form) for form in forms if isinstance(form, str)}:
                    raise ValueError("Original exact UBS lemma evidence changed")
            elif relation == "different_strong_same_consonants":
                if consonants(decision["lemma"]) not in {
                    consonants(form) for form in forms if isinstance(form, str)
                }:
                    raise ValueError("Original UBS consonant evidence changed")
            else:
                raise ValueError("Unsupported original source review relation")


def verify_macula(review, macula):
    pending = dict(review["word_witnesses"])
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            pair = pending.pop(row["xml:id"], None)
            if pair is None:
                continue
            decision, witness = pair
            expected = (
                decision["lang"], norm(decision["lemma"]),
                decision["original_strong"], witness["reference"],
                witness["original_sdbh"],
            )
            actual = (
                row["lang"], norm(row["lemma"]), row["strongnumberx"],
                row["ref"], row["sdbh"],
            )
            if actual != expected or row["class"] not in decision["original_source_classes"]:
                raise ValueError("Pinned original MACULA witness changed: " + row["xml:id"])
            if row["xml:id"] == decision["source_first_word"]["word_id"]:
                original = decision["source_first_word"]
                if (row["english"], row["pos"], row["class"]) != (
                        original["english"], original["pos"], original["class"]):
                    raise ValueError("Original word English/POS witness changed: " + row["xml:id"])
    if pending:
        raise ValueError("Missing original MACULA source witnesses: " + str(sorted(pending)))


def verify(ledger, register, entries, macula):
    result = verify_register(ledger, register)
    verify_ubs(ledger, entries)
    verify_macula(result, macula)
    return {
        "families": result["families"],
        "occurrences": result["occurrences"],
        "word_witnesses": len(result["word_witnesses"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("register", "decisions", "english", "macula"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    result = verify(
        json.loads(args.decisions.read_text(encoding="utf-8")),
        json.loads(args.register.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        args.macula,
    )
    if result != {"families": 16, "occurrences": 25, "word_witnesses": 19}:
        raise ValueError("Frozen original single-candidate review count changed")
    print("UBS_PINNED_SOLE_CANDIDATE_ABSTENTIONS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

