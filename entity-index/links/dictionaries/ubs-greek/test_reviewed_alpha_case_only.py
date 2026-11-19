#!/usr/bin/env python3
"""Protect exact Greek letter-name word IDs from speculative case aliases."""
import copy
import json
import runpy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MOD=runpy.run_path(str(ROOT/"build_reviewed_alpha_case_only.py"))
LEDGER=json.loads((ROOT/"v1_reviewed_case_only_alpha.json").read_text(encoding="utf-8"))


class GreekAlphaOriginalWordReviewTests(unittest.TestCase):
    def test_original_casefold_not_exact_lemma_or_strong_rewrite(self):
        self.assertNotEqual(MOD["nfc"]("Ἄλφα"), MOD["nfc"]("ἄλφα"))
        self.assertEqual(MOD["nfc"]("Ἄλφα").casefold(), MOD["nfc"]("ἄλφα").casefold())
        self.assertEqual(LEDGER["reviewed_original_lexeme"]["macula_original_strong"], "1")
        self.assertTrue(LEDGER["editorial_policy"]["source_greek_spelling_preserved"])
        self.assertTrue(LEDGER["editorial_policy"]["no_global_strong_alias"])

    def test_fail_closed_on_contextual_lexid_or_publication(self):
        for field,value in (
            ("publication_approved", True),
            ("no_contextual_lexid", False),
            ("historical_strong_index_unchanged", False),
            ("require_original_ubs_en_fr_lexical_ln_code", False),
        ):
            changed=copy.deepcopy(LEDGER)
            changed["editorial_policy"][field]=value
            with self.assertRaisesRegex(ValueError, "authorization"):
                MOD["validate"](changed, {"source_editions":LEDGER["source_editions"]}, [], [])

    def test_source_grammatical_labels_parsed_but_not_rewritten(self):
        en={"BaseForms":[{"PartsOfSpeech":["noun, n."],
                         "LEXMeanings":[{"LEXEntryCode":"61.7"}]}]}
        fr={"BaseForms":[{"PartsOfSpeech":["nom, n."],
                         "LEXMeanings":[{"LEXEntryCode":"61.7"}]}]}
        self.assertEqual(MOD["pos"](en), {"noun"})
        self.assertEqual(MOD["pos"](fr), {"nom"})
        self.assertEqual(MOD["ln"](en) & MOD["ln"](fr), {"61.7"})


if __name__=="__main__":
    unittest.main()
