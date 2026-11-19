#!/usr/bin/env python3
"""Fail-closed unit tests for lexeme-only Greek pronoun editorial promotion."""
from __future__ import annotations

import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_pronoun_candidate.py"))
LEDGER = json.loads((HERE / "v1_reviewed_pronoun_headwords.json").read_text(
    encoding="utf-8"
))
IDS = {p["lemma_nfc"]: p["ubs_main_id"] for p in LEDGER["reviewed_headword_families"]}


def entry(mid, lemma, lang, ln="92.7", part="pron"):
    return {"MainId": mid, "Lemma": lemma,
            "StrongCodes": ["G4675"],
            "BaseForms": [{"PartsOfSpeech": [part],
                           "LEXMeanings": [
                               {"LEXEntryCode": ln, "LEXID": "sense-" + lang}]}]}


def word(match_type):
    return {"entry_id": IDS["σύ"], "match_type": match_type,
            "original_lemma": "σύ", "original_strong": "5213",
            "original_ln": "92.7", "original_reference": "MAT 3:7!19",
            "original_class": "pron", "original_morph": "P-2DP",
            "corroborating_ubs_ln_codes": ["92.7"]}


class ReviewedGreekPronounTests(unittest.TestCase):
    def test_reviewed_original_word_and_wrong_original_fail_closed(self):
        item = word(MOD["APPROVED"])
        candidate = {"by_macula_word": {"n40003007019": item}}
        def lookup(**change):
            data = {"word_id": "n40003007019",
                    "reference": item["original_reference"],
                    "lemma": item["original_lemma"],
                    "strong": item["original_strong"],
                    "ln": item["original_ln"],
                    "morph": item["original_morph"]}
            data.update(change)
            return MOD["lookup_reviewed"](candidate, **data)
        good = lookup()
        self.assertEqual(good["status"],
                         "editorially_reviewed_original_greek_pronoun_headword_only")
        self.assertEqual(good["entry_ids"], [IDS["σύ"]])
        self.assertEqual(good["sense_ids"], [])
        for changed in (
            {"reference": "MAT 3:7!18"}, {"lemma": "σύ"},
            {"strong": "4675"}, {"ln": "92.6"},
            {"morph": "P-2AP"}, {"word_id": "n40003007018"},
        ):
            got = lookup(**changed)
            self.assertEqual(got["entry_ids"], [], changed)
            self.assertEqual(got["sense_ids"], [], changed)

    def test_unreviewed_source_word_stays_explicitly_unapproved(self):
        item = word(MOD["PREVIEW"]["MATCH_TYPE"])
        candidate = {"by_macula_word": {"n40003007019": item}}
        got = MOD["lookup_reviewed"](
            candidate, "n40003007019", item["original_reference"],
            "σύ", "5213", "92.7", "P-2DP"
        )
        self.assertEqual(got["status"],
                         "unapproved_original_word_entry_candidate_only")
        self.assertEqual(got["sense_ids"], [])

    def test_original_ubs_headword_and_source_pos_must_be_attested(self):
        en, fr = [], []
        for p in LEDGER["reviewed_headword_families"]:
            en.append(entry(p["ubs_main_id"], p["lemma_nfc"], "en"))
            fr.append(entry(p["ubs_main_id"], p["lemma_nfc"], "fr"))
        groups = MOD["review_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]}, en, fr
        )
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups["σύ"]["ubs_main_id"], IDS["σύ"])
        abbreviated = copy.deepcopy(en)
        abbreviated[0]["BaseForms"][0]["PartsOfSpeech"] = ["pprs."]
        abbreviated[1]["BaseForms"][0]["PartsOfSpeech"] = ["pprs."]
        abbreviated[2]["BaseForms"][0]["PartsOfSpeech"] = ["pdem."]
        self.assertEqual(len(MOD["review_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]},
            abbreviated, fr)), 3)
        broken = copy.deepcopy(en)
        broken[0]["BaseForms"][0]["PartsOfSpeech"] = ["verb"]
        with self.assertRaisesRegex(ValueError, "POS classification differs from pronoun expectation"):
            MOD["review_ledger"](
                LEDGER, {"source_editions": LEDGER["source_editions"]},
                broken, fr
            )
        unlabeled = copy.deepcopy(en)
        for headword in unlabeled:
            headword["BaseForms"][0]["PartsOfSpeech"] = []
        self.assertEqual(len(MOD["review_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]},
            unlabeled, fr)), 3)
        drift = copy.deepcopy(fr)
        drift[1]["Lemma"] = "other"
        with self.assertRaisesRegex(ValueError, "Unattested"):
            MOD["review_ledger"](
                LEDGER, {"source_editions": LEDGER["source_editions"]},
                en, drift
            )

    def test_refuse_missing_approval_and_unauthorized_publication(self):
        en = [entry(p["ubs_main_id"], p["lemma_nfc"], "en")
              for p in LEDGER["reviewed_headword_families"]]
        fr = [entry(p["ubs_main_id"], p["lemma_nfc"], "fr")
              for p in LEDGER["reviewed_headword_families"]]
        changed = copy.deepcopy(LEDGER)
        changed["editorial_policy"]["publication_approved"] = True
        with self.assertRaisesRegex(ValueError, "status, source or scope not pinned"):
            MOD["review_ledger"](
                changed, {"source_editions": LEDGER["source_editions"]},
                en, fr
            )
        changed = copy.deepcopy(LEDGER)
        changed["reviewed_headword_families"][0]["ubs_main_id"] = "fabricated-id"
        with self.assertRaisesRegex(ValueError, "Unattested"):
            MOD["review_ledger"](
                changed, {"source_editions": LEDGER["source_editions"]},
                en, fr
            )


if __name__ == "__main__":
    unittest.main()

