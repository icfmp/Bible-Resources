#!/usr/bin/env python3
"""Recheck source-pinned editorial *rejections*, never create a UBS lexeme link.

A mismatched POS/gloss is evidence for manual nonidentity reasoning, not a
general rule for automatically rejecting other lexemes. The editorial ledger
is deliberate; this program checks its exact original witnesses and UBS
headword metadata so an edition change cannot silently keep the decision.
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from pathlib import Path


VALID_REASONS = {
    "different_strong_same_consonants",
    "different_strong_exact_attested_lemma",
    "same_strong_family_unresolved",
}


def norm(value):
    return unicodedata.normalize("NFC", value)


def key(row):
    return row["lang"], norm(row["lemma"]), row["original_strong"]


def parts(entry):
    result = []
    for form in entry.get("BaseForms", []):
        for pos in form.get("PartsOfSpeech") or []:
            if pos not in result:
                result.append(pos)
    return result


def verify_metadata(ledger, register, entries):
    if ledger["source_editions"] != register["source_editions"]:
        raise ValueError("Source revisions differ from pinned lexical family register")
    if ledger["schema_version"] != 1:
        raise ValueError("Unsupported editorial ledger format")
    families = {key(f): f for f in register["families"]}
    by_id = {e["MainId"]: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate original UBS headword MainId")
    checked = set()
    total = 0
    ids = set()
    for d in ledger["decisions"]:
        k = key(d)
        if k in checked:
            raise ValueError("Duplicate editorial family decision")
        checked.add(k)
        f = families.get(k)
        if (not f or f["reason"] not in VALID_REASONS
                or d.get("candidate_relation", f["reason"]) != f["reason"]):
            raise ValueError("Decision does not concern a source-classified unresolved lexical family")
        if f["occurrences"] != d["occurrences"]:
            raise ValueError("Original family occurrence count changed")
        if d.get("decision") != "candidate_lexical_nonidentity" or not d.get("rationale"):
            raise ValueError("Unexplained or unsupported editorial conclusion")
        w = d["source_witness"]
        if not any(
            w["word_id"] == x["original_word_id"]
            and w["reference"] == x["reference"]
            and ("original_sdbh" not in w
                 or w["original_sdbh"] == x["original_sdbh"])
            for x in f["source_witnesses"]
        ):
            raise ValueError("Witness not in pinned unresolved family")
        candidate = d["ubs_candidate"]
        mid = candidate["main_id"]
        if f["ubs_candidate_entries"] != [mid]:
            raise ValueError("Not an exhaustive sole-candidate rejection")
        entry = by_id.get(mid)
        if entry is None:
            raise ValueError("UBS candidate headword no longer exists")
        if norm(entry["Lemma"]) != norm(candidate["lemma"]):
            raise ValueError("UBS original candidate lemma changed")
        if entry["StrongCodes"] != candidate["strong_codes"]:
            raise ValueError("UBS original candidate Strong metadata changed")
        if parts(entry) != candidate["parts_of_speech"]:
            raise ValueError("UBS original candidate POS metadata changed")
        if d["lang"] + d["original_strong"] in entry["StrongCodes"]:
            raise ValueError("Original Strong unexpectedly matches UBS candidate")
        # The actual published UBS gloss is an evidence anchor, not a
        # machine rule for no-link status or a contextual sense assignment.
        if d.get("ubs_attested_gloss"):
            observed = {
                gloss
                for form in (entry.get("BaseForms") or [])
                for sense in (form.get("LEXMeanings") or [])
                for detail in (sense.get("LEXSenses") or [])
                for gloss in (detail.get("Glosses") or [])
            }
            if d["ubs_attested_gloss"] not in observed:
                raise ValueError("UBS lexical meaning evidence changed")
        total += d["occurrences"]
        ids.add(w["word_id"])
    return {"families": len(checked), "occurrences": total, "word_ids": ids}


def verify_witness_words(ledger, macula):
    pending = {d["source_witness"]["word_id"]: d for d in ledger["decisions"]}
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            source_id = row["xml:id"]
            if source_id not in pending:
                continue
            d = pending.pop(source_id)
            w = d["source_witness"]
            expected = {
                "lang": d["lang"],
                "lemma": d["lemma"],
                "strongnumberx": d["original_strong"],
                "ref": w["reference"],
                "english": w["english"],
                "pos": w["pos"],
                "class": w["class"],
            }
            if "original_sdbh" in w:
                expected["sdbh"] = w["original_sdbh"]
            for col, wanted in expected.items():
                actual = row[col]
                if (norm(actual) if col == "lemma" else actual) != (
                    norm(wanted) if col == "lemma" else wanted
                ):
                    raise ValueError(f"Original MACULA witness changed: {source_id} {col}")
    if pending:
        raise ValueError(f"Pinned MACULA word IDs not present: {sorted(pending)}")


def verify(ledger, register, entries, macula):
    result = verify_metadata(ledger, register, entries)
    verify_witness_words(ledger, macula)
    return {k: v for k, v in result.items() if k != "word_ids"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("register", "decisions", "english", "macula"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    result = verify(
        json.loads(args.decisions.read_text(encoding="utf-8")),
        json.loads(args.register.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        args.macula,
    )
    print("UBS_SOURCE_PINNED_NONIDENTITY_DISPOSITIONS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
