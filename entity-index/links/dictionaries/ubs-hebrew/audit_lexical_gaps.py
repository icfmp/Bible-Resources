#!/usr/bin/env python3
"""Reproducible read-only triage of unmatched content-word occurrences.

Preserve Macula lemma, strong and sdbh exactly. Lexical-looking forms that match
a UBS lemma are only *review candidates*, never automatic crosswalk links.
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LEXICAL_CLASSES = frozenset(("noun", "verb", "adj", "adv", "num"))


def analyze(index, dictionary, source, top=60, expected_unresolved=None):
    from runpy import run_path
    lookup = run_path(str(Path(__file__).with_name("build_index.py")))["lookup"]
    ubs_lemmas = defaultdict(set)
    ubs_strongs = defaultdict(set)
    by_main = {}
    for item in dictionary:
        mid = item["MainId"]
        by_main[mid] = item
        # Exact NFC equality is conservative, NOT an orthographic harmonization.
        for lemma in [item["Lemma"], *(item.get("AlternateLemmas") or [])]:
            if isinstance(lemma, str):
                ubs_lemmas[unicodedata.normalize("NFC", lemma)].add(mid)
        for raw in item.get("StrongCodes") or []:
            ubs_strongs[str(raw)].add(mid)

    groups = defaultdict(lambda: {
        "total": 0, "strong": Counter(), "sdbh": Counter(),
        "morph": Counter(), "lang": Counter(), "word": Counter(),
        "refs": [], "same_spelling_ubs_ids": [],
    })
    counts = Counter()
    row_categories = Counter()
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        needed = {"xml:id", "class", "lemma", "strongnumberx", "sdbh", "ref",
                  "text", "morph", "lang"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("Missing required source columns")
        for row in reader:
            counts["all_source_rows"] += 1
            if row["class"] not in LEXICAL_CLASSES:
                continue
            counts["selected_lexical_rows"] += 1
            match = lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])
            if match["entry_ids"]:
                counts["lexical_linked"] += 1
                continue
            counts["lexical_unresolved"] += 1
            cls = row["class"]
            row_categories[cls] += 1
            # Group by original language AND exact source lemma, preventing
            # Hebrew/Aramaic homographs from being silently conflated.
            key = (row["lang"], row["lemma"])
            group = groups[key]
            group["total"] += 1
            group["strong"][row["strongnumberx"]] += 1
            group["sdbh"][row["sdbh"]] += 1
            group["morph"][row["morph"][:4]] += 1
            group["lang"][cls] += 1
            group["word"][row["text"]] += 1
            if len(group["refs"]) < 3:
                group["refs"].append({"id": row["xml:id"], "ref": row["ref"],
                                      "strong": row["strongnumberx"],
                                      "sdbh": row["sdbh"], "class": cls})
    if expected_unresolved is not None and counts["lexical_unresolved"] != expected_unresolved:
        raise ValueError("Lexical gap unexpectedly changed: " +
                         str(counts["lexical_unresolved"]))
    rows = []
    bucket_occurrences = Counter()
    for (language, lemma), group in groups.items():
        matching_ids = sorted(ubs_lemmas.get(unicodedata.normalize("NFC", lemma), ()))
        source_strongs = [(s, n) for s, n in group["strong"].most_common() if s]
        sdbh_count = sum(n for s, n in group["sdbh"].items() if s)
        strong_patterns = sorted(set(s for s, _ in source_strongs))
        if matching_ids:
            reason = "exact_nfc_lemma_candidate_only"
        elif sdbh_count:
            reason = "has_source_sdbh_but_no_matching_ubs_sense"
        elif any(any(ch.isalpha() for ch in s) for s in strong_patterns):
            reason = "strong_variant_without_verified_entry"
        else:
            reason = "lexical_entry_not_linked"
        bucket_occurrences[reason] += group["total"]
        rows.append({
            "language": language, "lemma": lemma, "occurrences": group["total"],
            "class_counts": dict(group["lang"]),
            "top_strong_codes": group["strong"].most_common(10),
            "source_sdbh_populated": sdbh_count,
            "source_sdbh_examples": [(s, n) for s, n in group["sdbh"].most_common(4) if s],
            "top_morph": group["morph"].most_common(4),
            "sample_refs": group["refs"],
            "exact_lemma_ubs_candidates": matching_ids[:15],
            "exact_lemma_candidate_count": len(matching_ids),
            "triage_bucket": reason,
        })
    rows.sort(key=lambda item: (-item["occurrences"], item["language"], item["lemma"]))
    total = sum(r["occurrences"] for r in rows)
    if total != counts["lexical_unresolved"]:
        raise AssertionError("Missing unresolved original tokens")
    return {
        "policy": "review_only_exact_source_lemma_candidates_not_verified_links",
        "summary": dict(counts),
        "unresolved_by_source_class": dict(sorted(row_categories.items())),
        "distinct_language_lemma_groups": len(rows),
        "distinct_lexical_group_counts_by_bucket": dict(Counter(
            item["triage_bucket"] for item in rows)),
        "unresolved_occurrences_by_triage_bucket": dict(bucket_occurrences),
        "top_10_occurrence_share_pct": round(
            100 * sum(x["occurrences"] for x in rows[:10]) / total, 2),
        "top_50_occurrence_share_pct": round(
            100 * sum(x["occurrences"] for x in rows[:50]) / total, 2),
        "top_100_occurrence_share_pct": round(
            100 * sum(x["occurrences"] for x in rows[:100]) / total, 2),
        "top_groups": rows[:top],
        "all_groups": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--macula", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-unresolved", type=int)
    a = parser.parse_args()
    result = analyze(
        json.loads(a.index.read_text(encoding="utf-8")),
        json.loads(a.english.read_text(encoding="utf-8")), a.macula,
        expected_unresolved=a.expected_unresolved)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False,
                                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for key in ("summary", "unresolved_by_source_class",
                "distinct_language_lemma_groups",
                "distinct_lexical_group_counts_by_bucket",
                "unresolved_occurrences_by_triage_bucket",
                "top_10_occurrence_share_pct", "top_50_occurrence_share_pct",
                "top_100_occurrence_share_pct"):
        print("LEXICAL_GAPS", key, json.dumps(result[key], ensure_ascii=False))
    for item in result["top_groups"][:25]:
        print("LEXICAL_GAP_TOP", json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
