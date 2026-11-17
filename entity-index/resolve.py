#!/usr/bin/env python3
"""Offline, evidence-aware original-word -> biblical entity candidate resolver."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class EntityResolver:
    """Never infer identity from lemma, spelling, Strong or verse co-occurrence."""

    def __init__(self, index: dict):
        if index.get("format") != "bible-entity-index" or index.get("schema_version") != 1:
            raise ValueError("Incompatible entity index schema")
        provenance = index.get("provenance", {})
        self.editions = provenance.get("source_editions")
        if not isinstance(self.editions, dict) or not self.editions:
            raise ValueError("Missing corpus edition/prefix provenance")
        self.words = index.get("by_word")
        if not isinstance(self.words, dict):
            raise ValueError("Missing exact-word index")
        self.unattested_words = index.get("unattested_source_words", {})
        if not isinstance(self.unattested_words, dict):
            raise ValueError("Invalid source-unattested word audit")
        if set(self.unattested_words) & set(self.words):
            raise ValueError("Source-unattested word must not remain lookup-indexed")
        self.unattested_verses = index.get("unattested_source_verses", {})
        if not isinstance(self.unattested_verses, dict):
            raise ValueError("Invalid pinned source-absent verse inventory")
        entities = index.get("entities")
        if not isinstance(entities, list):
            raise ValueError("Missing entity records")
        self.entities = {row["id"]: row for row in entities}
        if len(self.entities) != len(entities):
            raise ValueError("Duplicate entity IDs in index")

    def resolve(self, *, corpus: str, edition: str, word_id: str, verse_id: str) -> dict:
        """Return all distinct source-backed candidates for one exact word.

        Edition and ORG verse identity are mandatory, not optional fallbacks.
        This only resolves index claims; it does not verify each entity identity.
        """
        result = {
            "status": "",
            "corpus": corpus,
            "edition": edition,
            "word_id": word_id,
            "verse_id": verse_id,
            "candidates": [],
            "canonical_ids": [],
        }
        expected = self.editions.get(corpus)
        if not isinstance(expected, dict):
            result["status"] = "unavailable_corpus"
        elif edition != expected.get("edition"):
            result["status"] = "incompatible_source_edition"
        elif not (isinstance(verse_id, str) and len(verse_id) == 8
                  and verse_id.isdigit()):
            result["status"] = "invalid_verse_id"
        elif not (isinstance(word_id, str) and len(word_id) >= 9
                  and word_id.startswith(expected.get("word_id_prefix", "\0"))
                  and word_id[1:9].isdigit()):
            result["status"] = "invalid_source_word_id"
        elif word_id[1:9] != verse_id:
            result["status"] = "verse_context_mismatch"
        elif corpus + ":" + verse_id in self.unattested_verses:
            result["status"] = "verse_not_in_pinned_original_word_inventory"
            result["source_absence"] = self.unattested_verses[corpus + ":" + verse_id]
        elif corpus + ":" + word_id in self.unattested_words:
            result["status"] = "unattested_source_word_id"
            result["source_absence"] = self.unattested_words[corpus + ":" + word_id]
        else:
            hits = self.words.get(corpus + ":" + word_id, [])
            seen = set()
            for hit in hits:
                entity_id = hit["entity_id"]
                link_type = hit["link_type"]
                if (entity_id, link_type) in seen:
                    continue
                seen.add((entity_id, link_type))
                entity = self.entities.get(entity_id)
                if entity is None:
                    raise ValueError(f"Word index points to unknown entity: {entity_id}")
                result["candidates"].append({
                    "id": entity_id,
                    "canonical_id": entity["canonical_id"],
                    "kind": entity["kind"],
                    "link_type": link_type,
                    "review_status": entity["review_status"],
                    "source_record_id": entity["source_id"],
                    "reference_list_includes_verse": verse_id in entity["references"],
                    "editorial_scope_note": entity.get("editorial_reason"),
                })
            result["candidates"].sort(key=lambda x: (x["canonical_id"], x["id"], x["link_type"]))
            result["canonical_ids"] = sorted({
                candidate["canonical_id"] for candidate in result["candidates"]
            })
            if not result["candidates"]:
                result["status"] = "no_indexed_entity"
            elif len(result["canonical_ids"]) > 1:
                result["status"] = "ambiguous_source_candidates"
            else:
                # Even a single index annotation is NOT a verified historical identity.
                result["status"] = "source_candidate"
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--edition", required=True,
                        help="Exact pinned corpus identifier/version")
    parser.add_argument("--word-id", required=True)
    parser.add_argument("--verse-id", required=True,
                        help="Eight-digit original ORG book/chapter/verse ID")
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8"))
    result = EntityResolver(index).resolve(
        corpus=args.corpus, edition=args.edition,
        word_id=args.word_id, verse_id=args.verse_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
