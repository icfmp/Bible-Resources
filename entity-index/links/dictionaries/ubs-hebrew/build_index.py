#!/usr/bin/env python3
"""Generate a deterministic UBS Hebrew (EN/FR) to pinned Macula WLC bridge.

Links exact SDBH lexical sense IDs first, with a separate entry-only Strong
fallback. It never supplies dictionary prose or guesses a contextual sense.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

UBS_REVISION = "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"
MACULA_REVISION = "47db250bd55d0d8577f2a94fba114ef16c35b23c"
UBS_FILES = {
    "en": "dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-en.JSON",
    "fr": "dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-fr.JSON",
}
STRONG = re.compile(r"^([HA])0*([0-9]+)([a-z]?)$")
MACULA_STRONG = re.compile(r"^([0-9]+)([a-z]?)$")
LEX_ID = re.compile(r"^[0-9]{15}$")


def senses(entry):
    for form in entry.get("BaseForms") or []:
        for sense in form.get("LEXMeanings") or []:
            yield sense


def signature(entry):
    """Compare identifiers, not independently translated explanatory fields."""
    return (
        entry["Lemma"],
        tuple(entry.get("StrongCodes") or []),
        tuple(sorted((str(s["LEXID"]), str(s.get("LEXEntryCode") or ""))
                     for s in senses(entry))),
    )


def build(english, french):
    if not isinstance(english, list) or not isinstance(french, list):
        raise ValueError("Expected UBS array of dictionary records")
    en = {e["MainId"]: e for e in english}
    fr = {e["MainId"]: e for e in french}
    if len(en) != len(english) or len(fr) != len(french):
        raise ValueError("Duplicate UBS MainId")
    if en.keys() != fr.keys():
        raise ValueError("Bilingual MainId inventories differ")
    drift = [key for key in en if signature(en[key]) != signature(fr[key])]
    if drift:
        raise ValueError(f"EN/FR lexical ID drift; refusing to infer bilingual identity: {drift[:10]} (total {len(drift)})")
    by_strong = defaultdict(set)
    by_sdbh = defaultdict(set)
    by_entry_strong_family = defaultdict(set)
    skipped = set()
    sense_assignments = 0
    for mid, entry in en.items():
        for raw in entry.get("StrongCodes") or []:
            m = STRONG.fullmatch(str(raw))
            if not m:
                skipped.add(str(raw))
                continue
            by_strong[f"{m.group(1)}{int(m.group(2))}{m.group(3)}"].add(mid)
            by_entry_strong_family[mid].add(f"{m.group(1)}{int(m.group(2))}")
        for sense in senses(entry):
            sid = str(sense["LEXID"])
            if not LEX_ID.fullmatch(sid):
                raise ValueError(f"Malformed UBS lexical sense identifier: {mid} {sid}")
            by_sdbh[sid].add(mid)
            sense_assignments += 1
    return {
        "format": "bsi-ubs-hebrew-lexical-crosswalk",
        "schema_version": 1,
        "languages": ["en", "fr"],
        "license": "CC BY-SA 4.0",
        "dictionary": {
            "name": "UBS Dictionary of Biblical Hebrew",
            "repository": "https://github.com/ubsicap/ubs-open-license",
            "revision": UBS_REVISION,
            "edition": "0.9.4",
            "paths": UBS_FILES,
        },
        "macula": {
            "repository": "https://github.com/Clear-Bible/macula-hebrew",
            "revision": MACULA_REVISION,
            "corpus": "wlc",
            "lookup": ["sdbh", "strongnumberx", "lang"],
        },
        "policy": {
            "sdbh": "original_sense_id_only_if_corrobated_by_matching_ubs_entry_strong_family",
            "strong": "entry_only_exact_language_specific_numeric_or_suffix_code",
            "unresolved": "return_all_candidates_never_guess_contextual_sense",
            "definitions": "not_redistributed_look_up_UBS_original_edition",
        },
        "statistics": {
            "shared_entries": len(en),
            "shared_senses": sense_assignments,
            "unique_sdbh_ids": len(by_sdbh),
            "indexed_strong_numbers": len(by_strong),
            "excluded_non_numeric_strong_codes": len(skipped),
        },
        "by_sdbh": {k: sorted(v) for k, v in sorted(by_sdbh.items())},
        "by_entry_strong_family": {mid: sorted(by_entry_strong_family[mid]) for mid in sorted(en)},
        "by_strong": {k: sorted(v) for k, v in sorted(by_strong.items())},
    }


def lookup(index, sdbh, strongnumberx, lang):
    """Cross-check a sense ID against the UBS lexeme Strong family before use."""
    sdbh = str(sdbh or "").strip()
    raw_strong = str(strongnumberx or "").strip()
    lang = str(lang or "").strip()
    m = MACULA_STRONG.fullmatch(raw_strong)
    if sdbh and LEX_ID.fullmatch(sdbh) and m and lang in ("H", "A"):
        family = f"{lang}{int(m.group(1))}"
        # A numerically identical SDBH/LEXID can now point to a DIFFERENT
        # lexeme in the UBS edition. Never trust an ID without corroboration.
        direct = [mid for mid in index["by_sdbh"].get(sdbh, [])
                  if family in index["by_entry_strong_family"].get(mid, [])]
        if direct:
            return {
                "status": "direct_sense_candidates" if len(direct) > 1 else "direct_sense",
                "entry_ids": list(direct),
                "sense_ids": [sdbh],
                "evidence": "macula_sdbh_and_ubs_strong_numeric_family",
            }
    # Incompatible SDBH IDs are ignored: only the ORIGINAL exact Strong may
    # supply an entry-only fallback; never steal a sense from an unrelated ID.
    if lang not in ("H", "A") or not m:
        return {"status": "no_verified_lexical_link", "entry_ids": [],
                "sense_ids": [], "evidence": "none"}
    key = f"{lang}{int(m.group(1))}{m.group(2)}"
    candidates = index["by_strong"].get(key, [])
    return {
        "status": ("no_entry_match" if not candidates else
                   "ambiguous_entry_only" if len(candidates) > 1 else
                   "entry_only"),
        "entry_ids": list(candidates),
        "sense_ids": [],
        "evidence": "macula_strong_exact_only" if candidates else "none",
    }



def normalized_hebrew_consonants(text):
    """Strip vowel/cantillation marks, preserving shin and sin identity.

    Only suitable together with original language-specific Strong family,
    original word ID, and unique UBS entry; never a stand-alone match.
    """
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        char for char in decomposed
        if not unicodedata.combining(char) or char in ("\u05c1", "\u05c2")
    )


def build_word_links(index, english, macula):
    """Resolve WLC words using exact lemma in a Strong family without homonym guessing.

    A suffix mismatch is NEVER promoted to an ordinary Strong synonym. Every
    inferred headword is pinned to a particular original WLC word ID, and
    matching original lemma, language and Strong code are checked at lookup.
    No contextual sense identifier is inferred.
    """
    numeric_family = defaultdict(set)
    by_entry = {}
    for entry in english:
        mid = entry["MainId"]
        by_entry[mid] = entry
        for raw in entry.get("StrongCodes") or []:
            match = STRONG.fullmatch(str(raw))
            if match:
                numeric_family[f"{match.group(1)}{int(match.group(2))}"].add(mid)
    # Alternative entry-only evidence when cross-edition Strong numbers differ:
    # identical original fully pointed lemma + exact original 15-digit SDBH
    # identifier owned by a unique UBS entry, corroborated by H/A language.
    # The ID is never promoted to a contextual sense.
    by_exact_lemma_language = defaultdict(set)
    by_alternate_lemma_language = defaultdict(set)
    by_consonants_language = defaultdict(set)
    for mid, entry in by_entry.items():
        for raw in entry.get("StrongCodes") or []:
            m = STRONG.fullmatch(str(raw))
            if m:
                by_exact_lemma_language[
                    (m.group(1), unicodedata.normalize("NFC", entry["Lemma"]))
                ].add(mid)
                by_consonants_language[
                    (m.group(1), normalized_hebrew_consonants(entry["Lemma"]))
                ].add(mid)
                for alternate in entry.get("AlternateLemmas") or ():
                    if isinstance(alternate, str) and alternate:
                        by_alternate_lemma_language[
                            (m.group(1), unicodedata.normalize("NFC", alternate))
                        ].add(mid)
    word_links = {}
    seen = set()
    with macula.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"xml:id", "lemma", "sdbh", "strongnumberx", "lang", "class"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing original Macula fields: {sorted(required)}")
        for row in reader:
            wid = row["xml:id"]
            if wid in seen:
                raise ValueError(f"Duplicate original WLC word ID: {wid}")
            seen.add(wid)
            if row["class"] not in ("noun", "verb", "adj", "adv", "num"):
                continue
            # Original exact sense/Strong matches always take precedence.
            if lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])["entry_ids"]:
                continue
            source_code = MACULA_STRONG.fullmatch(row["strongnumberx"])
            if row["lang"] not in ("H", "A") or not source_code:
                continue
            family = f"{row['lang']}{int(source_code.group(1))}"
            # A numeric Strong family can contain several unrelated lexical
            # entries. Restrict to identical original lemma before deciding
            # uniqueness; still reject true homographs (same lemma, >1 ID).
            lemma = row["lemma"]
            normalized = unicodedata.normalize("NFC", lemma)
            matching = [
                mid for mid in numeric_family.get(family, set())
                if unicodedata.normalize("NFC", by_entry[mid]["Lemma"]) == normalized
            ]
            match_type = "exact_lemma"
            if not matching:
                # The 0.9.4 dictionary itself publishes AlternateLemmas.
                # These spellings, unlike inferred orthographic variants,
                # are authoritative editorial entry aliases. Strong family
                # and unique UBS headword are still mandatory.
                matching = [
                    mid for mid in numeric_family.get(family, set())
                    if any(
                        unicodedata.normalize("NFC", alternate) == normalized
                        for alternate in (by_entry[mid].get("AlternateLemmas") or [])
                        if isinstance(alternate, str)
                    )
                ]
                if matching:
                    match_type = "ubs_original_alternate_lemma_same_strong_family"
            if not matching and row["class"] in ("verb", "noun", "adj", "adv"):
                # Different vocalization is allowed only with independent
                # numeric Strong-family agreement and a unique consonantal
                # UBS headword. Reject all consonantal homographs; preserve
                # distinct shin/sin and do not alter the original lemma.
                root = normalized_hebrew_consonants(lemma)
                matching = [
                    mid for mid in numeric_family.get(family, set())
                    if normalized_hebrew_consonants(by_entry[mid]["Lemma"]) == root
                ]
                match_type = ("verb_consonants_same_strong_family" if row["class"] == "verb"
                              else "nonverb_consonants_same_strong_family")
            if len(matching) != 1:
                # Do not equate the original SDBH source ID with a UBS
                # contextual sense. However, when an *exact* original SDBH
                # identifier and the independently identical source lemma
                # both identify one language-correct UBS headword, allow
                # an entry-only link. A different Strong number is permitted
                # only by this stricter path, never by spelling alone.
                sid = row["sdbh"].strip()
                lemma_owners = by_exact_lemma_language.get((row["lang"], normalized), set())
                sid_owners = set(index["by_sdbh"].get(sid, [])) if LEX_ID.fullmatch(sid) else set()
                corroborated = lemma_owners & sid_owners
                if len(corroborated) == 1 and len(lemma_owners) == 1 and len(sid_owners) == 1:
                    mid = next(iter(corroborated))
                    match_type = "exact_lemma_and_original_sdbh_owning_ubs_entry"
                else:
                    # An *UBS-published* alternate form, separately backed by
                    # the exact source SDBH owner's entry, is stronger than
                    # inferred consonant resemblance. Still entry-only.
                    alternate_owners = by_alternate_lemma_language.get(
                        (row["lang"], normalized), set()
                    )
                    alternate_candidates = alternate_owners & sid_owners
                    if (len(sid_owners) == 1 and len(alternate_owners) == 1
                            and len(alternate_candidates) == 1):
                        mid = next(iter(alternate_candidates))
                        match_type = "alternate_lemma_and_original_sdbh_owner"
                    else:
                        # One original source sense ID PLUS a unique headword
                        # with the same Hebrew consonants and H/A language.
                    # Treat as entry-level evidence only, never a UBS sense.
                        root_owners = by_consonants_language.get(
                            (row["lang"], normalized_hebrew_consonants(lemma)), set()
                        )
                        root_candidates = root_owners & sid_owners
                        if len(sid_owners) != 1 or len(root_owners) != 1 or len(root_candidates) != 1:
                            continue
                        mid = next(iter(root_candidates))
                        match_type = "consonants_and_original_sdbh_owning_ubs_entry"
            else:
                mid = matching[0]
            word_links[wid] = {
                "entry_id": mid,
                "match_type": match_type,
                "lemma": lemma,
                "strong": row["strongnumberx"],
                "lang": row["lang"],
            }
    return dict(sorted(word_links.items()))


def lookup_word(index, word_id, sdbh, strongnumberx, lang, lemma):
    """Use an original pinned WLC word ID when exact ordinary matching fails."""
    ordinary = lookup(index, sdbh, strongnumberx, lang)
    if ordinary["entry_ids"]:
        return ordinary
    record = index.get("by_macula_word", {}).get(str(word_id))
    if record is None:
        return ordinary
    if ((record["lemma"], record["strong"], record["lang"]) != (
        str(lemma), str(strongnumberx), str(lang)
    ) or (
        record.get("match_type") == "editorially_reviewed_original_wlc_headword_only"
        and record.get("original_sdbh") != str(sdbh or "")
    )):
        return {
            "status": "source_word_mismatch",
            "entry_ids": [], "sense_ids": [], "evidence": "source_identity_mismatch",
        }
    return {
        "status": "entry_only",
        "entry_ids": [record["entry_id"]],
        "sense_ids": [],
        "evidence": (
            "macula_word_editorially_reviewed_headword_only"
            if record.get("match_type") == "editorially_reviewed_original_wlc_headword_only"
            else "macula_word_verb_consonants_unique_entry_same_strong_family"
            if record.get("match_type") == "verb_consonants_same_strong_family"
            else "macula_word_nonverb_consonants_unique_entry_same_strong_family"
            if record.get("match_type") == "nonverb_consonants_same_strong_family"
            else "macula_word_exact_lemma_and_source_sdbh_ubs_owner_entry_only"
            if record.get("match_type") == "exact_lemma_and_original_sdbh_owning_ubs_entry"
            else "macula_word_consonants_and_source_sdbh_ubs_owner_entry_only"
            if record.get("match_type") == "consonants_and_original_sdbh_owning_ubs_entry"
            else "macula_word_ubs_alternate_lemma_and_source_sdbh_owner_entry_only"
            if record.get("match_type") == "alternate_lemma_and_original_sdbh_owner"
            else "macula_word_ubs_published_alternate_lemma_same_strong_family"
            if record.get("match_type") == "ubs_original_alternate_lemma_same_strong_family"
            else "macula_word_exact_lemma_unique_entry_within_ubs_strong_family"
        ),
    }


def audit_word_links(index, macula):
    """Independent full-corpus delta, retaining the legacy generic lookup."""
    results = Counter()
    with macula.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            old = lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])
            new = lookup_word(index, row["xml:id"], row["sdbh"],
                              row["strongnumberx"], row["lang"], row["lemma"])
            results["original_word_rows"] += 1
            if old["entry_ids"]:
                results["generic_entry_links"] += 1
            if new["entry_ids"]:
                results["word_aware_entry_links"] += 1
            if new["evidence"] in (
                "macula_word_exact_lemma_unique_entry_within_ubs_strong_family",
                "macula_word_verb_consonants_unique_entry_same_strong_family",
                "macula_word_nonverb_consonants_unique_entry_same_strong_family",
                "macula_word_exact_lemma_and_source_sdbh_ubs_owner_entry_only",
                "macula_word_consonants_and_source_sdbh_ubs_owner_entry_only",
                "macula_word_ubs_published_alternate_lemma_same_strong_family",
                "macula_word_ubs_alternate_lemma_and_source_sdbh_owner_entry_only",
                "macula_word_editorially_reviewed_headword_only",
            ):
                results["additional_entry_only_links"] += 1
                results[new["evidence"]] += 1
            if new["sense_ids"]:
                results["sense_links"] += 1
            if old["entry_ids"] and old["entry_ids"] != new["entry_ids"]:
                raise AssertionError(f"Previously linked word changed: {row['xml:id']}")
    if results["additional_entry_only_links"] != len(index["by_macula_word"]):
        raise AssertionError("Original word-ID link count drift")
    return dict(sorted(results.items()))

def audit(index, macula):
    count = Counter()
    sample = {"direct_sense": None, "entry_only": None, "no_entry_match": None}
    with macula.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        required = {"xml:id", "sdbh", "strongnumberx", "lang"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Macula WLC TSV lacks columns {sorted(required)}")
        for row in reader:
            if not (len(row["xml:id"]) >= 13 and row["xml:id"][0] == "o"
                    and row["xml:id"][1:13].isdigit()
                    and not any(ch.isspace() for ch in row["xml:id"][13:])):
                raise ValueError(f"Malformed pinned original word: {row['xml:id']}")
            count["macula_words"] += 1
            if row["sdbh"].strip():
                count["macula_with_sdbh"] += 1
            outcome = lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])
            count[outcome["status"]] += 1
            if outcome["entry_ids"]:
                count["with_ubs_entry_candidates"] += 1
            if outcome["sense_ids"]:
                count["with_exact_ubs_sense_candidates"] += 1
            if len(outcome["entry_ids"]) > 1:
                count["ambiguous_ubs_entry_candidates"] += 1
            if len(outcome["sense_ids"]) > 1:
                count["multiple_lexical_sense_candidates"] += 1
            if outcome["status"] in sample and sample[outcome["status"]] is None:
                sample[outcome["status"]] = {
                    "word_id": row["xml:id"],
                    "sdbh": row["sdbh"], "lang": row["lang"],
                    "strongnumberx": row["strongnumberx"],
                    **outcome,
                }
    return dict(sorted(count.items())), sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--french", type=Path, required=True)
    parser.add_argument("--macula", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    en = json.loads(args.english.read_text(encoding="utf-8"))
    fr = json.loads(args.french.read_text(encoding="utf-8"))
    index = build(en, fr)
    index["by_macula_word"] = build_word_links(index, en, args.macula)
    coverage, sample = audit(index, args.macula)
    index["coverage"] = coverage
    index["coverage_with_word_ids"] = audit_word_links(index, args.macula)
    # Report edition-specific headword scope separately from the immutable
    # original-corpus coverage. No outside-scope entry becomes a fake link.
    from runpy import run_path
    scope_audit = run_path(
        str(Path(__file__).with_name("audit_dictionary_scope.py"))
    )["analyze"]
    scope = scope_audit(index, en, args.macula)["summary"]
    if scope["lexical_source_occurrences"] != 248680:
        raise ValueError("Unexpected pinned lexical-class source inventory")
    if scope["linked_occurrences"] + scope["indexable_scope_unresolved"] + scope["outside_indexed_ubs_headword_scope"] != scope["lexical_source_occurrences"]:
        raise AssertionError("Source lexical occurrences were lost in scope filtering")
    index["coverage_scope"] = {
        "name": "indexed_ubs_0_9_4_headword_scope",
        "limitations": "no_attested_exact_or_shin_sin_preserving_consonantal_headword_and_no_same_strong_family_is_out_of_scope_not_absolute_semantic_absence",
        "original_lexical_source_occurrences": scope["lexical_source_occurrences"],
        "linked_occurrences": scope["linked_occurrences"],
        "outside_indexed_headword_scope": scope["outside_indexed_ubs_headword_scope"],
        "indexable_denominator": scope["indexable_scope_denominator"],
        "indexable_unresolved": scope["indexable_scope_unresolved"],
        "coverage_pct": scope["indexable_scope_coverage_pct"],
        "full_source_coverage_pct": scope["all_source_lexical_coverage_pct"],
        "excluded_reason": "no_matching_strong_or_headword_in_ubs_inventory",
        "review": {
            key: scope[key] for key in (
                "different_strong_same_exact_headword_review",
                "different_strong_same_consonants_review",
                "matching_strong_family_unresolved_review",
                "source_code_unreadable_review",
            )
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n", encoding="utf-8")
    print("BSI_UBS_HEBREW_BUILD", json.dumps(index["statistics"], sort_keys=True))
    print("BSI_UBS_HEBREW_COVERAGE", json.dumps(coverage, sort_keys=True))
    print("BSI_UBS_HEBREW_WORD_LINKS", json.dumps(index["coverage_with_word_ids"], sort_keys=True))
    print("BSI_UBS_HEBREW_SCOPE", json.dumps(index["coverage_scope"], sort_keys=True))
    print("BSI_UBS_HEBREW_SAMPLES", json.dumps(sample, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
