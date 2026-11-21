#!/usr/bin/env python3
"""Read-only editorial evidence for 459 Greek words lacking an exact UBS headword.

The original Greek word IDs, Strong, Louw–Nida, morphology and references
are preserved. Original UBS EN/FR dictionary MainIds are consulted solely
for exact case-folded *diagnostics* and independent lexical-domain
co-occurrence; neither is a justified lexical headword equivalence,
automatic matching algorithm, contextual LEXID or publication.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED = "PRIVATE_source_pinned_Greek_unresolved_499_plus_224_ambiguities"


def nfc(s):
    return unicodedata.normalize("NFC", s)


def entries_with_codes(english, french):
    en = {r["MainId"]: r for r in english}
    fr = {r["MainId"]: r for r in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Pinned UBS Greek English/French entry inventory differs")
    exact, case, strong, by_ln = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
    for mid, row in en.items():
        if nfc(fr[mid]["Lemma"]) != nfc(row["Lemma"]):
            raise ValueError("Original UBS bilingual Greek lexeme spelling drift")
        lemma = nfc(row["Lemma"])
        exact[lemma].add(mid)
        case[lemma.casefold()].add(mid)
        if not lemma:
            raise ValueError("UBS dictionary headword missing")
        for source_strong in row.get("StrongCodes") or []:
            strong[source_strong].add(mid)
        codes_en = {
            m["LEXEntryCode"] for form in row.get("BaseForms") or []
            for m in form.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"), str)
        }
        codes_fr = {
            m["LEXEntryCode"] for form in fr[mid].get("BaseForms") or []
            for m in form.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"), str)
        }
        if codes_en != codes_fr:
            raise ValueError("Pinned UBS bilingual Greek LN code inventory differs")
        for code in codes_en:
            by_ln[code].add(mid)
    return en, exact, case, strong, by_ln


def audit(source, english, french):
    if (source.get("status") != EXPECTED
        or source.get("original_exception_counts", {}).get("no_nfc_identical_ubs_lemma") != 459
        or source.get("source_text_or_annotations_changed") is not False
        or source.get("publication_approved") is not False):
        raise ValueError("Original Greek 459-word source exception provenance drift")
    en, exact, case, strong, by_ln = entries_with_codes(english, french)
    groups = []
    observed_ids = set()
    total = 0
    categories = Counter()
    for family in source["original_exception_groups"]:
        if family["source_reason"] != "no_nfc_identical_ubs_lemma":
            continue
        lemma = family["lemma_nfc_comparison_only"]
        original_strong = family["original_strong"]
        witnesses = family["original_word_witnesses"]
        if (nfc(lemma) != lemma or not witnesses
            or len(witnesses) != family["original_word_count"]
            or exact.get(lemma)):
            raise ValueError("Original missing Greek source headword family has exact UBS match")
        original_classes, original_ln = Counter(), Counter()
        for row in witnesses:
            wid = row["original_word_id"]
            if (wid in observed_ids or nfc(row["original_lemma"]) != lemma
                or row["original_strong"] != original_strong
                or not row["original_reference"] or not row["original_morph"]):
                raise ValueError("Original Greek missing-headword source word-ID witness drift")
            observed_ids.add(wid)
            original_classes[row["original_class"]] += 1
            original_ln.update(row["original_ln"].split())
        case_only = sorted(case.get(lemma.casefold(), set()))
        source_strong_heads = sorted(strong.get("G" + original_strong, set())) if original_strong.isdigit() else []
        lex_domain_heads = sorted(set().union(*(by_ln.get(c, set()) for c in original_ln)) if original_ln else set())
        # Diagnostic evidence is not an editorially accepted equivalence.
        diagnostic = "case_insensitive_Ubs_spelling_present_NOT_APPROVED" if case_only else (
            "source_strong_attested_in_UBS_under_another_lemma_NOT_APPROVED" if source_strong_heads
            else "no_lexeme_spelling_or_strong_equivalence_in_pinned_UBS")
        categories[diagnostic] += len(witnesses)
        groups.append({
            "original_greek_lemma_nfc_for_comparison": lemma,
            "original_source_strong": original_strong,
            "original_word_count": len(witnesses),
            "original_source_classes": dict(sorted(original_classes.items())),
            "original_ln_code_counts": dict(sorted(original_ln.items())),
            "source_original_word_witnesses": witnesses,
            "ubs_case_only_spelling_main_ids": case_only,
            "ubs_exact_original_strong_main_ids_other_lemma": source_strong_heads,
            "ubs_shared_original_ln_headword_candidate_count_NOT_identity": len(lex_domain_heads),
            "ubs_shared_original_ln_headword_main_id_sample_NOT_identity": lex_domain_heads[:12],
            "classification": diagnostic,
            "editorial_status": "UNAPPROVED_no_exact_original_ubs_greek_lemma",
            "generated_strong_alias": None,
            "inferred_contextual_ubs_lexid": None,
        })
        total += len(witnesses)
    if total != 459 or len(observed_ids) != 459:
        raise ValueError("Original Greek 459-word source family count drift")
    groups.sort(key=lambda x: (-x["original_word_count"],
                               x["original_greek_lemma_nfc_for_comparison"],
                               x["original_source_strong"]))
    return {
        "status": "PRIVATE_459_UBS_Greek_v1_0_missing_exact_headword_source_evidence_ONLY",
        "source_editions": source["source_editions"],
        "original_words": total,
        "original_families": len(groups),
        "diagnostic_category_original_word_counts": dict(sorted(categories.items())),
        "source_word_families": groups,
        "automatic_lemma_mappings_approved": 0,
        "inferred_contextual_senses": 0,
        "modified_original_greek_or_strong": False,
        "historical_index_modified": False,
        "publication_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("source", "english", "french", "output"):
        p.add_argument("--" + k, required=True, type=Path)
    a = p.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    data = audit(read(a.source), read(a.english), read(a.french))
    a.output.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_CASEFOLD_SOURCE_EVIDENCE", json.dumps([{"lemma": x["original_greek_lemma_nfc_for_comparison"], "word_count": x["original_word_count"], "source_classes": x["original_source_classes"], "original_strong": x["original_source_strong"], "original_ln_codes": x["original_ln_code_counts"], "casefold_original_ubs_entry_ids": x["ubs_case_only_spelling_main_ids"]} for x in data["source_word_families"] if x["ubs_case_only_spelling_main_ids"]], ensure_ascii=False, sort_keys=True))
    print("GREEK_459_SOURCE_MISSING_UBS_ORIGINAL_HEADWORDS", json.dumps({
        "original_words": data["original_words"],
        "families": data["original_families"],
        "diagnostic_word_counts": data["diagnostic_category_original_word_counts"],
        "largest_source_families": [
            {"lemma": x["original_greek_lemma_nfc_for_comparison"],
             "words": x["original_word_count"],
             "diagnostic": x["classification"],
             "casefold_ubs_entry_count": len(x["ubs_case_only_spelling_main_ids"]),
             "same_source_strong_ubs_entry_count": len(x["ubs_exact_original_strong_main_ids_other_lemma"]),
             "ln_related_entry_count_not_identity": x["ubs_shared_original_ln_headword_candidate_count_NOT_identity"]}
            for x in data["source_word_families"][:25]],
        "new_approved": 0,
        "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
