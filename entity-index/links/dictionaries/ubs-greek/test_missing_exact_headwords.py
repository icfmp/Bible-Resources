#!/usr/bin/env python3
"""Offline negative tests for missing original UBS Greek source headwords."""
import copy
import runpy
import unittest
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name("audit_missing_exact_headwords.py")))


class GreekMissingUBSHeadwordsTests(unittest.TestCase):
    def test_lexical_source_provenance_not_casefold_approval(self):
        en = [{"MainId": "00001", "Lemma": "πόλις",
               "StrongCodes": ["G4172"],
               "BaseForms": [{"LEXMeanings": [{"LEXEntryCode": "1.89"}]}]}]
        fr = copy.deepcopy(en)
        result = MOD["entries_with_codes"](en, fr)
        self.assertEqual(result[2][MOD["nfc"]("πόλις").casefold()], {"00001"})
        self.assertEqual(result[3]["G4172"], {"00001"})
        self.assertEqual(result[4]["1.89"], {"00001"})

    def test_genuine_original_source_casefold_is_comparison_only(self):
        self.assertNotEqual(MOD["nfc"]("Πόλις"), MOD["nfc"]("πόλις"))
        self.assertEqual(MOD["nfc"]("Πόλις").casefold(),
                         MOD["nfc"]("πόλις").casefold())
        self.assertEqual(MOD["EXPECTED"],
                         "PRIVATE_source_pinned_Greek_unresolved_499_plus_224_ambiguities")

    def test_drift_in_original_en_fr_greek_lemma_is_rejected(self):
        en = [{"MainId": "a", "Lemma": "πόλις", "BaseForms": []}]
        fr = [{"MainId": "a", "Lemma": "ἄλλος", "BaseForms": []}]
        with self.assertRaisesRegex(ValueError, "spelling drift"):
            MOD["entries_with_codes"](en, fr)

    def test_source_uncorroborated_lexical_codes_rejected(self):
        en = [{"MainId": "a", "Lemma": "λόγος",
               "BaseForms": [{"LEXMeanings": [{"LEXEntryCode": "1.1"}]}]}]
        fr = [{"MainId": "a", "Lemma": "λόγος",
               "BaseForms": [{"LEXMeanings": [{"LEXEntryCode": "1.2"}]}]}]
        with self.assertRaisesRegex(ValueError, "LN code inventory"):
            MOD["entries_with_codes"](en, fr)

    def test_source_must_remain_unpublished(self):
        source = {"status": MOD["EXPECTED"],
                  "original_exception_counts": {"no_nfc_identical_ubs_lemma": 459},
                  "source_text_or_annotations_changed": False,
                  "publication_approved": True}
        with self.assertRaisesRegex(ValueError, "provenance drift"):
            MOD["audit"](source, [], [])


if __name__ == "__main__":
    unittest.main()
