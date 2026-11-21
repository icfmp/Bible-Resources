#!/usr/bin/env python3
"""Reconcile original-source 173 strict Greek candidates remaining after batch 3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

def triage(residual_328, batch3):
    if (residual_328.get("status") != "PRIVATE_328_original_Greek_word_witnesses_NOT_APPROVED"
            or residual_328.get("original_word_count") != 328
            or residual_328.get("publication_approved") is not False
            or batch3.get("status") != "source_verified_greek_lexical_headword_batch3_private_not_published"
            or batch3.get("source_editions") != residual_328.get("source_editions")
            or batch3.get("new_reviewed_original_words") != 155
            or batch3.get("remaining_strict_unapproved_words") != 173):
        raise ValueError("Original Greek 173-word editorial evidence drift")
    reviewed = {(r["lemma_nfc"], r["ubs_main_id"]): r["source_word_count"]
                for r in batch3["reviewed_families"]}
    if len(reviewed) != 19 or sum(reviewed.values()) != 155:
        raise ValueError("Greek third source-reviewed family ledger drift")
    remaining = []
    reviewed_ids = set()
    pending_ids = set()
    for family in residual_328["families"]:
        key = (family["lemma_nfc"], family["ubs_main_id"])
        witnesses = family["all_original_word_witnesses"]
        if len(witnesses) != family["original_word_count"]:
            raise ValueError("Unattested individual Greek lexical word witnesses")
        ids = {w["word_id"] for w in witnesses}
        if len(ids) != len(witnesses) or (ids & (reviewed_ids | pending_ids)):
            raise ValueError("Duplicated source-original Greek word ID")
        if key in reviewed:
            if reviewed[key] != len(witnesses):
                raise ValueError("Previously approved original Greek word count changed")
            reviewed_ids.update(ids)
        else:
            remaining.append(family)
            pending_ids.update(ids)
    if len(reviewed_ids) != 155 or len(pending_ids) != 173:
        raise ValueError("Greek 173-word residual population drift")
    return {
        "status": "PRIVATE_source_pinned_173_remaining_Greek_word_witnesses_UNAPPROVED",
        "source_editions": residual_328["source_editions"],
        "original_unapproved_word_count": 173,
        "remaining_original_family_count": len(remaining),
        "previous_155_approved_excluded": len(reviewed_ids),
        "publication_approved": False,
        "contextual_ubs_lexids_inferred": 0,
        "families": remaining,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for x in ("residual", "batch3", "output"):
        p.add_argument("--" + x, type=Path, required=True)
    args = p.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    report = triage(read(args.residual), read(args.batch3))
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("UBS_GREEK_STRICT_173_PENDING", json.dumps({
        "original_words": report["original_unapproved_word_count"],
        "families": report["remaining_original_family_count"],
        "examples": [
            {"lemma": f["lemma_nfc"], "headword": f["ubs_main_id"],
             "word_count": f["original_word_count"],
             "source_class": f["original_classes"],
             "source_strong": f["original_strong_counts"],
             "ubs_pos": f["ubs_original_pos"]}
            for f in report["families"][:120]
        ],
        "publication": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
