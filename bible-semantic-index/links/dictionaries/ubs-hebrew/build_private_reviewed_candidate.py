#!/usr/bin/env python3
"""Rebuild a PRIVATE, exact source-word-anchored UBS 0.9.4 candidate index.

Combines two source-reviewed original MACULA WLC headword-only overlays.
Never edits the frozen published index.json, original UBS/MACULA data, or
contextual UBS lexical sense IDs. It is not a v1.0 release approval.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
SCOPE = runpy.run_path(str(HERE / "audit_dictionary_scope.py"))["analyze"]
MATCH_TYPE = "editorially_reviewed_original_wlc_headword_only"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combine_source_word_overlays(base, first, second):
    if (first["source_editions"] != second["source_editions"]
            or first["source_editions"]["ubs_revision"] !=
               base["dictionary"]["revision"]
            or first["source_editions"]["macula_revision"] !=
               base["macula"]["revision"]):
        raise ValueError("Source-revision mismatch in original WLC overlays")
    a, b = first["by_macula_word"], second["by_macula_word"]
    prev = base["by_macula_word"]
    if set(a) & set(b) or set(prev) & (set(a) | set(b)):
        raise ValueError("Duplicate original WLC word anchor or existing link collision")
    merged = {**a, **b}
    for wid, rec in merged.items():
        if (not wid.startswith("o") or len(wid) < 13
                or rec.get("match_type") != MATCH_TYPE
                or not rec.get("entry_id")
                or rec.get("lang") not in ("H", "A")
                or rec.get("strong") is None
                or not isinstance(rec.get("lemma"), str)
                or not isinstance(rec.get("original_sdbh"), str)
                or not rec.get("reference")):
            raise ValueError("Malformed original WLC word anchor: " + wid)
    return dict(sorted(merged.items()))


def verify_original_macula_words(base, overlays, macula, english):
    by_id = {e["MainId"] for e in english}
    if len(by_id) != len(english):
        raise ValueError("Duplicate original UBS headword entry")
    if not all(rec["entry_id"] in by_id for rec in overlays.values()):
        raise ValueError("Staged UBS dictionary headword absent from original edition")
    pending = dict(overlays)
    word_count = 0
    lexical_count = 0
    with Path(macula).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"xml:id", "lemma", "strongnumberx", "lang", "sdbh",
                    "class", "ref"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Pinned original WLC columns changed")
        for row in reader:
            word_count += 1
            if row["class"] in ("noun", "verb", "adj", "adv", "num"):
                lexical_count += 1
            wid = row["xml:id"]
            record = pending.pop(wid, None)
            if record is None:
                continue
            if (record["lemma"] != row["lemma"]
                    or record["strong"] != row["strongnumberx"]
                    or record["lang"] != row["lang"]
                    or record["original_sdbh"] != row["sdbh"]
                    or record["reference"] != row["ref"]
                    or row["class"] not in ("noun", "verb", "adj", "adv", "num")):
                raise ValueError("Pinned original source word changed: " + wid)
            original = BUILD["lookup_word"](
                base, wid, row["sdbh"], row["strongnumberx"],
                row["lang"], row["lemma"])
            if original["entry_ids"] or original["sense_ids"]:
                raise ValueError("Candidate would overwrite existing source link: " + wid)
    if pending:
        raise ValueError("Source-reviewed WLC words missing from MACULA original")
    return {"original_macula_word_rows": word_count,
            "original_macula_lexical_word_rows": lexical_count,
            "verified_new_word_anchors": len(overlays)}


def make_candidate(base, first, second, macula, english, original_sha):
    overlays = combine_source_word_overlays(base, first, second)
    source = verify_original_macula_words(base, overlays, macula, english)
    if (len(first["by_macula_word"]) != 139 or
            len(second["by_macula_word"]) != 134 or
            source != {
                "original_macula_word_rows": 475911,
                "original_macula_lexical_word_rows": 248680,
                "verified_new_word_anchors": 273,
            }):
        raise ValueError("Unexpected pinned source corpus or reviewed word count")
    candidate = dict(base)
    candidate["by_macula_word"] = dict(sorted({
        **base["by_macula_word"], **overlays
    }.items()))
    # Verify that every new link resolves to one original UBS headword,
    # with the unchanged source WLC identity and NO contextual sense ID.
    for wid, rec in overlays.items():
        result = BUILD["lookup_word"](
            candidate, wid, rec["original_sdbh"], rec["strong"],
            rec["lang"], rec["lemma"])
        if (result["status"] != "entry_only"
                or result["entry_ids"] != [rec["entry_id"]]
                or result["sense_ids"]
                or result["evidence"] !=
                   "macula_word_editorially_reviewed_headword_only"):
            raise ValueError("Incompatible reviewed original word lookup: " + wid)
    current = BUILD["audit_word_links"](candidate, macula)
    previous = base["coverage_with_word_ids"]
    if (current["original_word_rows"] != previous["original_word_rows"]
            or current["generic_entry_links"] != previous["generic_entry_links"]
            or current["word_aware_entry_links"] !=
               previous["word_aware_entry_links"] + len(overlays)
            or current["additional_entry_only_links"] !=
               previous["additional_entry_only_links"] + len(overlays)
            or current.get("sense_links", 0) != previous.get("sense_links", 0)):
        raise ValueError("Full original word-link delta audit failed")
    candidate["coverage_with_word_ids"] = current
    source_scope = SCOPE(candidate, english, macula)["summary"]
    old_scope = base["coverage_scope"]
    if (source_scope["lexical_source_occurrences"] !=
            old_scope["original_lexical_source_occurrences"]
            or source_scope["linked_occurrences"] !=
               old_scope["linked_occurrences"] + len(overlays)
            or source_scope["indexable_scope_denominator"] !=
               old_scope["indexable_denominator"]
            or source_scope["outside_indexed_ubs_headword_scope"] !=
               old_scope["outside_indexed_headword_scope"]):
        raise ValueError("Indexed-headword lexical coverage changed outside approved words")
    candidate["coverage_scope"] = {
        **old_scope,
        "linked_occurrences": source_scope["linked_occurrences"],
        "indexable_unresolved": source_scope["indexable_scope_unresolved"],
        "coverage_pct": source_scope["indexable_scope_coverage_pct"],
        "full_source_coverage_pct":
            source_scope["all_source_lexical_coverage_pct"],
        "review": {
            key: source_scope[key] for key in old_scope["review"]
        }
    }
    candidate["policy"] = {
        **base["policy"],
        "reviewed_word_anchors":
            "original_WLC_word_ID_only_UBS_headword_no_contextual_senses"
    }
    candidate["editorial_candidate"] = {
        "status": "private_v1_candidate_not_published_or_approved",
        "original_index_sha256": original_sha,
        "original_index_left_unchanged": True,
        "source_corpus_left_unchanged": True,
        "new_headword_only_wlc_word_ids": len(overlays),
        "unresolved_original_wlc_word_ids": 1,
        "inferred_contextual_sense_ids": 0,
        "index_source_revisions": first["source_editions"],
        "source_evidence": [
            "reviewed_word_anchor_preview.json",
            "reviewed_additional_word_anchor_preview.json",
        ],
    }
    # Retain original by_sdbh, by_strong, and raw dictionary provenance.
    for field in ("by_sdbh", "by_strong", "by_entry_strong_family",
                  "coverage", "dictionary", "macula", "statistics"):
        if candidate[field] != base[field]:
            raise ValueError("Pinned baseline index field unexpectedly changed: " + field)
    return candidate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "first", "additional", "macula", "english",
                 "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    base = json.loads(args.index.read_text(encoding="utf-8"))
    first = json.loads(args.first.read_text(encoding="utf-8"))
    additional = json.loads(args.additional.read_text(encoding="utf-8"))
    english = json.loads(args.english.read_text(encoding="utf-8"))
    candidate = make_candidate(
        base, first, additional, args.macula,
        english, sha256_file(args.index)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(candidate, ensure_ascii=False,
                   sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8"
    )
    result = {
        "new_reviewed_word_ids": 273,
        "source_linked_lexical_words":
            candidate["coverage_scope"]["linked_occurrences"],
        "indexable_scope_coverage_pct":
            candidate["coverage_scope"]["coverage_pct"],
        "contextual_sense_ids_inferred": 0,
        "candidate_sha256": sha256_file(args.output),
    }
    print("UBS_PRIVATE_CANDIDATE_INDEX", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

