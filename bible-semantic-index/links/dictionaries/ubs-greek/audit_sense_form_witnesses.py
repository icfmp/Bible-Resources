#!/usr/bin/env python3
"""Privately inspect authentic UBS Greek sense-specific form witnesses.

This diagnostic does not make editorial selections. It reports only source
LEXID, LN, and form metadata for the original ἰδού/ἴδε ambiguity, checked
against the complete private MACULA original-word review artifact. UBS prose
and glosses are never copied to the report.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

TARGETS = {"ἰδού", "ἴδε"}
MAIN = "003615000000000"
SENSES = {"003615001008000", "003615001009000"}


def inspect(batches, en, fr):
    if (batches.get("status") != "PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET"
            or batches.get("original_multi_sense_word_count") != 2728
            or batches.get("contextually_verified") != 0
            or batches.get("published") is not False):
        raise ValueError("Review source register drift")
    result = {}
    for lang, records in (("en", en), ("fr", fr)):
        matches = [r for r in records if r.get("MainId") == MAIN]
        if len(matches) != 1:
            raise ValueError("Missing/duplicate original UBS Greek headword")
        senses = {}
        for base in matches[0].get("BaseForms") or []:
            for sense in base.get("LEXMeanings") or []:
                sid = sense.get("LEXID")
                if sid not in SENSES:
                    continue
                if sid in senses:
                    raise ValueError("Duplicated original UBS source LEXID")
                senses[sid] = {
                    "source_ln": sense.get("LEXEntryCode"),
                    "source_lex_forms": sense.get("LEXForms"),
                    "source_field_names": sorted(sense.keys()),
                }
        if set(senses) != SENSES:
            raise ValueError("Original UBS form-sensitive senses missing")
        result[lang] = senses
    ids = set()
    by_lemma = Counter()
    for batch in batches["review_batches"]:
        if batch["ubs_main_id"] != MAIN or batch["original_lemma"] not in TARGETS:
            continue
        if not SENSES.issubset(set(batch["candidate_ubs_lexids"])):
            continue
        for w in batch["word_id_evidence"]:
            wid = w["original_word_id"]
            if wid in ids or w["original_lemma"] != batch["original_lemma"]:
                raise ValueError("Original Greek source word identity mismatch")
            if w["editorial_contextual_lexid_selection"] is not None:
                raise ValueError("Unexpected prior editorial assignment")
            ids.add(wid)
            by_lemma[w["original_lemma"]] += 1
    return {
        "status": "PRIVATE_UBS_GREEK_FORM_WITNESS_DIAGNOSTIC_NO_EDITORIAL_CHOICES",
        "source_editions": batches["source_editions"],
        "target_original_word_id_count": len(ids),
        "target_original_lemma_counts": dict(sorted(by_lemma.items())),
        "source_sense_metadata": result,
        "selected_contextual_lexids": 0,
        "original_sources_modified": False,
        "published": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("batches", "english", "french", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    report = inspect(read(a.batches), read(a.english), read(a.french))
    a.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_SENSE_FORM_WITNESSES", json.dumps({
        "word_ids": report["target_original_word_id_count"],
        "source_lemma_counts": report["target_original_lemma_counts"],
        "sense_forms": report["source_sense_metadata"],
        "selected": 0, "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
