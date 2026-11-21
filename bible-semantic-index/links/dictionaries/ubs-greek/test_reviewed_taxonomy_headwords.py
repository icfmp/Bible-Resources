#!/usr/bin/env python3
"""Offline negative controls for attested Greek grammatical-taxonomy headword review."""
import copy
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOD = runpy.run_path(str(ROOT / "build_reviewed_taxonomy_headwords.py"))
LEDGER = json.loads((ROOT / "v1_reviewed_taxonomy_headwords.json").read_text(encoding="utf-8"))


class GreekLexicalTaxonomyTests(unittest.TestCase):
    def test_limited_source_specific_32_word_scope(self):
        approved, deferred = MOD["validate_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(approved), 4)
        self.assertEqual(sum(v["original_word_count"] for v in approved.values()), 32)
        self.assertEqual(len(deferred), 3)
        self.assertEqual(sum(v["original_word_count"] for v in deferred.values()), 3)
        self.assertEqual({v["macula_class"] for v in approved.values()}, {"num", "pron", "det"})

    def test_exact_source_grammatical_abbreviations(self):
        source_pos = MOD["parts_of_speech"]
        self.assertEqual(source_pos({"BaseForms": [
            {"PartsOfSpeech": ["adjc.", "advb."]}]}), {"adjc", "advb"})
        self.assertEqual(source_pos({"BaseForms": [
            {"PartsOfSpeech": ["prel."]}]}), {"prel"})
        self.assertEqual(source_pos({"BaseForms": [
            {"PartsOfSpeech": ["artc."]}]}), {"artc"})

    def test_fail_closed_on_source_edition_or_publication(self):
        for path, altered in (
            (("editorial_policy", "no_publication"), False),
            (("editorial_policy", "no_contextual_lexid"), False),
            (("editorial_policy", "no_source_edit"), False),
            (("source_editions", "ubs_revision"), "unverified"),
            (("new_source_reviewed_original_words",), 35),
        ):
            changed = copy.deepcopy(LEDGER)
            node = changed
            for k in path[:-1]:
                node = node[k]
            node[path[-1]] = altered
            with self.assertRaisesRegex(ValueError, "approval or pinned source"):
                MOD["validate_ledger"](
                    changed, {"source_editions": LEDGER["source_editions"]})

    def test_zero_strong_and_conjunction_adverb_not_promoted(self):
        reviewed, deferred = MOD["validate_ledger"](
            LEDGER, {"source_editions": LEDGER["source_editions"]})
        self.assertEqual(
            {x["lemma_nfc"] for x in deferred.values()},
            {"ὁπότε", "ἄμωμον", "Ἀρνί"})
        self.assertFalse(any("0" in x["original_strong_counts"] for x in reviewed.values()))

    def test_bilingual_original_ln_intersection_not_sense_selection(self):
        original_lexical_codes = MOD["original_lexical_codes"]
        en = {"BaseForms": [{"LEXMeanings": [{"LEXEntryCode": "10.1"}]}]}
        fr = {"BaseForms": [{"LEXMeanings": [{"LEXEntryCode": "10.1"}]}]}
        self.assertEqual(original_lexical_codes(en) & original_lexical_codes(fr), {"10.1"})
        self.assertTrue(LEDGER["editorial_policy"]["no_contextual_lexid"])


if __name__ == "__main__":
    unittest.main()
