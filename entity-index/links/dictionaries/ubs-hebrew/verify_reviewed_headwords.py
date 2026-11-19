#!/usr/bin/env python3
"""Verify five reviewed cross-Strong UBS headword identities against pinned sources.

Manual lexical entry decisions are distinct from automatic index links. Never
infer a contextual LEXID/SDBH sense, or a universal H/A Strong equivalence.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

UBS_STRONG = re.compile(r"^([HA])0*([0-9]+)[a-z]?$")
ORIGINAL_STRONG = re.compile(r"^[0-9]+[a-z]?$")
DISPOSITION = "source_reviewed_ubs_headword_entry_only"


def norm(text):
    return unicodedata.normalize("NFC", text)


def family_key(row):
    return row["lang"], norm(row["lemma"]), row["original_strong"]


def verify_register(ledger, register):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported editorial disposition format")
    if ledger.get("source_editions") != register["source_editions"]:
        raise ValueError("Source revisions do not match pinned inventory")
    families = {family_key(f): f for f in register["families"]}
    reviewed = set()
    expected_words = {}
    occurrences = 0
    for d in ledger["decisions"]:
        k = family_key(d)
        if k in reviewed:
            raise ValueError("Duplicate reviewed lexical family")
        reviewed.add(k)
        f = families.get(k)
        if (f is None
                or f["reason"] != "different_strong_exact_attested_lemma"
                or f["ubs_candidate_entries"] != [d["ubs_candidate_main_id"]]):
            raise ValueError("Family absent, ambiguous, or candidate source changed")
        if (f["occurrences"] != d["original_occurrences"]
                or f["source_classes"] != d["original_source_classes"]
                or f["source_witnesses"] != d["original_word_witnesses"]):
            raise ValueError("Original lexical family witnesses/counts changed")
        if (d.get("disposition") != DISPOSITION
                or d.get("headword_identity_reviewed") is not True
                or d.get("contextual_sense_id_approved") is not False
                or d.get("index_word_links_applied") is not False
                or d.get("source_data_modified") is not False
                or not d.get("rationale")
                or not d.get("editorial_meaning")):
            raise ValueError("Unsafe or undocumented lexical disposition")
        ev = d.get("evidence", {})
        if (not ev.get("ubs_dictionary_page", "").startswith(
                "https://freely-given.org/OBD/UBS/Heb/")
                or not ev.get("ubs_cited_passage")):
            raise ValueError("Missing lexical sense and passage evidence")
        if d["lang"] not in ("H", "A") or not ORIGINAL_STRONG.fullmatch(d["original_strong"]):
            raise ValueError("Malformed original lexical family key")
        occurrences += d["original_occurrences"]
        for w in d["original_word_witnesses"]:
            wid = w["original_word_id"]
            if wid in expected_words:
                raise ValueError("Original MACULA witness reused")
            expected_words[wid] = (d, w)
    return {"families": len(reviewed), "occurrences": occurrences,
            "word_witnesses": expected_words}


def verify_dictionary(ledger, entries):
    by_id = {e["MainId"]: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate original UBS MainId")
    for d in ledger["decisions"]:
        entry = by_id.get(d["ubs_candidate_main_id"])
        if entry is None:
            raise ValueError("Reviewed original UBS headword disappeared")
        form_set = {norm(x) for x in (
            entry["Lemma"], *(entry.get("AlternateLemmas") or ()))
            if isinstance(x, str) and x}
        if norm(d["lemma"]) not in form_set:
            raise ValueError("UBS published canonical/alternate lemma changed")
        source_full_code = d["lang"] + d["original_strong"]
        codes = entry.get("StrongCodes") or []
        if source_full_code in codes:
            raise ValueError("Cross-Strong discrepancy no longer exists")
        # The source code difference is *not* made into a global Strong alias.
        if not any(UBS_STRONG.fullmatch(str(code)) for code in codes):
            raise ValueError("Missing valid pinned UBS Strong metadata")
        if not entry.get("BaseForms"):
            raise ValueError("UBS headword no longer has lexical form metadata")


def verify_macula(review, macula):
    pending = dict(review["word_witnesses"])
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            pair = pending.pop(row["xml:id"], None)
            if pair is None:
                continue
            d, w = pair
            if (
                row["lang"] != d["lang"]
                or norm(row["lemma"]) != norm(d["lemma"])
                or row["strongnumberx"] != d["original_strong"]
                or row["class"] not in d["original_source_classes"]
                or row["ref"] != w["reference"]
                or row["sdbh"] != w["original_sdbh"]
            ):
                raise ValueError("Original MACULA word differs: " + row["xml:id"])
    if pending:
        raise ValueError("Missing original MACULA word IDs: " + str(sorted(pending)))


def verify(ledger, register, entries, macula):
    review = verify_register(ledger, register)
    verify_dictionary(ledger, entries)
    verify_macula(review, macula)
    return {"families": review["families"], "occurrences": review["occurrences"],
            "word_witnesses": len(review["word_witnesses"])}


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
    if result != {"families": 17, "occurrences": 154, "word_witnesses": 41}:
        raise ValueError("Pinned editorial review counts unexpectedly changed")
    print("UBS_PINNED_REVIEWED_HEADWORDS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

