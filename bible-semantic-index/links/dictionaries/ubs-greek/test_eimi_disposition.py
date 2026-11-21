#!/usr/bin/env python3
"""Fail-closed tests for the Greek copula original UBS source disposition."""
import copy
import runpy
import unittest
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name("audit_eimi_disposition.py")))
MID = "002258000000000"


def lexicon(lang, senses=None):
    return [{"MainId": MID, "Lemma": "εἰμί", "StrongCodes": ["G2258"],
             "BaseForms": [{"LEXMeanings": [] if senses is None else senses}]}]


def report():
    return {"status": MOD["EXPECTED_STATUS"],
            "source_editions": {"ubs_greek_edition": "1.0"},
            "methods": {"contextual_ubs_sense_ids_inferred": 0},
            "unmatched_families": [{
                "nfc_only_comparison_key": "εἰμί",
                "ubs_nfc_equal_headword_candidates": [MID],
                "original_strong": "2076", "original_source_occurrences": 8,
                "original_word_ids_sample": ["n40001001001"],
                "reason_counts": {"nfc_lemma_only_no_attested_ubs_ln": 8},
            }]}


class GreekEimiTests(unittest.TestCase):
    def test_original_source_has_no_invented_sense(self):
        result = MOD["audit"](report(), lexicon("en"), lexicon("fr"))
        self.assertEqual(result["original_missing_word_occurrences"], 8)
        self.assertEqual(result["original_word_strong_distribution"], {"2076": 8})
        self.assertEqual(result["new_ubs_lexid_inferred"], 0)
        self.assertEqual(result["new_source_word_links_approved"], 0)
        self.assertFalse(result["publication_approved"])

    def test_reject_changed_original_dictionary_semantics(self):
        with self.assertRaisesRegex(ValueError, "now has independently attested meanings"):
            MOD["audit"](report(), lexicon("en", [{"LEXID": "x"}]), lexicon("fr"))

    def test_reject_unapproved_promotion_or_mismatched_entry(self):
        bad = report()
        bad["unmatched_families"][0]["reason_counts"] = {
            "dual_source_lemma_and_ln_candidate_unapproved": 8}
        with self.assertRaisesRegex(ValueError, "unexpected candidate evidence"):
            MOD["audit"](bad, lexicon("en"), lexicon("fr"))
        fr = lexicon("fr")
        fr[0]["MainId"] = "different"
        with self.assertRaisesRegex(ValueError, "bilingual Strong or MainId"):
            MOD["audit"](report(), lexicon("en"), fr)


if __name__ == "__main__":
    unittest.main()
