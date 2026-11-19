#!/usr/bin/env python3
"""Offline regression coverage for frozen v1 multiple-headword abstentions."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = runpy.run_path(str(HERE / "verify_multi_headword_abstentions.py"))
LEDGER = json.loads((HERE / "v1_multi_headword_abstentions.json").read_text(encoding="utf-8"))
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))


class MultipleHeadwordAbstentionTests(unittest.TestCase):
    def test_exact_pinned_subpopulation_and_counts(self):
        result = VERIFY["verify_register"](LEDGER, REGISTER)
        self.assertEqual(result["families"], 48)
        self.assertEqual(result["occurrences"], 458)
        self.assertEqual(len(result["word_ids"]), 48)
        self.assertTrue(all(not x["lexical_identity_approved"]
                            and not x["contextual_sense_approved"]
                            and not x["source_data_modified"]
                            for x in LEDGER["dispositions"]))

    def test_missing_family_rejected(self):
        changed = copy.deepcopy(LEDGER)
        changed["dispositions"].pop()
        with self.assertRaisesRegex(ValueError, "Missing or additional"):
            VERIFY["verify_register"](changed, REGISTER)

    def test_changed_candidate_list_and_word_rejected(self):
        changed = copy.deepcopy(LEDGER)
        changed["dispositions"][0]["ubs_candidate_entries"].pop()
        with self.assertRaisesRegex(ValueError, "Candidate set"):
            VERIFY["verify_register"](changed, REGISTER)
        changed = copy.deepcopy(LEDGER)
        changed["dispositions"][0]["original_word_witness"]["reference"] = "GEN 1:1"
        with self.assertRaisesRegex(ValueError, "MACULA witness"):
            VERIFY["verify_register"](changed, REGISTER)

    def test_unsafe_acceptance_and_source_revision_rejected(self):
        changed = copy.deepcopy(LEDGER)
        changed["dispositions"][0]["lexical_identity_approved"] = True
        with self.assertRaisesRegex(ValueError, "unsafe lexical approval"):
            VERIFY["verify_register"](changed, REGISTER)
        changed = copy.deepcopy(LEDGER)
        changed["source_editions"]["ubs_revision"] = "different"
        with self.assertRaisesRegex(ValueError, "source editions"):
            VERIFY["verify_register"](changed, REGISTER)

    def test_cross_strong_requires_original_consonants_and_no_code_collision(self):
        witness = next(d for d in LEDGER["dispositions"]
                       if d["candidate_relation"] == "same_consonants_different_strong_family")
        entries = [
            {"MainId": mid, "Lemma": witness["lemma"],
             "StrongCodes": ["A9999"]}
            for mid in witness["ubs_candidate_entries"]
        ]
        VERIFY["verify_ubs"]({"dispositions": [witness]}, entries)
        modified = copy.deepcopy(entries)
        modified[0]["Lemma"] = "DIFFERENT"
        with self.assertRaisesRegex(ValueError, "consonants no longer match"):
            VERIFY["verify_ubs"]({"dispositions": [witness]}, modified)
        modified = copy.deepcopy(entries)
        modified[0]["StrongCodes"] = [witness["lang"] + witness["original_strong"]]
        with self.assertRaisesRegex(ValueError, "unexpectedly shares"):
            VERIFY["verify_ubs"]({"dispositions": [witness]}, modified)

    def test_headword_source_strong_family_guard(self):
        witness = LEDGER["dispositions"][0]
        entries = [{"MainId": mid, "StrongCodes": ["H7133"]}
                   for mid in witness["ubs_candidate_entries"]]
        VERIFY["verify_ubs"]({"dispositions": [witness]}, entries)
        entries[0]["StrongCodes"] = ["H7134"]
        with self.assertRaisesRegex(ValueError, "no longer shares"):
            VERIFY["verify_ubs"]({"dispositions": [witness]}, entries)


if __name__ == "__main__":
    unittest.main()

