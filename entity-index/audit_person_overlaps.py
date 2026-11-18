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



REVIEW_CLASSES = {
    "shared_genealogical_name_component",
    "unresolved_patronymic_name_variant",
    "unresolved_person_identity",
}


def verify_explicit_name_reviews(audit_report: dict, manifest: dict) -> dict:
    """Check every distinct-person direct-name overlap against pinned receipts.

    This does not change the original ambiguity audit or resolve any word.
    A legitimate compound component may name two historical persons without
    being an error. Other identity claims remain explicitly unresolved.
    """
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "exact_word_distinct_person_review":
        raise ValueError("Unsupported exact-person overlap review format")
    for corpus, source_edition in manifest.get("source_editions", {}).items():
        edition = audit_report.get("source_editions", {}).get(corpus, {}).get("edition")
        if source_edition != edition:
            raise ValueError(f"Wrong original-language review edition: {corpus}")
    if set(manifest.get("source_editions", {})) != set(audit_report.get("source_editions", {})):
        raise ValueError("Incomplete review source-edition pin")
    original = {
        (row["corpus"], row["word_id"]): row
        for row in audit_report["findings"]
        if row["classification"] == "multiple_explicit_names"
    }
    if len(original) != audit_report["statistics"]["multiple_explicit_names"]:
        raise ValueError("Duplicate original explicit-name word audit rows")
    reviewed = {}
    for item in manifest.get("cases", []):
        key = (item["corpus"], item["word_id"])
        if key in reviewed:
            raise ValueError(f"Duplicate exact-word review {key}")
        if key not in original:
            raise ValueError(f"Review does not match any live explicit name overlap: {key}")
        if item.get("classification") not in REVIEW_CLASSES:
            raise ValueError(f"Invalid exact-word review classification: {key}")
        evidence = item.get("evidence")
        if (not isinstance(evidence, list) or len(evidence) < 2
                or any(not isinstance(x, str) or not x.strip() for x in evidence)
                or not isinstance(item.get("reason"), str) or not item["reason"].strip()):
            raise ValueError(f"Source evidence required for exact-word review: {key}")
        people = [person["canonical_id"] for person in original[key]["canonical_people"]]
        if people != item.get("canonical_people"):
            raise ValueError(f"Stale or incorrect distinct-person identities: {key}")
        reviewed[key] = {
            "corpus": key[0],
            "word_id": key[1],
            "source_verse_id": original[key]["source_verse_id"],
            "canonical_people": people,
            "classification": item["classification"],
            "reason": item["reason"],
            "evidence": evidence,
        }
    if set(reviewed) != set(original):
        raise ValueError(
            f"Unreviewed exact-person name overlaps: {sorted(set(original)-set(reviewed))}")
    counts = {label: sum(
        item["classification"] == label for item in reviewed.values()
    ) for label in sorted(REVIEW_CLASSES)}
    return {
        "format": "bible-entity-reviewed-explicit-name-overlaps",
        "schema_version": 1,
        "source_commit": audit_report["source_commit"],
        "source_editions": audit_report["source_editions"],
        "statistics": {"reviewed_explicit_name_word_overlaps": len(reviewed), **counts},
        "cases": [reviewed[key] for key in sorted(reviewed)],
        "policy": (
            "Shared genealogical components are not competing alternative "
            "identifications; unresolved source identities remain unresolved. "
            "Do not delete, merge, prioritize or alter original source words."
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
