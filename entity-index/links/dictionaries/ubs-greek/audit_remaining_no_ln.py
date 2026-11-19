#!/usr/bin/env python3
"""Source-audit Greek UBS headwords without a corroborating lexical LN code.

Independently inspect all original SBLGNT word IDs and both pinned UBS 1.0
lexica. Separate the already source-reviewed εἰμί family from every
remaining lemma-only original word; never invent a contextual UBS sense.
This is an editorial evidence register, NOT lexical approval/publication.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAPS = runpy.run_path(str(HERE / "audit_source_gaps.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))


def nfc(s):
    return unicodedata.normalize("NFC", s)


def audit(report, baseline, english, french, macula_path):
    if (report.get("status") !=
        "source_pinned_read_only_review_UNAPPROVED_not_a_lexical_release"
        or report.get("summary", {}).get("nfc_lemma_only_no_attested_ubs_ln") != 3249
        or report.get("summary", {}).get("original_macula_words") != 137741
        or report.get("methods", {}).get("contextual_ubs_sense_ids_inferred") != 0):
        raise ValueError("Pinned original Greek no-LN source report drift")
    by_lemma, by_ln = GAPS["source_lexicon"](english, french, baseline)
    en = {r["MainId"]: r for r in english}
    fr = {r["MainId"]: r for r in french}
    if len(en) != len(english) or len(fr) != len(french) or set(en) != set(fr):
        raise ValueError("Pinned bilingual UBS Greek lexical headwords drift")
    groups = defaultdict(list)
    source_counts = Counter()
    seen = set()
    rows = 0
    for row in csv.DictReader(macula_path.open("r", encoding="utf-8-sig", newline=""), delimiter="\t"):
        wid = row["xml:id"]
        if wid in seen:
            raise ValueError("Duplicate original SBLGNT word ID: " + wid)
        seen.add(wid)
        rows += 1
        reason, entry, matches = GAPS["classify"](row, baseline, by_lemma, by_ln)
        if reason != "nfc_lemma_only_no_attested_ubs_ln":
            continue
        if entry is None or matches or not row["ref"] or not row["morph"]:
            raise ValueError("Original Greek no-LN lexical evidence unexpectedly corroborated")
        mid = entry["MainId"]
        if (mid not in fr or nfc(fr[mid]["Lemma"]) != nfc(row["lemma"])
                or not row["strong"].isdigit()):
            raise ValueError("Original Greek source lemma and UBS bilingual lexical entry drift")
        if nfc(row["lemma"]) == "εἰμί":
            source_counts["already_reviewed_eimi_entry_only"] += 1
            continue
        source_counts["remaining_unreviewed_no_ln"] += 1
        groups[(nfc(row["lemma"]), mid)].append({
            "original_word_id": wid,
            "original_reference": row["ref"],
            "original_greek_lemma": row["lemma"],
            "original_strong": row["strong"],
            "original_ln": row["ln"],
            "original_class": row["class"],
            "original_morph": row["morph"],
            "ubs_main_id": mid,
            "contextual_ubs_lexid": None,
        })
    if (rows != 137741 or source_counts != {
        "already_reviewed_eimi_entry_only": 2031,
        "remaining_unreviewed_no_ln": 1218,
    }):
        raise ValueError("Original Greek no-LN word inventory changed: " + repr(source_counts))
    families = []
    for (lemma, mid), witnesses in groups.items():
        entry = en[mid]
        src_parts = sorted({
            str(p) for form in entry.get("BaseForms") or []
            for p in form.get("PartsOfSpeech") or []
        })
        parts_fr = sorted({
            str(p) for form in fr[mid].get("BaseForms") or []
            for p in form.get("PartsOfSpeech") or []
        })
        ln_codes_en = sorted(by_ln[mid])
        lex_codes_fr = sorted({
            str(item["LEXEntryCode"])
            for form in fr[mid].get("BaseForms") or []
            for item in form.get("LEXMeanings") or []
            if isinstance(item.get("LEXEntryCode"), str)
        })
        if ln_codes_en != lex_codes_fr:
            raise ValueError("UBS bilingual source code parity drift: " + mid)
        families.append({
            "lemma_nfc": lemma,
            "ubs_main_id": mid,
            "ubs_original_lemma_en": entry["Lemma"],
            "ubs_original_lemma_fr": fr[mid]["Lemma"],
            "source_class_counts": dict(sorted(Counter(w["original_class"] for w in witnesses).items())),
            "original_strong_counts": dict(sorted(Counter(w["original_strong"] for w in witnesses).items())),
            "ubs_original_parts_of_speech_en": src_parts,
            "ubs_original_parts_of_speech_fr": parts_fr,
            "ubs_source_meaning_codes": ln_codes_en,
            "ubs_source_meanings_missing": len(ln_codes_en) == 0,
            "original_word_count": len(witnesses),
            "editorial_status": "UNAPPROVED_lemma_only_without_original_UBS_LN_match",
            "original_word_witnesses": witnesses,
        })
    families.sort(key=lambda x: (-x["original_word_count"], x["lemma_nfc"], x["ubs_main_id"]))
    if sum(f["original_word_count"] for f in families) != 1218:
        raise ValueError("Greek original source no-LN family census incomplete")
    return {
        "status": "PRIVATE_1218_original_Greek_lemma_only_without_UBS_LN_NOT_APPROVED",
        "source_editions": report["source_editions"],
        "all_original_words_audited": rows,
        "original_no_ln_words": 3249,
        "previously_reviewed_eimi_entry_only_words": 2031,
        "remaining_unapproved_original_words": 1218,
        "remaining_lexical_families": len(families),
        "new_contextual_ubs_lexids": 0,
        "publication_approved": False,
        "families": families,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("report", "index", "english", "french", "macula", "output"):
        p.add_argument("--" + k, type=Path, required=True)
    a = p.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    out = audit(read(a.report), read(a.index), read(a.english), read(a.french), a.macula)
    a.output.write_text(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("UBS_GREEK_NO_LN_RESIDUAL_1218", json.dumps({
        "original_word_count": out["remaining_unapproved_original_words"],
        "families": out["remaining_lexical_families"],
        "top_families": [{
            "lemma": x["lemma_nfc"], "mid": x["ubs_main_id"],
            "words": x["original_word_count"],
            "classes": x["source_class_counts"],
            "strong": x["original_strong_counts"],
            "ubs_pos_en": x["ubs_original_parts_of_speech_en"],
            "ubs_pos_fr": x["ubs_original_parts_of_speech_fr"],
            "ubs_original_ln_meanings_missing": x["ubs_source_meanings_missing"],
        } for x in out["families"][:70]],
        "published": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
