#!/usr/bin/env python3
"""Review exact original UBS Greek EN/FR AlternateLemmas for 409 individual word IDs.

This review only adds lexical HEADWORD identity where pinned UBS source
explicitly names the original MACULA lemma as its AlternateLemma and
each original SBLGNT word independently shares original UBS EN+FR
Louw–Nida lexical domain evidence. No contextual LEXID, Strong alias,
source spelling/POS/morphology edit or public release is permitted.
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

HERE=Path(__file__).resolve().parent
AUDIT=runpy.run_path(str(HERE/"audit_ubs_explicit_alternate_lemmas.py"))
STATUS="source_reviewed_explicit_bilingual_ubs_alternate_lemma_original_word_headword_only"
POLICY={
    "source_word_ids_are_exact":True,
    "bilingual_ubs_AlternateLemmas_exact_nfc":True,
    "original_word_specific_bilingual_ln_intersection":True,
    "only_unique_original_ubs_headword":True,
    "source_pos_differences_not_rewritten":True,
    "original_strong_never_aliased":True,
    "no_contextual_lexid_inferred":True,
    "preserve_old_index_and_all_overlays":True,
    "publication_approved":False,
}

def nfc(s):return unicodedata.normalize("NFC",s)

def ln(entry):
    return {str(m["LEXEntryCode"]) for form in entry.get("BaseForms") or []
            for m in form.get("LEXMeanings") or []
            if isinstance(m.get("LEXEntryCode"),str)}

def pos(entry):
    return sorted({str(p) for form in entry.get("BaseForms") or []
                   for p in form.get("PartsOfSpeech") or []})

def check_ledger(ledger,report):
    if (ledger.get("schema_version")!=1
        or ledger.get("status")!="PRIVATE_explicit_UBS_bilingual_original_Greek_alternate_headword_word_id_review"
        or ledger.get("source_editions")!=report.get("source_editions")
        or ledger.get("editorial_policy")!=POLICY
        or ledger.get("previous_individual_word_headword_reviews")!=9195
        or ledger.get("new_explicit_alternate_lemma_word_headword_reviews")!=409
        or ledger.get("original_ubs_lexemes_still_absent")!=47):
        raise ValueError("Original UBS Greek AlternateLemmas editorial source authorization drift")
    selected={}
    for row in ledger["reviewed_original_lexical_families"]:
        key=(row["macula_original_lemma_nfc"],row["macula_original_strong"],row["ubs_original_main_id"])
        if (key in selected or row["macula_original_lemma_nfc"]!=nfc(row["macula_original_lemma_nfc"])
            or row["macula_original_lemma_nfc"]!=row["attested_ubs_original_alternate_lemma"]
            or not row["macula_original_strong"].isdigit()
            or row["macula_original_word_count"]<1
            or not isinstance(row["macula_original_class_counts"],dict)
            or len(row["editorial_disposition"])<250
            or "HEADWORD" not in row["editorial_disposition"]):
            raise ValueError("Unattested original Greek exact alternate lemma editorial family")
        selected[key]=row
    if len(selected)!=20 or sum(x["macula_original_word_count"] for x in selected.values())!=409:
        raise ValueError("Incomplete original Greek 409-word, 20-family alternate lemma review")
    return selected

def build(candidate,report,ledger,english,french):
    verified=AUDIT["audit_from_report"](report,english,french) if "audit_from_report" in AUDIT else None
    # The report is checked exhaustively below using both pinned sources
    # and original individual-word witnesses, not the mere group counts.
    if (report.get("status")!="PRIVATE_Greek_original_UBS_explicit_alternate_lemmas_source_evidence_UNAPPROVED"
        or report.get("original_word_count")!=456
        or report.get("source_evidence_counts")!={"exact_original_ubs_alternate_lemma_and_ln":409,"not_in_original_ubs_alternate_lemmas":47}
        or report.get("new_source_word_lexical_headwords_approved")!=0
        or report.get("publication_approved") is not False):
        raise ValueError("Original Greek UBS explicit alternate lemma source report drift")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total")!=9195
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved")!=0
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or candidate["word_aware_coverage"].get("word_aware_entry_candidate_words")!=137285
        or len(candidate["by_macula_word"])!=9195
        or len(candidate.get("by_macula_ambiguous_word",{}))!=220):
        raise ValueError("Previously reviewed Greek original word lexical overlay drift")
    decisions=check_ledger(ledger,report)
    en={r["MainId"]:r for r in english};fr={r["MainId"]:r for r in french}
    if len(en)!=len(english) or len(fr)!=len(french) or set(en)!=set(fr):
        raise ValueError("Original UBS Greek EN/FR lexical inventory drift")
    selected_ids=set()
    matched_families=set()
    deferred=0
    result=copy.deepcopy(candidate)
    for family in report["source_families"]:
        if family["source_evidence_disposition"]=="not_in_original_ubs_alternate_lemmas":
            if family["original_ubs_explicit_alternate_headwords"] or family["source_original_word_count"]<1:
                raise ValueError("Original Greek nonmatching source lemma unexpectedly matched")
            deferred+=family["source_original_word_count"]
            continue
        if family["source_evidence_disposition"]!="exact_original_ubs_alternate_lemma_and_ln":
            raise ValueError("Source UBS alternate lemma ambiguity or absence cannot be auto-approved")
        links=family["original_ubs_explicit_alternate_headwords"]
        if len(links)!=1 or not links[0]["original_ln_domain_overlap"]:
            raise ValueError("UBS Greek alternate lemma is not uniquely source corroborated")
        link=links[0]
        mid=link["ubs_original_main_id"]
        key=(family["source_original_lemma"],family["source_original_strong"],mid)
        decision=decisions.get(key)
        if (not decision or key in matched_families
            or decision["macula_original_word_count"]!=family["source_original_word_count"]
            or decision["macula_original_class_counts"]!=family["source_original_class_counts"]
            or decision["macula_original_ln_counts"]!=family["source_original_ln_counts"]
            or mid not in en or mid not in fr
            or nfc(en[mid]["Lemma"])!=nfc(decision["ubs_original_main_lemma_nfc"])
            or nfc(fr[mid]["Lemma"])!=nfc(decision["ubs_original_main_lemma_nfc"])
            or decision["ubs_original_pos_en"]!=pos(en[mid])
            or decision["ubs_original_pos_fr"]!=pos(fr[mid])
            or decision["ubs_original_strong_codes_separate"]!=en[mid].get("StrongCodes")
            or decision["ubs_original_strong_codes_separate"]!=fr[mid].get("StrongCodes")
            or key[0] not in {nfc(v) for v in en[mid].get("AlternateLemmas") or [] if v}
            or key[0] not in {nfc(v) for v in fr[mid].get("AlternateLemmas") or [] if v}):
            raise ValueError("Original Greek source explicit UBS bilingual AlternateLemma, POS, lexical ID or Strong evidence drift: "+repr(key))
        matched_families.add(key)
        en_ln=ln(en[mid]);fr_ln=ln(fr[mid])
        if not en_ln or en_ln!=fr_ln:
            raise ValueError("Original UBS Greek bilingual lexical LN-domain source drift")
        expected_ids=set(link["original_word_ids_with_bilingual_source_ln"])
        if link["original_word_ids_without_bilingual_source_ln"] or len(expected_ids)!=family["source_original_word_count"]:
            raise ValueError("A Greek original word lacks individual original UBS LN corroboration")
        observed=set()
        for original in family["source_original_word_witnesses"]:
            wid=original["original_word_id"]
            if (wid in selected_ids or wid in candidate["by_macula_word"]
                or wid in candidate.get("by_macula_ambiguous_word",{})
                or wid not in expected_ids
                or nfc(original["original_lemma"])!=key[0]
                or original["original_strong"]!=key[1]
                or not original["original_reference"]
                or not original["original_class"]
                or not original["original_morph"]):
                raise ValueError("Unattested exact original Greek UBS alternative word-ID witness: "+wid)
            shared=sorted(set(original["original_ln"].split())&en_ln&fr_ln)
            if not shared:
                raise ValueError("No word-specific Greek original UBS bilingual LN witness: "+wid)
            observed.add(wid)
            selected_ids.add(wid)
            result["by_macula_word"][wid]={
                "entry_id":mid,
                "match_type":STATUS,
                "original_lemma":original["original_lemma"],
                "original_strong":original["original_strong"],
                "original_ln":original["original_ln"],
                "original_reference":original["original_reference"],
                "original_class":original["original_class"],
                "original_morph":original["original_morph"],
                "corroborating_ubs_ln_codes":shared,
                "original_ubs_primary_headword":en[mid]["Lemma"],
                "original_ubs_explicit_alternate_lemma":key[0],
                "original_ubs_strong_codes_separate_not_macula_alias":en[mid].get("StrongCodes") or [],
            }
        if observed!=expected_ids:
            raise ValueError("Original Greek bilingual UBS alternate word-ID source inventory incomplete")
    if (matched_families!=set(decisions) or len(selected_ids)!=409 or deferred!=47
        or len(result["by_macula_word"])!=9604):
        raise ValueError("Greek original alternate lexeme corpus counts or editorial decisions incomplete")
    for k,v in candidate.items():
        if k not in ("by_macula_word","editorial_candidate","word_aware_coverage") and result[k]!=v:
            raise ValueError("Original Greek historical Strong, source index or prior ambiguity modified")
    for wid,old in candidate["by_macula_word"].items():
        if result["by_macula_word"][wid]!=old:
            raise ValueError("Earlier source-reviewed original Greek lexical headword mutated")
    result["by_macula_word"]=dict(sorted(result["by_macula_word"].items()))
    result["editorial_candidate"]={
        **candidate["editorial_candidate"],
        "status":"PRIVATE_409_explicit_source_bilingual_UBS_alternate_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total":9604,
        "other_original_words_still_unapproved":0,
        "new_source_explicit_ubs_alternate_word_headwords":409,
        "new_inferred_contextual_lexical_sense_ids":0,
        "editorial_source_explicit_alternate_lemmas":"v1_reviewed_explicit_ubs_alternates.json",
        "publication_approved":False,
    }
    result["word_aware_coverage"]={
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords":9604,
        "word_aware_entry_candidate_words":137694,
        "remaining_no_ubs_headword_candidate_original_words":47,
        "other_unapproved_word_headword_candidates":0,
        "new_source_explicit_ubs_alternate_word_headwords":409,
        "new_inferred_contextual_lexical_sense_ids":0,
    }
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("candidate","report","ledger","english","french","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args();read=lambda x:json.loads(x.read_text(encoding="utf-8-sig"))
    output=build(read(a.candidate),read(a.report),read(a.ledger),read(a.english),read(a.french))
    a.output.write_bytes((json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8"))
    print("GREEK_BILINGUAL_409_ORIGINAL_ALTERNATE_HEADWORD_REVIEWS",json.dumps({
        "new_source_word_headwords":409,
        "all_source_reviewed_new_word_headwords":9604,
        "source_original_greek_word_coverage":137694,
        "remaining_without_attested_ubs_lexical_headword":47,
        "inferred_contextual_senses":0,
        "published":False,
        "sha256":hashlib.sha256(a.output.read_bytes()).hexdigest(),
    },sort_keys=True))
if __name__=="__main__":main()
