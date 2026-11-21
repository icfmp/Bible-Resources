#!/usr/bin/env python3
"""Offline negative tests for source-pinned UBS Greek LEXReferences verse keys."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path
mod=runpy.run_path(str(Path(__file__).with_name("audit_ubs_source_verse_witnesses.py")))
key=mod["verse_key"]
source=mod["source_lexical_references"]

class Tests(unittest.TestCase):
    def test_all_original_nt_book_codes_and_verse_key(self):
        self.assertEqual(len(mod["BOOK_NUMBER"]),27)
        self.assertEqual(key("MAT 1:20!5"),"040001020")
        self.assertEqual(key("1CO 14:20!8"),"046014020")
        self.assertEqual(key("REV 22:21!9"),"066022021")

    def test_invalid_reference_fails_closed(self):
        for bad in ("MAT 0:1!1","GEN 1:1!1","MAT 1:1000!1","MAT 1:20","MAT 1:20!bad"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):key(bad)

    def test_authentic_source_reference_shapes(self):
        en=[{"MainId":"a","BaseForms":[{"LEXMeanings":[
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":["04000102000005","04000102000011"]},
            {"LEXID":"s2","LEXEntryCode":"91.13","LEXReferences":["04000102100020"]},
        ]}]}]
        out=source(en,{"a":{"s1","s2"}})
        self.assertEqual(out["a"]["s1"]["verses"],{"040001020"})
        self.assertEqual(out["a"]["s1"]["source_reference_count"],2)
        self.assertEqual(out["a"]["s2"]["verses"],{"040001021"})

    def test_bad_reference_never_counts_as_witness(self):
        en=[{"MainId":"a","BaseForms":[{"LEXMeanings":[
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":["garbage"]},
        ]}]}]
        out=source(en,{"a":{"s1"}})
        self.assertEqual(out["a"]["s1"]["verses"],set())
        self.assertEqual(out["a"]["s1"]["invalid"],["garbage"])

    def test_duplicate_source_sense_fails(self):
        en=[{"MainId":"a","BaseForms":[{"LEXMeanings":[
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":[]},
            {"LEXID":"s1","LEXEntryCode":"91.13","LEXReferences":[]},
        ]}]}]
        with self.assertRaises(ValueError):source(en,{"a":{"s1"}})

    def test_missing_original_ubs_sense_fails(self):
        with self.assertRaises(ValueError):source(
            [{"MainId":"a","BaseForms":[{"LEXMeanings":[]}]}],
            {"a":{"missing"}},
        )

if __name__=="__main__":unittest.main()
