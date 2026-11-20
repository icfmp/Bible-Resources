#!/usr/bin/env python3
"""Exact original UBS bilingual AlternateLemmas against 456 source Greek words.

Do not infer contextual lexical senses, Strong aliases, accented
spellings, or dictionary lemmas. Only source-explicit original
AlternateLemmas whose Greek NFC string is equal to an original MACULA
lemma are considered. Every original word ID is kept as witness, and
its original LN corroboration in EN AND FR is reported separately.
"""
from __future__ import annotations
import argparse,json,unicodedata
from collections import defaultdict,Counter
from pathlib import Path


def nfc(v):return unicodedata.normalize("NFC",v)

def source_ln(entry):
    return {str(m["LEXEntryCode"]) for b in entry.get("BaseForms") or []
            for m in b.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"),str)}

def source_pos(entry):
    return sorted({str(p) for b in entry.get("BaseForms") or []
                   for p in b.get("PartsOfSpeech") or []})

def audit(report,english,french):
    if (report.get("status")!="PRIVATE_Greek_456_original_word_ubs_v1_variants_READ_ONLY_NOT_APPROVED"
        or report.get("original_word_count")!=456
        or report.get("new_source_lexical_headword_links")!=0
        or report.get("publication_approved") is not False):
        raise ValueError("Original Greek 456 source-lexeme report drift")
    en={x["MainId"]:x for x in english}
    fr={x["MainId"]:x for x in french}
    if len(en)!=len(english) or len(fr)!=len(french) or set(en)!=set(fr):
        raise ValueError("UBS original bilingual entry inventory mismatch")
    by_alternate=defaultdict(list)
    source_blank_alternate_entries=[]
    for mid,e in en.items():
        f=fr[mid]
        en_alt=e.get("AlternateLemmas") or []
        fr_alt=f.get("AlternateLemmas") or []
        if (nfc(e["Lemma"])!=nfc(f["Lemma"])
            or sorted(nfc(x) for x in en_alt)!=sorted(nfc(x) for x in fr_alt)
            or source_ln(e)!=source_ln(f)):
            raise ValueError("Original UBS EN/FR lemma alternate or LN source mismatch: "+mid)
        if not all(isinstance(x,str) for x in en_alt):
            raise ValueError("Original UBS alternate source lemma non-string: "+mid)
        if any(not x.strip() for x in en_alt):
            source_blank_alternate_entries.append(mid)  # Preserve this genuine source metadata defect.
        for alt in en_alt:
            if alt.strip():
                by_alternate[nfc(alt)].append(mid)
    source_word_ids=set()
    census=Counter()
    families=[]
    for family in report["families"]:
        lemma=family["original_lemma"]
        candidates=sorted(set(by_alternate.get(nfc(lemma),[])))
        source_original_ids=family["original_word_ids"]
        original_witnesses=family["original_word_witnesses"]
        if {w["original_word_id"] for w in original_witnesses}!=set(source_original_ids):
            raise ValueError("Original Greek UBS alternate lexical word ID witness inventory incomplete")
        if len(source_original_ids)!=family["original_words"] or set(source_original_ids)&source_word_ids:
            raise ValueError("Duplicate or incomplete Greek original word-ID source witness")
        source_word_ids.update(source_original_ids)
        source_ln_codes=set(family["original_ln_counts"])
        entries=[]
        for mid in candidates:
            e=en[mid]
            f=fr[mid]
            shared=sorted(source_ln_codes & source_ln(e) & source_ln(f))
            entries.append({
                "ubs_original_main_id":mid,
                "ubs_original_headword_en":e["Lemma"],
                "ubs_original_headword_fr":f["Lemma"],
                "ubs_original_alternate_lemma_nfc":lemma,
                "original_ln_domain_overlap":shared,
                "original_word_ids_with_bilingual_source_ln":[w["original_word_id"] for w in original_witnesses if set(w["original_ln"].split()) & source_ln(e) & source_ln(f)],
                "original_word_ids_without_bilingual_source_ln":[w["original_word_id"] for w in original_witnesses if not (set(w["original_ln"].split()) & source_ln(e) & source_ln(f))],
                "original_ubs_pos_en":source_pos(e),
                "original_ubs_pos_fr":source_pos(f),
                "original_ubs_strong_codes_distinct_from_macula":e.get("StrongCodes") or [],
                "lexical_headword_ONLY_no_contextual_sense":True,
            })
        disposition=("exact_original_ubs_alternate_lemma_and_ln" if len(entries)==1 and entries[0]["original_ln_domain_overlap"]
                     else "multiple_original_ubs_alternate_entries" if len(entries)>1
                     else "exact_original_ubs_alternate_lemma_NO_corresponding_source_ln" if entries
                     else "not_in_original_ubs_alternate_lemmas")
        census[disposition]+=len(source_original_ids)
        families.append({
            "source_original_lemma":lemma,
            "source_original_strong":family["original_strong"],
            "source_original_word_count":family["original_words"],
            "source_original_word_ids":source_original_ids,
            "source_original_word_witnesses":original_witnesses,
            "source_original_ln_counts":family["original_ln_counts"],
            "source_original_class_counts":family["original_class_counts"],
            "original_ubs_explicit_alternate_headwords":entries,
            "source_evidence_disposition":disposition,
            "editorial_status":"UNAPPROVED_original_lemma_alternate_candidate_ONLY",
        })
    if len(source_word_ids)!=456 or sum(census.values())!=456:
        raise ValueError("Incomplete pinned Greek 456 original word-ID lexical family census")
    families.sort(key=lambda x:(-x["source_original_word_count"],x["source_original_lemma"],x["source_original_strong"]))
    return {
        "status":"PRIVATE_Greek_original_UBS_explicit_alternate_lemmas_source_evidence_UNAPPROVED",
        "source_editions":report["source_editions"],
        "original_word_count":456,
        "original_ubs_blank_alternate_lemma_main_ids":sorted(source_blank_alternate_entries),
        "source_evidence_counts":dict(sorted(census.items())),
        "source_families":families,
        "new_source_word_lexical_headwords_approved":0,
        "original_strong_or_lemma_modified":False,
        "new_contextual_ubs_lexids":0,
        "publication_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("report","english","french","output"):
        p.add_argument("--"+x,required=True,type=Path)
    a=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding="utf-8-sig"))
    result=audit(read(a.report),read(a.english),read(a.french))
    a.output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_EXACT_UBS_ALTERNATE_LEMMAS_ORIGINAL_WORDS",json.dumps({
        "counts":result["source_evidence_counts"],
        "families":[{"source_lemma":x["source_original_lemma"],
                     "original_source_words":x["source_original_word_count"],
                     "original_strong":x["source_original_strong"],
                     "source_class":x["source_original_class_counts"],
                     "source_ln_codes":x["source_original_ln_counts"],
                     "disposition":x["source_evidence_disposition"],
                     "authentic_ubs_alternate_candidates":x["original_ubs_explicit_alternate_headwords"]}
                    for x in result["source_families"]
                    if x["source_evidence_disposition"]!="not_in_original_ubs_alternate_lemmas"],
        "approved":False,"published":False,
    },ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
