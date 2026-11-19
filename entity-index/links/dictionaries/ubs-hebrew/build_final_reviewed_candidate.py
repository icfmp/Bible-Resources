#!/usr/bin/env python3
"""Apply exactly two independently attested final WLC word-ID UBS headwords.

The 202-family baseline disposition register and original source index remain
immutable historical witnesses. Previously unlinked word-specific historical
abstentions are superseded *only* for the two exact reviewed original WLC
word IDs, and never for other spelling-identical named places.

This is private nonpublished index generation, NOT a permission to release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
AUDIT = runpy.run_path(str(HERE / "audit_final_lexical_uncertainties.py"))
SCOPE = runpy.run_path(str(HERE / "audit_dictionary_scope.py"))["analyze"]
MATCH_TYPE = "editorially_reviewed_original_wlc_headword_only"
FIELDS = {
    "word_id": "word_id",
    "reference": "reference",
    "lemma_original": "lemma_original",
    "strong_original": "strong_original",
    "sdbh_original": "sdbh_original",
    "lang": "lang",
    "class_original": "class_original",
    "pos_original": "pos_original",
    "english_original": "english_original",
    "gloss_original": "gloss_original",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_decisions(review, evidence, indexed, english):
    if (review.get("schema_version") != 1
            or review.get("status") !=
              "reviewed_last_source_word_specific_ubs_headword_approvals_not_published"
            or review["source_editions"] != evidence["source_editions"]
            or review["source_editions"] != indexed["editorial_candidate"]["index_source_revisions"]
            or review.get("remaining_source_specific_abstentions") != 24):
        raise ValueError("Unpinned final original source-word editorial review")
    policy = review["policy"]
    if (policy.get("original_macula_fields_immutable") is not True
            or policy.get("contextual_ubs_sense_inferred") is not False
            or policy.get("word_id_specific_only") is not True):
        raise ValueError("Unsafe dictionary/sense publication policy")
    if evidence["summary"] != {
            "sole_candidate_families": 16,
            "same_lexical_family_source_words_already_linked": 8,
            "sole_candidate_words": 25,
            "individually_unlinked_rapha_words": 1,
            "original_word_records_verified": 26,
            "inferred_contextual_senses": 0,
        }:
        raise ValueError("Original WLC source-word audited inventory drift")
    source = {item["word_id"]: item for item in evidence["source_words"]}
    if len(source) != 26 or len(review["approved_word_links"]) != 2:
        raise ValueError("Unexpected reviewed WLC final source words")
    candidates = {e["main_id"]: e for e in evidence["ubs_headword_candidates"]}
    by_ubs = {entry["MainId"]: entry for entry in english}
    approved = {}
    for row in review["approved_word_links"]:
        wid = row["word_id"]
        if wid in approved or wid not in source:
            raise ValueError("Unreviewed or duplicated exact WLC word ID: " + wid)
        witness = source[wid]
        if any(row[key] != witness[value] for key, value in FIELDS.items()):
            raise ValueError("Original WLC word fields changed: " + wid)
        if witness["source_family"] != "sole_candidate_identity_unverified":
            raise ValueError("Final word approval is not from old source abstention")
        if (not row.get("editorial_rationale")
                or len(row["editorial_rationale"]) < 160
                or not row.get("independent_evidence_url", "").startswith("https://")
                or row.get("source_text_modified") is not False
                or row.get("contextual_lexical_sense_id_approved") is not False):
            raise ValueError("Missing independent editorial provenance: " + wid)
        mid = row["ubs_main_id"]
        attested = candidates.get(mid)
        entry = by_ubs.get(mid)
        if (witness["candidate_id"] != mid or entry is None
                or attested is None or row["ubs_lemma"] != entry["Lemma"]
                or row["ubs_attested_gloss"]
                not in attested["english_headword_glosses_original"]
                or row["ubs_attested_gloss"]
                not in AUDIT["glosses"](entry)):
            raise ValueError("Pinned UBS original headword not attested: " + wid)
        prior = BUILD["lookup_word"](
            indexed, wid, witness["sdbh_original"],
            witness["strong_original"], witness["lang"],
            witness["lemma_original"],
        )
        if prior["entry_ids"] or prior["sense_ids"] or wid in indexed["by_macula_word"]:
            raise ValueError("Would overwrite an existing lexical link: " + wid)
        approved[wid] = {
            "entry_id": mid, "match_type": MATCH_TYPE,
            "lemma": witness["lemma_original"],
            "strong": witness["strong_original"],
            "lang": witness["lang"],
            "original_sdbh": witness["sdbh_original"],
            "reference": witness["reference"],
        }

    if set(approved) != {"o060190130101", "o090170390072"}:
        raise ValueError("Only source-attested Joshua 19:13 and 1 Samuel 17:39 allowed")
    for rec in evidence["source_words"]:
        if rec["word_id"] not in approved:
            old = BUILD["lookup_word"](
                indexed, rec["word_id"], rec["sdbh_original"],
                rec["strong_original"], rec["lang"], rec["lemma_original"],
            )
            if old["entry_ids"] or old["sense_ids"]:
                raise ValueError("One of 24 conserved source abstentions became linked")
    return dict(sorted(approved.items()))


def build_final(indexed, reviewed, evidence, english, macula, source_manifest):
    if (source_manifest["status"] != indexed["editorial_candidate"]["status"]
            or source_manifest["candidate_index_sha256"] !=
                indexed["editorial_candidate"].get("_original_candidate_sha256",
                    source_manifest["candidate_index_sha256"])
            or source_manifest["new_entry_only_word_links"] != 273):
        raise ValueError("Original candidate is not the frozen 273-word source-reviewed index")
    approved = verify_decisions(reviewed, evidence, indexed, english)
    candidate = dict(indexed)
    candidate["by_macula_word"] = dict(sorted({
        **indexed["by_macula_word"], **approved
    }.items()))
    for wid, rec in approved.items():
        got = BUILD["lookup_word"](
            candidate, wid, rec["original_sdbh"], rec["strong"],
            rec["lang"], rec["lemma"],
        )
        if (got["status"] != "entry_only"
                or got["entry_ids"] != [rec["entry_id"]]
                or got["sense_ids"]
                or got["evidence"] != "macula_word_editorially_reviewed_headword_only"):
            raise ValueError("Final exact source-WLC word lookup is unsafe: " + wid)
    for rec in evidence["source_words"]:
        if rec["word_id"] not in approved:
            got = BUILD["lookup_word"](
                candidate, rec["word_id"], rec["sdbh_original"],
                rec["strong_original"], rec["lang"], rec["lemma_original"],
            )
            if got["entry_ids"] or got["sense_ids"]:
                raise ValueError("One of the 24 unsupported links was fabricated")
    previous = indexed["coverage_with_word_ids"]
    current = BUILD["audit_word_links"](candidate, macula)
    for key in ("original_word_rows", "generic_entry_links", "sense_links"):
        if current[key] != previous[key]:
            raise ValueError("Original source or contextual UBS sense links changed")
    if (current["word_aware_entry_links"] != previous["word_aware_entry_links"] + 2
            or current["additional_entry_only_links"] !=
               previous["additional_entry_only_links"] + 2):
        raise ValueError("Unexpected source word link delta beyond the two approvals")
    candidate["coverage_with_word_ids"] = current
    actual_scope = SCOPE(candidate, english, macula)["summary"]
    old = indexed["coverage_scope"]
    if (actual_scope["lexical_source_occurrences"] !=
            old["original_lexical_source_occurrences"]
            or actual_scope["linked_occurrences"] != old["linked_occurrences"] + 2
            or actual_scope["indexable_scope_denominator"] != old["indexable_denominator"]
            or actual_scope["outside_indexed_ubs_headword_scope"] !=
               old["outside_indexed_headword_scope"]):
        raise ValueError("Unintended original WLC source-edition scope change")
    candidate["coverage_scope"] = {
        **old,
        "linked_occurrences": actual_scope["linked_occurrences"],
        "indexable_unresolved": actual_scope["indexable_scope_unresolved"],
        "coverage_pct": actual_scope["indexable_scope_coverage_pct"],
        "full_source_coverage_pct": actual_scope["all_source_lexical_coverage_pct"],
        "review": {key: actual_scope[key] for key in old["review"]},
    }
    editorial = indexed["editorial_candidate"]
    candidate["editorial_candidate"] = {
        **editorial,
        "new_headword_only_wlc_word_ids":
            editorial["new_headword_only_wlc_word_ids"] + 2,
        "additional_final_source_specific_approvals": 2,
        "remaining_source_specific_unlinked_words": 24,
        "source_evidence": [
            *editorial["source_evidence"],
            "v1_final_word_specific_approvals.json",
            "audit_final_lexical_uncertainties.py",
        ],
    }
    for field in (
        "by_sdbh", "by_strong", "by_entry_strong_family", "coverage",
        "dictionary", "macula", "statistics"
    ):
        if candidate[field] != indexed[field]:
            raise ValueError("Historical UBS source crosswalk identity changed: " + field)
    if (candidate["coverage_scope"]["linked_occurrences"] != 240373
            or candidate["coverage_scope"]["indexable_unresolved"] != 2374
            or candidate["coverage_scope"]["coverage_pct"] != 99.022
            or candidate["editorial_candidate"]["new_headword_only_wlc_word_ids"] != 275):
        raise ValueError("Independent full WLC editorial release delta incorrect")
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "source_manifest", "decisions", "source_evidence",
                 "english", "macula", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    indexed = json.loads(args.index.read_text(encoding="utf-8"))
    prior = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    if digest(args.index) != prior["candidate_index_sha256"]:
        raise ValueError("Input 273-word index SHA-256 does not match frozen source ledger")
    reviewed = json.loads(args.decisions.read_text(encoding="utf-8"))
    witness = json.loads(args.source_evidence.read_text(encoding="utf-8"))
    english = json.loads(args.english.read_text(encoding="utf-8"))
    final = build_final(indexed, reviewed, witness, english, args.macula, prior)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(final, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":")) + "\n",
                           encoding="utf-8")
    print("UBS_V1_FINAL_275_SOURCE_WORD_CANDIDATE", json.dumps({
        "final_private_candidate_sha256": digest(args.output),
        "original_source_linked_lexical_words":
            final["coverage_scope"]["linked_occurrences"],
        "ubs_indexed_headword_scope_pct": final["coverage_scope"]["coverage_pct"],
        "source_word_links_reviewed": final["editorial_candidate"]["new_headword_only_wlc_word_ids"],
        "retained_unsupported_source_words": 24,
        "contextual_sense_ids_inferred": 0,
        "published": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

