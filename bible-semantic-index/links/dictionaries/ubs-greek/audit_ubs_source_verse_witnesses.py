#!/usr/bin/env python3
"""Conservatively cross-check original UBS Greek LEXReferences against MACULA verses.

All 2,728 originally multi-LEXID MACULA word IDs retain their original
headword/LN/Greek/morph/Strong evidence. This READ-ONLY audit checks whether
one authentic original UBS Greek 1.0 LEXID alone cites the source verse AND
the entire pinned MACULA corpus has only one token of that exact established
UBS headword in that verse. It does NOT infer UBS word-position identity
from different token numbering systems or claim independent contextual
verification. Any competing candidate, ambiguous headword or verse-collision
is preserved as unresolved.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import runpy
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUDIT=runpy.run_path(str(HERE/"audit_contextual_sense_candidates.py"))
BOOKS=("MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI "
       "2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV").split()
BOOK_NUMBER={code:40+i for i,code in enumerate(BOOKS)}
REF_RE=re.compile(r"^([1-3]?[A-Z]{2,3}) (\d+):(\d+)!(\d+)$")
UBS_REF_RE=re.compile(r"^\d{14}$")
EXPECTED=2728


def verse_key(reference):
    m=REF_RE.fullmatch(reference)
    if not m or m.group(1) not in BOOK_NUMBER:
        raise ValueError("Unsupported original MACULA reference: "+repr(reference))
    ch,verse=int(m.group(2)),int(m.group(3))
    if not (0 < ch < 1000 and 0 < verse < 1000):
        raise ValueError("Invalid original Bible reference")
    return f"{BOOK_NUMBER[m.group(1)]:03d}{ch:03d}{verse:03d}"


def source_lexical_references(records, mids):
    out={}
    for entry in records:
        mid=entry.get("MainId")
        if mid not in mids:continue
        found={}
        for form in entry.get("BaseForms") or []:
            for sense in form.get("LEXMeanings") or []:
                sid=sense.get("LEXID")
                if sid not in mids[mid]:continue
                if sid in found:raise ValueError("Duplicated original UBS sense")
                refs=sense.get("LEXReferences")
                if not isinstance(refs,list) or any(not isinstance(r,str) for r in refs):
                    raise ValueError("Malformed original UBS LEXReferences")
                invalid=sorted(set(r for r in refs if not UBS_REF_RE.fullmatch(r)))
                # Invalid source reference metadata must never count as a witness.
                found[sid]={"ln":sense.get("LEXEntryCode"),
                            "verses":set(r[:9] for r in refs if UBS_REF_RE.fullmatch(r)),
                            "invalid":invalid,"source_reference_count":len(refs)}
        if set(found)!=mids[mid]:raise ValueError("Missing original UBS sense reference")
        out[mid]=found
    if set(out)!=set(mids):raise ValueError("Missing UBS headword reference")
    return out


def audit(index,reviewed,batches,en,fr,macula,form_defaults):
    if (batches.get("status")!="PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET"
        or batches.get("original_multi_sense_word_count")!=EXPECTED
        or batches.get("contextually_verified")!=0
        or batches.get("published") is not False):
        raise ValueError("Original source review register drift")
    if (form_defaults.get("additional_original_word_provisional_choices")!=223
        or form_defaults.get("independently_contextually_validated")!=0
        or form_defaults.get("published") is not False):
        raise ValueError("Earlier 223 source-form default decisions drift")
    already=form_defaults["new_word_id_to_source_form_supported_provisional_lexid"]
    if len(already)!=223:raise ValueError("Source form default word-ID coverage drift")
    wanted={}
    mids=defaultdict(set)
    for batch in batches["review_batches"]:
        mid=batch["ubs_main_id"]
        for sid in batch["candidate_ubs_lexids"]:mids[mid].add(sid)
        for word in batch["word_id_evidence"]:
            wid=word["original_word_id"]
            if wid in wanted:raise ValueError("Duplicate original source word-ID")
            if word["editorial_contextual_lexid_selection"] is not None:
                raise ValueError("Previous unreviewed contextual sense assignment")
            if word["original_lemma"]!=batch["original_lemma"]:
                raise ValueError("Original Greek lemma/batch mismatch")
            if set(x["original_ubs_lexid"] for x in word["source_ubs_lexid_candidate_pairs"]) != set(batch["candidate_ubs_lexids"]):
                raise ValueError("Original UBS LEXID source candidate mismatch")
            wanted[wid]={"word":word,"mid":mid,"candidates":set(batch["candidate_ubs_lexids"])}
    if len(wanted)!=EXPECTED or not set(already).issubset(wanted):
        raise ValueError("Original source ambiguities/previously adopted form words drift")
    eng=source_lexical_references(en,mids)
    fra=source_lexical_references(fr,mids)
    corpus_words=set()
    per_verse_headword=Counter()
    original_verses={}
    with macula.open("r",encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream,delimiter="\t"):
            wid=row["xml:id"]
            if wid in corpus_words:raise ValueError("Duplicated original MACULA word ID")
            corpus_words.add(wid)
            verse=verse_key(row["ref"])
            if wid in wanted:
                original_verses[wid]=verse
                witness=wanted[wid]["word"]
                for key,col in (("original_reference","ref"),("original_lemma","lemma"),
                                ("original_strong","strong"),("original_ln","ln"),
                                ("original_class","class"),("original_morph","morph")):
                    if witness[key]!=row[col]:
                        raise ValueError("Original word-specific source witness drift: "+wid)
            # Build exact source-backed headword identity independently of
            # contextual sense codes. Only source-verified unique headwords
            # contribute to verse uniqueness; unknown/ambiguous original words
            # cannot be silently counted as matching one particular headword.
            old=AUDIT["BUILD"]["lookup"](index,row["strong"],row["ln"])
            reviewed_word=reviewed["by_macula_word"].get(wid)
            reviewed_ambiguity=reviewed.get("by_macula_ambiguous_word",{}).get(wid)
            if reviewed_word is not None:
                heads=[reviewed_word["entry_id"]]
            elif reviewed_ambiguity is not None:
                heads=[reviewed_ambiguity["entry_id"]]
            else:
                heads=old["entry_ids"]
            if wid in wanted and wanted[wid]["mid"] not in heads:
                raise ValueError("Original reviewed word missing its authentic UBS headword")
            for mid in set(heads):
                if mid in mids:per_verse_headword[(verse,mid)]+=1
    if len(corpus_words)!=137741 or len(original_verses)!=EXPECTED:
        raise ValueError("Full original MACULA source inventory or review word IDs missing")
    decisions={}
    reasons=Counter()
    examples=defaultdict(list)
    for wid,original in sorted(wanted.items()):
        mid=original["mid"]
        word=original["word"]
        verse=original_verses[wid]
        if wid in already:
            reason="previous_source_form_provisional_choice_not_overwritten"
        elif per_verse_headword[(verse,mid)]!=1:
            reason="multiple_same_UBS_headword_original_words_in_source_verse"
        else:
            candidate_refs={}
            for sid in sorted(original["candidates"]):
                e,f=eng[mid][sid],fra[mid][sid]
                if e["ln"]!=f["ln"]:
                    raise ValueError("Original bilingual UBS source Louw-Nida mismatch")
                if e["invalid"] or f["invalid"]:
                    reason="source_UBS_reference_metadata_malformed_no_choice"
                    break
                if e["verses"]!=f["verses"]:
                    reason="original_UBS_EN_FR_reference_verses_disagree"
                    break
                candidate_refs[sid]=(verse in e["verses"])
            else:
                matches=sorted(sid for sid,confirmed in candidate_refs.items() if confirmed)
                if len(matches)==1:
                    sid=matches[0]
                    decisions[wid]={
                        **{key:word[key] for key in ("original_word_id","original_reference",
                            "original_lemma","original_strong","original_ln","original_class","original_morph")},
                        "ubs_original_main_id":mid,
                        "source_ubs_original_lexid_reference_candidate":sid,
                        "original_MACULA_verse_key":verse,
                        "original_UBS_lexid_verse_reference_count":eng[mid][sid]["source_reference_count"],
                        "other_original_UBS_lexid_candidates":sorted(original["candidates"]-{sid}),
                        "confidence":"original_bilingual_UBS_verse_witness_with_unique_MACULA_lexeme_PROVISIONAL_NOT_contextually_validated",
                        "independently_verse_context_semantically_verified":False,
                    }
                    reason="unique_authentic_bilingual_UBS_sense_verse_witness_candidate"
                elif not matches:reason="no_candidate_UBS_lexid_lists_original_source_verse"
                else:reason="multiple_candidate_UBS_lexids_list_original_source_verse"
        reasons[reason]+=1
        if len(examples[reason])<8:
            examples[reason].append({"original_word_id":wid,"original_reference":word["original_reference"],
                                     "original_lemma":word["original_lemma"],"ubs_main_id":mid})
    if len(decisions)!=reasons["unique_authentic_bilingual_UBS_sense_verse_witness_candidate"]:
        raise ValueError("Source-referenced editorial candidate count drift")
    if sum(reasons.values())!=EXPECTED or set(decisions)&set(already):
        raise ValueError("Greek source word-ID sense review accounting/deduplication drift")
    return {
        "status":"PRIVATE_UBS_Greek_word_specific_original_source_verse_sense_candidate_AUDIT_NOT_CONTEXT_VALIDATION",
        "source_editions":batches["source_editions"],
        "all_initial_original_multi_lexid_words":EXPECTED,
        "previously_staged_source_form_word_ids":len(already),
        "original_reference_witness_candidate_word_count":len(decisions),
        "other_original_multi_lexid_words_still_unresolved":EXPECTED-len(already)-len(decisions),
        "word_id_to_possible_UBS_original_source_reference_sense":dict(sorted(decisions.items())),
        "source_specific_dispositions":dict(sorted(reasons.items())),
        "source_disposition_examples":dict(sorted(examples.items())),
        "independently_contextually_validated":0,
        "corpus_or_ubs_modified":False,
        "published":False,
        "publication_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("index","reviewed","batches","english","french","macula","form_defaults","output"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    load=lambda f:json.loads(f.read_text(encoding="utf-8-sig"))
    report=audit(load(a.index),load(a.reviewed),load(a.batches),
                 load(a.english),load(a.french),a.macula,load(a.form_defaults))
    a.output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,
                                   separators=(",",":"))+"\n",encoding="utf-8")
    print("GREEK_UBS_SOURCE_ORIGINAL_VERSE_REFERENCE_CANDIDATES",json.dumps({
        "source_verse_unique_word_candidates":report["original_reference_witness_candidate_word_count"],
        "reasons":report["source_specific_dispositions"],
        "independent_contextual_validations":0,"published":False},sort_keys=True))


if __name__=="__main__":main()
