#!/usr/bin/env python3
"""Fail-closed tests for exact Greek original Strong=0 word-ID lexical reviews."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_missing_strong_word_headwords.py"))
LEDGER = json.loads((HERE / "v1_reviewed_missing_strong_word_headwords.json").read_text(encoding="utf-8"))


class MissingOriginalStrongTests(unittest.TestCase):
    def test_two_source_evidenced_original_word_headwords_only(self):
        approved, remaining = MOD["audit_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(approved), 2)
        self.assertEqual(len(remaining), 1)
        self.assertEqual({x["original_strong"] for x in approved.values()}, {"0"})

    def test_original_source_word_zero_never_becomes_a_strong_alias(self):
        for key, value in (
            ("do_not_infer_original_strong_code", False),
            ("do_not_infer_contextual_ubs_lexid", False),
            ("do_not_create_global_alias", False),
            ("publication_approved", True),
        ):
            changed = copy.deepcopy(LEDGER)
            changed["editorial_policy"][key] = value
            with self.assertRaisesRegex(ValueError, "authorization drift"):
                MOD["audit_ledger"](
                    changed, {"source_editions": LEDGER["source_editions"]})
        self.assertTrue(LEDGER["editorial_policy"]["original_macula_strong_zero_must_remain_zero"])

    def test_bilingual_source_noun_grammatical_labels(self):
        entry = {"BaseForms": [{"PartsOfSpeech": ["noun-name, m.", "noun, n."]}]}
        self.assertEqual(MOD["source_pos"](entry), {"noun-name", "noun"})

    def test_original_greek_headword_canonical_equality(self):
        self.assertEqual(MOD["nfc"]("Ἀρνί"), LEDGER["reviewed"][1]["lemma_nfc"])
        self.assertEqual(MOD["source_ln"]({"BaseForms": [
            {"LEXMeanings": [{"LEXEntryCode": "10.1"}]}]}), {"10.1"})


if __name__ == "__main__":
    unittest.main()
