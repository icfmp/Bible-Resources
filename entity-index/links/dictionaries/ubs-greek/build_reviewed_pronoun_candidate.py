#!/usr/bin/env python3
"""Review Greek pronoun HEADWORD identity on exact pinned original word IDs.

Use the existing source-attested 5,938-word preview as the exhaustive input.
For only explicitly reviewed family identities, require the original word's
unmodified Greek lemma (NFC compare), original MACULA pronoun class and original
LN code attested by the exact UBS 1.0 headword. This does not promote a sense,
rewrite the original Strong annotation or create a global lemma/Strong alias.

The resulting complete preview remains PRIVATE and NOT PUBLISHED. The
historical original index and source corpora remain byte-for-byte unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIEW = runpy.run_path(str(HERE / "build_private_word_candidate.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))
APPROVED = "source_reviewed_original_greek_pronoun_headword_only"
APPROVAL_STATUS = "reviewed_source_original_pronoun_headwords_private_not_published"


def nfc(value):
    return unicodedata.normalize("NFC", str(value))


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def review_ledger(ledger, source_report, english, french):
    if (ledger.get("schema_version") != 1
            or ledger.get("status") !=
                "source_attested_pronoun_headword_review_without_publication"
            or ledger.get("source_editions") != source_report["source_editions"]
            or ledger.get("editorial_policy") != {
                "accept_only_exact_original_word_id": True,
                "require_original_lemma_nfc_identity": True,
                "require_original_class_pronoun": True,
                "require_attested_common_ubs_original_ln": True,
                "no_original_text_strong_morphology_changes": True,
                "no_contextual_sense_ids": True,
                "no_global_strong_aliases": True,
                "original_index_unchanged": True,
                "publication_approved": False,
            }):
        raise ValueError("Pronoun editorial review status, source or scope not pinned")
    original_en = {x["MainId"]: x for x in english}
    original_fr = {x["MainId"]: x for x in french}
    if (len(original_en) != len(english)
            or len(original_fr) != len(french)
            or set(original_en) != set(original_fr)):
        raise ValueError("Pinned original UBS bilingual lexical headwords changed")
    reviewed = {}
    for decision in ledger["reviewed_headword_families"]:
        lemma = decision["lemma_nfc"]
        mid = decision["ubs_main_id"]
        if (lemma != nfc(lemma) or lemma in reviewed
                or mid not in original_en
                or nfc(original_en[mid]["Lemma"]) != lemma
                or nfc(original_fr[mid]["Lemma"]) != lemma
                or not isinstance(decision.get("rationale"), str)
                or len(decision["rationale"]) < 160):
            raise ValueError("Unattested or unsupported original UBS pronoun decision")
        entry = original_en[mid]
        parts = {
            str(part).lower()
            for form in entry.get("BaseForms") or []
            for part in form.get("PartsOfSpeech") or []
        }
        # UBS Greek v1.0 does not always provide a part-of-speech label.
        # Absence is not evidence of a different grammatical class. If the
        # original headword DOES label it, reject a contradictory category;
        # verify the original MACULA source word is a pronoun separately.
        # The original UBS Greek edition uses lexicographic POS abbreviations:
        # pprs. (personal pronoun), pdem. (demonstrative pronoun). Never
        # mistake these source abbreviations for unclassified or non-pronouns.
        if parts and not any(
            "pron" in part or part.rstrip(".") in ("pprs", "pdem")
            for part in parts
        ):
            raise ValueError(
                "Original UBS entry POS classification differs from pronoun expectation: " + mid + " " + repr(sorted(parts))
            )
        verified_ln = {
            item.get("LEXEntryCode")
            for form in entry.get("BaseForms") or []
            for item in form.get("LEXMeanings") or []
            if isinstance(item.get("LEXEntryCode"), str)
        }
        if not verified_ln:
            raise ValueError("Reviewed pronoun UBS entry has no original semantic codes")
        reviewed[lemma] = {"ubs_main_id": mid, "original_ln": verified_ln,
                           "rationale": decision["rationale"], "parts": sorted(parts)}
    if len(reviewed) != 3:
        raise ValueError("This editorial batch is restricted to three reviewed pronouns")
    return reviewed


def make_reviewed(baseline, baseline_raw, source_report, candidate, ledger,
                  english, french, macula_path):
    if (candidate.get("editorial_candidate", {}).get("status") != PREVIEW["STATUS"]
            or candidate["editorial_candidate"]["publication_approved"] is not False
            or candidate["editorial_candidate"]["editorial_acceptance"] !=
                "pending_separate_review"
            or source_report.get("methods", {}).get("source_word_links_accepted") is not False):
        raise ValueError("Input is not an unapproved frozen original-source preview")
    # Verify the original complete source inventory AGAIN, independently of
    # the previously staged CI artifact; no inherited attestations are trusted.
    validated = PREVIEW["independently_verify"](
        source_report, baseline, english, french, macula_path
    )
    if candidate["by_macula_word"] != validated:
        raise ValueError("Greek preliminary source-word candidate drift")
    for key, original in baseline.items():
        if candidate.get(key) != original:
            raise ValueError("Historical bilingual UBS index changed: " + key)
    groups = review_ledger(ledger, source_report, english, french)
    output = copy.deepcopy(candidate)
    counts = Counter()
    original_by_headword = Counter()
    approved_ids = set()
    for wid, rec in output["by_macula_word"].items():
        original = validated[wid]
        if rec != original:
            raise ValueError("Original word-specific lexical source witness changed")
        key = nfc(rec["original_lemma"])
        decision = groups.get(key)
        if decision is None:
            counts["original_unapproved_other_greek_words"] += 1
            continue
        if decision["ubs_main_id"] != rec["entry_id"]:
            raise ValueError("Editorial plan doesn't match original UBS headword")
        if rec["original_class"] != "pron":
            counts["original_matching_lemma_non_pronoun_words_left_unapproved"] += 1
            continue
        if (not rec["original_morph"] or not rec["original_reference"]
                or not rec["original_strong"].isdigit()
                or not rec["corroborating_ubs_ln_codes"]
                or not set(rec["corroborating_ubs_ln_codes"]).issubset(
                    decision["original_ln"])):
            raise ValueError("Unsupported original Greek pronoun source evidence")
        # Approved only for the *source-original word*, never for its Strong
        # family or an Louw–Nida sense: those annotations are untouched.
        rec["match_type"] = APPROVED
        counts["reviewed_source_pronoun_original_words"] += 1
        original_by_headword[key] += 1
        approved_ids.add(wid)
    if not approved_ids or len(original_by_headword) != len(groups):
        raise ValueError("No original source-bound pronoun evidence for one reviewed group")
    if (dict(sorted(original_by_headword.items())) !=
            ledger.get("source_verified_individual_word_counts")
            or len(approved_ids) !=
                ledger.get("original_source_word_approvals_total")
            or 5938 - len(approved_ids) !=
                ledger.get("remaining_5938_source_candidate_words_unapproved")):
        raise ValueError("Original Greek source-witnessed pronoun acceptance ledger drift")
    if (len(output["by_macula_word"]) != 5938
            or counts["reviewed_source_pronoun_original_words"] +
                counts["original_unapproved_other_greek_words"] +
                counts["original_matching_lemma_non_pronoun_words_left_unapproved"]
                != 5938):
        raise ValueError("Original complete Greek preview inventory not conserved")
    output["editorial_candidate"] = {
        **candidate["editorial_candidate"],
        "status": APPROVAL_STATUS,
        "editorial_acceptance": "three_original_greek_pronoun_headword_families_only",
        "source_pronoun_headword_approvals": counts[
            "reviewed_source_pronoun_original_words"],
        "other_original_words_still_unapproved": (
            5938 - counts["reviewed_source_pronoun_original_words"]),
        "source_specific_approved_headwords": dict(sorted(original_by_headword.items())),
        "editorial_source": "v1_reviewed_pronoun_headwords.json",
        "original_private_preview_sha256": sha256(canonical(candidate)),
        "source_editions": source_report["source_editions"],
        "new_inferred_contextual_lexical_sense_ids": 0,
        "original_index_sha256": sha256(baseline_raw),
        "publication_approved": False,
    }
    output["word_aware_coverage"] = {
        **candidate["word_aware_coverage"],
        "editorially_reviewed_pronoun_word_headwords": counts[
            "reviewed_source_pronoun_original_words"],
        "other_unapproved_word_headword_candidates": (
            5938 - counts["reviewed_source_pronoun_original_words"]),
        "new_inferred_contextual_lexical_sense_ids": 0,
    }
    # Every historical source linkage stays identical. New word-level
    # records differ from the original PREVIEW only in reviewed match_type.
    for key, value in candidate.items():
        if key not in ("editorial_candidate", "word_aware_coverage", "by_macula_word"):
            if output[key] != value:
                raise ValueError("Candidate source/Strong mapping was altered: " + key)
    for wid, record in output["by_macula_word"].items():
        old = candidate["by_macula_word"][wid]
        if {k:v for k,v in record.items() if k != "match_type"} != {
            k:v for k,v in old.items() if k != "match_type"
        }:
            raise ValueError("Original Greek WLC word identity mutated: " + wid)
        if (wid in approved_ids) != (record["match_type"] == APPROVED):
            raise ValueError("Unapproved Greek lexical entry promoted: " + wid)
    return output


def lookup_reviewed(candidate, word_id, reference, lemma, strong, ln, morph):
    item = (candidate.get("by_macula_word") or {}).get(word_id)
    if item is None:
        return PREVIEW["lookup_word"](candidate, word_id, reference, lemma,
                                      strong, ln, morph)
    if item.get("match_type") != APPROVED:
        return PREVIEW["lookup_word"](candidate, word_id, reference, lemma,
                                      strong, ln, morph)
    if any((
        item["original_reference"] != reference,
        item["original_lemma"] != lemma,
        item["original_strong"] != strong,
        item["original_ln"] != ln,
        item["original_morph"] != morph,
    )):
        return {"status": "source_edition_or_original_annotation_mismatch",
                "entry_ids": [], "sense_ids": []}
    return {
        "status": "editorially_reviewed_original_greek_pronoun_headword_only",
        "entry_ids": [item["entry_id"]],
        "sense_ids": [],
        "evidence": "exact_original_greek_word_identity_nfc_headword_and_ubs_original_ln",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("baseline", "source_report", "candidate", "review",
                  "english", "french", "macula", "output"):
        p.add_argument("--" + field, type=Path, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    baseline_raw = a.baseline.read_bytes()
    result = make_reviewed(read(a.baseline), baseline_raw,
                           read(a.source_report), read(a.candidate),
                           read(a.review), read(a.english), read(a.french),
                           a.macula)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(canonical(result))
    print("UBS_GREEK_REVIEWED_PRONOUN_WORDS", json.dumps({
        "source_specific_approved_headwords":
            result["editorial_candidate"]["source_specific_approved_headwords"],
        "reviewed_source_pronoun_original_words":
            result["editorial_candidate"]["source_pronoun_headword_approvals"],
        "unapproved_original_word_candidates":
            result["editorial_candidate"]["other_original_words_still_unapproved"],
        "private_candidate_sha256": sha256(a.output.read_bytes()),
        "inferred_contextual_ubs_sense_ids": 0,
        "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

