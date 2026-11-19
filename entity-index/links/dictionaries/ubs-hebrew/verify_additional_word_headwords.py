#!/usr/bin/env python3
"""Independently verify per-original-WLC-word editorial entry-only decisions.

The source-original 135-word audit is itself regenerated from pinned MACULA WLC
in CI. This verifier checks exact original word IDs and full source fields
against that independent report and the complete original MACULA TSV.
It never merges namesakes, restores Strong codes or supplies UBS sense IDs.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
MATCH_TYPE = "editorially_reviewed_original_wlc_headword_only"
REQUIRED_WORD_FIELDS = (
    "word_id", "entry_id", "lang", "lemma_original", "strong_original",
    "sdbh_original", "reference", "class_original", "pos_original",
    "morph_original", "english_original",
)


def key(lang, lemma, strong):
    return (lang, unicodedata.normalize("NFC", lemma), strong)


def lookup_original_words(report):
    words = {}
    for family in report["families"]:
        k = key(family["lang"], family["lemma_editorial"],
                family["strong_original"])
        for original in family["source_words_pending_individual_review"]:
            wid = original["word_id"]
            if wid in words:
                raise ValueError("Duplicate pending original WLC word")
            words[wid] = (k, family, original)
    return words


def verify_editorial_dispositions(review, report, ledger, original_preview,
                                  index, english):
    editions = review["source_editions"]
    if not (editions == report["source_editions"]
            == ledger["source_editions"]
            == original_preview["source_editions"]):
        raise ValueError("Source revision mismatch across independent ledgers")
    if (editions["ubs_revision"] != index["dictionary"]["revision"]
            or editions["macula_revision"] != index["macula"]["revision"]):
        raise ValueError("Original index revision mismatch")
    if review.get("schema_version") != 1:
        raise ValueError("Unsupported original word review schema")
    source = lookup_original_words(report)
    base_preview = original_preview["by_macula_word"]
    if set(source) & set(base_preview):
        raise ValueError("Pending original WLC word already in staged initial preview")
    families = {key(d["lang"], d["lemma"], d["original_strong"]): d
                for d in ledger["decisions"]}
    actual_ubs = {entry["MainId"]: entry for entry in english}
    if len(actual_ubs) != len(english):
        raise ValueError("Duplicate original UBS MainId")

    plans = {}
    for p in review["reviewed_families"]:
        k = key(p["lang"], p["lemma_editorial"], p["original_strong"])
        d = families.get(k)
        if k in plans or d is None:
            raise ValueError("Unknown or duplicated reviewed source family")
        plans[k] = p
        if (p["ubs_main_id"] != d["ubs_candidate_main_id"]
                or p["ubs_attested_gloss"] != d["evidence"]["ubs_attested_gloss"]
                or not p["lexical_rationale"]
                or not p["independently_reviewed_original_english_values"]):
            raise ValueError("Positive lexical family source evidence drift")
        entry = actual_ubs.get(p["ubs_main_id"])
        if entry is None:
            raise ValueError("Approved original UBS headword is absent")
        meanings = {
            gloss for form in entry.get("BaseForms") or []
            for sense in form.get("LEXMeanings") or []
            for lex in sense.get("LEXSenses") or []
            for gloss in lex.get("Glosses") or []
        }
        if p["ubs_attested_gloss"] not in meanings:
            raise ValueError("Approved UBS meaning absent from pinned edition")

    approved = {}
    for d in review["approved_word_decisions"]:
        wid = d["word_id"]
        if wid in approved or wid not in source:
            raise ValueError("Duplicated or unknown approved original WLC word")
        k, f, w = source[wid]
        p = plans.get(k)
        if p is None or d["entry_id"] != p["ubs_main_id"]:
            raise ValueError("Original WLC word uses an unreviewed UBS headword")
        expected = {
            "word_id": w["word_id"], "entry_id": p["ubs_main_id"],
            "lang": f["lang"], "lemma_original": w["lemma_original"],
            "strong_original": w["strong_original"],
            "sdbh_original": w["sdbh_original"], "reference": w["reference"],
            "class_original": w["class_original"], "pos_original": w["pos_original"],
            "morph_original": w["morph_original"],
            "english_original": w["english_original"],
        }
        if any(d[field] != expected[field] for field in REQUIRED_WORD_FIELDS):
            raise ValueError("Original word evidence mismatch: " + wid)
        if (d["english_original"]
                not in p["independently_reviewed_original_english_values"]):
            raise ValueError("Original word meaning not editorially approved: " + wid)
        if (d.get("lexical_identity_editorially_approved") is not True
                or d.get("contextual_sense_id_approved") is not False
                or d.get("source_data_modified") is not False
                or d.get("link_applied_to_index") is not False):
            raise ValueError("Unsafe individual source-word identity approval")
        old = BUILD["lookup_word"](index, wid, d["sdbh_original"],
            d["strong_original"], d["lang"], d["lemma_original"])
        if old["entry_ids"] or wid in index.get("by_macula_word", {}):
            raise ValueError("Approved WLC word already has a lexical link")
        approved[wid] = d

    reserved = {}
    for d in review["unresolved_source_word_abstentions"]:
        wid = d["word_id"]
        if wid in reserved or wid in approved or wid not in source:
            raise ValueError("Duplicate/unknown original WLC no-link decision")
        k, f, w = source[wid]
        if not d.get("reason") or d["reference"] != w["reference"]:
            raise ValueError("Unsupported original WLC abstention evidence")
        if (d["original_english"] != w["english_original"]
                or d["lang"] != f["lang"]
                or d["lemma_original"] != w["lemma_original"]
                or d["original_strong"] != w["strong_original"]):
            raise ValueError("Original WLC abstention source mismatch")
        if k in plans:
            raise ValueError("Original abstention cannot be part of approved lexical family")
        reserved[wid] = d

    if set(approved) | set(reserved) != set(source):
        raise ValueError("Not every pending original word has a source-supported decision")
    if len(plans) != 19 or len(approved) != 134 or len(reserved) != 1:
        raise ValueError("Pinned individual editorial review inventory changed")
    overlay = {
        wid: {
            "entry_id": d["entry_id"], "match_type": MATCH_TYPE,
            "lemma": d["lemma_original"], "strong": d["strong_original"],
            "lang": d["lang"], "original_sdbh": d["sdbh_original"],
            "reference": d["reference"],
        } for wid, d in approved.items()
    }
    trial = dict(index)
    trial["by_macula_word"] = {
        **index.get("by_macula_word", {}), **base_preview, **overlay
    }
    for wid, record in overlay.items():
        result = BUILD["lookup_word"](
            trial, wid, record["original_sdbh"], record["strong"],
            record["lang"], record["lemma"]
        )
        if (result["entry_ids"] != [record["entry_id"]]
                or result["sense_ids"] != []
                or result["status"] != "entry_only"
                or result["evidence"] !=
                    "macula_word_editorially_reviewed_headword_only"):
            raise ValueError("Staged original word cannot be looked up safely")
    return {
        "format": "bsi-ubs-wlc-additional-reviewed-word-headword-overlay",
        "schema_version": 1,
        "source_editions": editions,
        "policy": ("Individually reviewed exact WLC word IDs only; "
                   "headword entry-only, zero contextual sense IDs, "
                   "no family-wide or original source changes"),
        "summary": {
            "new_individually_approved_original_words": len(overlay),
            "source_words_preserved_unlinked_as_uncertain": len(reserved),
            "combined_staged_original_wlc_words": len(base_preview) + len(overlay),
            "new_contextual_sense_ids": 0,
        },
        "by_macula_word": dict(sorted(overlay.items())),
    }


def verify_macula_originals(review, path):
    pending = {d["word_id"]: d for d in review["approved_word_decisions"]}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            d = pending.pop(row["xml:id"], None)
            if d is None:
                continue
            if (row["lemma"] != d["lemma_original"]
                    or row["strongnumberx"] != d["strong_original"]
                    or row["lang"] != d["lang"]
                    or row["sdbh"] != d["sdbh_original"]
                    or row["class"] != d["class_original"]
                    or row["pos"] != d["pos_original"]
                    or row["morph"] != d["morph_original"]
                    or row["english"] != d["english_original"]
                    or row["ref"] != d["reference"]):
                raise ValueError("Original MACULA word changed: " + row["xml:id"])
    if pending:
        raise ValueError("Approved original WLC word missing from frozen source")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("decisions", "audit", "ledger", "preview", "index", "english",
                 "macula", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    review, report, ledger, initial, index, english = (
        json.loads(getattr(a, name).read_text(encoding="utf-8"))
        for name in ("decisions", "audit", "ledger", "preview", "index", "english")
    )
    verify_macula_originals(review, a.macula)
    staged = verify_editorial_dispositions(
        review, report, ledger, initial, index, english)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        json.dumps(staged, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("UBS_ADDITIONAL_WORD_HEADWORD_ONLY_REVIEW",
          json.dumps(staged["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

