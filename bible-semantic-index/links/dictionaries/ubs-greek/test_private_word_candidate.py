#!/usr/bin/env python3
"""Regression checks for UBS Greek source-witnessed private candidate lookup."""
from __future__ import annotations

import copy
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOD = runpy.run_path(str(ROOT / "build_private_word_candidate.py"))

WID = "n40003007019"
ENTRY = "004674000000000"
WITNESS = {
    "entry_id": ENTRY,
    "match_type": MOD["MATCH_TYPE"],
    "original_lemma": "σύ",
    "original_strong": "5213",
    "original_ln": "92.7",
    "original_reference": "MAT 3:7!19",
    "original_class": "pron",
    "original_morph": "P-2DP",
    "corroborating_ubs_ln_codes": ["92.7"],
}


class PrivateGreekCandidateLookupTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "by_macula_word": {WID: copy.deepcopy(WITNESS)}
        }

    def lookup(self, **overrides):
        a = {
            "word_id": WID,
            "reference": WITNESS["original_reference"],
            "lemma": WITNESS["original_lemma"],
            "strong": WITNESS["original_strong"],
            "ln": WITNESS["original_ln"],
            "morph": WITNESS["original_morph"],
        }
        a.update(overrides)
        return MOD["lookup_word"](self.candidate, **a)

    def test_exact_original_word_id_only_unapproved_entry_without_sense(self):
        result = self.lookup()
        self.assertEqual(result["status"],
                         "unapproved_original_word_entry_candidate_only")
        self.assertEqual(result["entry_ids"], [ENTRY])
        self.assertEqual(result["sense_ids"], [])
        self.assertEqual(result["matched_source_ln_codes"], ["92.7"])

    def test_wrong_source_word_id_and_verse_fail_closed(self):
        self.assertEqual(
            self.lookup(word_id="n40003007018")["entry_ids"], []
        )
        self.assertEqual(
            self.lookup(reference="MAT 3:7!18")["entry_ids"], []
        )

    def test_source_strong_drift_fails_without_lexeme_alias(self):
        self.assertEqual(self.lookup(strong="4675")["entry_ids"], [])
        self.assertEqual(self.lookup(strong="5213a")["entry_ids"], [])

    def test_source_accent_morphology_and_lexical_domain_drift_fail(self):
        self.assertEqual(self.lookup(lemma="σύ")["entry_ids"], [])
        self.assertEqual(self.lookup(ln="92.6")["entry_ids"], [])
        self.assertEqual(self.lookup(morph="P-2AP")["entry_ids"], [])

    def test_unknown_or_guessed_matching_type_never_falls_back_to_first(self):
        self.candidate["by_macula_word"][WID]["match_type"] = "guessed"
        self.assertEqual(self.lookup()["status"], "unrecognized_editorial_match_type")
        self.assertEqual(self.lookup()["entry_ids"], [])

    def test_existing_index_only_has_frozen_original_strong_lexical_maps(self):
        idx = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
        self.assertNotIn("by_macula_word", idx)
        self.assertEqual(idx["coverage"]["with_ubs_entry_candidates"], 128090)
        self.assertEqual(idx["coverage"]["with_corresponding_sense_candidates"],
                         118272)
        self.assertEqual(idx["coverage"]["ambiguous_ubs_entry_candidates"], 224)


if __name__ == "__main__":
    unittest.main()

