#!/usr/bin/env python3
"""One-pass, read-only feasibility audit for Hebrew UBS 0.9.4 sense v1.1.

Compare each original WLC word to the full source-reviewed v1 lexical lookup,
then inspect authentic UBS EN+FR LEXReferences for its independently verified
headword. Original MACULA SDBH numeric identity is NEVER promoted to a UBS
contextual sense across editions.

A sole UBS LEXID citing a verse is only a *verse witness candidate*, NOT
independently validated word-level semantic disambiguation. If that same UBS
lexeme occurs twice in the verse, or multiple senses cite the verse, abstain.
Preserve all original source words, source annotations and lexical version.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import runpy
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = runpy.run_path(str(HERE / "build_index.py"))
MACULA_REVISION = BUILD["MACULA_REVISION"]
UBS_REVISION = BUILD["UBS_REVISION"]
WORD_ID = re.compile(r"^o(\d{2})(\d{3})(\d{3})\d{4}[\u0590-\u05ff]*$")
NUMERIC_REFERENCE = re.compile(r"^\d{14}$")
EXPECTED = 475911
LEXICAL_CLASSES = {"noun", "verb", "adj", "adv", "num"}
TIER = ("verse_citation_unique_headword", "unverified_candidate_not_published")


def verse_from_word_id(word_id):
    match = WORD_ID.fullmatch(word_id)
    if not match:
        raise ValueError("Unexpected original WLC word id: " + repr(word_id))
    book,chapter,verse = (int(s) for s in match.groups())
    if not 1 <= book <= 39 or not 1 <= chapter <= 999 or not 1 <= verse <= 999:
        raise ValueError("Original WLC OT source verse outside canonical bounds")
    return f"{book:03d}{chapter:03d}{verse:03d}"


def sense_inventory(english, french):
    """No inference from untranslated prose; compare exact source IDs and ref data."""
    if len(english) != 7943 or len(french) != 7943:
        raise ValueError("UBS Hebrew 0.9.4 headword source census changed")
    by_language = []
    for items in (english, french):
        inventory = {}
        for entry in items:
            mid = entry["MainId"]
            if mid in inventory:
                raise ValueError("Duplicated original UBS MainId")
            senses = {}
            for meaning in BUILD["senses"](entry):
                sid = meaning["LEXID"]
                if sid in senses:
                    raise ValueError("Duplicated UBS source sense within headword")
                source_refs = meaning.get("LEXReferences")
                if source_refs is None:
                    source_refs = []
                if not isinstance(source_refs, list):
                    raise ValueError("Unexpected UBS original sense reference structure")
                invalid = [r for r in source_refs if not isinstance(r, str) or not NUMERIC_REFERENCE.fullmatch(r)]
                valid = set(r for r in source_refs if isinstance(r, str) and NUMERIC_REFERENCE.fullmatch(r))
                senses[sid] = {
                    "source_entry_code": meaning.get("LEXEntryCode"),
                    "exact_references": valid,
                    "verse_references": {r[:9] for r in valid},
                    "reference_count": len(source_refs),
                    "invalid_reference_count": len(invalid),
                }
            inventory[mid] = {
                "lemma": entry["Lemma"],
                "alternate_lemmas": tuple(entry.get("AlternateLemmas") or ()),
                "strong_codes": tuple(entry.get("StrongCodes") or ()),
                "senses": senses,
            }
        by_language.append(inventory)
    eng, fra = by_language
    if set(eng) != set(fra):
        raise ValueError("Bilingual UBS headword inventory changed")
    counts = Counter()
    parity = Counter()
    for mid in eng:
        a, b = eng[mid], fra[mid]
        if (a["lemma"], a["strong_codes"], set(a["senses"])) != (
            b["lemma"], b["strong_codes"], set(b["senses"])
        ):
            raise ValueError("Bilingual UBS lexical identities disagree")
        if a["alternate_lemmas"] != b["alternate_lemmas"]:
            parity["alternate_lemma_drift_headwords"] += 1
        if a["alternate_lemmas"]:
            counts["headwords_with_alternate_lemmas"] += 1
        for sid, info in a["senses"].items():
            other = b["senses"][sid]
            counts["original_ubs_sense_ids"] += 1
            if info["verse_references"]:
                counts["senses_with_reference_verses_en"] += 1
            if other["verse_references"]:
                counts["senses_with_reference_verses_fr"] += 1
            if info["verse_references"] != other["verse_references"]:
                parity["sense_reference_verse_mismatch"] += 1
            if info["invalid_reference_count"] or other["invalid_reference_count"]:
                counts["senses_with_noncanonical_references"] += 1
            if info["source_entry_code"] != other["source_entry_code"]:
                parity["sense_entry_code_mismatch"] += 1
    if counts["original_ubs_sense_ids"] != 16619:
        raise ValueError("Original UBS sense census drift")
    return eng, fra, dict(counts), dict(parity)


def assess(index, english, french, macula):
    if (index.get("dictionary", {}).get("revision") != UBS_REVISION or
        index.get("macula", {}).get("revision") != MACULA_REVISION or
        index.get("coverage_scope", {}).get("linked_occurrences") != 240373 or
        index.get("coverage_scope", {}).get("coverage_pct") != 99.022 or
        index.get("editorial_candidate", {}).get("new_headword_only_wlc_word_ids") != 275):
        raise ValueError("Final published Hebrew v1.0 original lexical source baseline drift")
    eng, fra, source_counts, source_parity = sense_inventory(english, french)
    stages = Counter()
    verse_mid_count = Counter()
    words = []
    seen = set()
    with macula.open(encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src, delimiter="\t")
        required = {"xml:id", "ref", "lemma", "strongnumberx", "sdbh", "lang", "class"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("MACULA pinned WLC TSV columns changed")
        for row in reader:
            wid = row["xml:id"]
            if wid in seen:
                raise ValueError("Duplicated original MACULA word ID")
            seen.add(wid)
            verse = verse_from_word_id(wid)
            original_ref = row["ref"]
            # Verify original text's verse against original ID without
            # assuming source word ordinal equals UBS reference ordinal.
            if not isinstance(original_ref, str) or not original_ref:
                raise ValueError("Missing original WLC verse reference")
            link = BUILD["lookup_word"](
                index, wid, row["sdbh"], row["strongnumberx"],
                row["lang"], row["lemma"]
            )
            mids = link["entry_ids"]
            if any(mid not in eng for mid in mids):
                raise ValueError("Original v1 linked UBS headword not in source edition")
            stages["all_original_wlc_words"] += 1
            is_lexical = row["class"] in LEXICAL_CLASSES
            if is_lexical:
                stages["original_lexical_class_words"] += 1
            if mids:
                stages["all_words_with_any_lexical_headword"] += 1
                if is_lexical:
                    stages["lexical_words_with_any_headword"] += 1
            if len(mids) == 1:
                verse_mid_count[(verse, mids[0])] += 1
            elif len(mids) > 1:
                stages["multiple_ubs_headword_candidates"] += 1
            else:
                stages["no_source_supported_ubs_headword"] += 1
            if link["sense_ids"]:
                stages["existing_v1_source_corrob_sdbh_sense_words"] += 1
            if len(mids) == 1 and not link["sense_ids"]:
                words.append((wid, original_ref, verse, mids[0], row["class"],
                              row["lang"], link["status"]))
    if len(seen) != EXPECTED or stages["original_lexical_class_words"] != 248680:
        raise ValueError("Original WLC complete corpus size/class census drift")

    dispositions = Counter()
    examples = defaultdict(list)
    families = Counter()
    candidates = {}
    for wid, ref, verse, mid, source_class, lang, old_status in words:
        original_senses = eng[mid]["senses"]
        other_senses = fra[mid]["senses"]
        if not original_senses:
            outcome = "ubs_entry_has_no_source_senses"
        elif verse_mid_count[(verse, mid)] != 1:
            outcome = "multiple_source_words_same_headword_same_verse"
        elif len(original_senses) == 1:
            outcome = "one_ubs_sense_for_headword_no_context_validation"
        else:
            source_issues = any(
                entry["invalid_reference_count"] or
                other_senses[sid]["invalid_reference_count"] or
                entry["verse_references"] != other_senses[sid]["verse_references"]
                for sid, entry in original_senses.items()
            )
            if source_issues:
                outcome = "noncanonical_or_bilingual_discordant_ubs_source_refs"
            else:
                matches = [
                    sid for sid, entry in original_senses.items()
                    if verse in entry["verse_references"]
                ]
                if len(matches) == 1:
                    outcome = "unique_ubs_verse_witness_candidate_NOT_context_verified"
                    sid = matches[0]
                    candidates[wid] = {
                        "original_word_id": wid,
                        "original_reference": ref,
                        "ubs_headword": mid,
                        "source_candidate_lexid": sid,
                        "all_original_ubs_senses_for_entry": sorted(original_senses),
                        "evidence": "unique_UBS_EN_FR_sense_verse_citation_one_MACULA_word_same_headword_in_verse",
                        "contextually_semantically_verified": False,
                    }
                    families[mid] += 1
                elif matches:
                    outcome = "multiple_ubs_senses_cite_same_verse"
                else:
                    outcome = "no_ubs_sense_cites_word_verse"
        dispositions[outcome] += 1
        if len(examples[outcome]) < 5:
            examples[outcome].append({
                "word_id": wid, "reference": ref,
                "source_ubs_headword": mid, "source_class": source_class
            })
    if sum(dispositions.values()) != len(words):
        raise ValueError("Source-linked word disposition conservation failure")
    return {
        "status": "PRIVATE_UBS_HEBREW_V11_SOURCE_ONLY_SEMANTIC_FEASIBILITY_AUDIT_NO_CHOICES",
        "source_editions": {"ubs_hebrew": UBS_REVISION, "macula_wlc": MACULA_REVISION},
        "original_ubs_headwords": len(eng),
        "source_sense_inventory": source_counts,
        "bilingual_source_parity_cautions": source_parity,
        "corpus": dict(sorted(stages.items())),
        "entry_only_review_word_count": len(words),
        "source_only_semantic_candidate_dispositions": dict(sorted(dispositions.items())),
        "candidate_word_count": len(candidates),
        "candidate_headword_families": len(families),
        "top_candidate_headword_families": [
            {"ubs_main_id": mid, "candidate_words": n}
            for mid, n in families.most_common(20)
        ],
        "original_word_id_to_private_verse_witness_candidate": dict(sorted(candidates.items())),
        "disposition_examples": dict(sorted(examples.items())),
        "independently_contextually_validated": 0,
        "original_source_or_v1_release_modified": False,
        "publication_approved": False,
        "published": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("index", "english", "french", "macula", "output"):
        p.add_argument("--" + k, type=Path, required=True)
    a = p.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    report = assess(load(a.index), load(a.english), load(a.french), a.macula)
    a.output.write_text(json.dumps(report, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":")) + "\n", encoding="utf-8")
    print("UBS_HEBREW_V11_ONE_PASS_SOURCE_SEMANTIC_FEASIBILITY",
          json.dumps({
              "original_words": report["corpus"]["all_original_wlc_words"],
              "entry_only_review_words": report["entry_only_review_word_count"],
              "source_senses": report["source_sense_inventory"]["original_ubs_sense_ids"],
              "candidate_words": report["candidate_word_count"],
              "headwords": report["candidate_headword_families"],
              "dispositions": report["source_only_semantic_candidate_dispositions"],
              "source_sense_reference_inventory": report["source_sense_inventory"],
              "bilingual_reference_cautions": report["bilingual_source_parity_cautions"],
              "existing_v1_sdbh_sense_candidates": report["corpus"].get("existing_v1_source_corrob_sdbh_sense_words", 0),
              "contextually_verified": 0, "published": False,
          }, sort_keys=True))


if __name__ == "__main__":
    main()
