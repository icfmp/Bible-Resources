#!/usr/bin/env python3
"""Offline fail-closed tests of the remaining Greek lexical evidence inventory."""
import copy
import runpy
import unittest
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name("audit_remaining_headwords.py")))
MAIN = "000000000000001"
APPROVED = MOD["APPROVED"]
UNAPPROVED = MOD["UNAPPROVED"]


def lexicon(lang):
    return [{"MainId": MAIN, "Lemma": "λόγος",
             "BaseForms": [{"PartsOfSpeech": ["n."], "LEXMeanings": [
                 {"LEXEntryCode": "33.98", "LEXID": lang + "-1"}]}]}]


def candidate():
    reviewed = {}
    for i in range(5033):
        reviewed["n%011d" % i] = {"match_type": APPROVED}
    for i in range(5033, 5938):
        reviewed["n%011d" % i] = {
            "match_type": UNAPPROVED, "entry_id": MAIN,
            "original_lemma": "λόγος", "original_strong": "3056",
            "original_reference": "MAT 1:1!1", "original_ln": "33.98",
            "original_morph": "N-NSM", "original_class": "noun",
            "corroborating_ubs_ln_codes": ["33.98"]}
    return {"editorial_candidate": {
        "source_editions": MOD["SOURCE_REVISIONS"],
        "publication_approved": False,
        "source_pronoun_headword_approvals": 5033,
        "other_original_words_still_unapproved": 905},
        "by_macula_word": reviewed}


class GreekEvidenceTests(unittest.TestCase):
    def test_all_unapproved_stay_unapproved_and_word_specific(self):
        report = MOD["prepare"](candidate(), lexicon("en"), lexicon("fr"))
        self.assertEqual(report["unapproved_words"], 905)
        self.assertEqual(report["unapproved_families"], 1)
        self.assertEqual(len(report["families"][0]["all_original_word_witnesses"]), 905)
        self.assertEqual(report["families"][0]["editorial_status"],
                         "UNAPPROVED_requires_separate_lexical_family_review")
        self.assertEqual(report["families"][0]["contextual_sense_ids_selected"], [])
        self.assertFalse(report["publication_approved"])

    def test_fail_closed_on_original_greek_lemma_drift(self):
        broken = candidate()
        broken["by_macula_word"]["n00000005033"]["original_lemma"] = "ἄλλος"
        with self.assertRaisesRegex(ValueError, "Unattested bilingual"):
            MOD["prepare"](broken, lexicon("en"), lexicon("fr"))

    def test_fail_closed_on_missing_bilingual_ln_attestation(self):
        broken_fr = lexicon("fr")
        broken_fr[0]["BaseForms"][0]["LEXMeanings"] = []
        with self.assertRaisesRegex(ValueError, "LN corroboration"):
            MOD["prepare"](candidate(), lexicon("en"), broken_fr)

    def test_fail_closed_on_publication_or_counter_drift(self):
        broken = candidate()
        broken["editorial_candidate"]["publication_approved"] = True
        with self.assertRaisesRegex(ValueError, "metadata drift"):
            MOD["prepare"](broken, lexicon("en"), lexicon("fr"))
        broken = candidate()
        broken["by_macula_word"]["n00000005033"]["match_type"] = APPROVED
        with self.assertRaisesRegex(ValueError, "inventory drift"):
            MOD["prepare"](broken, lexicon("en"), lexicon("fr"))


if __name__ == "__main__":
    unittest.main()
