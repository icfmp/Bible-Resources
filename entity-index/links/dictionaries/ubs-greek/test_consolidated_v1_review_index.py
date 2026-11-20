#!/usr/bin/env python3
"""Offline contract tests for the private consolidated UBS Greek review index."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name("build_consolidated_v1_review_index.py")))
build = MOD["build"]
lookup = MOD["lookup"]


class ContractTests(unittest.TestCase):
    def test_unknown_original_word_has_no_fabricated_lexid(self):
        result = lookup({"by_original_macula_word_id": {}}, "missing")
        self.assertEqual(result, {"original_word_id": "missing",
                                  "status": "unknown_original_word_id"})

    def test_exact_approved_word_status_preserves_all_candidates(self):
        record = {"by_original_macula_word_id": {
            "n40001001003": {
                "original_reference": "MAT 1:1!3",
                "original_lemma": "Ἰησοῦς",
                "ubs_main_ids": ["002427000000000"],
                "ubs_lexid_candidates_from_original_ln": ["s1", "s2"],
                "provisional_ubs_lexid": None,
                "status": "ambiguous_ubs_senses",
                "evidence_tier": None,
            }}}
        found = lookup(record, "n40001001003")
        self.assertEqual(found["status"], "ambiguous_ubs_senses")
        self.assertIsNone(found["provisional_ubs_lexid"])
        self.assertEqual(found["ubs_lexid_candidates_from_original_ln"], ["s1", "s2"])

    def test_no_source_index_fails_closed(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            build({"coverage": {"macula_words": 0}}, {}, {}, {}, {}, {}, {}, {})

    def test_release_rights_metadata_contract_is_explicit(self):
        from pathlib import Path
        builder = Path(__file__).with_name("build_consolidated_v1_review_index.py").read_text()
        self.assertIn("Biblica, Inc.", builder)
        self.assertIn("CC BY-SA 4.0", builder)
        self.assertIn("CC BY 4.0 dataset", builder)
        self.assertIn("UBS MARBLE @ln/@domain", builder)
        self.assertIn("NOT_APPROVED", builder)
        self.assertIn("RELEASE_READINESS.md", builder)

    def test_unpublished_source_evidence_contract(self):
        self.assertEqual(MOD["TOTAL"], 137741)
        self.assertEqual([t[2] for t in MOD["TIERS"]],
                         [122504, 170, 223, 258, 40])
        self.assertEqual(sum(t[2] for t in MOD["TIERS"]), 123195)
        self.assertEqual(len({t[0] for t in MOD["TIERS"]}), 5)


if __name__ == "__main__":
    unittest.main()
