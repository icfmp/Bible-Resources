#!/usr/bin/env python3
"""Read-only original Greek source evidence for the sole ὁπότε lexical POS difference."""
from __future__ import annotations
import argparse,json,unicodedata
from pathlib import Path

def nfc(s):return unicodedata.normalize("NFC",s)

def lexical_pos(row):
    return sorted({str(p) for f in row.get("BaseForms") or [] for p in f.get("PartsOfSpeech") or []})

def ln(row):
    return {str(m["LEXEntryCode"]) for f in row.get("BaseForms") or []
            for m in f.get("LEXMeanings") or [] if isinstance(m.get("LEXEntryCode"),str)}

def audit(candidate,residual,english,french):
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total")!=9194
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved")!=1
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or residual.get("source_editions") is None):
        raise ValueError("Original Greek pinned source-review candidate drift")
    rows=[f for f in residual["families"] if f["lemma_nfc"]=="ὁπότε"]
    if len(rows)!=1 or rows[0]["original_word_count"]!=1 or rows[0]["original_classes"]!={"conj":1}:
        raise ValueError("Greek ὁπότε original conjunction source inventory changed")
    family=rows[0]
    mid=family["ubs_main_id"]
    en={x["MainId"]:x for x in english};fr={x["MainId"]:x for x in french}
    if mid not in en or mid not in fr or nfc(en[mid]["Lemma"])!="ὁπότε" or nfc(fr[mid]["Lemma"])!="ὁπότε":
        raise ValueError("Original UBS Greek bilingual ὁπότε headword absent")
    if lexical_pos(en[mid])!=["advb."] or lexical_pos(fr[mid])!=["advb."]:
        raise ValueError("Original Greek ὁπότε UBS grammatical source unexpected")
    w=family["all_original_word_witnesses"][0]
    row=candidate["by_macula_word"].get(w["word_id"])
    if (not row or row["match_type"]!="nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"
        or row["entry_id"]!=mid or row["original_lemma"]!=w["original_lemma"]
        or row["original_ln"]!=w["original_ln"] or row["original_reference"]!=w["reference"]
        or row["original_morph"]!=w["original_morph"] or row["original_class"]!="conj"):
        raise ValueError("Original Greek word-ID original source morphology/LN changed")
    domains=sorted(set(w["original_ln"].split())&ln(en[mid])&ln(fr[mid]))
    if not domains or domains!=w["attested_headword_ln_codes"]:
        raise ValueError("Original Greek source lexical LN domain not attested in both UBS editions")
    return {"status":"PRIVATE_single_Greek_temporal_lexeme_POS_evidence_UNAPPROVED",
            "source_editions":residual["source_editions"],
            "original_word_id":w["word_id"],"original_lemma":w["original_lemma"],
            "original_strong":w["original_strong"],"original_ln":w["original_ln"],
            "original_class":w["original_class"],"original_reference":w["reference"],
            "original_morph":w["original_morph"],"corroborated_bilingual_ln":domains,
            "ubs_original_lemma_en":en[mid]["Lemma"],"ubs_original_lemma_fr":fr[mid]["Lemma"],
            "ubs_original_main_id":mid,"ubs_original_pos_en":lexical_pos(en[mid]),
            "ubs_original_pos_fr":lexical_pos(fr[mid]),
            "no_contextual_lexid_inferred":True,"publication_approved":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("candidate","residual","english","french","output"):
        p.add_argument("--"+x,type=Path,required=True)
    a=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding="utf-8-sig"))
    r=audit(read(a.candidate),read(a.residual),read(a.english),read(a.french))
    a.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_HOPOTE_SINGLE_ORIGINAL_WORD_EVIDENCE",json.dumps(r,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
