#!/usr/bin/env python3
"""Classify 224 genuinely original Greek Strong-derived multi-headword candidates.

Evidence from the fully source-audited original Greek exception register is
read-only. Lexical lemma identity and original LN code intersection can
disambiguate a candidate headword at an original word ID, but are NOT
contextual UBS semantic sense approvals or changes to the Strong index.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def classify(source):
    if (source.get("status") != "PRIVATE_source_pinned_Greek_unresolved_499_plus_224_ambiguities"
        or source.get("original_exception_counts", {}).get("multiple_existing_ubs_headwords") != 224
        or source.get("publication_approved") is not False
        or source.get("new_lexical_headword_links_approved") != 0):
        raise ValueError("Original Greek 224-word ambiguity source drift")
    counts = Counter()
    categories = defaultdict(list)
    observed = set()
    for group in source["original_exception_groups"]:
        if group["source_reason"] != "multiple_existing_ubs_headwords":
            continue
        for witness in group["original_word_witnesses"]:
            wid = witness["original_word_id"]
            if wid in observed or not witness["original_reference"] or not witness["original_morph"]:
                raise ValueError("Unattested or duplicate original Greek ambiguous word ID")
            observed.add(wid)
            all_heads = set(witness["existing_original_ubs_main_ids"])
            lemma_heads = set(witness["same_nfc_lemma_candidate_main_ids"])
            exact_ln = witness["matching_original_ubs_ln_codes_by_main_id"]
            if (len(all_heads) < 2 or not lemma_heads.issubset(all_heads)
                or not set(exact_ln).issubset(all_heads)):
                raise ValueError("Original Greek UBS ambiguous headword source witnesses drift")
            corroborated = lemma_heads & set(exact_ln)
            if len(corroborated) == 1:
                category = "unique_original_nfc_lemma_and_ln_headword_witness"
            elif len(lemma_heads) == 1:
                category = "unique_original_nfc_lemma_without_confirming_same_headword_ln"
            elif len(lemma_heads) > 1:
                category = "multiple_original_nfc_identical_headwords_unresolved"
            else:
                category = "no_nfc_identical_original_ubs_headword_among_legacy_strong_candidates"
            counts[category] += 1
            categories[category].append({
                **witness,
                "original_lemma_matching_ubs_main_ids": sorted(lemma_heads),
                "original_same_lemma_and_ln_ubs_main_ids": sorted(corroborated),
                "editorial_status": "PREVIEW_ONLY_requires_original_word_specific_lexical_review",
            })
    if len(observed) != 224 or sum(counts.values()) != 224:
        raise ValueError("Original Greek multiheadword inventory incomplete")
    return {
        "status": "PRIVATE_original_Greek_224_Strong_ambiguity_reason_partition_NOT_APPROVED",
        "source_editions": source["source_editions"],
        "original_ambiguous_word_ids": 224,
        "reason_counts": dict(sorted(counts.items())),
        "reason_witnesses": dict(sorted(categories.items())),
        "original_strong_headword_candidates_unchanged": True,
        "contextual_ubs_lexids_inferred": 0,
        "new_approved_lexical_headwords": 0,
        "publication_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("source", "output"):
        p.add_argument("--" + k, type=Path, required=True)
    a = p.parse_args()
    data = json.loads(a.source.read_text(encoding="utf-8-sig"))
    result = classify(data)
    a.output.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    grouped = Counter(
        (x["original_lemma"], x["original_strong"],
         x["original_same_lemma_and_ln_ubs_main_ids"][0])
        for x in result["reason_witnesses"].get(
            "unique_original_nfc_lemma_and_ln_headword_witness", [])
    )
    print("UBS_GREEK_220_INDIVIDUAL_WORD_HEADWORD_GROUPS", json.dumps(
        [{"lemma": lemma, "source_strong": strong, "ubs_main_id": mid,
          "original_words": count}
         for (lemma, strong, mid), count in sorted(
             grouped.items(), key=lambda item: (-item[1], item[0]))],
        ensure_ascii=False, sort_keys=True))
    print("UBS_GREEK_224_STRONG_AMBIGUITY_REVIEW", json.dumps({
        "counts": result["reason_counts"],
        "word_examples": {
            category: [
                {"word_id": x["original_word_id"],
                 "ref": x["original_reference"],
                 "lemma": x["original_lemma"],
                 "strong": x["original_strong"],
                 "source_ubs_main_ids": x["existing_original_ubs_main_ids"],
                 "lemma_matching_ids": x["original_lemma_matching_ubs_main_ids"],
                 "lemma_ln_matching_ids": x["original_same_lemma_and_ln_ubs_main_ids"]}
                for x in rows[:6]
            ]
            for category, rows in result["reason_witnesses"].items()
        },
        "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
