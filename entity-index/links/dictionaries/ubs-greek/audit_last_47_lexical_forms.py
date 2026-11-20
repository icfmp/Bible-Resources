#!/usr/bin/env python3
"""Original-source investigation of 47 Greek words absent from UBS primary/alternate lemmas.

Read only the pinned bilingual UBS Greek NT Dictionary 1.0 and the
original MACULA word-ID witnesses. Search only metadata fields
BaseForms.Inflections and BaseForms.RelatedLemmas plus original lexical
domain cross-references. An inflected form or a shared semantic domain
does NOT establish a Greek lexical headword; report possible evidence
for source-editorial examination, never auto-map or rewrite Strong.
"""
from __future__ import annotations
import argparse,json,unicodedata
from collections import Counter,defaultdict
from pathlib import Path


def nfc(v):return unicodedata.normalize("NFC",v)

def codes(e):
    return {str(s["LEXEntryCode"]) for f in e.get("BaseForms") or []
            for s in f.get("LEXMeanings") or []
            if isinstance(s.get("LEXEntryCode"),str)}

def metadata_inspection(entry):
    examples={}
    for form in entry.get("BaseForms") or []:
        for field in ("Inflections","RelatedLemmas"):
            val=form.get(field)
            if val is not None and field not in examples:
                sample=val[:2] if isinstance(val,list) else val
                examples[field]={"type":type(val).__name__,"sample":sample}
    return examples

def scan_text_atoms(value):
    """Metadata tokens only. No definitions, heuristic stemming or prose."""
    if isinstance(value,str):
        if value and len(value)<60 and " " not in value and "\n" not in value:
            yield nfc(value)
    elif isinstance(value,list):
        for x in value:
            yield from scan_text_atoms(x)
    elif isinstance(value,dict):
        # The field/value schema must be inspected before using matches as evidence.
        for k,v in value.items():
            if any(marker in k.lower() for marker in ("lemma","greek","inflect","form","spelling")):
                yield from scan_text_atoms(v)


def audit(alternates,english,french):
    if (alternates.get("status")!="PRIVATE_Greek_original_UBS_explicit_alternate_lemmas_source_evidence_UNAPPROVED"
        or alternates.get("source_evidence_counts")!={"exact_original_ubs_alternate_lemma_and_ln":409,"not_in_original_ubs_alternate_lemmas":47}
        or alternates.get("new_source_word_lexical_headwords_approved")!=0
        or alternates.get("publication_approved") is not False):
        raise ValueError("Greek remaining 47 source-word lexical exclusion report drift")
    en={x["MainId"]:x for x in english}
    fr={x["MainId"]:x for x in french}
    if len(en)!=len(english) or len(fr)!=len(french) or set(en)!=set(fr):
        raise ValueError("Original UBS bilingual Greek lexical inventory drift")
    inflections=defaultdict(list)
    by_domain=defaultdict(list)
    for mid,e in en.items():
        f=fr[mid]
        if nfc(e["Lemma"])!=nfc(f["Lemma"]) or codes(e)!=codes(f):
            raise ValueError("Original UBS Greek EN/FR lexical headword or LN drift")
        for domain in codes(e):
            by_domain[domain].append(mid)
        for form in e.get("BaseForms") or []:
            for atom in scan_text_atoms(form.get("Inflections")):
                inflections[atom].append(mid)
    families=[]
    summary=Counter()
    ids=set()
    for original in alternates["source_families"]:
        if original["source_evidence_disposition"]!="not_in_original_ubs_alternate_lemmas":
            continue
        lemma=original["source_original_lemma"]
        words=original["source_original_word_witnesses"]
        original_ids=original["source_original_word_ids"]
        if (len(words)!=original["source_original_word_count"]
            or set(original_ids)!={x["original_word_id"] for x in words}
            or ids.intersection(original_ids)):
            raise ValueError("Original Greek 47-word source witnesses overlap or differ")
        ids.update(original_ids)
        source_domains={x for row in words for x in row["original_ln"].split()}
        matching_inflections=sorted(set(inflections.get(nfc(lemma),[])))
        matched=[]
        for mid in matching_inflections:
            common=sorted(source_domains&codes(en[mid])&codes(fr[mid]))
            matched.append({
                "ubs_original_main_id":mid,
                "original_ubs_lemma":en[mid]["Lemma"],
                "original_ln_code_overlap_NOT_sense":common,
                "source_inflection_metadata_en":metadata_inspection(en[mid]),
                "source_inflection_metadata_fr":metadata_inspection(fr[mid]),
                "editorial_status":"DIAGNOSTIC_ONLY_NOT_A_LEXICAL_HEADWORD_APPROVAL",
            })
        nearby=sorted({m for code in source_domains for m in by_domain.get(code,[])})
        category=("source_inflection_string_exists_NOT_APPROVED" if matched else
                  "no_exact_inflection_metadata_match_IN_UBS_1_0")
        summary[category]+=len(original_ids)
        families.append({
            "original_macula_lemma":lemma,
            "original_macula_strong":original["source_original_strong"],
            "original_word_count":len(original_ids),
            "original_word_ids":original_ids,
            "original_source_LN_counts":original["source_original_ln_counts"],
            "original_source_class_counts":original["source_original_class_counts"],
            "original_ubs_exact_inflection_string_matches_NOT_APPROVED":matched,
            "other_ubs_entries_sharing_original_LN_domain_count_NOT_identity":len(nearby),
            "other_ubs_entries_sharing_original_LN_domain_sample_NOT_identity":nearby[:8],
            "source_evidence_category":category,
            "editorial_status":"UNLINKED_original_UBS_Greek_1_0_lemma_absent",
        })
    if len(ids)!=47 or sum(summary.values())!=47:
        raise ValueError("Greek remaining 47 original word IDs not exhaustively audited")
    families.sort(key=lambda r:(-r["original_word_count"],r["original_macula_lemma"]))
    return {
        "status":"PRIVATE_remaining_47_original_Greek_UBS_1_0_missing_headword_evidence_UNAPPROVED",
        "source_editions":alternates["source_editions"],
        "remaining_original_word_ids":47,
        "remaining_source_lexical_families":len(families),
        "source_evidence_counts":dict(sorted(summary.items())),
        "remaining_original_word_families":families,
        "original_greek_and_strong_modified":False,
        "contextual_senses_inferred":0,
        "new_lexical_headwords_approved":0,
        "publication_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("alternates","english","french","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding="utf-8-sig"))
    output=audit(read(a.alternates),read(a.english),read(a.french))
    a.output.write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_47_SOURCE_MISSING_UBS_LEXICAL_HEADWORDS_EVIDENCE",json.dumps({
        "counts":output["source_evidence_counts"],
        "families":output["remaining_source_lexical_families"],
        "remaining":[{"lemma":x["original_macula_lemma"],
                      "words":x["original_word_count"],
                      "strong":x["original_macula_strong"],
                      "ln":x["original_source_LN_counts"],
                      "classes":x["original_source_class_counts"],
                      "inflection_candidate_mids": [y["ubs_original_main_id"] for y in x["original_ubs_exact_inflection_string_matches_NOT_APPROVED"]],
                      "nearby_ln_count_NOT_identity":x["other_ubs_entries_sharing_original_LN_domain_count_NOT_identity"]}
                     for x in output["remaining_original_word_families"]],
        "published":False,
    },ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
