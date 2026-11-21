#!/usr/bin/env python3
"""Offline regression checks for source-segment lexical nonidentity decisions."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = runpy.run_path(str(HERE / "verify_source_morpheme_abstentions.py"))
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))
LEDGER = json.loads((HERE / "v1_source_morpheme_abstentions.json").read_text(encoding="utf-8"))


class SourceMorphemeTests(unittest.TestCase):
    def test_pinned_families_and_original_witnesses(self):
        result = VERIFY["verify_register"](LEDGER, REGISTER)
        self.assertEqual(result["families"], 10)
        self.assertEqual(result["occurrences"], 27)
        self.assertEqual(len(result["word_ids"]), 19)
        self.assertTrue(all(not x["lexical_identity_approved"]
                            and not x["source_data_modified"]
                            for x in LEDGER["decisions"]))

    def test_duplicate_family_and_candidate_drift_are_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"].append(copy.deepcopy(ledger["decisions"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            VERIFY["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["ubs_candidate_entry_id"] = "000000000000000"
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            VERIFY["verify_register"](ledger, REGISTER)

    def test_source_witness_and_unsafe_approval_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["source_word_witnesses"][0]["reference"] = "GEN 1:1"
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            VERIFY["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["lexical_identity_approved"] = True
        with self.assertRaisesRegex(ValueError, "unsafe original morpheme"):
            VERIFY["verify_register"](ledger, REGISTER)

    def test_revision_drift_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["source_editions"]["ubs_revision"] = "changed"
        with self.assertRaisesRegex(ValueError, "Pinned source revision"):
            VERIFY["verify_register"](ledger, REGISTER)

    def test_lexical_morpheme_not_conflated_with_whole_headword(self):
        d = LEDGER["decisions"][0]
        candidate = {"MainId": d["ubs_candidate_entry_id"],
                     "Lemma": "לֵב",
                     "StrongCodes": ["H3820b"]}
        VERIFY["verify_ubs"]({"decisions": [d]}, [candidate])
        candidate["Lemma"] = d["lemma"]
        with self.assertRaisesRegex(ValueError, "Lexical surface now matches"):
            VERIFY["verify_ubs"]({"decisions": [d]}, [candidate])
        candidate["Lemma"] = "לֵב"
        candidate["StrongCodes"] = ["H3821"]
        with self.assertRaisesRegex(ValueError, "Strong family changed"):
            VERIFY["verify_ubs"]({"decisions": [d]}, [candidate])


if __name__ == "__main__":
    unittest.main()

