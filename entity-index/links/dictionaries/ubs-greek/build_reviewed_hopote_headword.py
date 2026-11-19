#!/usr/bin/env python3
"""Review the sole exact Greek temporal headword, preserving both source POS taxonomies.

The original MACULA source says class conj and morphology ADV; the authentic
UBS EN/FR lexicon says advb. A unique original Greek NFC lemma and bilingual
Louw–Nida 67.30 independently establish HEADWORD identity at exactly this
source word ID without changing original class, meaning or historic Strong.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
import unicodedata
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=runpy.run_path(str(HERE/"audit_hopote_original_word.py"))
OLD="nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
NEW="source_reviewed_original_greek_temporal_headword_conj_vs_adverb_taxonomy_only"
POLICY={
    "exact_original_macula_word_id": True,
    "original_greek_lemma_nfc_equal_ubs": True,
    "original_greek_and_strong_unchanged": True,
    "original_source_conj_class_retained": True,
    "original_source_adv_morphology_retained": True,
    "original_ubs_advb_pos_retained": True,
    "original_bilingual_ln_lexical_code_attested": True,
    "no_contextual_ubs_lexid": True,
    "no_global_strong_alias": True,
    "historical_index_unchanged": True,
    "publication_approved": False,
}


def nfc(v):return unicodedata.normalize("NFC",v)


def ledger_approval(ledger,evidence):
    if (ledger.get("schema_version")!=1
        or ledger.get("status")!="PRIVATE_source_attested_Greek_temporal_lexical_headword_only_original_word_review"
        or ledger.get("source_editions")!=evidence.get("source_editions")
        or ledger.get("editorial_policy")!=POLICY
        or ledger.get("previous_extra_reviewed_original_headwords")!=9194
        or ledger.get("original_word_specific_new_headwords")!=1
        or ledger.get("no_ubs_source_lemma_words_still_unmatched")!=456):
        raise ValueError("Greek temporal conjunction/adverb editorial source authorization drift")
    decision=ledger["reviewed_original_word"]
    immutable=("original_word_id","original_lemma","original_strong",
               "original_ln","original_reference","original_class","original_morph")
    if any(decision.get(k)!=evidence.get(k) for k in immutable):
        raise ValueError("Exact original Greek temporal word ID, lemma, Strong, LN, verse or morph changed")
    if (decision["original_class"]!="conj"
        or decision["original_morph"]!="ADV"
        or nfc(decision["original_lemma"])!=nfc(evidence["ubs_original_lemma_en"])
        or decision["ubs_main_id"]!=evidence["ubs_original_main_id"]
        or decision["ubs_original_pos_en"]!=evidence["ubs_original_pos_en"]
        or decision["ubs_original_pos_fr"]!=evidence["ubs_original_pos_fr"]
        or decision["ubs_ln_code"] not in evidence["corroborated_bilingual_ln"]
        or decision["original_ln"]!=decision["ubs_ln_code"]
        or decision["ubs_original_pos_en"]!=["advb."]
        or decision["ubs_original_pos_fr"]!=["advb."]
        or len(decision["editorial_basis"])<300
        or len(ledger.get("external_grammar_context",[]))<2):
        raise ValueError("Greek original temporal adverb/conjunction headword independent source evidence incomplete")
    return decision


def review(candidate,residual,english,french,evidence,ledger):
    verified=SOURCE["audit"](candidate,residual,english,french)
    if verified!=evidence:
        raise ValueError("Greek original temporal word source evidence report mutated")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total")!=9194
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved")!=1
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or len(candidate.get("by_macula_word",{}))!=9195
        or len(candidate.get("by_macula_ambiguous_word",{}))!=220):
        raise ValueError("Original Greek source word review overlay or existing Strong ambiguities changed")
    decision=ledger_approval(ledger,evidence)
    wid=decision["original_word_id"]
    old=candidate["by_macula_word"].get(wid)
    if not old or old["match_type"]!=OLD or old["entry_id"]!=decision["ubs_main_id"]:
        raise ValueError("Original Greek temporal word-ID source lexeme remains unresolved or previously approved")
    source_values={
        "original_lemma":decision["original_lemma"],
        "original_strong":decision["original_strong"],
        "original_ln":decision["original_ln"],
        "original_reference":decision["original_reference"],
        "original_class":decision["original_class"],
        "original_morph":decision["original_morph"],
        "corroborating_ubs_ln_codes":[decision["ubs_ln_code"]],
    }
    if any(old.get(k)!=v for k,v in source_values.items()):
        raise ValueError("Original Greek temporal source word annotations differ from authoritative evidence")
    out=copy.deepcopy(candidate)
    out["by_macula_word"][wid]["match_type"]=NEW
    if any({k:v for k,v in row.items() if k!="match_type"}!={k:v for k,v in out["by_macula_word"][kword].items() if k!="match_type"}
           for kword,row in candidate["by_macula_word"].items()):
        raise ValueError("Greek original word Strong, LN, morphology or source lemma was modified")
    if any(out[key]!=candidate[key] for key in candidate
           if key not in ("by_macula_word","editorial_candidate","word_aware_coverage")):
        raise ValueError("Historical UBS Greek Strong/lexical index mutated")
    if sum(x["match_type"]==OLD for x in out["by_macula_word"].values())!=0 or sum(x["match_type"]==NEW for x in out["by_macula_word"].values())!=1:
        raise ValueError("Greek sole remaining strict source word was not uniquely reviewed")
    out["editorial_candidate"]={
        **candidate["editorial_candidate"],
        "status":"PRIVATE_source_reviewed_all_original_Greek_lemma_matching_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total":9195,
        "other_original_words_still_unapproved":0,
        "new_source_reviewed_temporal_Greek_headword":1,
        "editorial_source_temporal_taxonomy":"v1_reviewed_hopote_temporal_headword.json",
        "new_inferred_contextual_lexical_sense_ids":0,
        "publication_approved":False,
    }
    out["word_aware_coverage"]={
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords":9195,
        "other_unapproved_word_headword_candidates":0,
        "word_aware_entry_candidate_words":candidate["word_aware_coverage"]["word_aware_entry_candidate_words"],
        "remaining_no_ubs_headword_candidate_original_words":candidate["word_aware_coverage"]["remaining_no_ubs_headword_candidate_original_words"],
        "new_inferred_contextual_lexical_sense_ids":0,
    }
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("candidate","residual","english","french","evidence","ledger","output"):
        p.add_argument("--"+x,type=Path,required=True)
    a=p.parse_args()
    read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
    result=review(read(a.candidate),read(a.residual),read(a.english),
                  read(a.french),read(a.evidence),read(a.ledger))
    a.output.write_bytes((json.dumps(result,sort_keys=True,ensure_ascii=False,
                          separators=(",",":"))+"\n").encode("utf-8"))
    print("GREEK_TEMPORAL_ORIGINAL_WORD_LEXICAL_HEADWORD_REVIEWED",json.dumps({
        "new_original_word_headword":1,
        "additional_individual_source_reviewed_word_headwords":9195,
        "headword_original_word_candidate_coverage":137285,
        "source_original_words":137741,
        "without_any_original_ubs_lexeme_headword":456,
        "original_text_or_morphology_modified":False,
        "new_contextual_sense_ids":0,
        "published":False,
        "sha256":hashlib.sha256(a.output.read_bytes()).hexdigest(),
    },sort_keys=True))


if __name__=="__main__":main()
