#!/usr/bin/env python3
"""Fail-closed offline lexical-entry-only review tests for eight Greek families."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_no_ln_batch5.py"))
LEDGER = json.loads((HERE / "v1_reviewed_no_ln_families_batch5.json").read_text(encoding="utf-8"))


class GreekNoLnBatch5Tests(unittest.TestCase):
    def test_reviewed_source_families_and_explicit_word_counts(self):
        reviewed = MOD["review_ledger"](LEDGER, {
            "source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(reviewed), 8)
        self.assertEqual(sum(x["original_word_count"] for x in reviewed.values()), 1218)
        self.assertEqual(reviewed[("ἑαυτοῦ", "001461000000000")]["original_word_count"], 493)

    def test_source_grammatical_abbreviations_and_bilingual_verbs(self):
        expected = MOD["PARTS"]
        pos = MOD["pos_value"]
        self.assertTrue(pos(["prfl."]) & expected["pron"][0])
        self.assertTrue(pos(["pprs."]) & expected["pron"][1])
        self.assertTrue(pos(["pdem."]) & expected["pron"][0])
        self.assertTrue(pos(["verb"]) & expected["verb"][0])
        self.assertTrue(pos(["verbe"]) & expected["verb"][1])
        self.assertFalse(pos(["adjc."]) & expected["pron"][0])
        self.assertFalse(pos(["verb"]) & expected["verb"][1])

    def test_refuse_published_lexid_and_unverified_edition(self):
        for field, value in (
            ("publication_approved", True),
            ("never_infer_contextual_ubs_lexid", False),
            ("no_global_strong_alias", False),
        ):
            altered = copy.deepcopy(LEDGER)
            altered["editorial_policy"][field] = value
            with self.assertRaisesRegex(ValueError, "editorial evidence"):
                MOD["review_ledger"](altered, {
                    "source_editions": LEDGER["source_editions"]})
        altered = copy.deepcopy(LEDGER)
        altered["source_editions"]["ubs_revision"] = "unverified"
        with self.assertRaisesRegex(ValueError, "editorial evidence"):
            MOD["review_ledger"](altered, {
                "source_editions": LEDGER["source_editions"]})

    def test_no_ln_source_not_claimed_as_lexid(self):
        self.assertTrue(LEDGER["editorial_policy"]["allow_entry_only_without_contextual_ln"])
        self.assertTrue(LEDGER["editorial_policy"]["never_infer_contextual_ubs_lexid"])


if __name__ == "__main__":
    unittest.main()
