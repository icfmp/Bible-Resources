#!/usr/bin/env python3
"""Verify mathematical Greek word coverage and independent editorial approvals.

An existing, already counted word-ID candidate cannot increase the count of
covered source words merely because editorial status becomes reviewed.
Word-aware source candidates are the original 128,090 Strong matched word IDs
plus the DISTINCT original by_macula_word IDs. Reviewed/preview status is a
separate measurement, and original Strong ambiguity overlays are already
part of the historical baseline count.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

UNAPPROVED="nfc_canonically_identical_lemma_and_original_ln_unapproved_word_candidate"


def verify(base, candidate):
    for key,value in base.items():
        if candidate.get(key)!=value:
            raise ValueError("Historical UBS Greek baseline index modified: "+key)
    total=base["coverage"]["macula_words"]
    direct=base["coverage"]["with_ubs_entry_candidates"]
    overlay=candidate["by_macula_word"]
    ambiguity=candidate.get("by_macula_ambiguous_word",{})
    if not isinstance(overlay,dict) or not isinstance(ambiguity,dict):
        raise ValueError("Original Greek word-specific lexical overlays invalid")
    if set(overlay)&set(ambiguity):
        raise ValueError("Greek original Strong word-ID ambiguity double-counted as missing-source")
    if len(overlay)!=len(set(overlay)) or len(ambiguity)!=len(set(ambiguity)):
        raise ValueError("Duplicated original Greek word ID")
    checked=direct+len(overlay)
    remaining=total-checked
    if remaining<0:
        raise ValueError("Greek lexical source candidate coverage exceeds original word inventory")
    word=candidate["word_aware_coverage"]
    edited=candidate["editorial_candidate"]
    approved=sum(1 for row in overlay.values() if row.get("match_type")!=UNAPPROVED)
    pending=len(overlay)-approved
    if (word["word_aware_entry_candidate_words"]!=checked
        or word["remaining_no_ubs_headword_candidate_original_words"]!=remaining
        or edited["reviewed_original_headword_words_total"]!=approved
        or word["editorially_reviewed_original_word_headwords"]!=approved
        or edited["other_original_words_still_unapproved"]!=pending
        or word["other_unapproved_word_headword_candidates"]!=pending
        or edited["new_inferred_contextual_lexical_sense_ids"]!=0
        or word["new_inferred_contextual_lexical_sense_ids"]!=0
        or edited["publication_approved"] is not False):
        raise ValueError("Greek original lexical headword source coverage/status double count or policy drift")
    if any("sense_id" in r for r in overlay.values()):
        raise ValueError("Inferred contextual UBS lexical sense found in original word overlay")
    if any("sense_id" in r for r in ambiguity.values()):
        raise ValueError("Inferred contextual UBS lexical sense found in Strong ambiguity overlay")
    return {
        "original_sblgnt_words": total,
        "historical_strong_candidate_words": direct,
        "new_distinct_original_word_candidate_ids": len(overlay),
        "total_distinct_lexical_entry_candidate_words": checked,
        "candidate_word_ids_with_only_preview_status": pending,
        "editorially_reviewed_extra_word_headword_ids": approved,
        "source_supported_lexical_headword_word_coverage": direct+approved,
        "remaining_without_editorially_supported_lexical_headword": total-direct-approved,
        "remaining_without_any_candidate_word_entry": remaining,
        "reviewed_original_word_strong_ambiguities_not_double_counted": len(ambiguity),
        "original_index_unchanged": True,
        "published": False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--candidate",type=Path,required=True)
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8-sig"))
    result=verify(read(args.baseline),read(args.candidate))
    print("UBS_GREEK_WORD_COVERAGE_MATHEMATICAL_INVARIANTS",json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
