#!/usr/bin/env python3
"""Source-pinned read-only UBS Greek ↔ original MACULA SBLGNT gap inventory.

This classifies *candidate evidence*, never authorizes lexical identity:
a lemma match, Strong-family shape, and/or Louw–Nida code alone cannot
establish a contextual headword or sense. All source-word annotations
are preserved exactly as read. Only original IDs, lexical labels and
metadata (not Bible verses or UBS dictionary definitions) are exported.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
SOURCE = {
    "ubs_revision": BUILD["UBS_REVISION"],
    "macula_revision": BUILD["MACULA_REVISION"],
    "ubs_edition": "1.0",
    "macula_corpus": "sblgnt",
}
REQUIRED_COLUMNS = ("xml:id", "lemma", "strong", "ln")


def norm(value):
    """Unicode normalization for lookup comparison only, never source mutation."""
    return unicodedata.normalize("NFC", str(value))


def lexical_forms(entry):
    """Only attested original UBS headwords; never infer from spelling."""
    forms = [entry["Lemma"]]
    forms.extend(entry.get("AlternateLemmas") or [])
    return {norm(form) for form in forms if isinstance(form, str) and form}


def candidates_for_original(row, exact_headwords, by_ln):
    mids = exact_headwords.get(norm(row["lemma"]), ())
    ln_pairs = {
        (mid, sense)
        for code in row["ln"].split()
        for mid, sense in by_ln.get(code, ())
    }
    ln_mids = {mid for mid, _ in ln_pairs}
    common = set(mids) & ln_mids
    return {
        "exact_original_ubs_lemma_main_ids": sorted(mids),
        "independent_original_ln_headword_main_ids": sorted(ln_mids),
        "lemma_and_ln_same_headword_main_ids": sorted(common),
        "ln_sense_reference_pairs": [list(pair) for pair in sorted(ln_pairs)],
    }


def collect(index, english, french, macula_path):
    """Partition every original word and preserve all zero-match witnesses."""
    # The existing bilingual verifier is the authority for semantic ID parity.
    verified = BUILD["build"](english, french)
    for field in ("by_strong", "by_ln", "statistics", "dictionary", "macula"):
        if verified[field] != index[field]:
            raise ValueError("Original Greek index drift against source: " + field)
    exact_headwords = defaultdict(set)
    for entry in english:
        for form in lexical_forms(entry):
            exact_headwords[form].add(entry["MainId"])

    words = set()
    counts = Counter()
    families = {}
    with Path(macula_path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not set(REQUIRED_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError("Original MACULA Greek source TSV columns changed")
        for row in reader:
            wid = row["xml:id"]
            if not wid.startswith("n") or wid in words:
                raise ValueError("Original Greek word ID missing, malformed or repeated: " + wid)
            words.add(wid)
            counts["source_original_word_rows"] += 1
            lookup = BUILD["lookup"](index, row["strong"], row["ln"])
            if lookup["status"] == "unsupported_strong_structure":
                outcome = "original_strong_annotation_not_supported"
                counts["unsupported_original_strong_rows"] += 1
            elif lookup["entry_ids"]:
                counts["already_linked_source_rows"] += 1
                if lookup["sense_ids"]:
                    counts["with_source_ln_matching_ubs_sense_candidates"] += 1
                if len(lookup["entry_ids"]) > 1:
                    counts["with_multiple_ubs_headword_candidates"] += 1
                continue
            else:
                outcome = "no_strong_to_ubs_headword_candidate"
                counts["no_original_ubs_headword_rows"] += 1

            family_key = (row["strong"], norm(row["lemma"]), outcome)
            f = families.get(family_key)
            if f is None:
                f = {
                    "strong_original": row["strong"],
                    "lemma_original": row["lemma"],
                    "disposition": "unreviewed_original_source_gap",
                    "classification": outcome,
                    "original_word_occurrences": 0,
                    "source_pos_counts": Counter(),
                    "source_class_counts": Counter(),
                    "source_ln_counts": Counter(),
                    "original_word_examples": [],
                    # These are review *candidates*, not approved lexical links.
                    "candidate_evidence": candidates_for_original(
                        row, exact_headwords, index["by_ln"]
                    ),
                }
                families[family_key] = f
            f["original_word_occurrences"] += 1
            counts["original_unlinked_words_to_review"] += 1
            for column, target in (("pos", "source_pos_counts"),
                                   ("class", "source_class_counts")):
                if row.get(column):
                    f[target][row[column]] += 1
            for code in row["ln"].split():
                f["source_ln_counts"][code] += 1
            # For a repeated Strong+lemma family, a different original LN
            # annotation can yield *different* possible UBS entries. Union
            # evidence is only an inventory, never a contextual decision.
            current = candidates_for_original(row, exact_headwords, index["by_ln"])
            for field in ("independent_original_ln_headword_main_ids",
                          "lemma_and_ln_same_headword_main_ids",
                          "exact_original_ubs_lemma_main_ids",
                          "ln_sense_reference_pairs"):
                old = f["candidate_evidence"][field]
                new = current[field]
                f["candidate_evidence"][field] = sorted(
                    set(map(tuple, old)) | set(map(tuple, new))
                ) if field == "ln_sense_reference_pairs" else sorted(set(old) | set(new))
                if field == "ln_sense_reference_pairs":
                    f["candidate_evidence"][field] = [
                        list(pair) for pair in f["candidate_evidence"][field]
                    ]
            if len(f["original_word_examples"]) < 4:
                f["original_word_examples"].append({
                    "original_word_id": wid,
                    "source_ref_original": row.get("ref", ""),
                    "lemma_original": row["lemma"],
                    "strong_original": row["strong"],
                    "ln_original": row["ln"],
                    "pos_original": row.get("pos", ""),
                    "class_original": row.get("class", ""),
                    "morph_original": row.get("morph", ""),
                })

    expected = index.get("coverage", {})
    exact_checks = {
        "macula_words": counts["source_original_word_rows"],
        "with_ubs_entry_candidates": counts["already_linked_source_rows"],
        "with_corresponding_sense_candidates": counts[
            "with_source_ln_matching_ubs_sense_candidates"],
        "ambiguous_ubs_entry_candidates": counts[
            "with_multiple_ubs_headword_candidates"],
        "unsupported_compound_strong": counts[
            "unsupported_original_strong_rows"],
        "no_ubs_entry": counts["no_original_ubs_headword_rows"],
    }
    for field, value in exact_checks.items():
        if value != expected.get(field):
            raise ValueError(
                "Full original source-to-UBS dictionary count drift: " + field
            )
    if sum((
        counts["already_linked_source_rows"],
        counts["unsupported_original_strong_rows"],
        counts["no_original_ubs_headword_rows"],
    )) != counts["source_original_word_rows"]:
        raise ValueError("Incomplete lossless source-word classification")

    result = []
    for f in families.values():
        f["source_pos_counts"] = dict(sorted(f["source_pos_counts"].items()))
        f["source_class_counts"] = dict(sorted(f["source_class_counts"].items()))
        f["source_ln_counts"] = dict(sorted(f["source_ln_counts"].items()))
        if f["candidate_evidence"]["exact_original_ubs_lemma_main_ids"]:
            counts["exact_headword_candidate_families"] += 1
            counts["exact_headword_candidate_original_occurrences"] += (
                f["original_word_occurrences"])
        if f["candidate_evidence"]["independent_original_ln_headword_main_ids"]:
            counts["ln_only_evidence_families"] += 1
            counts["ln_only_evidence_original_occurrences"] += (
                f["original_word_occurrences"])
        if f["candidate_evidence"]["lemma_and_ln_same_headword_main_ids"]:
            counts["lemma_and_ln_combined_candidate_families"] += 1
            counts["lemma_and_ln_combined_original_occurrences"] += (
                f["original_word_occurrences"])
        result.append(f)
    result.sort(key=lambda f: (
        -f["original_word_occurrences"], f["strong_original"],
        norm(f["lemma_original"]), f["classification"],
    ))
    counts["distinct_unmatched_original_families"] = len(result)
    counts["unsupported_original_families"] = sum(
        x["classification"] == "original_strong_annotation_not_supported"
        for x in result
    )
    return {
        "schema_version": 1,
        "status": "original_source_verified_review_inventory_no_lexical_identity_approved",
        "source_editions": SOURCE,
        "policy": {
            "source_words_modified": False,
            "original_index_modified": False,
            "ubs_entry_or_lexid_inferred": False,
            "possible_ln_or_lemma_matches_are_not_approved_links": True,
            "source_families_must_be_reviewed_individually": True,
        },
        "summary": dict(sorted(counts.items())),
        "families": result,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "english", "french", "macula", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    read_json = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    result = collect(read_json(args.index), read_json(args.english),
                     read_json(args.french), args.macula)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                      indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_ORIGINAL_SOURCE_GAP_AUDIT",
          json.dumps(result["summary"], sort_keys=True))
    for f in result["families"][:35]:
        print("UBS_GREEK_UNMATCHED_FAMILY", json.dumps({
            "strong": f["strong_original"], "lemma": f["lemma_original"],
            "source_occurrences": f["original_word_occurrences"],
            "class_counts": f["source_class_counts"],
            "candidate_ubs_lemma_headwords":
                f["candidate_evidence"]["exact_original_ubs_lemma_main_ids"],
            "candidate_ubs_ln_headwords":
                f["candidate_evidence"]["independent_original_ln_headword_main_ids"][:15],
        }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

