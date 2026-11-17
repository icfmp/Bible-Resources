#!/usr/bin/env python3
"""Audit exact original-word identity overlaps without changing source evidence.

A collision is an audit candidate, NOT a proven tagging mistake. Aliases that
resolve to one canonical identity and repeated indirect pointers remain intact.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

RANK = {
    "multiple_explicit_names": 0,
    "mixed_name_and_indirect": 1,
    "indirect_only": 2,
}


def audit(index: dict) -> dict:
    if index.get("format") != "bible-entity-index" or index.get("schema_version") != 1:
        raise ValueError("Incompatible entity index")
    entries = index.get("entities")
    by_word = index.get("by_word")
    if not isinstance(entries, list) or not isinstance(by_word, dict):
        raise ValueError("Missing indexed entity evidence")
    by_id = {e["id"]: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError("Repeated derived entity identifier")

    findings = []
    counts = defaultdict(int)
    for exact_word, hits in sorted(by_word.items()):
        if not isinstance(hits, list):
            raise ValueError("Invalid source word candidate list")
        people = defaultdict(lambda: {"source_records": set(), "link_types": set()})
        for hit in hits:
            entity_id = hit["entity_id"]
            entry = by_id.get(entity_id)
            if entry is None:
                raise ValueError(f"Word points to unknown derived record: {entity_id}")
            if entry["kind"] != "person":
                continue
            canonical = entry["canonical_id"]
            people[canonical]["source_records"].add(entity_id)
            people[canonical]["link_types"].add(hit["link_type"])
        if len(people) < 2:
            continue
        explicit = [
            ident for ident, evidence in people.items()
            if "explicit_instances" in evidence["link_types"]
        ]
        if len(explicit) >= 2:
            classification = "multiple_explicit_names"
        elif len(explicit) == 1:
            classification = "mixed_name_and_indirect"
        else:
            classification = "indirect_only"
        corpus, word_id = exact_word.split(":", 1)
        counts[classification] += 1
        findings.append({
            "corpus": corpus,
            "word_id": word_id,
            "source_verse_id": word_id[1:9],
            "classification": classification,
            "canonical_people": [
                {
                    "canonical_id": ident,
                    "records": sorted(evidence["source_records"]),
                    "link_types": sorted(evidence["link_types"]),
                }
                for ident, evidence in sorted(people.items())
            ],
        })
    findings.sort(key=lambda r: (
        RANK[r["classification"]], r["corpus"],
        r["source_verse_id"], r["word_id"]))
    return {
        "format": "bible-entity-identity-overlap-audit",
        "schema_version": 1,
        "source_commit": index["provenance"]["source_commit"],
        "source_editions": index["provenance"]["source_editions"],
        "statistics": {
            "distinct_person_original_word_overlap_candidates": len(findings),
            **{name: counts[name] for name in RANK},
        },
        "findings": findings,
        "warning": (
            "All findings are candidate ambiguities, not proven editorial mistakes. "
            "Never delete or choose a candidate without original-language context."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=20)
    args = ap.parse_args()
    if args.sample < 0:
        ap.error("--sample must not be negative")
    report = audit(json.loads(args.index.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print("PERSON_IDENTITY_OVERLAP_AUDIT", json.dumps(report["statistics"], sort_keys=True))
    for item in report["findings"][:args.sample]:
        print("PERSON_IDENTITY_OVERLAP_SAMPLE", json.dumps({
            "classification": item["classification"],
            "word_id": item["word_id"],
            "canonical_people": [v["canonical_id"] for v in item["canonical_people"]],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
