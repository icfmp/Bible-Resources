#!/usr/bin/env python3
"""Offline, source-fidelity and no-lexical-guess tests for Greek gap review."""
from __future__ import annotations

import copy
import csv
import json
import runpy
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = runpy.run_path(str(ROOT / "audit_unmatched_words.py"))
BUILD = runpy.run_path(str(ROOT / "build_index.py"))


def entry(mid, lemma, strong, ln, sense, language):
    return {
        "MainId": mid, "Lemma": lemma,
        "StrongCodes": [strong],
        "BaseForms": [{"LEXMeanings": [{
            "LEXID": sense, "LEXEntryCode": ln,
            "LEXSenses": [{"LanguageCode": language, "DefinitionShort": "never copied"}],
        }]}],
    }


class OriginalGreekUnmatchedSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "source.tsv"
        self.rows = [
            {"xml:id": "n40001001001", "lemma": "λόγος",
             "strong": "3056", "ln": "33.98", "ref": "MAT 1:1!1", "pos": "noun"},
            {"xml:id": "n40001001002", "lemma": "λόγος",
             "strong": "9999", "ln": "33.98", "ref": "MAT 1:1!2", "pos": "noun"},
            {"xml:id": "n40001001003", "lemma": "ἀγάπη",
             "strong": "26", "ln": "25.43", "ref": "MAT 1:1!3", "pos": "noun"},
            {"xml:id": "n40001001004", "lemma": "ἄγνωστος",
             "strong": "9998", "ln": "33.98", "ref": "MAT 1:1!4", "pos": "adj"},
            {"xml:id": "n40001001005", "lemma": "λόγος",
             "strong": "3056+26", "ln": "33.98", "ref": "MAT 1:1!5", "pos": "noun"},
            {"xml:id": "n40001001006", "lemma": "βίβλος",
             "strong": "9997", "ln": "", "ref": "MAT 1:1!6", "pos": "noun"},
        ]
        self.en = [
            entry("id-logos", "λόγος", "G3056", "33.98", "lex-logos", "en"),
            entry("id-agape", "ἀγάπη", "G0026", "25.43", "lex-agape", "en"),
        ]
        self.fr = [
            entry("id-logos", "λόγος", "G3056", "33.98", "lex-logos", "fr"),
            entry("id-agape", "ἀγάπη", "G0026", "25.43", "lex-agape", "fr"),
        ]
        self.index = BUILD["build"](self.en, self.fr)
        self.write_rows(self.rows)
        self.index["coverage"] = BUILD["audit_macula"](self.index, self.path)

    def write_rows(self, rows):
        with self.path.open("w", newline="", encoding="utf-8") as out:
            w = csv.DictWriter(out, fieldnames=[
                "xml:id", "lemma", "strong", "ln", "ref", "pos"
            ], delimiter="\t")
            w.writeheader()
            w.writerows(rows)

    def test_all_original_words_partitioned_without_overwriting_baseline(self):
        before = copy.deepcopy(self.index)
        r = AUDIT["collect"](self.index, self.en, self.fr, self.path)
        c = r["summary"]
        self.assertEqual(c["source_original_word_rows"], 6)
        self.assertEqual(c["already_linked_source_rows"], 2)
        self.assertEqual(c["with_source_ln_matching_ubs_sense_candidates"], 2)
        self.assertEqual(c["no_original_ubs_headword_rows"], 3)
        self.assertEqual(c["unsupported_original_strong_rows"], 1)
        self.assertEqual(c["original_unlinked_words_to_review"], 4)
        self.assertEqual(c["distinct_unmatched_original_families"], 4)
        self.assertEqual(self.index, before)
        self.assertTrue(r["policy"]["possible_ln_or_lemma_matches_are_not_approved_links"])
        self.assertTrue(all(x["disposition"] == "unreviewed_original_source_gap"
                            for x in r["families"]))
        self.assertFalse(r["policy"]["ubs_entry_or_lexid_inferred"])

    def test_proposals_are_evidence_only_never_guess_an_entry(self):
        r = AUDIT["collect"](self.index, self.en, self.fr, self.path)
        x = next(f for f in r["families"] if f["strong_original"] == "9999")
        ev = x["candidate_evidence"]
        self.assertEqual(ev["exact_original_ubs_lemma_main_ids"], ["id-logos"])
        self.assertEqual(ev["independent_original_ln_headword_main_ids"], ["id-logos"])
        self.assertEqual(ev["lemma_and_ln_same_headword_main_ids"], ["id-logos"])
        self.assertEqual(ev["ln_sense_reference_pairs"], [["id-logos", "lex-logos"]])
        self.assertEqual(x["original_word_examples"][0]["strong_original"], "9999")
        self.assertEqual(x["disposition"], "unreviewed_original_source_gap")
        self.assertEqual(self.index["by_strong"].get("9999"), None)
        no_lemma = next(f for f in r["families"]
                        if f["strong_original"] == "9998")
        self.assertEqual(no_lemma["candidate_evidence"]["exact_original_ubs_lemma_main_ids"], [])
        self.assertEqual(no_lemma["candidate_evidence"]["independent_original_ln_headword_main_ids"],
                         ["id-logos"])

    def test_reject_duplicate_source_ids(self):
        self.rows[-1]["xml:id"] = self.rows[0]["xml:id"]
        self.write_rows(self.rows)
        with self.assertRaisesRegex(ValueError, "repeated"):
            AUDIT["collect"](self.index, self.en, self.fr, self.path)

    def test_reject_drift_in_baseline_coverage(self):
        changed = copy.deepcopy(self.index)
        changed["coverage"]["no_ubs_entry"] -= 1
        with self.assertRaisesRegex(ValueError, "count drift"):
            AUDIT["collect"](changed, self.en, self.fr, self.path)

    def test_reject_ubs_en_fr_sense_parity_drift(self):
        fr = copy.deepcopy(self.fr)
        fr[0]["BaseForms"][0]["LEXMeanings"][0]["LEXID"] = "wrong-id"
        with self.assertRaisesRegex(ValueError, "English and French IDs differ"):
            AUDIT["collect"](self.index, self.en, fr, self.path)


if __name__ == "__main__":
    unittest.main()

