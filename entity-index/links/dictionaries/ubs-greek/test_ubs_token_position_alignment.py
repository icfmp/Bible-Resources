#!/usr/bin/env python3
"""Regression checks for literal UBS-to-MACULA token-position diagnostics."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name("audit_ubs_token_position_alignment.py")))
locators=m["locators"]
source_refs=m["source_refs"]

class Tests(unittest.TestCase):
    def test_word_position_factors_are_hypotheses_not_accepted_equivalence(self):
        verse,locs=locators("MAT 3:11!2")
        self.assertEqual(verse,"040003011")
        self.assertEqual(locs,{1:"04000301100002",2:"04000301100004",
                               3:"04000301100006",4:"04000301100008"})
        self.assertEqual(locators("REV 22:21!7")[1][2],"06602202100014")

    def test_invalid_original_word_locator_rejected(self):
        for reference in ("GEN 1:1!2","MAT 3:11","MAT 3:11!0","MAT 0:1!2"):
            with self.subTest(reference=reference),self.assertRaises(ValueError):
                locators(reference)

    def test_source_lexical_reference_ids_retained(self):
        src=[{"MainId":"a","BaseForms":[{"LEXMeanings":[
            {"LEXID":"s1","LEXEntryCode":"91.13",
             "LEXReferences":["04000301100004","not-a-reference"]}]}]}]
        result=source_refs(src)
        self.assertEqual(result["a"]["s1"]["valid"],{"04000301100004"})
        self.assertEqual(result["a"]["s1"]["bad"],["not-a-reference"])

    def test_duplicate_source_sense_rejected(self):
        src=[{"MainId":"a","BaseForms":[{"LEXMeanings":[
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":[]},
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":[]}]}]}]
        with self.assertRaises(ValueError):source_refs(src)

if __name__=="__main__":unittest.main()
