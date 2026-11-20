#!/usr/bin/env python3
"""Fail-closed tests for fourth original Greek source-word editorial batch."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_families_batch4.py"))
LEDGER = json.loads((HERE / "v1_reviewed_families_batch4.json").read_text(encoding="utf-8"))


class GreekBatch4Tests(unittest.TestCase):
    def test_explicit_editorial_partition(self):
        decisions, pending = MOD["validate_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(decisions), 101)
        self.assertEqual(sum(x["source_word_count"] for x in decisions.values()), 138)
        self.assertEqual(len(pending), 7)
        self.assertEqual(sum(x["source_word_count"] for x in pending.values()), 35)

    def test_generic_grammatical_metadata_matching(self):
        norm = MOD["normalized_pos"]
        grammar = MOD["GRAMMAR"]
        for source_class, label in (
            ("noun", "noun-name, f."), ("verb", "verb"), ("adj", "adjc."),
            ("adv", "advb."), ("prep", "prep. (with gen.)"), ("conj", "conj.")):
            self.assertTrue(norm([label]) & grammar[source_class])
        self.assertFalse(norm(["verb"]) & grammar["noun"])
        self.assertFalse(norm(["adjc."]) & grammar["conj"])

    def test_refuse_unapproved_lexid_or_publication(self):
        for key, value in (("no_contextual_lexid", False),
                           ("no_global_strong_alias", False),
                           ("publication_approved", True)):
            altered = copy.deepcopy(LEDGER)
            altered["editorial_policy"][key] = value
            with self.assertRaisesRegex(ValueError, "scope drift"):
                MOD["validate_ledger"](
                    altered, {"source_editions": LEDGER["source_editions"]})

    def test_zero_strong_and_grammar_conflicts_left_deferred(self):
        self.assertEqual(
            {x["lemma_nfc"] for x in LEDGER["deferred_families"]},
            {"τεσσεράκοντα", "ἐνενήκοντα", "ὅστις",
             "ἄμωμον", "Ἀρνί", "ὁ", "ὁπότε"})
        self.assertTrue(all("0" not in r["original_strong_counts"]
                            for r in LEDGER["reviewed_families"]))


if __name__ == "__main__":
    unittest.main()
