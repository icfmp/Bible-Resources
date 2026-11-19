#!/usr/bin/env python3
"""Read-only, exhaustive reasons for unresolved UBS Hebrew–MACULA WLC links.

This report is not a crosswalk. Candidate relations are never promoted to
verified links merely because they share a numeric prefix or spelling.
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SENSE = re.compile(r"^[0-9]{15}$")
NUMERIC = re.compile(r"^[0-9]+$")
STRONG = re.compile(r"^[HA]0*([0-9]+)$")
SUFFIX_STRONG = re.compile(r"^([HA])0*([0-9]+)([a-z])$")


def analyze(index, dictionary, source):
    ids = {e["MainId"] for e in dictionary}
    entry_strongs = defaultdict(set)
    for item in dictionary:
        for raw in item.get("StrongCodes") or []:
            match = STRONG.fullmatch(str(raw))
            if match:
                entry_strongs[item["MainId"]].add(f"{raw[0]}{int(match.group(1))}")
    variant_index = defaultdict(set)
    for item in dictionary:
        for raw in item.get("StrongCodes") or []:
            matched = SUFFIX_STRONG.fullmatch(str(raw))
            if matched:
                variant_index[f"{matched.group(1)}{int(matched.group(2))}{matched.group(3)}"].add(item["MainId"])
    summary = Counter()
    examples = {}
    sdbh_prefixes = Counter()
    suffixes = Counter()
    matched_variants = Counter()
    unmatched_variants = Counter()
    conflicts = Counter()
    statuses = Counter()
    from runpy import run_path
    lookup = run_path(str(Path(__file__).with_name("build_index.py")))["lookup"]

    with Path(source).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            result = lookup(index, row["sdbh"], row["strongnumberx"], row["lang"])
            statuses[result["status"]] += 1
            if result["entry_ids"]:
                continue
            summary["unresolved_rows"] += 1
            code = row["sdbh"].strip()
            strong = row["strongnumberx"].strip()
            language = row["lang"].strip()
            if code:
                summary["unresolved_with_sdbh"] += 1
                if not SENSE.fullmatch(code):
                    category="malformed_sdbh"
                else:
                    parent=code[:6]+"000000000"
                    if parent in ids:
                        summary["sdbh_parent_in_edition"] += 1
                        sdbh_prefixes[parent] += 1
                        if language in ("H","A") and NUMERIC.fullmatch(strong):
                            expected=f"{language}{int(strong)}"
                            if expected in entry_strongs[parent]:
                                category="sdbh_parent_and_strong_agree"
                            else:
                                category="sdbh_parent_strong_disagree"
                                conflicts[(parent, expected)] += 1
                        else:
                            category="sdbh_parent_but_strong_not_exact_numeric"
                    else:
                        category="sdbh_parent_missing_in_edition"
            elif language not in ("H","A"):
                category="no_sdbh_unsupported_language"
            elif not NUMERIC.fullmatch(strong):
                category="no_sdbh_non_numeric_strong"
            else:
                category="no_sdbh_numeric_strong_absent"
            summary[category] += 1
            if strong and not NUMERIC.fullmatch(strong):
                suffixes[strong] += 1
                match=SUFFIX_STRONG.fullmatch(f"{language}{strong}")
                if match:
                    normalized=f"{match.group(1)}{int(match.group(2))}{match.group(3)}"
                    if normalized in variant_index:
                        summary["exact_ubs_suffix_strong_match"] += 1
                        matched_variants[(normalized, tuple(sorted(variant_index[normalized])))] += 1
                    else:
                        unmatched_variants[normalized] += 1
            if category not in examples:
                examples[category] = {
                    "word_id":row["xml:id"],"ref":row["ref"],
                    "sdbh":code,"strongnumberx":strong,"lang":language,
                    "lemma":row["lemma"],"candidate_parent":code[:6]+"000000000" if SENSE.fullmatch(code) else None,
                }
    return {
        "summary":dict(summary.most_common()),
        "lookup_statuses":dict(statuses.most_common()),
        "examples":examples,
        "top_unresolved_sdbh_entry_prefixes":sdbh_prefixes.most_common(15),
        "top_non_numeric_macula_strongs":suffixes.most_common(15),
        "distinct_ubs_suffix_strong_codes":len(variant_index),
        "top_exact_ubs_suffix_matches": [
            {"strong":code,"entry_ids":list(ids),"rows":count}
            for (code,ids),count in matched_variants.most_common(20)
        ],
        "top_unmatched_suffix_codes":unmatched_variants.most_common(20),
        "top_sdbh_parent_strong_conflicts": [
            {"parent":parent,"strong":strong,"rows":n}
            for (parent,strong),n in conflicts.most_common(15)
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index",type=Path,required=True)
    p.add_argument("--english",type=Path,required=True)
    p.add_argument("--macula",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    index=json.loads(a.index.read_text(encoding="utf-8"))
    entries=json.loads(a.english.read_text(encoding="utf-8"))
    report=analyze(index,entries,a.macula)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("UNRESOLVED_REASON_SUMMARY",json.dumps(report["summary"],ensure_ascii=False))
    print("UNRESOLVED_TOP_NON_NUMERIC_STRONG",json.dumps(report["top_non_numeric_macula_strongs"],ensure_ascii=False))
    print("UNRESOLVED_UBS_EXACT_SUFFIX_MATCHES",json.dumps(report["top_exact_ubs_suffix_matches"],ensure_ascii=False))
    print("UNRESOLVED_UBS_SUFFIX_CODE_COUNT",report["distinct_ubs_suffix_strong_codes"])
    print("UNRESOLVED_TOP_SDBH_CONFLICTS",json.dumps(report["top_sdbh_parent_strong_conflicts"],ensure_ascii=False))


if __name__=="__main__":
    main()
