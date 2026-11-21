#!/usr/bin/env python3
"""Final bounded Greek source-word lexical exceptions and ambiguous Strong census.

All original SBLGNT word IDs are independently reread from the pinned
source and original UBS Greek 1.0 EN/FR dictionaries. The historical Strong
bridge and any private reviewed word-specific overlay remain unchanged.
Matching lexical lemmas / original LN are comparison evidence only.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAPS = runpy.run_path(str(HERE / "audit_source_gaps.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))
PENDING = "nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
EXPECTED = {
    "no_nfc_identical_ubs_lemma": 459,
    "unsupported_original_compound_strong": 5,
    "multiple_existing_ubs_headwords": 224,
    "strict_source_evidence_unapproved": 35,
}


def nfc(value):
    return unicodedata.normalize("NFC", value)


def original_word(row):
    return {
        "original_word_id": row["xml:id"],
        "original_reference": row["ref"],
        "original_lemma": row["lemma"],
        "original_strong": row["strong"],
        "original_ln": row["ln"],
        "original_class": row["class"],
        "original_morph": row["morph"],
    }


def audit(baseline, source_report, reviewed, english, french, macula):
    if (source_report.get("status") !=
            "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release"
        or source_report.get("summary", {}).get("original_macula_words") != 137741
        or source_report.get("summary", {}).get("no_nfc_identical_ubs_lemma") != 459
        or source_report.get("summary", {}).get("unsupported_original_compound_strong") != 5
        or reviewed.get("editorial_candidate", {}).get("reviewed_original_headword_words_total") != 9152
        or reviewed.get("editorial_candidate", {}).get("other_original_words_still_unapproved") != 35
        or reviewed.get("editorial_candidate", {}).get("publication_approved") is not False):
        raise ValueError("Original Greek source exception census/edition drift")
    for k, v in baseline.items():
        if reviewed[k] != v:
            raise ValueError("Historical UBS Greek lexical baseline modified: " + k)
    by_lemma, by_ln = GAPS["source_lexicon"](english, french, baseline)
    en = {entry["MainId"]: entry for entry in english}
    fr = {entry["MainId"]: entry for entry in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Original UBS bilingual lexical headwords drift")
    groups = defaultdict(list)
    summary = Counter()
    ids = set()
    source_rows = 0
    with macula.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            wid = row["xml:id"]
            if wid in ids:
                raise ValueError("Duplicate Greek original word ID: " + wid)
            ids.add(wid)
            source_rows += 1
            reason, headword, codes = GAPS["classify"](row, baseline, by_lemma, by_ln)
            old = BUILD["lookup"](baseline, row["strong"], row["ln"])
            witness = original_word(row)
            if reason == "no_nfc_identical_ubs_lemma":
                if headword is not None or by_lemma.get(nfc(row["lemma"])):
                    raise ValueError("Unattested Greek no-exact-lemma reason")
                groups[("no_nfc_identical_ubs_lemma", row["strong"], nfc(row["lemma"]))].append(witness)
                summary["no_nfc_identical_ubs_lemma"] += 1
            elif reason == "unsupported_original_compound_strong":
                if old["status"] != "unsupported_strong_structure":
                    raise ValueError("Original Greek composite Strong classification drift")
                groups[("unsupported_original_compound_strong", row["strong"], nfc(row["lemma"]))].append(witness)
                summary["unsupported_original_compound_strong"] += 1
            if len(old["entry_ids"]) > 1:
                if reason != "existing_ubs_entry_word":
                    raise ValueError("Original multiple UBS heads aren't previously matched")
                orig_lemma = nfc(row["lemma"])
                same_lemma = sorted(mid for mid in old["entry_ids"] if nfc(en[mid]["Lemma"]) == orig_lemma)
                common_ln = {}
                for mid in old["entry_ids"]:
                    codes = sorted(set(row["ln"].split()) & by_ln[mid])
                    if codes:
                        common_ln[mid] = codes
                if set(old["entry_ids"]) - set(fr):
                    raise ValueError("Original ambiguous candidate lacks French bilingual entry")
                witness["existing_original_ubs_main_ids"] = old["entry_ids"]
                witness["same_nfc_lemma_candidate_main_ids"] = same_lemma
                witness["matching_original_ubs_ln_codes_by_main_id"] = common_ln
                witness["editorial_status"] = "AMBIGUOUS_original_Strong_all_entries_preserved"
                groups[("multiple_existing_ubs_headwords", row["strong"], orig_lemma)].append(witness)
                summary["multiple_existing_ubs_headwords"] += 1
            pending = (reviewed.get("by_macula_word") or {}).get(wid)
            if pending is not None and pending["match_type"] == PENDING:
                if (pending["original_lemma"] != row["lemma"] or
                    pending["original_strong"] != row["strong"] or
                    pending["original_ln"] != row["ln"] or
                    pending["original_reference"] != row["ref"] or
                    pending["original_class"] != row["class"] or
                    pending["original_morph"] != row["morph"]):
                    raise ValueError("Greek original strict unresolved source annotation drift: " + wid)
                witness["preexisting_source_ubs_headword_candidate"] = pending["entry_id"]
                witness["common_attested_ln"] = pending["corroborating_ubs_ln_codes"]
                witness["editorial_status"] = "UNAPPROVED_source_POS_or_Strong_discrepancy"
                groups[("strict_source_evidence_unapproved", row["strong"], nfc(row["lemma"]))].append(witness)
                summary["strict_source_evidence_unapproved"] += 1
    if source_rows != 137741 or dict(summary) != EXPECTED:
        raise ValueError("Original Greek exceptional lexical word-ID census drift: " + repr(summary))
    result = []
    for (reason, strong, lemma), words in groups.items():
        result.append({
            "source_reason": reason,
            "original_strong": strong,
            "lemma_nfc_comparison_only": lemma,
            "original_word_count": len(words),
            "original_word_witnesses": words,
            "editorial_status": "NOT_AUTOMATICALLY_APPROVED_or_RESOLVED",
        })
    result.sort(key=lambda r: (r["source_reason"], -r["original_word_count"],
                               r["lemma_nfc_comparison_only"], r["original_strong"]))
    return {
        "status": "PRIVATE_source_pinned_Greek_unresolved_499_plus_224_ambiguities",
        "source_editions": source_report["source_editions"],
        "all_original_sblgnt_word_rows_audited": source_rows,
        "original_exception_counts": dict(sorted(summary.items())),
        "original_exception_groups": result,
        "source_text_or_annotations_changed": False,
        "new_contextual_ubs_senses_inferred": 0,
        "new_lexical_headword_links_approved": 0,
        "original_ambiguous_ubs_entries_all_preserved": True,
        "publication_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("baseline", "source_report", "reviewed", "english", "french", "macula", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    report = audit(read(a.baseline), read(a.source_report), read(a.reviewed),
                   read(a.english), read(a.french), a.macula)
    a.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_FINAL_ORIGINAL_SOURCE_EXCEPTIONS", json.dumps({
        "summary": report["original_exception_counts"],
        "no_exact_lemma_families": [
            {"lemma": f["lemma_nfc_comparison_only"],
             "source_strong": f["original_strong"],
             "words": f["original_word_count"]}
            for f in report["original_exception_groups"]
            if f["source_reason"] == "no_nfc_identical_ubs_lemma"
        ][:65],
        "composite_strong_families": [
            {"lemma": f["lemma_nfc_comparison_only"],
             "source_strong": f["original_strong"],
             "words": f["original_word_count"]}
            for f in report["original_exception_groups"]
            if f["source_reason"] == "unsupported_original_compound_strong"
        ],
        "source_ambiguity_group_examples": [
            {"lemma": f["lemma_nfc_comparison_only"],
             "source_strong": f["original_strong"],
             "words": f["original_word_count"]}
            for f in report["original_exception_groups"]
            if f["source_reason"] == "multiple_existing_ubs_headwords"
        ][:20],
        "new_approved": 0,
        "publication": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
