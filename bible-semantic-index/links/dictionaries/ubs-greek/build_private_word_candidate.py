#!/usr/bin/env python3
"""Build source-verified, UNAPPROVED UBS Greek word-ID candidate overlay.

The original UBS Greek EN/FR 1.0 entries and MACULA Greek SBLGNT original
word IDs are separately verified from exact official source revisions. All
historical lexical maps and source text remain untouched. This builder
does not declare editorial approval or publish any semantic information.

A Unicode NFC-equal lexeme and an exactly attested Louw–Nida code in the
unique original UBS headword allow a *candidate headword*, not a guaranteed
contextual sense. Original Strong source fields are immutable and are not
made global aliases of other Strong values.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import runpy
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
WORD_ID = re.compile(r"n[0-9]{11}\Z")
LEXICAL_CODE = re.compile(r"[0-9]+\.[0-9]+[a-z]?\Z")
MATCH_TYPE = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
STATUS = "private_original_word_candidate_not_editorially_approved_not_published"
FIELDS = {
    "original_word_id": "xml:id",
    "original_reference": "ref",
    "original_lemma": "lemma",
    "original_strong": "strong",
    "original_ln": "ln",
    "original_class": "class",
    "original_morph": "morph",
}


def nfc(value):
    return unicodedata.normalize("NFC", value)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(data):
    return (json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def original_ubs(english, french, old_index):
    rebuilt = BUILD["build"](english, french)
    if any(rebuilt[k] != old_index[k] for k in (
            "by_ln", "by_strong", "statistics", "dictionary", "macula",
            "format", "schema_version", "languages", "license")):
        raise ValueError("Pinned bilingual UBS v1 source or original index drift")
    if (rebuilt["dictionary"]["revision"] != BUILD["UBS_REVISION"]
            or rebuilt["macula"]["revision"] != BUILD["MACULA_REVISION"]
            or old_index["coverage"]["macula_words"] != 137741
            or old_index["coverage"]["with_ubs_entry_candidates"] != 128090):
        raise ValueError("Unexpected Greek original corpus edition or baseline")
    by_id = {e["MainId"]: e for e in english}
    if len(by_id) != len(english):
        raise ValueError("Duplicate original UBS MainId")
    by_lemma = defaultdict(set)
    by_ln = {}
    for e in english:
        mid = e["MainId"]
        by_lemma[nfc(e["Lemma"])].add(mid)
        by_ln[mid] = {d["LEXEntryCode"] for b in e.get("BaseForms") or []
                      for d in b.get("LEXMeanings") or []
                      if isinstance(d.get("LEXEntryCode"), str)
                      and LEXICAL_CODE.fullmatch(d["LEXEntryCode"])}
    return by_id, by_lemma, by_ln


def independently_verify(ledger, index, english, french, macula):
    if (ledger.get("status") !=
            "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release"
            or ledger.get("source_editions") != {
                "ubs_greek_edition": "1.0",
                "ubs_revision": BUILD["UBS_REVISION"],
                "macula_sblgnt_revision": BUILD["MACULA_REVISION"]
            } or ledger.get("methods", {}).get("source_word_links_accepted") is not False
            or ledger.get("methods", {}).get("contextual_ubs_sense_ids_inferred") != 0):
        raise ValueError("Original unapproved source-word register drift")
    expected = ledger["summary"]
    if (expected.get("missing_original_word_entry") != 9651
            or expected.get("existing_ubs_entry_words") != 128090
            or expected.get("dual_source_lemma_and_ln_candidate_unapproved") != 5938
            or expected.get("nfc_lemma_only_no_attested_ubs_ln") != 3249
            or expected.get("no_nfc_identical_ubs_lemma") != 459
            or expected.get("unsupported_original_compound_strong") != 5
            or expected.get("original_macula_words") != 137741
            or expected.get("original_missing_families") != 238):
        raise ValueError("Original Greek unresolved population changed")
    by_id, by_lemma, by_ln = original_ubs(english, french, index)
    witnesses = ledger["unapproved_source_word_headword_preview"]
    if len(witnesses) != 5938:
        raise ValueError("Approved historical inventory/preview length changed")
    seen = set()
    validated = {}
    totals = Counter()
    with macula.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        for row in rows:
            wid = row["xml:id"]
            if not WORD_ID.fullmatch(wid) or wid in seen:
                raise ValueError("Missing/duplicate/malformed original Greek token word ID")
            seen.add(wid)
            totals["source_word_records"] += 1
            old = BUILD["lookup"](index, row["strong"], row["ln"])
            if old["entry_ids"]:
                totals["already_linked_unchanged"] += 1
                if wid in witnesses:
                    raise ValueError("Unapproved preview overwrites original Strong link")
                continue
            totals["unmatched_original_word_records"] += 1
            ref = witnesses.get(wid)
            if ref is None:
                continue
            if (ref.get("status") != "source_candidate_NOT_editorially_approved"
                    or any(ref.get(key) != row[source] for key, source in FIELDS.items())
                    or ref.get("contextual_ubs_sense_id") is not None):
                raise ValueError("Unapproved Greek source record changed: " + wid)
            mid = ref["ubs_main_id"]
            entry = by_id.get(mid)
            if not entry or entry["Lemma"] != ref.get("ubs_original_lemma"):
                raise ValueError("UBS headword missing from original source: " + wid)
            if by_lemma[nfc(row["lemma"])] != {mid}:
                raise ValueError("Greek headword lemma differs or is homographic: " + wid)
            codes = tuple(sorted({
                code for code in row["ln"].split()
                if LEXICAL_CODE.fullmatch(code) and code in by_ln[mid]
            }))
            if (not codes or list(codes) != ref["shared_attested_ln_codes"]
                    or not row["strong"].isdigit()):
                raise ValueError("Original Greek Louw-Nida corroboration not attested: " + wid)
            # Never infer source contextual lexical sense or rewrite original Strong.
            validated[wid] = {
                "entry_id": mid,
                "match_type": MATCH_TYPE,
                "original_lemma": row["lemma"],
                "original_strong": row["strong"],
                "original_ln": row["ln"],
                "original_reference": row["ref"],
                "original_class": row["class"],
                "original_morph": row["morph"],
                "corroborating_ubs_ln_codes": list(codes),
            }
            totals["word_specific_entry_only_candidates"] += 1
    if seen != set(witnesses).union(seen):
        raise ValueError("Source-preview word-ID inventory contains alien IDs")
    if totals != {
        "source_word_records": 137741,
        "already_linked_unchanged": 128090,
        "unmatched_original_word_records": 9651,
        "word_specific_entry_only_candidates": 5938,
    }:
        raise ValueError("Source full-corpus independent verification drift: "
                         + json.dumps(dict(totals), sort_keys=True))
    if set(validated) != set(witnesses):
        raise ValueError("Original-source verified candidate identity incomplete")
    return dict(sorted(validated.items()))


def lookup_word(candidate, word_id, reference, lemma, strong, ln, morph):
    """Fail closed for non-source-matching token; never return a guessed sense."""
    data = (candidate.get("by_macula_word") or {}).get(word_id)
    if data is None:
        return {
            "status": "no_reviewed_source_word_candidate",
            "entry_ids": [], "sense_ids": [],
        }
    if any((
        data["original_reference"] != reference,
        data["original_lemma"] != lemma,
        data["original_strong"] != strong,
        data["original_ln"] != ln,
        data["original_morph"] != morph,
    )):
        return {
            "status": "source_edition_or_original_annotation_mismatch",
            "entry_ids": [], "sense_ids": [],
        }
    if data["match_type"] != MATCH_TYPE:
        return {
            "status": "unrecognized_editorial_match_type",
            "entry_ids": [], "sense_ids": [],
        }
    return {
        "status": "unapproved_original_word_entry_candidate_only",
        "entry_ids": [data["entry_id"]],
        "sense_ids": [],
        "evidence": "source_word_nfc_lemma_and_ln_bilingual_dictionary",
        "matched_source_ln_codes": data["corroborating_ubs_ln_codes"],
    }


def build_candidate(original, original_bytes, report, english, french, macula):
    validated = independently_verify(report, original, english, french, macula)
    candidate = copy.deepcopy(original)
    candidate["by_macula_word"] = validated
    candidate["word_aware_coverage"] = {
        "original_sblgnt_word_records": 137741,
        "existing_strong_entry_candidate_words_unchanged": 128090,
        "new_unapproved_source_word_entry_candidates": 5938,
        "word_aware_entry_candidate_words": 134028,
        "remaining_no_ubs_headword_candidate_original_words": 3713,
        "existing_corresponding_sense_candidate_words_unchanged": 118272,
        "new_inferred_contextual_lexical_sense_ids": 0,
        "preexisting_ambiguous_strong_entry_words_unchanged": 224,
        "original_gap_classes_still_unlinked": {
            "nfc_lemma_only_no_attested_ubs_ln": 3249,
            "no_nfc_identical_ubs_lemma": 459,
            "unsupported_original_compound_strong": 5,
        },
    }
    candidate["editorial_candidate"] = {
        "status": STATUS,
        "original_index_left_unchanged": True,
        "original_source_corpora_left_unchanged": True,
        "original_index_sha256": sha256(original_bytes),
        "source_editions": report["source_editions"],
        "word_id_specific_unapproved_entry_only_candidates": 5938,
        "inferred_contextual_lexical_sense_ids": 0,
        "headword_evidence": "exact_original_macula_word_id_plus_canonical_lemma_and_UBS_original_LN",
        "editorial_acceptance": "pending_separate_review",
        "publication_approved": False,
    }
    for key, value in original.items():
        if candidate[key] != value:
            raise ValueError("Existing independent original UBS lexical map changed: " + key)
    if len(validated) != 5938:
        raise ValueError("Missing original MACULA source-specific candidate rows")
    for key in ("n40003007019", "n40002006022", "n40003003001"):
        record = validated.get(key)
        if record is None:
            raise ValueError("Original Greek pronoun witness absent: " + key)
        result = lookup_word(
            candidate, key, record["original_reference"],
            record["original_lemma"], record["original_strong"],
            record["original_ln"], record["original_morph"])
        if (result["status"] != "unapproved_original_word_entry_candidate_only"
                or len(result["entry_ids"]) != 1 or result["sense_ids"]):
            raise ValueError("Original Greek word-specific safe lookup failed")
    for key in ("n40001020030", "n40001018019", "n40001020005"):
        if key in validated:
            raise ValueError("Unsupported Greek original source lexical word linked: " + key)
    return candidate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("index", "report", "english", "french", "macula", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    old_bytes = args.index.read_bytes()
    baseline = json.loads(old_bytes)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    english = json.loads(args.english.read_text(encoding="utf-8-sig"))
    french = json.loads(args.french.read_text(encoding="utf-8-sig"))
    candidate = build_candidate(
        baseline, old_bytes, report, english, french, args.macula)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(candidate))
    print("UBS_GREEK_PRIVATE_WORD_HEADWORD_PREVIEW", json.dumps({
        "candidate_sha256": sha256(args.output.read_bytes()),
        **candidate["word_aware_coverage"],
        "published": False,
        "editorially_approved": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

