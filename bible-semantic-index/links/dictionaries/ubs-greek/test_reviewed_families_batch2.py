#!/usr/bin/env python3
"""Negative offline tests for original Greek word-ID-only lexical batch 2."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_families_batch2.py"))
LEDGER = json.loads((HERE / "v1_reviewed_families_batch2.json").read_text(encoding="utf-8"))


class OriginalGreekBatch2Tests(unittest.TestCase):
    def test_pinned_editorial_scope(self):
        selected = MOD["validate_ledger"](LEDGER)
        self.assertEqual(len(selected), 10)
        self.assertEqual(sum(x["source_word_count"] for x in selected.values()), 577)
        self.assertEqual(LEDGER["remaining_unapproved_words"], 328)

    def test_original_grammar_and_dictionary_abbreviation(self):
        self.assertTrue(MOD["grammar_matches"]("adj", ["adjc."]))
        self.assertTrue(MOD["grammar_matches"]("adj", ["advb.", "adjc."]))
        self.assertTrue(MOD["grammar_matches"]("verb", ["verb"]))
        self.assertFalse(MOD["grammar_matches"]("adj", ["verb"]))
        self.assertFalse(MOD["grammar_matches"]("verb", ["adjc."]))
        self.assertFalse(MOD["grammar_matches"]("adj", []))

    def test_no_unauthorized_publication_or_source_drift(self):
        for path, value in (
            (("editorial_policy", "publish"), True),
            (("editorial_policy", "infer_contextual_senses"), True),
            (("source_editions", "ubs_revision"), "unverified"),
            (("remaining_unapproved_words",), 0),
        ):
            modified = copy.deepcopy(LEDGER)
            node = modified
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
            with self.assertRaisesRegex(ValueError, "authorization or pinned source drift"):
                MOD["validate_ledger"](modified)

    def test_fail_closed_on_duplicate_or_wrong_greek_lexeme(self):
        broken = copy.deepcopy(LEDGER)
        broken["reviewed_families"][1]["lemma_nfc"] = broken["reviewed_families"][0]["lemma_nfc"]
        broken["reviewed_families"][1]["ubs_main_id"] = broken["reviewed_families"][0]["ubs_main_id"]
        with self.assertRaisesRegex(ValueError, "Unattested editorial"):
            MOD["validate_ledger"](broken)
        broken = copy.deepcopy(LEDGER)
        broken["reviewed_families"][0]["source_word_count"] += 1
        with self.assertRaisesRegex(ValueError, "source-word scope drift"):
            MOD["validate_ledger"](broken)


if __name__ == "__main__":
    unittest.main()
