#!/usr/bin/env python3
"""Negative and byte-determinism tests for the public UBS identifier-only archive."""
from __future__ import annotations
import hashlib
import json
import runpy
import tempfile
import unittest
import zipfile
from pathlib import Path

M = runpy.run_path(str(Path(__file__).with_name("build_public_identifier_release.py")))
ids = M["_ids"]
project = M["project"]
package = M["package"]


class Tests(unittest.TestCase):
    def test_unknown_ubs_identifiers_rejected(self):
        for value in ([1], ["something"], ["003615000000000", "003615000000000"],
                      ["003615000000000", "X0036150000000"]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ids(value)

    def test_valid_original_ubs_identifier(self):
        self.assertEqual(ids(["003615000000000", "003615001009000"]),
                         ["003615000000000", "003615001009000"])

    def test_unreviewed_or_unpinned_private_source_rejected(self):
        with self.assertRaises((ValueError, KeyError)):
            project({"status": "PUBLIC"})


    def test_deterministic_minimal_archive_and_original_annotation_exclusion(self):
        public = {
            "schema": "bsi.ubs-greek-word-crosswalk.v1",
            "by_word_id": {"n40001001003": {
                "status": "ubs_entry_only",
                "entry_ids": ["003615000000000"],
                "provisional_lexid": None,
                "candidate_lexids": [],
                "evidence_tier": None}},
            "license": "CC BY-SA 4.0",
            "contextual_semantics_independently_verified": False}
        with tempfile.TemporaryDirectory() as d:
            first = Path(d) / "BSI-UBS-Greek-0.1.0.zip"
            second = Path(d) / "copy.zip"
            a = package(public, first)
            b = package(public, second)
            self.assertEqual(a, b)
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.namelist(),
                                 ["ATTRIBUTION.md", "README.md", "index.json", "manifest.json"])
                index = archive.read("index.json")
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["sha256"], hashlib.sha256(index).hexdigest())
                for forbidden in ("original_lemma", "original_ln", "original_strong",
                                  "original_morph", "original_reference"):
                    self.assertNotIn(forbidden.encode(), index)
                self.assertIn(b"bsi.ubs-greek-word-crosswalk.v1", index)
                self.assertIn(b"CC BY-SA 4.0", archive.read("ATTRIBUTION.md"))
                self.assertIn(b"Biblica", archive.read("ATTRIBUTION.md"))
            self.assertEqual(first.with_name(first.name + ".sha256").read_text().split()[0], a)


if __name__ == "__main__":
    unittest.main()
