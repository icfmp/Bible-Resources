#!/usr/bin/env python3
"""Fail-closed regression tests of source-form Greek UBS provisional sense choices."""
from __future__ import annotations
import copy
import runpy
import unittest
from pathlib import Path

mod=runpy.run_path(str(Path(__file__).with_name("build_form_supported_provisional_senses.py")))
make=mod["make"]
MAIN=mod["MAIN"]
IDE=mod["IDE"]
IDOU=mod["IDOU"]


def fixture():
    def word(n,lemma):
        return {
            "original_word_id":f"n{n:011d}","original_reference":"MAT 1:20!5",
            "original_lemma":lemma,"original_strong":"2400",
            "original_ln":"91.13","original_class":"intj","original_morph":"INJ",
            "editorial_contextual_lexid_selection":None,"contextually_verified":False,
            "source_ubs_lexid_candidate_pairs":[
                {"original_ubs_main_id":MAIN,"original_ubs_lexid":s,"original_ln":"91.13"}
                for s in (IDE,IDOU)],
        }
    batches={
      "status":"PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET",
      "original_multi_sense_word_count":2728,"contextually_verified":0,
      "source_modified":False,"published":False,
      "source_editions":{"ubs_greek_revision":"pinned"},
      "review_batches":[
        {"ubs_main_id":MAIN,"original_lemma":"ἴδε",
         "candidate_ubs_lexids":[IDE,IDOU],"word_id_evidence":[word(0,"ἴδε")]},
        {"ubs_main_id":MAIN,"original_lemma":"ἰδού",
         "candidate_ubs_lexids":[IDE,IDOU],"word_id_evidence":[word(1,"ἰδού")]},
        {"ubs_main_id":"another","original_lemma":"λόγος",
         "candidate_ubs_lexids":["s1","s2"],"word_id_evidence":[
             {"original_word_id":f"n{i:011d}"} for i in range(2,2728)]},
      ],
    }
    lex={
        "MainId":MAIN,"BaseForms":[{"LEXMeanings":[
            {"LEXID":IDE,"LEXEntryCode":"91.13","LEXForms":["ἴδε"]},
            {"LEXID":IDOU,"LEXEntryCode":"91.13","LEXForms":["ἰδού[a]"]},
        ]}],
    }
    return batches,[lex],[copy.deepcopy(lex)]


class Tests(unittest.TestCase):
    def test_exact_source_form_selection_only(self):
        b,e,f=fixture()
        result=make(b,e,f,expected=2)
        self.assertEqual(result["additional_original_word_provisional_choices"],2)
        self.assertEqual(result["all_other_original_ambiguities_still_unselected"],2726)
        choices=result["new_word_id_to_source_form_supported_provisional_lexid"]
        self.assertEqual(choices["n00000000000"]["editorial_provisional_ubs_lexid"],IDE)
        self.assertEqual(choices["n00000000001"]["editorial_provisional_ubs_lexid"],IDOU)
        self.assertTrue(all(not v["verse_context_semantically_verified"] for v in choices.values()))
        self.assertFalse(result["publication_approved"])

    def test_bilingual_source_form_drift_rejected(self):
        b,e,f=fixture()
        f[0]["BaseForms"][0]["LEXMeanings"][1]["LEXForms"]=["wrong"]
        with self.assertRaises(ValueError):make(b,e,f,expected=2)

    def test_missing_source_ln_rejected(self):
        b,e,f=fixture()
        b["review_batches"][0]["word_id_evidence"][0]["source_ubs_lexid_candidate_pairs"][0]["original_ln"]="91.10"
        with self.assertRaises(ValueError):make(b,e,f,expected=2)

    def test_source_contextual_choice_not_overwritten(self):
        b,e,f=fixture()
        b["review_batches"][1]["word_id_evidence"][0]["editorial_contextual_lexid_selection"]=IDOU
        with self.assertRaises(ValueError):make(b,e,f,expected=2)

    def test_extra_ubs_candidate_is_excluded(self):
        b,e,f=fixture()
        b["review_batches"][1]["candidate_ubs_lexids"].append("third-sense")
        result=make(b,e,f,expected=1)
        self.assertEqual(len(result["same_family_extra_sense_candidate_not_selected"]),1)
        self.assertNotIn("n00000000001",result["new_word_id_to_source_form_supported_provisional_lexid"])

    def test_strict_original_word_id_uniqueness(self):
        b,e,f=fixture()
        b["review_batches"][2]["word_id_evidence"][0]["original_word_id"]="n00000000000"
        with self.assertRaises(ValueError):make(b,e,f,expected=2)


if __name__=="__main__":
    unittest.main()
