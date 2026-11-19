#!/usr/bin/env python3
"""Offline negative tests for source-word-specific no-LN headword approvals."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_no_ln_headwords.py"))
LEDGER = json.loads((HERE / "v1_reviewed_no_ln_headwords.json").read_text(encoding="utf-8"))


class GreekNoLnTests(unittest.TestCase):
    def test_original_word_evidence_is_entry_only(self):
        row = {"xml:id": "n40001001001", "lemma": "εἰμί", "class": "verb",
               "strong": "2076", "ln": "13.1", "morph": "V-PAI-3S", "ref": "MAT 1:1!1"}
        item = MOD["validate_original_word"](
            row, "original-ubs-main-id", LEDGER["reviewed_headword_families"][0],
            {"by_strong": {}, "by_ln": {}}, {"2076": 10})
        self.assertEqual(item["entry_id"], "original-ubs-main-id")
        self.assertEqual(item["corroborating_ubs_ln_codes"], [])
        self.assertEqual(item["original_strong"], "2076")
        self.assertEqual(item["original_ln"], "13.1")
        self.assertEqual(item["match_type"], MOD["NEW"])

    def test_original_word_grammar_strong_or_lemma_drift_rejected(self):
        row = {"xml:id": "n40001001001", "lemma": "εἰμί", "class": "verb",
               "strong": "2076", "ln": "13.1", "morph": "V-PAI-3S", "ref": "MAT 1:1!1"}
        for field, value in (("lemma", "ἄλλος"), ("class", "noun"),
                             ("strong", "2258"), ("morph", ""), ("ref", "")):
            bad = dict(row, **{field: value})
            with self.assertRaisesRegex(ValueError, "Unattested original Greek"):
                MOD["validate_original_word"](
                    bad, "original-ubs-main-id", LEDGER["reviewed_headword_families"][0],
                    {"by_strong": {}, "by_ln": {}}, {"2076": 10})

    def test_existing_original_strong_link_never_overwritten(self):
        row = {"xml:id": "n40001001001", "lemma": "εἰμί", "class": "verb",
               "strong": "2076", "ln": "13.1", "morph": "V-PAI-3S", "ref": "MAT 1:1!1"}
        with self.assertRaisesRegex(ValueError, "Unattested original Greek"):
            MOD["validate_original_word"](
                row, "original-ubs-main-id", LEDGER["reviewed_headword_families"][0],
                {"by_strong": {"2076": ["already-linked"]}, "by_ln": {}}, {"2076": 10})


if __name__ == "__main__":
    unittest.main()
