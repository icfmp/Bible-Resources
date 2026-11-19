#!/usr/bin/env python3
"""Classify still-unapproved source-attested Greek headwords after editorial batch 2.

Only the original 905 word-ID witnesses and committed source-reviewed family
ledger are used. No source Greek word or historical lexical map is changed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SOURCE = "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release"


def build(evidence, batch2):
    if (evidence.get("status") !=
            "PRIVATE_original_word_evidence_ONLY_no_editorial_promotion_no_publication"
            or evidence.get("unapproved_words") != 905
            or evidence.get("publication_approved") is not False
            or evidence.get("source_editions") != batch2.get("source_editions")
            or batch2.get("expected_original_words") != 577):
        raise ValueError("Original Greek source evidence drift")
    reviewed = {
        (x["lemma_nfc"], x["ubs_main_id"]): x["source_word_count"]
        for x in batch2["reviewed_families"]
    }
    if len(reviewed) != 10 or sum(reviewed.values()) != 577:
        raise ValueError("Original 577-word reviewed family ledger drift")
    remaining = []
    excluded = Counter()
    for f in evidence["families"]:
        key = (f["lemma_nfc"], f["ubs_main_id"])
        if key in reviewed:
            if f["original_word_count"] != reviewed[key]:
                raise ValueError("Original Greek previously approved family mutated")
            excluded[key[0]] += f["original_word_count"]
            continue
        if len(f["all_original_word_witnesses"]) != f["original_word_count"]:
            raise ValueError("Missing original Greek word witness")
        remaining.append(f)
    if (sum(f["original_word_count"] for f in remaining) != 328
            or sum(excluded.values()) != 577):
        raise ValueError("Greek 328-word residual original source inventory drift")
    return {
        "status": "PRIVATE_328_original_Greek_word_witnesses_NOT_APPROVED",
        "source_editions": evidence["source_editions"],
        "original_word_count": 328,
        "family_count": len(remaining),
        "previous_batch2_excluded_words": 577,
        "previous_batch2_excluded_families": dict(sorted(excluded.items())),
        "publication_approved": False,
        "contextual_sense_ids_inferred": 0,
        "families": remaining,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("evidence", "batch2", "output"):
        p.add_argument("--" + field, type=Path, required=True)
    a = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8"))
    result = build(read(a.evidence), read(a.batch2))
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("UBS_GREEK_328_REMAINING_FAMILIES", json.dumps({
        "family_count": result["family_count"],
        "original_word_count": result["original_word_count"],
        "top_families": [
            {"lemma": f["lemma_nfc"], "mid": f["ubs_main_id"],
             "words": f["original_word_count"],
             "macula_classes": f["original_classes"],
             "ubs_english_pos": f["ubs_original_pos"],
             "source_strong_counts": f["original_strong_counts"]}
            for f in result["families"][:80]
        ],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
