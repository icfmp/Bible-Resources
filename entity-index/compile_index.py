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
    for ref in decision.get("remove_references", []):
        if not isinstance(ref, str) or len(ref) != 8 or not ref.isdigit():
            raise ValueError(f"{entry['source_id']}: invalid removed verse reference")
        if references.count(ref) != 1:
            raise ValueError(
                f"{entry['source_id']}: cannot remove missing or non-unique verse: {ref}")
        references.remove(ref)
    for ref in decision.get("add_references", []):
        if not isinstance(ref, str) or len(ref) != 8 or not ref.isdigit():
            raise ValueError(f"{entry['source_id']}: invalid added verse reference")
        if ref in references:
            raise ValueError(f"{entry['source_id']}: verse already referenced: {ref}")
        references.append(ref)


def canonical_source_corpus(source_lock: dict, raw_corpus: str) -> str:
    """Resolve an observed ACAI field label to a pinned source corpus key."""
    mapping = source_lock.get("source_corpora")
    if not isinstance(mapping, dict):
        raise ValueError("Missing pinned source corpus-name crosswalk")
    resolved = mapping.get(raw_corpus)
    if not isinstance(resolved, str) or resolved not in source_lock["source_editions"]:
        raise ValueError(f"Unrecognized original source corpus: {raw_corpus!r}")
    return resolved


def build(source_root: Path, source_lock: dict, editorial: dict,
          source_absences: dict | None = None,
          source_verse_absences: dict | None = None,
          reference_qualifications: dict | None = None) -> dict:
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
    # Hash every original JSON byte stream, in a deterministic relative-path
    # order. A Git commit label alone does not detect a modified worktree.
    source_manifest = hashlib.sha256()
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
            rel = path.relative_to(source_root).as_posix().encode("utf-8")
            raw_hash = hashlib.sha256(raw).digest()
            source_manifest.update(len(rel).to_bytes(4, "big"))
            source_manifest.update(rel)
            source_manifest.update(raw_hash)
            originals.append((record, raw_hash.hex()))
    source_snapshot_sha256 = source_manifest.hexdigest()
    locked_snapshot = source_lock.get("source_snapshot_sha256")
    if locked_snapshot is not None:
        if (not isinstance(locked_snapshot, str)
                or len(locked_snapshot) != 64
                or any(c not in "0123456789abcdef" for c in locked_snapshot)):
            raise ValueError("Invalid pinned original JSON snapshot SHA-256")
        if locked_snapshot != source_snapshot_sha256:
            raise ValueError(
                "Original JSON source snapshot digest mismatch: "
                f"locked {locked_snapshot}; actual {source_snapshot_sha256}")
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
                        standard_corpus = canonical_source_corpus(source_lock, corpus)
                        source_format = source_lock["source_editions"][standard_corpus]
                        expected_prefix = source_format["word_id_prefix"]
                        digits = source_format["word_id_digits"]
                        if (not isinstance(digits, int) or isinstance(digits, bool)
                                or digits < 8):
                            raise ValueError(
                                f"Invalid original word ID digit count for {standard_corpus}")
                        if not word.startswith(expected_prefix):
                            raise ValueError(
                                f"{entry['id']}: {corpus} word prefix incompatible: {word!r}")
                        if len(word) != digits + len(expected_prefix) or not word[len(expected_prefix):].isdigit():
                            raise ValueError(
                                f"{entry['id']}: {corpus} malformed original word ID: {word!r}")
                        candidates[f"{standard_corpus}:{word}"].add((entry["id"], field))
    # A pinned-source audit may prove that an imported annotation refers to
    # a word ID that does not exist in the claimed original-language edition.
    # Keep all source groups in 'entities'; suppress only unsafe lookup claims
    # and emit a reversible, provenance-rich diagnostics record.
    if source_absences is None:
        source_absences = {
            "schema_version": 1, "corpus": "wlc",
            "source_edition": source_lock["source_editions"]["wlc"]["edition"],
            "word_ids": [], "provenance": [],
        }
    if source_absences.get("schema_version") != 1:
        raise ValueError("Unsupported missing-word audit schema")
    corpus = source_absences.get("corpus")
    edition = source_absences.get("source_edition")
    catalog = source_lock["source_editions"].get(corpus)
    if not isinstance(catalog, dict) or catalog.get("edition") != edition:
        raise ValueError("Missing-word audit is not pinned to this original edition")
    prefix = catalog.get("word_id_prefix")
    digits = catalog.get("word_id_digits")
    reported_ids = source_absences.get("word_ids")
    evidence = source_absences.get("provenance")
    if not isinstance(reported_ids, list) or not isinstance(evidence, list):
        raise ValueError("Malformed source-word audit manifest")
    if reported_ids and not evidence:
        raise ValueError("Unattested word claims require source provenance")
    if len(set(reported_ids)) != len(reported_ids):
        raise ValueError("Duplicate source-unattested word ID")
    unattested = {}
    for word_id in sorted(reported_ids):
        if (not isinstance(word_id, str) or not isinstance(prefix, str)
                or not isinstance(digits, int) or isinstance(digits, bool)
                or len(word_id) != len(prefix) + digits
                or not word_id.startswith(prefix)
                or not word_id[len(prefix):].isdigit()):
            raise ValueError(f"Invalid source-unattested word ID: {word_id!r}")
        key = f"{corpus}:{word_id}"
        if key not in candidates:
            raise ValueError(f"Unattested word not in source index: {key}")
        if any(field != "subject_referents" for _, field in candidates[key]):
            raise ValueError(f"Unattested word also has direct/pronominal claims: {key}")
        unattested[key] = {
            "source_edition": edition,
            "evidence": evidence,
            "source_claims": [{"entity_id": entity_id, "link_type": field}
                              for entity_id, field in sorted(candidates.pop(key))],
        }
    by_word = {
        word: [{"entity_id": entity_id, "link_type": field}
               for entity_id, field in sorted(hits)]
        for word, hits in sorted(candidates.items())
    }
    # Source may intentionally contain repeated indirect word groups.
    # Report raw assignments separately from distinct entity/field claims:
    # the inverse lookup necessarily collapses identical candidate pairs.
    unattested_raw_assignments = sum(
        1 for entity in entries
        for corpora in entity["occurrences"].values()
        for source_corpus, groups in corpora.items()
        for group in groups
        for word in group
        if f"{canonical_source_corpus(source_lock, source_corpus)}:{word}" in unattested
    )
    # This is an edition-specific source-WORD-INVENTORY compatibility
    # annotation, not a decision about canonical Bible versification or
    # which textual readings are genuine. Raw entity references stay intact.
    if source_verse_absences is None:
        source_verse_absences = {
            "schema_version": 1, "corpus": "sblgnt",
            "source_edition": source_lock["source_editions"]["sblgnt"]["edition"],
            "verse_ids": [], "provenance": [],
        }
    if source_verse_absences.get("schema_version") != 1:
        raise ValueError("Unsupported absent-verse inventory schema")
    verse_corpus = source_verse_absences.get("corpus")
    verse_edition = source_verse_absences.get("source_edition")
    verse_catalog = source_lock["source_editions"].get(verse_corpus)
    if not isinstance(verse_catalog, dict) or verse_catalog.get("edition") != verse_edition:
        raise ValueError("Absent-verse inventory not pinned to this original edition")
    reported_verses = source_verse_absences.get("verse_ids")
    verse_evidence = source_verse_absences.get("provenance")
    if not isinstance(reported_verses, list) or not isinstance(verse_evidence, list):
        raise ValueError("Malformed absent-verse inventory manifest")
    if reported_verses and not verse_evidence:
        raise ValueError("Absent-verse inventory needs source audit provenance")
    if len(reported_verses) != len(set(reported_verses)):
        raise ValueError("Duplicate source-absent verse IDs")
    # An optional source-cited interpretive layer distinguishes an alternate
    # verse number from a textual-variant reading. No source references or
    # original words are reclassified or rewritten by this metadata.
    context_by_verse = {}
    if "verse_qualifications" in source_verse_absences:
        contexts = source_verse_absences["verse_qualifications"]
        if not isinstance(contexts, list):
            raise ValueError("Malformed source verse-qualification list")
        permitted = {
            "traditional_textual_variant_not_in_pinned_main_text",
            "doxology_in_edition_apparatus_not_main_word_inventory",
            "alternate_verse_number_for_final_benediction",
        }
        for context in contexts:
            if not isinstance(context, dict):
                raise ValueError("Invalid source verse-qualification record")
            verse = context.get("verse_id")
            explanation = context.get("explanation")
            evidence = context.get("evidence")
            classification = context.get("classification")
            if (not isinstance(verse, str)
                    or len(verse) != 8 or not verse.isdigit()
                    or classification not in permitted
                    or not isinstance(explanation, str) or not explanation.strip()
                    or not isinstance(evidence, list) or len(evidence) < 2
                    or any(not isinstance(e, str) or not e.strip() for e in evidence)):
                raise ValueError(f"Invalid source verse-qualification evidence: {context!r}")
            if verse in context_by_verse:
                raise ValueError(f"Duplicate source verse qualification: {verse}")
            equivalent = context.get("equivalent_benediction_source_verse")
            if equivalent is not None:
                if (classification != "alternate_verse_number_for_final_benediction"
                        or not isinstance(equivalent, str)
                        or len(equivalent) != 8 or not equivalent.isdigit()
                        or equivalent == verse or equivalent[:5] != verse[:5]):
                    raise ValueError(f"Invalid verse-number comparison: {verse}")
            if (classification == "alternate_verse_number_for_final_benediction"
                    and equivalent is None):
                raise ValueError(f"Missing benediction comparison verse: {verse}")
            context_by_verse[verse] = {
                "classification": classification,
                "explanation": explanation,
                "evidence": evidence,
            }
            if equivalent is not None:
                context_by_verse[verse]["equivalent_benediction_source_verse"] = equivalent
        if set(context_by_verse) != set(reported_verses):
            raise ValueError(
                f"Unqualified pinned source verses: "
                f"{sorted(set(reported_verses) - set(context_by_verse))}")
    unattested_verses = {}
    for verse in sorted(reported_verses):
        if not isinstance(verse, str) or len(verse) != 8 or not verse.isdigit():
            raise ValueError(f"Malformed source-absent verse ID: {verse!r}")
        claims = [entry["id"] for entry in entries if verse in entry["references"]]
        if not claims:
            raise ValueError(f"Source-absent verse not referenced in derived index: {verse}")
        unattested_verses[f"{verse_corpus}:{verse}"] = {
            "source_edition": verse_edition,
            "source_reference_claims": claims,
            "evidence": verse_evidence,
            "scope": "absent_from_pinned_original_word_inventory_only",
            **({"source_context": context_by_verse[verse]}
               if verse in context_by_verse else {}),
        }
    # Reference claims without matching source-edition word anchors may derive
    # from textual variants, later epistle subscriptions or historical
    # identifications. Their reference lists stay exactly as imported.
    if reference_qualifications is None:
        reference_qualifications = {
            "schema_version": 1, "corpus": "sblgnt",
            "source_edition": source_lock["source_editions"]["sblgnt"]["edition"],
            "claims": [],
        }
    if reference_qualifications.get("schema_version") != 1:
        raise ValueError("Unsupported reference-qualification schema")
    ref_corpus = reference_qualifications.get("corpus")
    ref_edition = reference_qualifications.get("source_edition")
    ref_catalog = source_lock["source_editions"].get(ref_corpus)
    if not isinstance(ref_catalog, dict) or ref_catalog.get("edition") != ref_edition:
        raise ValueError("Reference qualifications not pinned to original edition")
    claim_rows = reference_qualifications.get("claims")
    if not isinstance(claim_rows, list):
        raise ValueError("Malformed reference qualification claims")
    by_source_id = {entry["source_id"]: entry for entry in entries}
    qualified = defaultdict(list)
    seen_claims = set()
    allowed = {
        "textual_variant_name_not_in_pinned_edition",
        "traditional_subscription_candidate",
    }
    for claim in claim_rows:
        if not isinstance(claim, dict):
            raise ValueError("Malformed reference qualification claim")
        source_id, verse = claim.get("source_id"), claim.get("verse_id")
        cls, proof = claim.get("classification"), claim.get("evidence")
        if (not isinstance(source_id, str)
                or not isinstance(verse, str) or len(verse) != 8
                or not verse.isdigit() or cls not in allowed
                or not isinstance(proof, list) or not proof
                or any(not isinstance(v, str) or not v.strip() for v in proof)):
            raise ValueError(f"Invalid reference qualification claim: {claim!r}")
        claim_key = (source_id, verse)
        if claim_key in seen_claims:
            raise ValueError(f"Duplicate reference qualification: {claim_key}")
        seen_claims.add(claim_key)
        entry = by_source_id.get(source_id)
        if entry is None:
            raise ValueError(f"Reference qualification points to absent index record: {source_id}")
        if verse not in entry["references"]:
            raise ValueError(f"Reference qualification has no source reference: {claim_key}")
        for field, corpora in entry["occurrences"].items():
            for raw_corpus, groups in corpora.items():
                if canonical_source_corpus(source_lock, raw_corpus) != ref_corpus:
                    continue
                for group in groups:
                    if any(word[1:9] == verse for word in group):
                        raise ValueError(
                            f"Reference qualification conflicts with exact original word "
                            f"anchor: {source_id} {verse} {field}")
        qualified[f"{ref_corpus}:{verse}"].append({
            "entity_id": entry["id"],
            "source_id": source_id,
            "source_edition": ref_edition,
            "classification": cls,
            "evidence": proof,
        })
    qualified = {
        ref: sorted(rows, key=lambda row: (row["entity_id"], row["source_id"]))
        for ref, rows in sorted(qualified.items())
    }
    return {
        "format": "bible-entity-index",
        "schema_version": 1,
        "provenance": {
            "source_repository": source_lock["source_repository"],
            "source_commit": source_lock["source_commit"],
            "source_snapshot_sha256": source_snapshot_sha256,
            "source_license": source_lock["source_license"],
            "source_credit": source_lock["source_credit"],
            "reviewed_hebrew_source": source_lock["reviewed_hebrew_source"],
            "reviewed_greek_source": source_lock["reviewed_greek_source"],
            "source_editions": source_lock["source_editions"],
            "source_corpora": source_lock["source_corpora"],
        },
        "statistics": {
            "source_records": len(originals),
            "index_entities": len(entries),
            "quarantined_records": len(quarantined),
            "reviewed_entries": sum(e["review_status"] == "editorially_reviewed"
                                    for e in entries),
            "indexed_distinct_source_words": len(by_word),
            "unattested_distinct_source_words": len(unattested),
            "unattested_raw_word_assignments": unattested_raw_assignments,
            "unattested_source_verses": len(unattested_verses),
            "qualified_source_verse_contexts": len(context_by_verse),
            "unattested_source_verse_reference_claims": sum(
                len(x["source_reference_claims"])
                for x in unattested_verses.values()),
            "qualified_source_reference_claims": sum(
                len(rows) for rows in qualified.values()),
        },
        "quarantined": sorted(quarantined, key=lambda x: x["source_id"]),
        "entities": entries,
        "by_word": by_word,
        "unattested_source_words": unattested,
        "unattested_source_verses": unattested_verses,
        "qualified_source_references": qualified,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Local immutable snapshot of the ACAI repository")
    parser.add_argument("--lock", type=Path, default=Path(__file__).with_name("source.lock.json"))
    parser.add_argument("--decisions", type=Path, default=Path(__file__).with_name("editorial-decisions.json"))
    parser.add_argument("--source-absences", type=Path,
                        default=Path(__file__).with_name("source-unattested-words.json"),
                        help="Pinned source-word audit evidence; only affects derived lookup")
    parser.add_argument("--source-verse-absences", type=Path,
                        default=Path(__file__).with_name("source-unattested-verses.json"),
                        help="Edition-specific pinned original-word verse inventory evidence")
    parser.add_argument("--reference-qualifications", type=Path,
                        default=Path(__file__).with_name("source-reference-qualifications.json"),
                        help="Pinned source-specific textual variant/subscription claim receipts")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-source-commit", action="store_true",
                        help="Require the local Git HEAD to equal the source lock")
    args = parser.parse_args()
    lock = read_json(args.lock)
    if args.verify_source_commit:
        if not lock.get("source_snapshot_sha256"):
            raise SystemExit(
                "Pinned source verification requires a source_snapshot_sha256 lock")
        import subprocess
        actual = subprocess.check_output(
            ["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
        if actual != lock["source_commit"]:
            raise SystemExit(f"Wrong pinned source revision: {actual}")
        worktree = subprocess.check_output(
            ["git", "-C", str(args.source), "status", "--porcelain",
             "--untracked-files=all"], text=True)
        if worktree.strip():
            raise SystemExit(
                "Pinned source checkout has modified or untracked files; "
                "do not build against a dirty source snapshot")
    result = build(args.source, lock, read_json(args.decisions),
                   read_json(args.source_absences),
                   read_json(args.source_verse_absences),
                   read_json(args.reference_qualifications))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")
    print(json.dumps(result["statistics"], sort_keys=True))


if __name__ == "__main__":
    main()
