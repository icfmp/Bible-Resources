#!/usr/bin/env python3
"""Build a minimal, bilingual UBS Greek lexeme/sense crosswalk for Macula.

Only stable lexical identifiers are copied. No dictionary definitions.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

UBS_REVISION = "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"
MACULA_REVISION = "8423afe47b9e8f24b7772e808af45c7159a6fe7e"
UBS_FILES = {
    "en": "dictionaries/greek/JSON/UBSGreekNTDic-v1.0-en.JSON",
    "fr": "dictionaries/greek/JSON/UBSGreekNTDic-v1.0-fr.JSON",
}
UBS_BLOBS = {
    "en": "b6f2535c3ed8988480f479fdaf4f69867a776119",
    "fr": "42b1abeaa7f7f7abaf72f6edd7e45badea42b90f",
}
STRONG_CODE = re.compile(r"G[0-9]{4,5}$")
MACULA_STRONG = re.compile(r"[0-9]+$")
UBS_SENSE_CODE = re.compile(r"[0-9]+\.[0-9]+[a-z]?$")


def sense_records(record):
    for form in record.get("BaseForms") or []:
        for item in form.get("LEXMeanings") or []:
            yield item


def signature(record):
    return (
        record["Lemma"],
        tuple(record.get("StrongCodes") or []),
        tuple(sorted((x["LEXID"], x["LEXEntryCode"]) for x in sense_records(record))),
    )


def build(en, fr):
    en_by_id = {x["MainId"]: x for x in en}
    fr_by_id = {x["MainId"]: x for x in fr}
    if len(en_by_id) != len(en) or len(fr_by_id) != len(fr):
        raise ValueError("Duplicate UBS lexical entry ID")
    if en_by_id.keys() != fr_by_id.keys():
        raise ValueError("English and French MainId inventories differ")
    for key in en_by_id:
        if signature(en_by_id[key]) != signature(fr_by_id[key]):
            raise ValueError(f"English and French IDs differ: {key}")

    strong_index = defaultdict(set)
    ln_index = defaultdict(set)
    ignored_variant_strongs = set()
    lexical_senses = 0
    for mid, entry in en_by_id.items():
        for strong in entry.get("StrongCodes") or []:
            if not STRONG_CODE.fullmatch(strong):
                ignored_variant_strongs.add(strong)
                continue
            strong_index[str(int(strong[1:]))].add(mid)
        for item in sense_records(entry):
            lexical_senses += 1
            code = item.get("LEXEntryCode")
            if code and UBS_SENSE_CODE.fullmatch(str(code)):
                ln_index[code].add((mid, item["LEXID"]))
    result = {
        "format": "bsi-ubs-greek-lexical-crosswalk",
        "schema_version": 1,
        "languages": ["en", "fr"],
        "license": "CC BY-SA 4.0",
        "dictionary": {
            "name": "UBS Dictionary of the Greek New Testament",
            "repository": "https://github.com/ubsicap/ubs-open-license",
            "revision": UBS_REVISION,
            "edition": "1.0",
            "paths": UBS_FILES,
            "git_blob_sha": UBS_BLOBS,
        },
        "macula": {
            "repository": "https://github.com/Clear-Bible/macula-greek",
            "revision": MACULA_REVISION,
            "corpus": "sblgnt",
            "lookup": ["strong", "ln"],
        },
        "policy": {
            "strong": "exact_numeric_codes_only_no_variant_suffix_guess",
            "ln": "exact_code_and_parent_lexeme_intersection_only",
            "unresolved": "return_candidates_never_infer_a_unique_sense",
            "definitions": "not_redistributed_look_up_original_UBS_edition",
        },
        "statistics": {
            "shared_entries": len(en),
            "shared_senses": lexical_senses,
            "indexed_strong_numbers": len(strong_index),
            "indexed_lexical_codes": len(ln_index),
            "excluded_suffixed_strong_codes": len(ignored_variant_strongs),
        },
        "by_strong": {k: sorted(v) for k, v in sorted(strong_index.items(), key=lambda x: int(x[0]))},
        "by_ln": {k: [list(p) for p in sorted(v)] for k, v in sorted(ln_index.items())},
    }
    return result


def lookup(index, strong, ln):
    """Return all lexical and sense candidates; no context sense is fabricated."""
    strong = str(strong).strip()
    ln = str(ln).strip()
    if not MACULA_STRONG.fullmatch(strong):
        return {"status": "unsupported_strong_structure", "entry_ids": [], "sense_ids": []}
    entry_ids = index["by_strong"].get(str(int(strong)), [])
    sense_refs = [tuple(pair) for code in ln.split() for pair in index["by_ln"].get(code, [])]
    sense_refs = sorted(set(pair for pair in sense_refs if pair[0] in entry_ids))
    return {
        "status": ("no_entry_match" if not entry_ids else
                   "ambiguous_entry" if len(entry_ids) > 1 else
                   "entry_with_sense_candidates" if sense_refs else "entry_only"),
        "entry_ids": list(entry_ids),
        "sense_ids": [sense_id for _, sense_id in sense_refs],
    }


def audit_macula(index, tsv_path):
    total = 0
    found_entry = 0
    found_sense = 0
    ambiguous = 0
    multi_codes = 0
    missing = 0
    with tsv_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"xml:id", "lemma", "strong", "ln"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("Pinned Macula source missing required columns")
        for row in reader:
            total += 1
            if not row["xml:id"].startswith("n"):
                raise ValueError("Invalid Macula Greek word ID")
            result = lookup(index, row["strong"], row["ln"])
            if result["status"] == "unsupported_strong_structure":
                multi_codes += 1
            elif result["entry_ids"]:
                found_entry += 1
                if result["sense_ids"]:
                    found_sense += 1
                if len(result["entry_ids"]) > 1:
                    ambiguous += 1
            else:
                missing += 1
    return {
        "macula_words": total,
        "with_ubs_entry_candidates": found_entry,
        "with_corresponding_sense_candidates": found_sense,
        "ambiguous_ubs_entry_candidates": ambiguous,
        "unsupported_compound_strong": multi_codes,
        "no_ubs_entry": missing,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--french", type=Path, required=True)
    parser.add_argument("--macula", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    en = json.loads(args.english.read_text(encoding="utf-8-sig"))
    fr = json.loads(args.french.read_text(encoding="utf-8-sig"))
    index = build(en, fr)
    index["coverage"] = audit_macula(index, args.macula)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"))+"\n",
        encoding="utf-8")
    print(json.dumps({**index["statistics"], **index["coverage"]}, sort_keys=True))


if __name__ == "__main__":
    main()
