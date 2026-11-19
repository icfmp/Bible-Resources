#!/usr/bin/env python3
"""Stage explicitly witnessed UBS headword-only links without changing index.json.

This is a review preview, not a release or an authorization to generalize
from sampled WLC words to an entire lexical family. Contextual sense IDs
are never supplied. Original WLC fields are checked against pinned sources.
"""
from __future__ import annotations

import argparse
import csv
import json
import runpy
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = runpy.run_path(str(HERE / "verify_reviewed_headwords.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))
MATCH_TYPE = "editorially_reviewed_original_wlc_headword_only"


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def stage(ledger: dict, index: dict, macula: Path) -> dict:
    """Stage only specific source word IDs witnessed in positive reviews."""
    editions = ledger["source_editions"]
    if (editions["ubs_revision"] != index["dictionary"]["revision"]
            or editions["macula_revision"] != index["macula"]["revision"]):
        raise ValueError("Pinned source revisions disagree with baseline index")
    pending: dict[str, tuple[dict, dict]] = {}
    family_keys = set()
    for decision in ledger["decisions"]:
        key = (decision["lang"], nfc(decision["lemma"]),
               decision["original_strong"])
        if key in family_keys:
            raise ValueError("Duplicate reviewed family")
        family_keys.add(key)
        if (decision.get("disposition") !=
                "source_reviewed_ubs_headword_entry_only"
                or decision.get("headword_identity_reviewed") is not True
                or decision.get("contextual_sense_id_approved") is not False
                or decision.get("index_word_links_applied") is not False
                or decision.get("source_data_modified") is not False):
            raise ValueError("Unsafe positive review status")
        for witness in decision["original_word_witnesses"]:
            word_id = witness["original_word_id"]
            if word_id in pending:
                raise ValueError("Original WLC witness appears twice: " + word_id)
            pending[word_id] = (decision, witness)

    staged = {}
    with Path(macula).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        required = {"xml:id", "lemma", "lang", "strongnumberx",
                    "sdbh", "class", "ref"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Pinned MACULA WLC source missing fields")
        for row in reader:
            word_id = row["xml:id"]
            pair = pending.pop(word_id, None)
            if pair is None:
                continue
            decision, witness = pair
            if (row["lang"] != decision["lang"]
                    or nfc(row["lemma"]) != nfc(decision["lemma"])
                    or row["strongnumberx"] != decision["original_strong"]
                    or row["sdbh"] != witness["original_sdbh"]
                    or row["ref"] != witness["reference"]
                    or row["class"] not in decision["original_source_classes"]):
                raise ValueError("Pinned original WLC witness changed: " + word_id)
            original = BUILD["lookup_word"](
                index, word_id, row["sdbh"], row["strongnumberx"],
                row["lang"], row["lemma"])
            if original["entry_ids"] or word_id in index.get("by_macula_word", {}):
                raise ValueError("Reviewed witness is not originally unlinked: " + word_id)
            staged[word_id] = {
                "entry_id": decision["ubs_candidate_main_id"],
                "match_type": MATCH_TYPE,
                "lemma": row["lemma"],
                "strong": row["strongnumberx"],
                "lang": row["lang"],
                "original_sdbh": row["sdbh"],
                "reference": row["ref"],
            }
    if pending:
        raise ValueError("Original reviewed WLC witnesses absent: " +
                         str(sorted(pending)))
    # This is an overlay preview: never modify the published frozen baseline.
    trial = dict(index)
    trial["by_macula_word"] = {
        **index.get("by_macula_word", {}), **staged
    }
    for word_id, record in staged.items():
        out = BUILD["lookup_word"](
            trial, word_id, record["original_sdbh"],
            record["strong"], record["lang"], record["lemma"])
        if (out["entry_ids"] != [record["entry_id"]]
                or out["sense_ids"] != []
                or out["status"] != "entry_only"
                or out["evidence"] != "macula_word_editorially_reviewed_headword_only"):
            raise ValueError("Unexpected staged lookup result: " + word_id)
    return {
        "format": "bsi-ubs-hebrew-source-reviewed-word-anchor-preview",
        "schema_version": 1,
        "source_editions": editions,
        "policy": ("Reviewed exact WLC word witnesses only, entry-only; "
                   "no contextual LEXID/SDBH sense, global Strong alias, "
                   "unwitnessed family expansion, or baseline index edit"),
        "summary": {
            "reviewed_families": len(family_keys),
            "reviewed_family_occurrences_not_automatically_linked": sum(
                d["original_occurrences"] for d in ledger["decisions"]),
            "staged_original_word_ids": len(staged),
            "new_contextual_senses": 0,
        },
        "by_macula_word": dict(sorted(staged.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("decisions", "register", "index", "english", "macula",
                 "output"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    ledger = json.loads(args.decisions.read_text(encoding="utf-8"))
    register = json.loads(args.register.read_text(encoding="utf-8"))
    index = json.loads(args.index.read_text(encoding="utf-8"))
    english = json.loads(args.english.read_text(encoding="utf-8"))
    VERIFY["verify"](ledger, register, english, args.macula)
    staged = stage(ledger, index, args.macula)
    expected = {"reviewed_families": 81,
                "reviewed_family_occurrences_not_automatically_linked": 274,
                "staged_original_word_ids": 139,
                "new_contextual_senses": 0}
    if staged["summary"] != expected:
        raise ValueError("Source-pinned reviewed word inventory changed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(staged, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print("UBS_REVIEWED_WORD_ANCHOR_PREVIEW",
          json.dumps(staged["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

