#!/usr/bin/env python3
"""Audit all pinned original WLC words in source-reviewed positive UBS families.

The first 139 reviewed word IDs are already staged as an entry-only preview.
Enumerate the remaining source occurrences as *unreviewed*, preserving original
raw Hebrew, source English, POS, morphology, verse, Strong and SDBH. This
report never silently creates lexical links or chooses a contextual sense.
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def family_key(lang, lemma, strong):
    return (lang, unicodedata.normalize("NFC", lemma), strong)


def collect(ledger, preview, index, macula):
    if preview["source_editions"] != ledger["source_editions"]:
        raise ValueError("Unpinned original source editions")
    families = {}
    for d in ledger["decisions"]:
        k = family_key(d["lang"], d["lemma"], d["original_strong"])
        if k in families:
            raise ValueError("Duplicated source-reviewed lexical family")
        families[k] = d
    expected = preview["by_macula_word"]
    witnessed = {}
    remaining = defaultdict(list)
    source_counts = Counter()
    with Path(macula).open(encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src, delimiter="\t")
        required = {"xml:id", "lemma", "lang", "strongnumberx",
                    "sdbh", "class", "pos", "english", "morph", "ref"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Incomplete pinned MACULA source columns")
        for row in reader:
            k = family_key(row["lang"], row["lemma"], row["strongnumberx"])
            d = families.get(k)
            if d is None or row["class"] not in d["original_source_classes"]:
                continue
            wid = row["xml:id"]
            source_counts[k] += 1
            old_link = index.get("by_macula_word", {}).get(wid)
            # Every positive-family original source token is unresolved in the
            # pinned index: any new pre-existing link must halt this audit.
            if old_link is not None:
                raise ValueError("Unexpected already-linked original word " + wid)
            word = {
                "word_id": wid,
                "reference": row["ref"],
                "lemma_original": row["lemma"],
                "strong_original": row["strongnumberx"],
                "sdbh_original": row["sdbh"],
                "class_original": row["class"],
                "pos_original": row["pos"],
                "english_original": row["english"],
                "morph_original": row["morph"],
            }
            if wid in expected:
                anchor = expected[wid]
                if (anchor["lemma"] != row["lemma"]
                        or anchor["lang"] != row["lang"]
                        or anchor["strong"] != row["strongnumberx"]
                        or anchor["original_sdbh"] != row["sdbh"]
                        or anchor["reference"] != row["ref"]
                        or anchor["entry_id"] != d["ubs_candidate_main_id"]):
                    raise ValueError("Original WLC preview word drift: " + wid)
                if wid in witnessed:
                    raise ValueError("Duplicate anchored WLC word " + wid)
                witnessed[wid] = word
            else:
                remaining[k].append(word)
    if set(witnessed) != set(expected):
        raise ValueError("A source word from the staged preview is missing")
    reports = []
    for key, d in sorted(families.items()):
        count = source_counts[key]
        if count != d["original_occurrences"]:
            raise ValueError("Family source occurrence count drift: " + repr(key) +
                             " expected " + str(d["original_occurrences"]) +
                             " saw " + str(count))
        unresolved = sorted(remaining[key], key=lambda w:w["word_id"])
        reports.append({
            "lang": key[0],
            "lemma_editorial": d["lemma"],
            "strong_original": key[2],
            "candidate_ubs_main_id": d["ubs_candidate_main_id"],
            "editorial_meaning": d["editorial_meaning"],
            "ubs_attested_gloss": d["evidence"]["ubs_attested_gloss"],
            "reviewed_original_occurrences": count,
            "already_reviewed_word_ids": count - len(unresolved),
            "new_word_id_count": len(unresolved),
            "source_words_pending_individual_review": unresolved,
        })
    report = {
        "format": "bsi-ubs-reviewed-families-original-word-audit",
        "schema_version": 1,
        "source_editions": ledger["source_editions"],
        "policy": "Read-only source-original word enumeration; pending words are NOT editorially reviewed word links and carry NO inferred lexical sense.",
        "summary": {
            "reviewed_headword_families": len(reports),
            "original_family_occurrences": sum(x["reviewed_original_occurrences"] for x in reports),
            "already_reviewed_exact_word_ids": len(witnessed),
            "additional_words_pending_individual_review": sum(x["new_word_id_count"] for x in reports),
            "source_word_ids_with_contextual_senses_inferred": 0,
        },
        "families": reports,
    }
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("decisions", "preview", "index", "macula", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    a = p.parse_args()
    report = collect(
        json.loads(a.decisions.read_text(encoding="utf-8")),
        json.loads(a.preview.read_text(encoding="utf-8")),
        json.loads(a.index.read_text(encoding="utf-8")),
        a.macula,
    )
    if report["summary"] != {
            "reviewed_headword_families": 81,
            "original_family_occurrences": 274,
            "already_reviewed_exact_word_ids": 139,
            "additional_words_pending_individual_review": 135,
            "source_word_ids_with_contextual_senses_inferred": 0,
    }:
        raise ValueError("Original source-positive family population changed")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("UBS_ALL_POSITIVE_SOURCE_WORD_AUDIT",
          json.dumps(report["summary"], sort_keys=True))
    print("UBS_PENDING_WORDS_EVIDENCE",
          json.dumps([
              x for x in report["families"] if x["new_word_id_count"] > 0
          ], ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()

