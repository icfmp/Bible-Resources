#!/usr/bin/env python3
"""Offline negative tests for third Greek source-word lexical editorial batch."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_families_batch3.py"))
LEDGER = json.loads((HERE / "v1_reviewed_families_batch3.json").read_text(encoding="utf-8"))


class GreekBatch3Tests(unittest.TestCase):
    def test_exact_explicit_family_count(self):
        decisions = MOD["select"](LEDGER, {
            "source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(decisions), 19)
        self.assertEqual(sum(v["source_word_count"] for v in decisions.values()), 155)

    def test_lexical_source_pos_not_assumed(self):
        self.assertTrue(MOD["pos_compatible"]("noun", ["noun-name, f."]))
        self.assertTrue(MOD["pos_compatible"]("noun", ["noun, m."]))
        self.assertTrue(MOD["pos_compatible"]("verb", ["verb"]))
        self.assertTrue(MOD["pos_compatible"]("adj", ["adjc."]))
        self.assertFalse(MOD["pos_compatible"]("noun", ["verb"]))
        self.assertFalse(MOD["pos_compatible"]("adj", ["advb."]))
        self.assertFalse(MOD["pos_compatible"]("verb", []))

    def test_refuse_unapproved_publication_and_source_drift(self):
        for key, value in (
            ("no_publication", False),
            ("no_contextual_ubs_sense", False),
            ("no_global_strong_aliases", False),
        ):
            edited = copy.deepcopy(LEDGER)
            edited["editorial_policy"][key] = value
            with self.assertRaisesRegex(ValueError, "scope or source revision"):
                MOD["select"](edited, {"source_editions": LEDGER["source_editions"]})
        edited = copy.deepcopy(LEDGER)
        edited["reviewed_families"][0]["source_word_count"] += 1
        with self.assertRaisesRegex(ValueError, "inventory drift"):
            MOD["select"](edited, {"source_editions": LEDGER["source_editions"]})


if __name__ == "__main__":
    unittest.main()
