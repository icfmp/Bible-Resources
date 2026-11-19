#!/usr/bin/env python3
"""Review ten exact original Greek lexical headword families, without contextual sense inference."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

import runpy

HERE = Path(__file__).resolve().parent
EVIDENCE = runpy.run_path(str(HERE / "audit_remaining_headwords.py"))
PREVIOUS = "source_reviewed_original_greek_pronoun_headword_only"
PENDING = EVIDENCE["UNAPPROVED"]
NEW = "source_reviewed_original_greek_headword_batch2_only"


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def validate_ledger(ledger):
    if (ledger.get("schema_version") != 1
        or ledger.get("status") != "SOURCE_ATTESTED_HEADWORD_ONLY_PRIVATE_NOT_PUBLISHED"
        or ledger.get("source_editions") != EVIDENCE["SOURCE_REVISIONS"]
        or ledger.get("editorial_policy") != {
            "original_word_ids_only": True,
            "require_original_lemma_nfc": True,
            "require_bilingual_ln_in_headword": True,
            "require_compatible_source_grammar": True,
            "preserve_original_strong": True,
            "infer_contextual_senses": False,
            "publish": False,
        }
        or ledger.get("prior_reviewed_words") != 5033
        or ledger.get("expected_original_words") != 577
        or ledger.get("remaining_unapproved_words") != 328):
        raise ValueError("Greek editorial authorization or pinned source drift")
    selected = {}
    for row in ledger["reviewed_families"]:
        key = (row["lemma_nfc"], row["ubs_main_id"])
        if (key in selected or row["lemma_nfc"] != unicodedata.normalize("NFC", row["lemma_nfc"])
            or row["macula_class"] not in ("adj", "verb")
            or not isinstance(row["source_word_count"], int)
            or row["source_word_count"] <= 0
            or len(row["editorial_basis"]) < 140):
            raise ValueError("Unattested editorial headword decision")
        selected[key] = row
    if len(selected) != 10 or sum(v["source_word_count"] for v in selected.values()) != 577:
        raise ValueError("Ten-family source-word scope drift")
    return selected


def grammar_matches(source_class, parts):
    normalized = {str(p).lower().rstrip(".") for p in parts}
    if not normalized:
        return False  # Never infer grammar from absence of source POS.
    # UBS source lexicographic abbreviations: adjc. / advb. / verb
    expected = {"adj": {"adjc", "adj", "adjective"}, "verb": {"verb"}}[source_class]
    return bool(expected & normalized)


def review(candidate, source_families, english, french, ledger):
    selected = validate_ledger(ledger)
    evidence = EVIDENCE["prepare"](candidate, english, french)
    if evidence != source_families:
        raise ValueError("Original-source family evidence file drift")
    by_family = {(row["lemma_nfc"], row["ubs_main_id"]): row
                 for row in evidence["families"]}
    count = Counter()
    approved_ids = {}
    for key, decision in selected.items():
        family = by_family.get(key)
        if not family or family["original_word_count"] != decision["source_word_count"]:
            raise ValueError("Reviewed lexical family original word count drift: " + repr(key))
        if family["original_classes"] != {decision["macula_class"]: decision["source_word_count"]}:
            raise ValueError("Original MACULA class disagrees with editorial lemma: " + repr(key))
        if not grammar_matches(decision["macula_class"], family["ubs_original_pos"]):
            raise ValueError("Original UBS POS disagrees with MACULA source class: " + repr(key))
        for word in family["all_original_word_witnesses"]:
            wid = word["word_id"]
            if wid in approved_ids:
                raise ValueError("Duplicate approved original Greek word ID")
            if not word["attested_headword_ln_codes"]:
                raise ValueError("Original UBS LN witness absent")
            approved_ids[wid] = key
        count[key] = len(family["all_original_word_witnesses"])
    if len(approved_ids) != 577:
        raise ValueError("Reviewed original word-ID inventory drift")
    output = copy.deepcopy(candidate)
    for wid, source in output["by_macula_word"].items():
        if wid in approved_ids:
            if source["match_type"] != PENDING or (unicodedata.normalize("NFC", source["original_lemma"]), source["entry_id"]) != approved_ids[wid]:
                raise ValueError("Greek unapproved source original word identity mutated")
            source["match_type"] = NEW
    kinds = Counter(v["match_type"] for v in output["by_macula_word"].values())
    if kinds != {PREVIOUS: 5033, NEW: 577, PENDING: 328}:
        raise ValueError("Greek individual original-word review count drift")
    for wid, old in candidate["by_macula_word"].items():
        new = output["by_macula_word"][wid]
        if {k: v for k, v in old.items() if k != "match_type"} != {
                k: v for k, v in new.items() if k != "match_type"}:
            raise ValueError("Original Greek lexical annotation mutated: " + wid)
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": "private_source_reviewed_greek_lexical_headwords_batch2_NOT_PUBLISHED",
        "editorial_acceptance": "original_word_ids_only_5033_pronouns_plus_577_lexical_batch2",
        "source_families_lexical_batch2_approvals": 577,
        "reviewed_original_headword_words_total": 5610,
        "other_original_words_still_unapproved": 328,
        "source_batch2_lexical_family_counts": {
            key[0]: n for key, n in sorted(count.items())},
        "editorial_source_batch2": "v1_reviewed_families_batch2.json",
        "new_inferred_contextual_lexical_sense_ids": 0,
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords": 5610,
        "other_unapproved_word_headword_candidates": 328,
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    for key in ("by_strong", "by_ln", "coverage", "statistics", "languages",
                "license", "format", "schema_version", "dictionary", "macula"):
        if output[key] != candidate[key]:
            raise ValueError("Original UBS Strong/LN bridge or source changed")
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "evidence", "english", "french", "ledger", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    read = lambda x: json.loads(x.read_text(encoding="utf-8-sig"))
    result = review(read(args.candidate), read(args.evidence),
                    read(args.english), read(args.french), read(args.ledger))
    args.output.write_bytes(canonical(result))
    print("GREEK_HEADWORD_BATCH2_SOURCE_VERIFIED", json.dumps({
        "new_word_id_headwords": 577, "reviewed_total": 5610,
        "strict_unapproved_remaining": 328,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "no_contextual_senses": True, "published": False
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
