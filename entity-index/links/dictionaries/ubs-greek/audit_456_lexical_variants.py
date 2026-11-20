#!/usr/bin/env python3
"""Read-only diagnostics for unattested Greek lemma variants in original UBS 1.0.

Do not use accent-stripping, substring matching, stemming, semantic-domain
overlap or external lexicons to create lexical links. Enumerate only candidate
evidence for human/editorial source review; all original MACULA word IDs,
Greek, Strong, LN, morphology and UBS original MainIds are immutable.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path


def nfc(v):return unicodedata.normalize("NFC",v)

def accentless(v):
    # DIAGNOSTIC ONLY: never use as accepted lexeme identity.
    return "".join(ch for ch in unicodedata.normalize("NFD",v)
                   if unicodedata.category(ch)!="Mn").casefold()

def source_codes(entry):
    return {str(s["LEXEntryCode"]) for base in entry.get("BaseForms") or []
            for s in base.get("LEXMeanings") or []
            if isinstance(s.get("LEXEntryCode"),str)}

def source_pos(entry):
    return sorted({str(p) for base in entry.get("BaseForms") or []
                   for p in base.get("PartsOfSpeech") or []})

def source_variant_metadata(entry):
    """Record metadata keys, not definition prose or generated links."""
    observations=[]
    for key,value in entry.items():
        if any(marker in key.lower() for marker in ("spell","variant","alternat","otherform","crossref","reference","alias")):
            # Do not redistribute verbatim prose; show field type/shape only.
            observations.append({"key":key,"kind":type(value).__name__,
                                 "elements":len(value) if isinstance(value,(list,dict)) else None})
    for form in entry.get("BaseForms") or []:
        for key,value in form.items():
            if any(marker in key.lower() for marker in ("spell","variant","alternat","otherform","crossref","reference","alias")):
                observations.append({"key":"BaseForms."+key,"kind":type(value).__name__,
                                     "elements":len(value) if isinstance(value,(list,dict)) else None})
    return observations


def audit(missing,english,french):
    if (missing.get("status")!="PRIVATE_459_UBS_Greek_v1_0_missing_exact_headword_source_evidence_ONLY"
        or missing.get("original_words")!=459
        or missing.get("automatic_lemma_mappings_approved")!=0
        or missing.get("publication_approved") is not False):
        raise ValueError("Original Greek missing-headword pinned source report drift")
    en={x["MainId"]:x for x in english}
    fr={x["MainId"]:x for x in french}
    if len(en)!=len(english) or len(fr)!=len(french) or set(en)!=set(fr):
        raise ValueError("Original UBS Greek bilingual lexical inventory differs")
    stripped=defaultdict(list)
    for mid,entry in en.items():
        if nfc(entry["Lemma"])!=nfc(fr[mid]["Lemma"]):
            raise ValueError("UBS original Greek bilingual headword spelling drift")
        stripped[accentless(entry["Lemma"])].append(mid)
    records=[]
    seen_word_ids=set()
    diagnostics=Counter()
    for family in missing["source_word_families"]:
        lemma=family["original_greek_lemma_nfc_for_comparison"]
        if family["ubs_case_only_spelling_main_ids"]:
            continue  # Exactly three Ἄλφα word IDs reviewed in #412.
        if family["classification"]!="no_lexeme_spelling_or_strong_equivalence_in_pinned_UBS":
            raise ValueError("Unexpected source case/Strong equivalence in Greek residual")
        mids=sorted(stripped.get(accentless(lemma),[]))
        original_ln=set(family["original_ln_code_counts"])
        candidates=[]
        for mid in mids:
            shared_en=sorted(original_ln & source_codes(en[mid]))
            shared_fr=sorted(original_ln & source_codes(fr[mid]))
            if shared_en!=shared_fr:
                raise ValueError("Independent UBS original bilingual lexical LN code drift")
            candidates.append({
                "ubs_main_id":mid,
                "original_ubs_greek_lemma":en[mid]["Lemma"],
                "source_greek_equivalence_status":"ACCENTLESS_DIAGNOSTIC_ONLY_NOT_VERIFIED_LEXEME",
                "original_ln_overlap_bilingual":shared_en,
                "ubs_original_lexical_parts_of_speech_en":source_pos(en[mid]),
                "ubs_original_lexical_parts_of_speech_fr":source_pos(fr[mid]),
                "original_ubs_alternative_spelling_metadata_shape":source_variant_metadata(en[mid]),
            })
        witness_ids=[x["original_word_id"] for x in family["source_original_word_witnesses"]]
        if len(witness_ids)!=family["original_word_count"] or set(witness_ids)&seen_word_ids:
            raise ValueError("Duplicate or missing original Greek source-word IDs")
        seen_word_ids.update(witness_ids)
        diagnostics["with_accentless_greek_spelling_candidate" if mids else "without_accentless_greek_spelling_candidate"]+=len(witness_ids)
        records.append({
            "original_lemma":lemma,
            "original_strong":family["original_source_strong"],
            "original_words":len(witness_ids),
            "original_word_ids":witness_ids,
            "original_word_witnesses":family["source_original_word_witnesses"],
            "original_ln_counts":family["original_ln_code_counts"],
            "original_class_counts":family["original_source_classes"],
            "original_ubs_v1_headword_accentless_diagnostic_only":candidates,
            "editorial_approval":False,
        })
    if len(seen_word_ids)!=456 or sum(diagnostics.values())!=456:
        raise ValueError("Original Greek source word gaps did not contain exactly 456 independent word IDs")
    records.sort(key=lambda x:(-x["original_words"],x["original_lemma"],x["original_strong"]))
    return {
        "status":"PRIVATE_Greek_456_original_word_ubs_v1_variants_READ_ONLY_NOT_APPROVED",
        "source_editions":missing["source_editions"],
        "original_word_count":456,
        "original_lexical_families":len(records),
        "source_diagnostics_counts":dict(sorted(diagnostics.items())),
        "families":records,
        "new_source_lexical_headword_links":0,
        "new_inferred_contextual_ubs_lexids":0,
        "original_source_or_index_modified":False,
        "publication_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("missing","english","french","output"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    result=audit(read(a.missing),read(a.english),read(a.french))
    a.output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GREEK_UBS_ORIGINAL_ALTERNATE_LEMMAS_FOR_SOURCE_FAMILIES",json.dumps([
        {"main_id":entry["MainId"],"lemma":entry["Lemma"],
         "original_alternate_lemmas":entry.get("AlternateLemmas") or []}
        for entry in read(a.english)
        if entry["MainId"] in {"002417000000000","002418000000000","003615000000000"}
    ],ensure_ascii=False,sort_keys=True))
    print("GREEK_UBS_SOURCE_ALTERNATIVE_METADATA_DIAGNOSTICS",json.dumps([
        {"main_id":mid,"lemma":entry["Lemma"],"source_lexical_ln_codes":sorted(source_codes(entry)),
         "source_original_strong_codes":entry.get("StrongCodes") or [],
         "source_lemma_alternative_metadata":source_variant_metadata(entry),
         "source_top_level_keys":sorted(entry),
         "source_first_baseform_keys":sorted(entry["BaseForms"][0]) if entry.get("BaseForms") else []}
        for mid,entry in ((x["MainId"],x) for x in read(a.english))
        if source_codes(entry)&{"93.480a","93.480b","91.13","91.10","7.16","53.9"}
    ][:36],ensure_ascii=False,sort_keys=True))
    print("GREEK_ACCENTLESS_SOURCE_DIAGNOSTICS_ONLY",json.dumps([
        {"lemma":x["original_lemma"],"count":x["original_words"],
         "original_strong":x["original_strong"],
         "diagnostic_ubs":x["original_ubs_v1_headword_accentless_diagnostic_only"]}
        for x in result["families"] if x["original_ubs_v1_headword_accentless_diagnostic_only"]
    ],ensure_ascii=False,sort_keys=True))
    print("GREEK_456_ORIGINAL_VARIANT_LEXICAL_AUDIT",json.dumps({
        "words":result["original_word_count"],
        "families":result["original_lexical_families"],
        "counts":result["source_diagnostics_counts"],
        "top":[{"lemma":x["original_lemma"],"words":x["original_words"],
                "original_strong":x["original_strong"],
                "original_ln_counts":x["original_ln_counts"],
                "original_class_counts":x["original_class_counts"],
                "potential_original_ubs_headwords":x["original_ubs_v1_headword_accentless_diagnostic_only"]}
               for x in result["families"][:30]],
        "approved":False,
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":main()
