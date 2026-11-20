#!/usr/bin/env python3
"""Source-preserving negative tests for Hebrew sense feasibility (never assign)."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

AUDIT = runpy.run_path(str(Path(__file__).with_name("audit_v11_semantic_feasibility.py")))
verse = AUDIT["verse_from_word_id"]


class OnePassSemanticFeasibilityTest(unittest.TestCase):
    def test_original_hebrew_and_aramaic_wlc_id_verse_mapping(self):
        self.assertEqual(verse("o010010010011"), "001001001")
        self.assertEqual(verse("o060190130101"), "006019013")
        self.assertEqual(verse("o090170390072"), "009017039")
        self.assertEqual(verse("o010010050031ה"), "001001005")

    def test_noncanonical_source_word_ids_rejected(self):
        for wid in ("n010010010011", "o400010010011", "o000010010011",
                    "o010000010011", "o010010000011", "o01001001001",
                    "o0100100100119"):
            with self.subTest(wid=wid), self.assertRaises(ValueError):
                verse(wid)

    def test_ubs_bilingual_sense_references_are_not_semantic_proof(self):
        # Source citations must not become contextual semantic approval.
        self.assertEqual(AUDIT["TIER"],
                         ("verse_citation_unique_headword",
                          "unverified_candidate_not_published"))
        self.assertEqual(AUDIT["EXPECTED"], 475911)

    def test_source_inventory_schema_checked_without_headword_guess(self):
        with self.assertRaises(ValueError):
            AUDIT["sense_inventory"](
                [{"MainId": "123", "BaseForms": []}],
                [{"MainId": "123", "BaseForms": []}],
            )


if __name__ == "__main__":
    unittest.main()
