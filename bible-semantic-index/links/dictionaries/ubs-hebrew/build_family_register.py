#!/usr/bin/env python3
"""Reproducible v1 family register for every unresolved UBS Hebrew WLC lexeme.

Automated *triage* is never editorial approval: no new crosswalk entries are
written. Group by original source (language, NFC lemma, full Strong code).
All original corpus references are counted; representative witnesses remain.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from runpy import run_path

# GitHub workflow executes with python -I: resolve sibling source utilities
# explicitly rather than relying on an ambient PYTHONPATH.
_scope = run_path(str(Path(__file__).with_name("audit_dictionary_scope.py")))
_build = run_path(str(Path(__file__).with_name("build_index.py")))
inventory = _scope["inventory"]
consonants = _scope["consonants"]
LEXICAL_CLASSES = _scope["LEXICAL_CLASSES"]
MACULA_STRONG = _scope["MACULA_STRONG"]
lookup_word = _build["lookup_word"]

STATUSES = {
    "unattested_indexed_headword": "excluded_from_ubs_0_9_4_scope_only",
    "different_strong_exact_attested_lemma": "editorial_identity_review",
    "different_strong_same_consonants": "editorial_identity_review",
    "same_strong_family_unresolved": "homograph_or_spelling_review",
    "source_strong_unreadable": "source_annotation_review",
}

def classify(row, families, exact, plain):
    m = MACULA_STRONG.fullmatch(row["strongnumberx"])
    language = row["lang"]
    if language not in ("H", "A") or not m:
        return "source_strong_unreadable", []
    strong_family = families.get((language, int(m.group(1))), set())
    if strong_family:
        return "same_strong_family_unresolved", sorted(strong_family)
    exact_owners = exact.get(unicodedata.normalize("NFC", row["lemma"]), set())
    if exact_owners:
        return "different_strong_exact_attested_lemma", sorted(exact_owners)
    consonantal_owners = plain.get(consonants(row["lemma"]), set())
    if consonantal_owners:
        return "different_strong_same_consonants", sorted(consonantal_owners)
    return "unattested_indexed_headword", []

def collect(index, entries, macula):
    families, exact, plain, by_id = inventory(entries)
    groups = {}
    all_counts = Counter()
    for idx, row in enumerate(csv.DictReader(Path(macula).open(encoding="utf-8-sig", newline=""), delimiter="\t")):
        if row["class"] not in LEXICAL_CLASSES:
            continue
        all_counts["lexical_source_occurrences"] += 1
        match = lookup_word(index, row["xml:id"], row["sdbh"], row["strongnumberx"], row["lang"], row["lemma"])
        if match["entry_ids"]:
            all_counts["already_linked"] += 1
            continue
        reason, candidates = classify(row, families, exact, plain)
        all_counts[reason] += 1
        key = (row["lang"], unicodedata.normalize("NFC", row["lemma"]), row["strongnumberx"])
        if key not in groups:
            groups[key] = {
                "lang": key[0], "lemma": key[1], "original_strong": key[2],
                "reason": reason, "state": STATUSES[reason],
                "review_decision": "not_editorially_validated",
                "occurrences": 0, "source_classes": Counter(),
                "ubs_candidate_entries": candidates, "source_witnesses": [],
            }
        family = groups[key]
        if family["reason"] != reason or family["ubs_candidate_entries"] != candidates:
            raise AssertionError(f"Inconsistent lexical classification: {key}")
        family["occurrences"] += 1
        family["source_classes"][row["class"]] += 1
        if len(family["source_witnesses"]) < 3:
            family["source_witnesses"].append({
                "original_word_id": row["xml:id"], "reference": row["ref"],
                "original_sdbh": row["sdbh"],
            })
    ordered = []
    for (language, lemma, strong), item in sorted(groups.items(), key=lambda kv: (-kv[1]["occurrences"], kv[0])):
        item["source_classes"] = dict(sorted(item["source_classes"].items()))
        ordered.append(item)
    by_reason_families = Counter(item["reason"] for item in ordered)
    by_reason_occurrences = Counter()
    for item in ordered:
        by_reason_occurrences[item["reason"]] += item["occurrences"]
    source_total = all_counts["lexical_source_occurrences"]
    linked = all_counts["already_linked"]
    unresolved = sum(item["occurrences"] for item in ordered)
    out_of_scope = all_counts["unattested_indexed_headword"]
    assert linked + unresolved == source_total
    assert unresolved == sum(by_reason_occurrences.values())
    scope = index.get("coverage_scope", {})
    if scope:
        for field, actual in (
            ("original_lexical_source_occurrences", source_total),
            ("linked_occurrences", linked),
            ("outside_indexed_headword_scope", out_of_scope),
            ("indexable_unresolved", unresolved - out_of_scope),
        ):
            if scope[field] != actual:
                raise AssertionError(f"Scope drift in {field}: {actual} != {scope[field]}")
    return {
        "format": "bsi-ubs-hebrew-lexical-family-register",
        "schema_version": 1,
        "source_editions": {
            "ubs_revision": index["dictionary"]["revision"],
            "macula_revision": index["macula"]["revision"],
        },
        "policy": {
            "scope": "selected_MACULA_source_classes_noun_verb_adj_adv_num",
            "family_key": ["lang", "NFC(lemma)", "original_strong_full_code"],
            "verification": "algorithmic_triage_not_editorial_validation",
            "no_implicit_links": True,
            "unattested_meaning": "no_matching_UBS_0_9_4_indexed_Strong_family_or_main_or_alternate_lemma_under_checked_spelling_rules",
            "confidence_caveat": "candidate_headwords_are_unverified; same_lemma_or_consonants_does_not_prove_lexical_identity",
        },
        "summary": {
            "lexical_source_occurrences": source_total,
            "linked_occurrences": linked,
            "unresolved_occurrences": unresolved,
            "unresolved_families": len(ordered),
            "outside_scope_occurrences": out_of_scope,
            "inside_scope_unresolved_occurrences": unresolved - out_of_scope,
            "families_by_reason": dict(sorted(by_reason_families.items())),
            "occurrences_by_reason": dict(sorted(by_reason_occurrences.items())),
            "families_with_editorial_decision": 0,
        },
        "families": ordered,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "english", "macula", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    report = collect(
        json.loads(args.index.read_text(encoding="utf-8")),
        json.loads(args.english.read_text(encoding="utf-8")),
        args.macula,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("UBS_FAMILY_REGISTER_SUMMARY", json.dumps(report["summary"], sort_keys=True))
    for item in report["families"][:15]:
        print("UBS_FAMILY_TOP", json.dumps(item, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
