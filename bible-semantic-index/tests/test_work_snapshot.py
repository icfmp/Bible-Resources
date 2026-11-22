#!/usr/bin/env python3
"""Snapshot archive immutability, tampering, missing files and source status tests."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
script = HERE.parent / "scripts" / "work_snapshot.py"
spec = importlib.util.spec_from_file_location("bsi_snapshot", script)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)

COMMIT = "a" * 40


def fixture(kind):
    if kind == "entity":
        return {
            "complete-entity-index.json": {"format": "bible-entity-index", "schema_version": 1,
                                          "entities": [], "by_word": {}},
            "public-projection.json": {"version": 1},
            "public-labels-en.json": {"version": 1},
        }
    if kind == "ubs-greek":
        return {
            "complete-word-review-index.json": {
                "original_word_ids": 137741,
                "provisional_semantic_word_ids": 123195,
                "by_original_macula_word_id": {str(i): {} for i in range(137741)},
                "publication_approved": False,
            },
            "context-review-batches.json": {"status": "PRIVATE"},
        }
    return {
        "reviewed-lexical-candidate.json": {"status": "PRIVATE"},
        "semantic-feasibility-audit.json": {
            "candidate_word_count": 53981, "independently_contextually_validated": 0,
            "publication_approved": False,
        },
        "contextual-pilot-witnesses.json": {
            "sample_words": 72, "candidate_lexids_approved": 0,
            "publication_approved": False,
        },
    }


class SnapshotTests(unittest.TestCase):
    def build(self, d, kind):
        p = Path(d)
        input_paths = {}
        for name, value in fixture(kind).items():
            file = p / name
            file.write_text(json.dumps(value), encoding="utf-8")
            input_paths[name] = file
        output = p / snapshot.archive_name(kind, COMMIT)
        snapshot.pack(kind, COMMIT, input_paths, output)
        return output, input_paths

    def test_reproducible_for_each_resource_with_exact_manifest(self):
        for kind in snapshot.REQUIRED:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                out, files = self.build(directory, kind)
                digest = snapshot.sha(out.read_bytes())
                manifest = snapshot.verify(out)
                self.assertFalse(manifest["public_release"])
                self.assertEqual(manifest["source_revisions"], snapshot.SOURCE_LOCKS[kind])
                snapshot.pack(kind, COMMIT, files, out)
                self.assertEqual(digest, snapshot.sha(out.read_bytes()))
                self.assertEqual(set(manifest["contents"]),
                                 {"data/" + name for name in snapshot.REQUIRED[kind]})

    def test_missing_or_extra_source_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            output, files = self.build(directory, "entity")
            removed = dict(files)
            removed.pop("complete-entity-index.json")
            with self.assertRaises(ValueError):
                snapshot.pack("entity", COMMIT, removed, output)
            self.assertRaises(ValueError, snapshot.parse_files,
                              ["anything=" + str(output)], "entity")

    def test_tampered_archive_or_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            out, _ = self.build(directory, "ubs-hebrew")
            out.with_suffix(out.suffix + ".manifest.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "manifest sidecar"):
                snapshot.verify(out)
            self.build(directory, "ubs-hebrew")
            out.write_bytes(out.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "digest"):
                snapshot.verify(out)

    def test_version_and_contextual_evidence_rejected_on_drift(self):
        with self.assertRaises(ValueError):
            snapshot.archive_name("entity", "main")
        with self.assertRaises(ValueError):
            snapshot.archive_name("unknown", COMMIT)
        with self.assertRaises(ValueError):
            snapshot.inspect_source_state("ubs-hebrew", "semantic-feasibility-audit.json",
                                         b'{"candidate_word_count":53981,"publication_approved":true}')


if __name__ == "__main__":
    unittest.main()
