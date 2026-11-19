#!/usr/bin/env python3
"""Offline regression tests for source-keyed UBS positive headword decisions."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = runpy.run_path(str(HERE / "verify_reviewed_headwords.py"))
LEDGER = json.loads((HERE / "v1_reviewed_headword_dispositions.json").read_text(encoding="utf-8"))
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))


class ReviewedHeadwordTests(unittest.TestCase):
    def test_complete_exact_pinned_five_family_batch(self):
        result = CHECK["verify_register"](LEDGER, REGISTER)
        self.assertEqual(result["families"], 5)
        self.assertEqual(result["occurrences"], 107)
        self.assertEqual(len(result["word_witnesses"]), 15)
        self.assertTrue(all(not d["contextual_sense_id_approved"]
                            and not d["index_word_links_applied"]
                            for d in LEDGER["decisions"]))

    def test_missing_rationale_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        del ledger["decisions"][0]["rationale"]
        with self.assertRaisesRegex(ValueError, "Unsafe or undocumented"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_changed_candidate_and_original_witness_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["ubs_candidate_main_id"] = "000000000000000"
        with self.assertRaisesRegex(ValueError, "candidate source changed"):
            CHECK["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["original_word_witnesses"][0]["reference"] = "DAN 2:1"
        with self.assertRaisesRegex(ValueError, "witnesses/counts changed"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_drift_and_unauthorized_sense_link_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["source_editions"]["macula_revision"] = "changed"
        with self.assertRaisesRegex(ValueError, "Source revisions"):
            CHECK["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["contextual_sense_id_approved"] = True
        with self.assertRaisesRegex(ValueError, "Unsafe or undocumented"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_original_dictionary_entry_and_cross_strong_invariant(self):
        d = LEDGER["decisions"][0]
        original = {"MainId": d["ubs_candidate_main_id"], "Lemma": d["lemma"],
                    "StrongCodes": ["H1840", "H1841"],
                    "BaseForms": [{"LEXMeanings": []}]}
        CHECK["verify_dictionary"]({"decisions": [d]}, [original])
        invalid = copy.deepcopy(original)
        invalid["StrongCodes"] = ["A1841"]
        with self.assertRaisesRegex(ValueError, "discrepancy"):
            CHECK["verify_dictionary"]({"decisions": [d]}, [invalid])
        invalid = copy.deepcopy(original)
        invalid["Lemma"] = "UNRELATED"
        with self.assertRaisesRegex(ValueError, "canonical/alternate"):
            CHECK["verify_dictionary"]({"decisions": [d]}, [invalid])


if __name__ == "__main__":
    unittest.main()

