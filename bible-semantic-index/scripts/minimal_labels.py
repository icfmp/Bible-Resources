#!/usr/bin/env python3
"""Extract minimal English labels for a filtered BSI candidate from pinned ACAI.

No descriptions, multilingual tables or other original fields are distributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FOLDERS = {
    "person": "people", "place": "places", "group": "groups",
    "deity": "deities", "flora": "flora", "fauna": "fauna",
    "realia": "realia", "keyterm": "keyterms",
}


def label_manifest(source: Path, index: dict) -> dict:
    if index.get("schema_version") != 1 or not index.get("distribution_profile"):
        raise ValueError("Requires an explicitly filtered BSI distribution")
    labels = {}
    missing = []
    for item in index["entities"]:
        source_id = item["source_id"]
        prefix, _, stem = source_id.partition(":")
        if prefix not in FOLDERS or not stem or "/" in stem or "\\" in stem or stem in (".", ".."):
            raise ValueError(f"Unsupported source ID: {source_id}")
        path = source / FOLDERS[prefix] / "json" / (stem + ".json")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["source_sha256"]:
            raise ValueError(f"Source content hash mismatch: {source_id}")
        original = json.loads(raw)
        if original.get("id") != source_id:
            raise ValueError(f"Source identity mismatch: {source_id}")
        label = original.get("localizations", {}).get("eng", {}).get("preferred_label")
        if not isinstance(label, str) or not label.strip():
            missing.append(item["id"])
            continue
        labels[item["id"]] = {
            "label": label,
            "language": "en",
            "source_id": source_id,
            "review_status": "source_unreviewed_label",
        }
    return {
        "format": "bsi-minimal-labels",
        "schema_version": 1,
        "source_snapshot_sha256": index["provenance"]["source_snapshot_sha256"],
        "source_license": index["provenance"]["source_license"],
        "distribution_profile": index["distribution_profile"]["name"],
        "labels": dict(sorted(labels.items())),
        "missing_ids": missing,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    result = label_manifest(args.source, index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"labels": len(result["labels"]),
                      "missing": len(result["missing_ids"])}, sort_keys=True))


if __name__ == "__main__":
    main()
