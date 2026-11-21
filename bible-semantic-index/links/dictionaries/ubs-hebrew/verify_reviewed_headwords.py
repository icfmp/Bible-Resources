#!/usr/bin/env python3
"""Verify manually reviewed UBS headword identities against pinned sources.

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
VALID_REASONS = {
    "different_strong_exact_attested_lemma",
    "different_strong_same_consonants",
    "same_strong_family_unresolved",
}


def consonants(text):
    """Compare Hebrew consonants with original shin/sin identity retained."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        char for char in decomposed
        if not unicodedata.combining(char) or char in ("\u05c1", "\u05c2")
    )


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
                or f["reason"] not in VALID_REASONS
                or d.get("candidate_relation") != f["reason"]
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
                or not ev.get("ubs_cited_passage")
                or not ev.get("ubs_attested_gloss")):
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
        forms = [entry["Lemma"], *(entry.get("AlternateLemmas") or ())]
        form_set = {norm(x) for x in forms if isinstance(x, str) and x}
        source_number = int(re.match(r"^[0-9]+", d["original_strong"]).group(0))
        source_family = any(
            (m := UBS_STRONG.fullmatch(str(code)))
            and m.group(1) == d["lang"]
            and int(m.group(2)) == source_number
            for code in (entry.get("StrongCodes") or [])
        )
        relation = d["candidate_relation"]
        if relation == "same_strong_family_unresolved":
            if not source_family:
                raise ValueError("Pinned UBS numeric Strong family changed")
        else:
            if source_family:
                raise ValueError("Different-Strong original family now shares numeric Strong")
            if relation == "different_strong_exact_attested_lemma":
                if norm(d["lemma"]) not in form_set:
                    raise ValueError("UBS published canonical/alternate lemma changed")
            elif relation == "different_strong_same_consonants":
                if not any(isinstance(form, str) and
                           consonants(form) == consonants(d["lemma"])
                           for form in forms):
                    raise ValueError("UBS consonantal candidate changed")
            else:
                raise ValueError("Unsupported reviewed lexical candidate relation")
        if not entry.get("BaseForms"):
            raise ValueError("UBS headword no longer has lexical form metadata")
        glosses = {
            gloss
            for form in entry["BaseForms"]
            for sense in (form.get("LEXMeanings") or [])
            for language in (sense.get("LEXSenses") or [])
            for gloss in (language.get("Glosses") or [])
        }
        if d["evidence"]["ubs_attested_gloss"] not in glosses:
            raise ValueError("Reviewed meaning absent from pinned UBS lexical source")


def verify_macula(review, macula):
    pending = dict(review["word_witnesses"])
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            pair = pending.pop(row["xml:id"], None)
            if pair is None:
                continue
            d, w = pair
            # Optional independently transcribed source English is checked
            # only for the first pinned word witness of a reviewed family.
            if (row["xml:id"] == d["original_word_witnesses"][0]["original_word_id"]
                    and "original_word_english" in d["evidence"]
                    and row["english"] != d["evidence"]["original_word_english"]):
                raise ValueError("Original MACULA English witness changed: " + row["xml:id"])
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
    if result != {"families": 81, "occurrences": 274, "word_witnesses": 139}:
        raise ValueError("Pinned editorial review counts unexpectedly changed")
    print("UBS_PINNED_REVIEWED_HEADWORDS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

