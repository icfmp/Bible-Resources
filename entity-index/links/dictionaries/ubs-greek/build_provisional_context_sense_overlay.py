#!/usr/bin/env python3
"""Build PRIVATE reversible source-attested Greek UBS LEXID *candidate* overlays.

Conservatively adopt a single authentic UBS LEXID as a PROVISIONAL
editorial candidate only when (a) a word-specific lexical HEADWORD
is already source-supported; (b) exactly one LEXID in that UBS headword
matches the original MACULA word-specific LN code(s), in BOTH UBS EN/FR
source editions. This is NOT completed verse-context semantic review,
and no contextual UBS meaning is asserted as fully verified. Every
unresolved word is retained in a separate explicit, private register.
Original sources, historical index, dictionary, headword overlay and
original Strong are never modified.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,runpy
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUDIT=runpy.run_path(str(HERE/"audit_contextual_sense_candidates.py"))
TOTAL=137741
UNIQUE=122504
UNRESOLVED=TOTAL-UNIQUE

def make(index,reviewed,en,fr,macula,audit):
    if (audit.get("status")!="PRIVATE_SOURCE_UBS_Greek_v1_0_original_word_sense_CANDIDATE_CENSUS_NOT_SEMANTIC_VALIDATION"
        or audit.get("original_word_ids")!=TOTAL
        or audit.get("original_word_sense_candidate_outcomes",{}).get(
            "unique_source_attested_ubs_lexid_candidate_NOT_contextually_validated")!=UNIQUE
        or audit.get("lexical_sense_contextually_verified")!=0
        or audit.get("automatic_contextual_lexid_assignments")!=0
        or audit.get("publication_approved") is not False):
        raise ValueError("Unreviewed Greek original-context candidate source census drift")
    senses=AUDIT["verify_sources"](index,en,fr)
    if (len(reviewed["by_macula_word"])!=9604
        or len(reviewed.get("by_macula_ambiguous_word",{}))!=220
        or reviewed["editorial_candidate"]["publication_approved"] is not False):
        raise ValueError("Greek lexical source headword review drift")
    choices={}
    pending={}
    outcomes=Counter()
    families=defaultdict(Counter)
    classes=defaultdict(Counter)
    observed=set()
    with macula.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle,delimiter="\t")
        for row in reader:
            wid=row["xml:id"]
            if wid in observed: raise ValueError("Original Greek source-word ID repeated")
            observed.add(wid)
            group,mids,triples=AUDIT["candidates_for_original_word"](row,index,reviewed,senses)
            unique_senses={(mid,lexid) for mid,lexid,ln in triples}
            witness=AUDIT["original_word"](row)
            if len(mids)==1 and len(unique_senses)==1:
                mid,lexid=next(iter(unique_senses))
                matched=sorted({ln for m,s,ln in triples if m==mid and s==lexid})
                if (not matched or mid not in senses
                    or not any((lexid,ln) in senses[mid] for ln in matched)):
                    raise ValueError("Source UBS Greek original LEXID and LN evidence missing")
                choices[wid]={
                    **witness,
                    "ubs_original_main_id":mid,
                    "ubs_original_lexid":lexid,
                    "source_macula_ubs_ln_overlap":matched,
                    "original_headword_evidence":group,
                    "editorial_status":"PROVISIONAL_unique_original_source_attested_LN_and_UBS_LEXID_NOT_contextually_verified",
                    "verse_context_semantically_verified":False,
                }
                disposition="unique_source_attested_ubs_lexid_candidate_NOT_contextually_validated"
            else:
                disposition=("no_ubs_headword" if not mids else
                             "multiple_original_ubs_lexical_headwords" if len(mids)>1 else
                             "no_original_ln_matching_ubs_lexical_sense" if not triples else
                             "multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated")
                pending[wid]={
                    **witness,
                    "original_headword_evidence":group,
                    "source_original_ubs_main_id_candidates":mids,
                    "source_ubs_lexid_candidate_pairs":[
                        {"original_ubs_main_id":m,"original_ubs_lexid":s,"original_ln":ln}
                        for m,s,ln in triples],
                    "editorial_status":disposition,
                    "verse_context_semantically_verified":False,
                }
            outcomes[disposition]+=1
            if disposition!="unique_source_attested_ubs_lexid_candidate_NOT_contextually_validated":
                families[disposition][row["lemma"]]+=1
                classes[disposition][row["class"]]+=1
    if len(observed)!=TOTAL or len(choices)!=UNIQUE or len(pending)!=UNRESOLVED:
        raise ValueError("Original Greek word-specific editorial provisional candidate census incomplete")
    if dict(outcomes)!=audit["original_word_sense_candidate_outcomes"]:
        raise ValueError("Original Greek semantic candidates no longer match independently verified source report")
    common={
        "source_editions":audit["source_editions"],
        "all_original_word_ids":TOTAL,
        "original_source_or_ubs_lexicon_modified":False,
        "contextual_senses_independently_verified":0,
        "published":False,
    }
    accepted={
        **common,
        "status":"PRIVATE_PROVISIONAL_Greek_UBS_original_source_unique_LN_LEXID_candidates_NOT_semantically_verified",
        "provisional_source_supported_original_word_count":len(choices),
        "word_id_to_provisional_ubs_lexid":dict(sorted(choices.items())),
        "meaning_edits_or_textual_translations":0,
        "public_release_approved":False,
    }
    uncertain={
        **common,
        "status":"PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review",
        "unresolved_original_word_count":len(pending),
        "unresolved_reason_counts":{k:v for k,v in sorted(outcomes.items()) if k!="unique_source_attested_ubs_lexid_candidate_NOT_contextually_validated"},
        "unresolved_by_original_source_class":{k:dict(sorted(c.items())) for k,c in sorted(classes.items())},
        "largest_unresolved_original_lemma_families":{
            k:[{"original_lemma":lemma,"original_word_count":n}
               for lemma,n in sorted(f.items(),key=lambda t:(-t[1],t[0]))[:35]]
            for k,f in sorted(families.items())},
        "word_id_to_unresolved_original_source_evidence":dict(sorted(pending.items())),
        "public_release_approved":False,
    }
    return accepted,uncertain

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("index","reviewed","english","french","macula","audit","accepted","unresolved"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    load=lambda q:json.loads(q.read_text(encoding="utf-8-sig"))
    good,unresolved=make(load(a.index),load(a.reviewed),load(a.english),load(a.french),a.macula,load(a.audit))
    for path,record in ((a.accepted,good),(a.unresolved,unresolved)):
        path.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print("GREEK_UBS_PRIVATE_PROVISIONAL_CONTEXTUAL_CANDIDATES",json.dumps({
        "provisional_source_supported_unique_lexid_word_ids":good["provisional_source_supported_original_word_count"],
        "remaining_original_word_ids":unresolved["unresolved_original_word_count"],
        "remaining_by_original_reason":unresolved["unresolved_reason_counts"],
        "top_ambiguous_families":unresolved["largest_unresolved_original_lemma_families"]["multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated"][:15],
        "top_no_original_ln_families":unresolved["largest_unresolved_original_lemma_families"]["no_original_ln_matching_ubs_lexical_sense"][:15],
        "candidate_sha256":hashlib.sha256(a.accepted.read_bytes()).hexdigest(),
        "unresolved_sha256":hashlib.sha256(a.unresolved.read_bytes()).hexdigest(),
        "contextually_verified":0,
        "published":False,
    },ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
