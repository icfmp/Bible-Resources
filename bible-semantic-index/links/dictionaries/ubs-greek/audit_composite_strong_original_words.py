#!/usr/bin/env python3
"""Audit five original MACULA composite Strong Greek words without splitting them.

Original source Strong strings like '5228+1537+4053' remain immutable.
Read only original word IDs, Greek NFC lemmas, source LN, morphology and
bilingual original UBS 1.0 lexical entries. Exact Greek headword and
Louw–Nida source agreement may support a future word-ID-only headword
review; they never justify treating any compound component as Strong.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED = "PRIVATE_source_pinned_Greek_unresolved_499_plus_224_ambiguities"
COMPOUND = re.compile(r"[1-9][0-9]*(?:\+[1-9][0-9]*)+\Z")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def original_pos(entry):
    return sorted({str(p) for f in entry.get("BaseForms") or []
                   for p in f.get("PartsOfSpeech") or []})


def ln(entry):
    return {str(m["LEXEntryCode"]) for f in entry.get("BaseForms") or []
            for m in f.get("LEXMeanings") or []
            if isinstance(m.get("LEXEntryCode"), str)}


def audit(report, english, french):
    if (report.get("status") != EXPECTED
        or report.get("original_exception_counts", {}).get("unsupported_original_compound_strong") != 5
        or report.get("publication_approved") is not False):
        raise ValueError("Original Greek composite Strong source-provenance drift")
    en = {x["MainId"]:x for x in english}
    fr = {x["MainId"]:x for x in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("UBS Greek original bilingual entries drift")
    lexemes = defaultdict(list)
    for mid, x in en.items():
        if nfc(fr[mid]["Lemma"]) != nfc(x["Lemma"]):
            raise ValueError("UBS original Greek bilingual headword lemma disagreement")
        lexemes[nfc(x["Lemma"])].append(mid)
    families = []
    count = Counter()
    ids = set()
    for g in report["original_exception_groups"]:
        if g["source_reason"] != "unsupported_original_compound_strong":
            continue
        source_strong = g["original_strong"]
        lemma = g["lemma_nfc_comparison_only"]
        witnesses = g["original_word_witnesses"]
        if (not COMPOUND.fullmatch(source_strong) or
            not witnesses or len(witnesses) != g["original_word_count"]):
            raise ValueError("Unsupported original Greek composite Strong source witness")
        for row in witnesses:
            wid = row["original_word_id"]
            if (wid in ids or row["original_strong"] != source_strong
                or nfc(row["original_lemma"]) != lemma
                or not row["original_reference"] or not row["original_morph"]):
                raise ValueError("Original Greek source composite Strong original-word mismatch")
            ids.add(wid)
        mids = sorted(lexemes.get(lemma, []))
        alternatives = []
        for mid in mids:
            original_ln = set().union(*(w["original_ln"].split() for w in witnesses))
            common_en = sorted(original_ln & ln(en[mid]))
            common_fr = sorted(original_ln & ln(fr[mid]))
            if common_en != common_fr:
                raise ValueError("Original Greek UBS EN/FR composite-lexeme LN disagreement")
            alternatives.append({
                "ubs_original_main_id": mid,
                "ubs_original_headword_en": en[mid]["Lemma"],
                "ubs_original_headword_fr": fr[mid]["Lemma"],
                "original_ubs_lexical_pos_en": original_pos(en[mid]),
                "original_ubs_lexical_pos_fr": original_pos(fr[mid]),
                "matching_original_ln_codes": common_en,
                "source_ubs_strong_codes": en[mid].get("StrongCodes") or [],
                "lexical_entry_not_contextual_sense": True,
            })
        if not mids:
            reason = "no_original_ubs_nfc_identical_headword"
        elif len(mids) > 1:
            reason = "multiple_original_ubs_nfc_identical_headwords"
        elif alternatives[0]["matching_original_ln_codes"]:
            reason = "one_original_ubs_nfc_headword_with_attested_original_ln"
        else:
            reason = "one_original_ubs_nfc_headword_without_original_ln"
        count[reason] += len(witnesses)
        families.append({
            "source_lemma_nfc_for_comparison": lemma,
            "source_original_composite_strong": source_strong,
            "source_original_word_count": len(witnesses),
            "source_original_word_witnesses": witnesses,
            "source_original_classes": dict(sorted(Counter(w["original_class"] for w in witnesses).items())),
            "original_ubs_lexical_headword_candidates_NOT_APPROVED": alternatives,
            "source_evidence_disposition": reason,
            "original_strong_was_split_or_modified": False,
            "new_contextual_ubs_lexid": None,
            "editorial_approved": False,
        })
    if len(ids) != 5 or len(families) != 3 or sum(count.values()) != 5:
        raise ValueError("Original Greek five composite Strong words not exhaustively source-audited")
    families.sort(key=lambda x: (-x["source_original_word_count"],x["source_lemma_nfc_for_comparison"]))
    return {
        "status": "PRIVATE_original_Greek_five_compound_Strong_source_lexeme_review_UNAPPROVED",
        "source_editions": report["source_editions"],
        "original_word_count": 5,
        "original_family_count": 3,
        "source_evidence_disposition_counts": dict(sorted(count.items())),
        "original_source_lexical_families": families,
        "original_strong_components_preserved": True,
        "new_source_headword_links_approved": 0,
        "new_contextual_semantic_senses": 0,
        "publication_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("report","english","french","output"):
        p.add_argument("--"+name, required=True, type=Path)
    a=p.parse_args()
    read=lambda f:json.loads(f.read_text(encoding="utf-8-sig"))
    data=audit(read(a.report),read(a.english),read(a.french))
    a.output.write_text(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("GREEK_FIVE_COMPOSITE_STRONG_SOURCE_LEXICAL_EVIDENCE",json.dumps({
        "source_evidence_counts":data["source_evidence_disposition_counts"],
        "families":[{
            "lemma":f["source_lemma_nfc_for_comparison"],
            "original_composite_strong":f["source_original_composite_strong"],
            "original_word_count":f["source_original_word_count"],
            "original_classes":f["source_original_classes"],
            "original_word_ln_witnesses":[{"word_id":w["original_word_id"],"ln":w["original_ln"],"reference":w["original_reference"]} for w in f["source_original_word_witnesses"]],
            "original_ubs_candidates":f["original_ubs_lexical_headword_candidates_NOT_APPROVED"],
        } for f in data["original_source_lexical_families"]],
        "published":False,
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
