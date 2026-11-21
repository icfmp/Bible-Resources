#!/usr/bin/env python3
"""Synthetic regression tests for public BSI projection."""
import copy
import unittest
from pathlib import Path
import runpy

exclude_kinds = runpy.run_path(str((Path(__file__).resolve().parents[1] / 'scripts' / 'distribution_profile.py')))['exclude_kinds']


def entry(entity_id, kind, word):
    return {
        "id": entity_id, "kind": kind, "source_id": entity_id,
        "review_status": "source_unreviewed",
        "occurrences": {
            "explicit_instances": {"wlc": [[word]]},
            "pronominal_referents": {}, "subject_referents": {},
        },
    }


class PublicProjectionTests(unittest.TestCase):
    def test_removes_keyterms_from_every_lookup_without_mutating_source(self):
        k = entry("keyterm:Grace", "keyterm", "o010010010011")
        p = entry("person:Adam", "person", "o010010010011")
        source = {
            "schema_version": 1, "entities": [k, p],
            "quarantined": [
                {"source_id": "keyterm:Unused"},
                {"source_id": "person:Unknown"}],
            "by_word": {
                "wlc:o010010010011": [
                    {"entity_id": "keyterm:Grace", "link_type": "explicit_instances"},
                    {"entity_id": "person:Adam", "link_type": "explicit_instances"}],
                "wlc:o010010010021": [
                    {"entity_id": "keyterm:Grace", "link_type": "explicit_instances"}],
            },
            "unattested_source_words": {
                "wlc:o010010010011": {"source_claims": [
                    {"entity_id": "keyterm:Grace"},
                    {"entity_id": "person:Adam"}]},
            },
            "unattested_source_verses": {
                "sblgnt:43001001": {"source_reference_claims": [
                    "keyterm:Grace", "person:Adam"]},
            },
            "qualified_source_references": {
                "sblgnt:43001001": [
                    {"entity_id": "keyterm:Grace", "source_id": "keyterm:Grace"},
                    {"entity_id": "person:Adam", "source_id": "person:Adam"}],
            },
            "provenance": {"source_corpora": {"wlc": "wlc"}},
            "statistics": {"source_records": 2},
        }
        original = copy.deepcopy(source)
        output = exclude_kinds(source, {"keyterm"})
        self.assertEqual(source, original)
        self.assertEqual([x["id"] for x in output["entities"]], ["person:Adam"])
        self.assertEqual(list(output["by_word"]), ["wlc:o010010010011"])
        self.assertEqual(output["by_word"]["wlc:o010010010011"][0]["entity_id"], "person:Adam")
        self.assertEqual(output["quarantined"], [{"source_id": "person:Unknown"}])
        self.assertEqual(output["statistics"]["unattested_raw_word_assignments"], 1)
        self.assertEqual(output["statistics"]["source_records"], 2)
        self.assertEqual(output["qualified_source_references"]["sblgnt:43001001"][0]["entity_id"], "person:Adam")
        self.assertEqual(output, exclude_kinds(source, {"keyterm"}))

    def test_fails_closed_if_no_excluded_category(self):
        with self.assertRaisesRegex(ValueError, "Unsupported BSI"):
            exclude_kinds({}, {"keyterm"})


if __name__ == "__main__":
    unittest.main()
