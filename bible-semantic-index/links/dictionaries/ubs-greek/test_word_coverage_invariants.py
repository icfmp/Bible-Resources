#!/usr/bin/env python3
"""Regression tests against double-counting reviewed original Greek word IDs."""
import copy
import runpy
import unittest
from pathlib import Path

MOD=runpy.run_path(str(Path(__file__).with_name("validate_word_coverage_invariants.py")))


def pair():
    base={"coverage":{"macula_words":10,"with_ubs_entry_candidates":5},
          "by_strong":{"1":["a"]},"by_ln":{}}
    candidate=copy.deepcopy(base)
    candidate["by_macula_word"]={
        "n1":{"match_type":"source_reviewed_original_greek_entry_only"},
        "n2":{"match_type":MOD["UNAPPROVED"]},
    }
    candidate["by_macula_ambiguous_word"]={
        "n3":{"match_type":"source_reviewed_original_strong_ambiguity"}}
    candidate["word_aware_coverage"]={
        "word_aware_entry_candidate_words":7,
        "remaining_no_ubs_headword_candidate_original_words":3,
        "editorially_reviewed_original_word_headwords":1,
        "other_unapproved_word_headword_candidates":1,
        "new_inferred_contextual_lexical_sense_ids":0,
    }
    candidate["editorial_candidate"]={
        "reviewed_original_headword_words_total":1,
        "other_original_words_still_unapproved":1,
        "new_inferred_contextual_lexical_sense_ids":0,
        "publication_approved":False,
    }
    return base,candidate


class GreekWordCoverageInvariantsTests(unittest.TestCase):
    def test_approved_existing_word_does_not_change_candidate_total(self):
        base,candidate=pair()
        got=MOD["verify"](base,candidate)
        self.assertEqual(got["total_distinct_lexical_entry_candidate_words"],7)
        self.assertEqual(got["source_supported_lexical_headword_word_coverage"],6)
        self.assertEqual(got["reviewed_original_word_strong_ambiguities_not_double_counted"],1)

    def test_promoting_preview_does_not_add_another_word(self):
        base,c=pair()
        c["by_macula_word"]["n2"]["match_type"]="source_reviewed_headword_only"
        c["editorial_candidate"]["reviewed_original_headword_words_total"]=2
        c["editorial_candidate"]["other_original_words_still_unapproved"]=0
        c["word_aware_coverage"]["editorially_reviewed_original_word_headwords"]=2
        c["word_aware_coverage"]["other_unapproved_word_headword_candidates"]=0
        self.assertEqual(MOD["verify"](base,c)["total_distinct_lexical_entry_candidate_words"],7)

    def test_double_counting_editorial_review_rejected(self):
        base,c=pair()
        c["word_aware_coverage"]["word_aware_entry_candidate_words"]=8
        with self.assertRaisesRegex(ValueError,"double count"):
            MOD["verify"](base,c)

    def test_historical_strong_index_mutation_rejected(self):
        base,c=pair()
        c["by_strong"]["1"]=["other"]
        with self.assertRaisesRegex(ValueError,"baseline index modified"):
            MOD["verify"](base,c)

    def test_ambiguous_word_id_overlap_rejected(self):
        base,c=pair()
        c["by_macula_ambiguous_word"]["n1"]={"entry_id":"c"}
        with self.assertRaisesRegex(ValueError,"double-counted"):
            MOD["verify"](base,c)

    def test_unapproved_sense_or_publication_rejected(self):
        base,c=pair()
        c["editorial_candidate"]["publication_approved"]=True
        with self.assertRaisesRegex(ValueError,"policy drift"):
            MOD["verify"](base,c)
        base,c=pair()
        c["by_macula_word"]["n1"]["sense_id"]="invented"
        with self.assertRaisesRegex(ValueError,"contextual UBS lexical sense"):
            MOD["verify"](base,c)


if __name__=="__main__":
    unittest.main()
