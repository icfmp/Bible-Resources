#!/usr/bin/env python3
"""Private source-form-based UBS Greek *provisional* word-specific LEXID choices.

The pinned original UBS Greek 1.0 EN/FR explicitly distinguishes ἴδε
(LEXID 003615001008000) from ἰδού[a] (LEXID 003615001009000),
even though both share Louw–Nida 91.13. This is evidence for a
SOURCE-FORM editorial default, not independent verse-context validation.
Only words with exactly these two source candidate LEXIDs are eligible;
a third sense candidate, even in the same family, must remain unresolved.
"""
from __future__ import annotations
import argparse
import json
import unicodedata
from pathlib import Path

MAIN="003615000000000"
IDE="003615001008000"
IDOU="003615001009000"
PAIR={IDE,IDOU}
EXPECTED=223
LEMMA_FORMS={"ἴδε":(IDE,"ἴδε"), "ἰδού":(IDOU,"ἰδού[a]")}


def normalized(value):
    return unicodedata.normalize("NFC",value)


def verify_source(en,fr):
    for language, records in (("en",en),("fr",fr)):
        hits=[r for r in records if r.get("MainId")==MAIN]
        if len(hits)!=1:
            raise ValueError("Missing or duplicated source UBS Greek MainId: "+language)
        selected={}
        for base in hits[0].get("BaseForms") or []:
            for meaning in base.get("LEXMeanings") or []:
                sid=meaning.get("LEXID")
                if sid not in PAIR:continue
                if sid in selected:
                    raise ValueError("Duplicated authentic UBS source LEXID")
                if meaning.get("LEXEntryCode")!="91.13":
                    raise ValueError("UBS source Louw-Nida code drift")
                forms=meaning.get("LEXForms")
                if not isinstance(forms,list) or not all(isinstance(f,str) for f in forms):
                    raise ValueError("Original UBS LEXForms malformed")
                selected[sid]=set(map(normalized,forms))
        if set(selected)!=PAIR:
            raise ValueError("Original UBS form-sensitive LEXIDs absent")
        for lemma,(lexid,source_form) in LEMMA_FORMS.items():
            if normalized(source_form) not in selected[lexid]:
                raise ValueError("Original UBS bilingual form witness absent for "+lemma)
            other=next(iter(PAIR-{lexid}))
            if normalized(source_form) in selected[other]:
                raise ValueError("Original UBS source form does not disambiguate")
    return True


def make(batches,en,fr,expected=EXPECTED):
    if (batches.get("status")!="PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET"
        or batches.get("original_multi_sense_word_count")!=2728
        or batches.get("contextually_verified")!=0
        or batches.get("source_modified") is not False
        or batches.get("published") is not False):
        raise ValueError("Source original Greek review batch identity drift")
    verify_source(en,fr)
    decisions={}
    excluded=[]
    all_original_word_ids=set()
    for batch in batches["review_batches"]:
        mids=set(batch["candidate_ubs_lexids"])
        for word in batch["word_id_evidence"]:
            wid=word["original_word_id"]
            if wid in all_original_word_ids:raise ValueError("Duplicate original Greek word ID")
            all_original_word_ids.add(wid)
            if batch["ubs_main_id"]!=MAIN or batch["original_lemma"] not in LEMMA_FORMS:
                continue
            if (word["original_lemma"]!=batch["original_lemma"]
                or word["editorial_contextual_lexid_selection"] is not None
                or word["contextually_verified"] is not False):
                raise ValueError("Source word evidence drift / prior editorial choice")
            lemma=word["original_lemma"]
            if mids!=PAIR:
                excluded.append({"original_word_id":wid, "original_lemma":lemma,
                                 "original_reference":word["original_reference"],
                                 "source_candidate_lexids":sorted(mids),
                                 "reason":"extra_attested_UBS_sense_candidate_requires_context_review"})
                continue
            if not any(p["original_ln"]=="91.13"
                       and p["original_ubs_lexid"]==LEMMA_FORMS[lemma][0]
                       and p["original_ubs_main_id"]==MAIN
                       for p in word["source_ubs_lexid_candidate_pairs"]):
                raise ValueError("Missing original word-specific LN witness")
            for p in word["source_ubs_lexid_candidate_pairs"]:
                if (p["original_ubs_main_id"]!=MAIN
                    or p["original_ubs_lexid"] not in PAIR
                    or p["original_ln"]!="91.13"):
                    raise ValueError("Original UBS source candidate pair unexpectedly changed")
            lexid,form=LEMMA_FORMS[lemma]
            decisions[wid]={
                **{k:word[k] for k in ("original_word_id","original_reference",
                                     "original_lemma","original_strong","original_ln",
                                     "original_class","original_morph")},
                "ubs_main_id":MAIN,
                "editorial_provisional_ubs_lexid":lexid,
                "original_source_lex_form_with_tag":form,
                "original_source_ln":"91.13",
                "other_attested_candidate_lexids":sorted(mids-{lexid}),
                "editorial_basis":"unique bilingual UBS v1.0 LEXForms witness for exact original Greek lemma, with original MACULA LN",
                "confidence":"source_form_supported_provisional_NOT_contextually_validated",
                "verse_context_semantically_verified":False,
            }
    if len(all_original_word_ids)!=2728 or len(decisions)!=expected:
        raise ValueError("Unexpected original Greek full review coverage or eligible form-word count")
    if expected==EXPECTED and (len(excluded)!=1 or len(decisions)!=223):
        raise ValueError("Unexpected extra form-sensitive UBS Greek candidates")
    return {
        "status":"PRIVATE_Greek_UBS_original_word_form_specific_PROVISIONAL_editorial_LEXIDs",
        "source_editions":batches["source_editions"],
        "all_original_ambiguities":2728,
        "additional_original_word_provisional_choices":len(decisions),
        "new_word_id_to_source_form_supported_provisional_lexid":dict(sorted(decisions.items())),
        "same_family_extra_sense_candidate_not_selected":excluded,
        "all_other_original_ambiguities_still_unselected":2728-len(decisions),
        "independently_contextually_validated":0,
        "source_modified":False,
        "published":False,
        "publication_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("batches","english","french","output"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    out=make(read(a.batches),read(a.english),read(a.french))
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("UBS_GREEK_PRIVATE_SOURCE_FORM_PROVISIONAL_SENSE_DEFAULTS",json.dumps({
        "source_form_supported_provisional":out["additional_original_word_provisional_choices"],
        "excluded_extra_candidate":len(out["same_family_extra_sense_candidate_not_selected"]),
        "still_ambiguous":out["all_other_original_ambiguities_still_unselected"],
        "independently_contextually_validated":0,
        "published":False,
    },sort_keys=True))


if __name__=="__main__":main()
