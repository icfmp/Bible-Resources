#!/usr/bin/env python3
"""Build a standalone, offline biblical entity-to-original-word index.

ACAI is a pinned data witness, not the authority for our published identities.
Neither biblical source words nor original source files are ever edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

CATEGORIES = {
    "people": "person",
    "places": "place",
    "groups": "group",
    "deities": "deity",
    "fauna": "fauna",
    "flora": "flora",
    "realia": "realia",
    "keyterms": "keyterm",
}
LINK_FIELDS = ("explicit_instances", "pronominal_referents", "subject_referents")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def checked_groups(groups, context):
    """Validate without silently altering segment order or repetitions."""
    if not isinstance(groups, dict):
        raise ValueError(f"{context}: expected corpus-to-groups dictionary")
    for corpus, rows in groups.items():
        if not isinstance(corpus, str) or not corpus or not isinstance(rows, list):
            raise ValueError(f"{context}: invalid corpus or group list")
        for row in rows:
            if not isinstance(row, list) or not row:
                raise ValueError(f"{context}: invalid empty or non-list word group")
            for word in row:
                if (not isinstance(word, str) or len(word) < 9
                        or word[0] not in ("o", "n")
                        or not word[1:9].isdigit()):
                    raise ValueError(f"{context}: invalid original-word ID {word!r}")
    return groups


def apply_word_edits(entry, decision):
    occurrence = entry["occurrences"]["explicit_instances"]
    for corpus, groups in checked_groups(
            decision.get("remove_explicit_instances", {}),
            f"{entry['source_id']} removal").items():
        present = occurrence.get(corpus, [])
        for group in groups:
            if group not in present:
                raise ValueError(f"{entry['source_id']}: absent group cannot be removed: {group}")
            present.remove(group)
    for corpus, groups in checked_groups(
            decision.get("add_explicit_instances", {}),
            f"{entry['source_id']} addition").items():
        present = occurrence.setdefault(corpus, [])
        for group in groups:
            if group in present:
                raise ValueError(f"{entry['source_id']}: source group already exists: {group}")
            present.append(group)
    references = entry["references"]
    for ref in decision.get("add_references", []):
        if not isinstance(ref, str) or len(ref) != 8 or not ref.isdigit():
            raise ValueError(f"{entry['source_id']}: invalid added verse reference")
        if ref in references:
            raise ValueError(f"{entry['source_id']}: verse already referenced: {ref}")
        references.append(ref)


def build(source_root: Path, source_lock: dict, editorial: dict) -> dict:
    if source_lock.get("schema_version") != 1 or editorial.get("schema_version") != 1:
        raise ValueError("Unsupported lock or editorial decision schema")
    decisions = {}
    for decision in editorial["decisions"]:
        original_id = decision["source_id"]
        if original_id in decisions:
            raise ValueError(f"Duplicate editorial decision for {original_id}")
        if decision["action"] not in ("quarantine", "replace_identity", "amend_occurrences"):
            raise ValueError(f"Unsupported action for {original_id}")
        if not decision.get("reason") or not decision.get("evidence"):
            raise ValueError(f"Missing editorial justification or evidence: {original_id}")
        decisions[original_id] = decision

    originals = []
    for dirname, prefix in CATEGORIES.items():
        folder = source_root / dirname / "json"
        if not folder.is_dir():
            raise ValueError(f"Missing source category: {folder}")
        for path in sorted(folder.glob("*.json")):
            raw = path.read_bytes()
            record = json.loads(raw)
            source_id = record.get("id")
            if source_id != f"{prefix}:{path.stem}":
                raise ValueError(f"Source ID/path disagreement: {path} ({source_id})")
            originals.append((record, hashlib.sha256(raw).hexdigest()))
    expected = source_lock["source_records_expected"]
    if len(originals) != expected:
        raise ValueError(f"Incomplete source snapshot: {len(originals)} entries; expected {expected}")
    original_ids = {record["id"] for record, _ in originals}
    if len(original_ids) != len(originals):
        raise ValueError("Repeated original entity ID")
    if unknown := set(decisions) - original_ids:
        raise ValueError(f"Editorial decisions target nonexistent records: {sorted(unknown)}")

    new_ids = {
        source_id: decision.get("id", source_id)
        for source_id, decision in decisions.items()
        if decision["action"] == "replace_identity"
    }
    entries = []
    quarantined = []
    for original, raw_hash in originals:
        source_id = original["id"]
        decision = decisions.get(source_id)
        action = decision["action"] if decision else "retain_source_candidate"
        if action == "quarantine":
            quarantined.append({
                "source_id": source_id,
                "source_sha256": raw_hash,
                "reason": decision["reason"],
                "evidence": decision["evidence"],
            })
            continue
        original_primary = original.get("primary_id", source_id)
        entity_id = new_ids.get(source_id, source_id)
        canonical_id = new_ids.get(original_primary, original_primary)
        if decision and decision.get("canonical_id"):
            canonical_id = decision["canonical_id"]
        kind = (decision.get("kind") if decision else None) or entity_id.split(":", 1)[0]
        refs = original.get("references", [])
        if not isinstance(refs, list) or any(
                not isinstance(ref, str) or len(ref) != 8 or not ref.isdigit()
                for ref in refs):
            raise ValueError(f"{source_id}: malformed verse references")
        occurrences = {
            field: checked_groups(
                json.loads(json.dumps(original.get(field, {}))),
                f"{source_id}:{field}")
            for field in LINK_FIELDS
        }
        entry = {
            "id": entity_id,
            "kind": kind,
            "canonical_id": canonical_id,
            "source_id": source_id,
            "source_primary_id": original_primary,
            "source_sha256": raw_hash,
            "review_status": "editorially_reviewed" if decision else "source_unreviewed",
            "references": list(refs),
            "key_references": original.get("key_references", []),
            "occurrences": occurrences,
        }
        if decision:
            if action in ("replace_identity", "amend_occurrences"):
                apply_word_edits(entry, decision)
            entry["editorial_evidence"] = decision["evidence"]
            entry["editorial_reason"] = decision["reason"]
        entries.append(entry)

    entries.sort(key=lambda x: x["id"])
    assigned_ids = [entry["id"] for entry in entries]
    if len(set(assigned_ids)) != len(entries):
        raise ValueError("Two source records resolve to the same output entity ID")
    # Deliberately never select a single entity when two source records
    # mention the same original word. Preserve ambiguity and link type.
    candidates = defaultdict(set)
    for entry in entries:
        for field, corpora in entry["occurrences"].items():
            for corpus, groups in corpora.items():
                for group in groups:
                    for word in group:
                        candidates[f"{corpus}:{word}"].add((entry["id"], field))
    by_word = {
        word: [{"entity_id": entity_id, "link_type": field}
               for entity_id, field in sorted(hits)]
        for word, hits in sorted(candidates.items())
    }
    return {
        "format": "bible-entity-index",
        "schema_version": 1,
        "provenance": {
            "source_repository": source_lock["source_repository"],
            "source_commit": source_lock["source_commit"],
            "source_license": source_lock["source_license"],
            "source_credit": source_lock["source_credit"],
            "reviewed_hebrew_source": source_lock["reviewed_hebrew_source"],
            "reviewed_greek_source": source_lock["reviewed_greek_source"],
            "source_editions": source_lock["source_editions"],
        },
        "statistics": {
            "source_records": len(originals),
            "index_entities": len(entries),
            "quarantined_records": len(quarantined),
            "reviewed_entries": sum(e["review_status"] == "editorially_reviewed"
                                    for e in entries),
            "indexed_distinct_source_words": len(by_word),
        },
        "quarantined": sorted(quarantined, key=lambda x: x["source_id"]),
        "entities": entries,
        "by_word": by_word,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Local immutable snapshot of the ACAI repository")
    parser.add_argument("--lock", type=Path, default=Path(__file__).with_name("source.lock.json"))
    parser.add_argument("--decisions", type=Path, default=Path(__file__).with_name("editorial-decisions.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-source-commit", action="store_true",
                        help="Require the local Git HEAD to equal the source lock")
    args = parser.parse_args()
    lock = read_json(args.lock)
    if args.verify_source_commit:
        import subprocess
        actual = subprocess.check_output(
            ["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
        if actual != lock["source_commit"]:
            raise SystemExit(f"Wrong pinned source revision: {actual}")
    result = build(args.source, lock, read_json(args.decisions))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")
    print(json.dumps(result["statistics"], sort_keys=True))


if __name__ == "__main__":
    main()
