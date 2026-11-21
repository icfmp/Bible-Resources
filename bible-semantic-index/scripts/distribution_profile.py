#!/usr/bin/env python3
"""Derive a deterministic category-excluded BSI distribution from an audited index.

This is a distribution projection, not a rewrite of the pinned ACAI witness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def exclude_kinds(index: dict, kinds: set[str]) -> dict:
    if not kinds or not all(isinstance(k, str) and k for k in kinds):
        raise ValueError("At least one nonempty category must be excluded")
    if index.get("schema_version") != 1 or not isinstance(index.get("entities"), list):
        raise ValueError("Unsupported BSI index")
    result = json.loads(json.dumps(index))
    originals = result["entities"]
    dropped = {e["id"] for e in originals if e["kind"] in kinds}
    if not dropped:
        raise ValueError("Excluded category is absent: " + ", ".join(sorted(kinds)))
    removed_source_ids = {e["source_id"] for e in originals if e["id"] in dropped}
    result["entities"] = [e for e in originals if e["id"] not in dropped]
    result["quarantined"] = [
        q for q in result["quarantined"]
        if q["source_id"].split(":", 1)[0] not in kinds
    ]
    result["by_word"] = {
        key: kept for key, hits in result["by_word"].items()
        if (kept := [h for h in hits if h["entity_id"] not in dropped])
    }
    result["unattested_source_words"] = {
        key: {**value, "source_claims": claims}
        for key, value in result["unattested_source_words"].items()
        if (claims := [c for c in value["source_claims"]
                       if c["entity_id"] not in dropped])
    }
    result["unattested_source_verses"] = {
        key: {**value, "source_reference_claims": claims}
        for key, value in result["unattested_source_verses"].items()
        if (claims := [c for c in value["source_reference_claims"]
                       if c not in dropped])
    }
    result["qualified_source_references"] = {
        key: kept for key, rows in result["qualified_source_references"].items()
        if (kept := [r for r in rows if r["entity_id"] not in dropped
                     and r["source_id"] not in removed_source_ids])
    }
    stats = result["statistics"]
    stats["index_entities"] = len(result["entities"])
    stats["quarantined_records"] = len(result["quarantined"])
    stats["reviewed_entries"] = sum(
        e["review_status"] == "editorially_reviewed" for e in result["entities"])
    stats["indexed_distinct_source_words"] = len(result["by_word"])
    stats["unattested_distinct_source_words"] = len(result["unattested_source_words"])
    # Raw-word assignment count cannot be inferred from deduplicated inverse claims.
    # Compute it from the preserved original, repeated occurrence groups.
    missing = set(result["unattested_source_words"])
    source_corpora = result["provenance"]["source_corpora"]
    stats["unattested_raw_word_assignments"] = sum(
        1 for e in result["entities"] for field in e["occurrences"].values()
        for corpus, groups in field.items() for group in groups for word in group
        if f"{source_corpora[corpus]}:{word}" in missing
    )
    stats["unattested_source_verses"] = len(result["unattested_source_verses"])
    stats["unattested_source_verse_reference_claims"] = sum(
        len(v["source_reference_claims"])
        for v in result["unattested_source_verses"].values())
    stats["qualified_source_reference_claims"] = sum(
        len(v) for v in result["qualified_source_references"].values())
    result["distribution_profile"] = {
        "name": "bsi-v0.1-without-keyterms" if kinds == {"keyterm"} else "category-exclusion",
        "excluded_kinds": sorted(kinds),
        "excluded_entity_count": len(dropped),
        "source_records_unchanged": True,
    }
    # No excluded entity may leak via any public inverse or QA lookup.
    encoded = json.dumps({
        k: result[k] for k in (
            "entities", "quarantined", "by_word", "unattested_source_words",
            "unattested_source_verses", "qualified_source_references")
    })
    if any('"' + entity_id + '"' in encoded for entity_id in dropped):
        raise ValueError("Excluded entity reference leaked into distribution")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Must not overwrite the original audited index")
    index = json.loads(args.input.read_text(encoding="utf-8"))
    result = exclude_kinds(index, {"keyterm"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result["distribution_profile"], sort_keys=True))


if __name__ == "__main__":
    main()
