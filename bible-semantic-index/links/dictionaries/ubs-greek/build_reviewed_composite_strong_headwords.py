#!/usr/bin/env python3
"""Source-review five original Greek word-ID headwords without splitting Strong.

Keep original MACULA composite Strong and independent original UBS
StrongCodes as distinct annotations. An exact original Greek lemma and
independent UBS EN/FR Louw–Nida code support a lexical headword-only
word-ID link; no global Strong alias or contextual lexical sense is inferred.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import runpy
import unicodedata
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=runpy.run_path(str(HERE/"audit_composite_strong_original_words.py"))
STATUS="source_reviewed_original_greek_composite_strong_word_headword_only"
PATTERN=re.compile(r"[1-9][0-9]*(?:\+[1-9][0-9]*)+\Z")
POLICY={
    "original_macula_word_id_required": True,
    "original_compound_strong_preserved_exactly": True,
    "original_greek_nfc_headword_exact": True,
    "require_original_bilingual_ubs_ln_corroboration": True,
    "require_source_grammatical_class_compatible": True,
    "preserve_separate_original_ubs_strong_codes": True,
    "never_alias_macula_composite_to_ubs_strong": True,
    "no_contextual_ubs_lexid_inferred": True,
    "old_index_and_word_annotations_unmodified": True,
    "no_publication": True,
}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def pos(entry):
    return sorted({str(p) for f in entry.get("BaseForms") or []
                   for p in f.get("PartsOfSpeech") or []})


def ln(entry):
    return {str(m["LEXEntryCode"]) for f in entry.get("BaseForms") or []
            for m in f.get("LEXMeanings") or []
            if isinstance(m.get("LEXEntryCode"),str)}


def grammar_supported(source_class, english_parts, french_parts):
    if source_class=="adv":
        return (any("advb" in x.lower() for x in english_parts)
                and any("advb" in x.lower() for x in french_parts))
    if source_class=="noun":
        return (any(x.lower().startswith("noun") for x in english_parts)
                and any(x.lower().startswith("nom") for x in french_parts))
    return False


def review_ledger(ledger, report):
    if (ledger.get("schema_version")!=1
        or ledger.get("status")!="PRIVATE_original_Greek_composite_Strong_word_specific_lexical_headword_review"
        or ledger.get("source_editions")!=report.get("source_editions")
        or ledger.get("editorial_policy")!=POLICY
        or ledger.get("previous_source_word_headword_reviews")!=9189
        or ledger.get("source_word_headword_review_count")!=5
        or ledger.get("strict_lemma_ln_unapproved_original_words")!=1
        or ledger.get("other_original_words_without_equivalent_ubs_headword")!=456):
        raise ValueError("Greek composite source Strong editorial approval, policy or pinned source drift")
    decisions={}
    for row in ledger["reviewed_families"]:
        key=(row["lemma_nfc"],row["original_macula_strong"],row["ubs_main_id"])
        if (key in decisions or nfc(row["lemma_nfc"])!=row["lemma_nfc"]
            or not PATTERN.fullmatch(row["original_macula_strong"])
            or row["original_macula_class"] not in ("adv","noun")
            or row["original_word_count"]<1
            or len(row.get("editorial_basis",""))<250
            or not row["original_ubs_strong_codes"]
            or not row["source_original_ln_code"]
            or not isinstance(row.get("exact_original_word_ids_with_missing_ln_allowed"), list)
            or len(set(row["exact_original_word_ids_with_missing_ln_allowed"])) != len(row["exact_original_word_ids_with_missing_ln_allowed"])):
            raise ValueError("Greek composite original-word lexical decision lacks independent evidence")
        decisions[key]=row
    if len(decisions)!=3 or sum(row["original_word_count"] for row in decisions.values())!=5:
        raise ValueError("Original Greek three composite families and five source words not accounted for")
    return decisions


def review(candidate, raw_source, report, ledger, english, french):
    independently_verified=SOURCE["audit"](raw_source,english,french)
    if independently_verified!=report:
        raise ValueError("Greek five original compound Strong source report drift")
    if (candidate["editorial_candidate"].get("reviewed_original_headword_words_total")!=9189
        or candidate["editorial_candidate"].get("other_original_words_still_unapproved")!=1
        or candidate["editorial_candidate"].get("publication_approved") is not False
        or len(candidate.get("by_macula_ambiguous_word",{}))!=220
        or len(candidate.get("by_macula_word",{}))!=9190):
        raise ValueError("Existing source-reviewed Greek word candidate or ambiguity source drift")
    decisions=review_ledger(ledger,report)
    en={x["MainId"]:x for x in english}
    fr={x["MainId"]:x for x in french}
    if len(en)!=len(english) or len(fr)!=len(french) or set(en)!=set(fr):
        raise ValueError("Original UBS Greek lexical inventory/bilingual IDs changed")
    out=copy.deepcopy(candidate)
    new_ids=set()
    missing_ln_seen=set()
    groups=set()
    for family in report["original_source_lexical_families"]:
        alternatives=family["original_ubs_lexical_headword_candidates_NOT_APPROVED"]
        if (family["source_evidence_disposition"]!="one_original_ubs_nfc_headword_with_attested_original_ln"
            or len(alternatives)!=1 or not alternatives[0]["matching_original_ln_codes"]):
            raise ValueError("Original Greek compound Strong does not have a unique independent lexical headword")
        alt=alternatives[0]
        mid=alt["ubs_original_main_id"]
        key=(family["source_lemma_nfc_for_comparison"],
             family["source_original_composite_strong"],mid)
        decision=decisions.get(key)
        if (decision is None or key in groups
            or family["source_original_word_count"]!=decision["original_word_count"]
            or family["source_original_classes"]!={decision["original_macula_class"]:decision["original_word_count"]}
            or alt["matching_original_ln_codes"]!=[decision["source_original_ln_code"]]
            or alt["source_ubs_strong_codes"]!=decision["original_ubs_strong_codes"]
            or alt["original_ubs_lexical_pos_en"]!=decision["original_ubs_pos_en"]
            or alt["original_ubs_lexical_pos_fr"]!=decision["original_ubs_pos_fr"]
            or not grammar_supported(decision["original_macula_class"],
                                     alt["original_ubs_lexical_pos_en"],
                                     alt["original_ubs_lexical_pos_fr"])
            or mid not in en or mid not in fr
            or nfc(en[mid]["Lemma"])!=key[0] or nfc(fr[mid]["Lemma"])!=key[0]
            or en[mid].get("StrongCodes")!=alt["source_ubs_strong_codes"]
            or fr[mid].get("StrongCodes")!=alt["source_ubs_strong_codes"]
            or pos(en[mid])!=alt["original_ubs_lexical_pos_en"]
            or pos(fr[mid])!=alt["original_ubs_lexical_pos_fr"]):
            raise ValueError("Original Greek compound Strong headword source/grammar/bilingual evidence drift: "+repr(key))
        en_codes,fr_codes=ln(en[mid]),ln(fr[mid])
        if not en_codes or en_codes!=fr_codes:
            raise ValueError("Original UBS Greek composite lexeme LN code parity changed")
        groups.add(key)
        source_zero_ln_ids=set(decision["exact_original_word_ids_with_missing_ln_allowed"])
        family_zero_ln_ids={w["original_word_id"] for w in family["source_original_word_witnesses"] if not w["original_ln"]}
        if source_zero_ln_ids != family_zero_ln_ids:
            raise ValueError("Missing original Greek LN annotations differ from explicit individual-word editorial scope")
        for word in family["source_original_word_witnesses"]:
            wid=word["original_word_id"]
            shared=sorted(set(word["original_ln"].split())&en_codes&fr_codes)
            if (wid in new_ids or wid in candidate["by_macula_word"]
                or wid in candidate.get("by_macula_ambiguous_word",{})
                or word["original_strong"]!=decision["original_macula_strong"]
                or nfc(word["original_lemma"])!=decision["lemma_nfc"]
                or word["original_class"]!=decision["original_macula_class"]
                or not word["original_morph"] or not word["original_reference"]
                or (not shared and (wid not in source_zero_ln_ids or word["original_ln"]))
                or (shared and decision["source_original_ln_code"] not in shared)):
                raise ValueError("Original Greek compound Strong word-ID, lemma, morphology or LN drift: "+repr({"wid":wid,"lemma":word["original_lemma"],"strong":word["original_strong"],"class":word["original_class"],"ln":word["original_ln"],"shared":shared,"expected_ln":decision["source_original_ln_code"],"already_indexed":wid in candidate["by_macula_word"],"already_ambiguous":wid in candidate.get("by_macula_ambiguous_word",{})}))
            new_ids.add(wid)
            if not shared:
                missing_ln_seen.add(wid)
            out["by_macula_word"][wid]={
                "entry_id":mid,
                "match_type":STATUS,
                "original_lemma":word["original_lemma"],
                "original_strong":word["original_strong"],
                "original_ln":word["original_ln"],
                "original_reference":word["original_reference"],
                "original_class":word["original_class"],
                "original_morph":word["original_morph"],
                "corroborating_ubs_ln_codes":shared,
                "ubs_original_strong_codes_separate_not_alias":alt["source_ubs_strong_codes"],
                "source_lexical_headword_evidence":("exact_Greek_lemma_and_compatible_source_class_entry_only_original_LN_absent" if not shared else "exact_Greek_lemma_and_original_bilingual_LN_word_only"),
            }
    if len(groups)!=3 or groups!=set(decisions) or len(new_ids)!=5 or len(out["by_macula_word"])!=9195 or len(missing_ln_seen)!=1:
        raise ValueError("Greek all five source-original compound Strong words were not reviewed")
    for key,value in candidate.items():
        if key not in ("by_macula_word","editorial_candidate","word_aware_coverage") and out[key]!=value:
            raise ValueError("Historical source Greek Strong lexical index or ambiguity review modified")
    for wid,old in candidate["by_macula_word"].items():
        if out["by_macula_word"][wid]!=old:
            raise ValueError("Earlier source-reviewed Greek original word annotation modified")
    out["by_macula_word"]=dict(sorted(out["by_macula_word"].items()))
    out["editorial_candidate"]={
        **candidate["editorial_candidate"],
        "status":"PRIVATE_five_source_Greek_compound_Strong_word_headwords_NOT_PUBLISHED",
        "reviewed_original_headword_words_total":9194,
        "new_original_compound_Strong_word_headwords":5,
        "original_compound_word_ids_with_missing_ln_preserved":sorted(missing_ln_seen),
        "other_original_words_still_unapproved":1,
        "editorial_source_compound_strong":"v1_reviewed_composite_strong_headwords.json",
        "new_inferred_contextual_lexical_sense_ids":0,
        "publication_approved":False,
    }
    out["word_aware_coverage"]={
        **candidate["word_aware_coverage"],
        "editorially_reviewed_original_word_headwords":9194,
        "word_aware_entry_candidate_words":137285,
        "remaining_no_ubs_headword_candidate_original_words":456,
        "source_reviewed_original_compound_Strong_word_headwords":5,
        "source_reviewed_compound_word_headwords_without_original_ln":len(missing_ln_seen),
        "other_unapproved_word_headword_candidates":1,
        "new_inferred_contextual_lexical_sense_ids":0,
    }
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("candidate","raw_source","report","ledger","english","french","output"):
        p.add_argument("--"+x, required=True, type=Path)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    result=review(read(a.candidate),read(a.raw_source),read(a.report),
                  read(a.ledger),read(a.english),read(a.french))
    a.output.write_bytes((json.dumps(result,sort_keys=True,ensure_ascii=False,
                          separators=(",",":"))+"\n").encode("utf-8"))
    print("GREEK_FIVE_ORIGINAL_COMPOSITE_STRONG_HEADWORDS_SOURCE_REVIEWED",json.dumps({
        "additional_original_word_headwords_reviewed":5,
        "original_strong_composites_modified":False,
        "original_words_with_missing_ln_left_missing":1,
        "total_source_reviewed_word_headwords":9194,
        "source_supported_lexical_word_coverage":137284,
        "original_words_without_editorially_approved_headwords":457,
        "contextual_lexids_inferred":0,
        "published":False,
        "sha256":hashlib.sha256(a.output.read_bytes()).hexdigest(),
    },sort_keys=True))


if __name__=="__main__":
    main()
