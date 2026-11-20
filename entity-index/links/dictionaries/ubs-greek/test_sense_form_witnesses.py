#!/usr/bin/env python3
"""Offline negative checks for the original-source UBS Greek sense-form audit."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path

mod=runpy.run_path(str(Path(__file__).with_name("audit_sense_form_witnesses.py")))
inspect=mod["inspect"]
a,b=sorted(mod["SENSES"])

def sample():
    batches={"status":"PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET",
             "original_multi_sense_word_count":2728,"contextually_verified":0,
             "published":False,"source_editions":{"ubs_greek_revision":"pinned"},
             "review_batches":[{"ubs_main_id":mod["MAIN"],"original_lemma":"ἰδού",
               "candidate_ubs_lexids":[a,b],
               "word_id_evidence":[{"original_word_id":"n1","original_lemma":"ἰδού",
                                    "editorial_contextual_lexid_selection":None}]}]}
    record={"MainId":mod["MAIN"],"BaseForms":[{"LEXMeanings":[
        {"LEXID":a,"LEXEntryCode":"91.13","LEXForms":["ἴδε"]},
        {"LEXID":b,"LEXEntryCode":"91.13","LEXForms":["ἰδού"]}]}]}
    return batches,[record],[record.copy()]

class FormAuditTests(unittest.TestCase):
    def test_no_editorial_selection(self):
        d,en,fr=sample()
        result=inspect(d,en,fr)
        self.assertEqual(result["target_original_word_id_count"],1)
        self.assertEqual(result["selected_contextual_lexids"],0)
        self.assertFalse(result["published"])
        self.assertEqual(result["source_sense_metadata"]["en"][a]["source_lex_forms"],["ἴδε"])

    def test_missing_source_sense_rejected(self):
        d,en,fr=sample()
        fr[0]={"MainId":mod["MAIN"],"BaseForms":[{"LEXMeanings":[
            {"LEXID":a,"LEXEntryCode":"91.13"}]}]}
        with self.assertRaises(ValueError):inspect(d,en,fr)

    def test_previous_assignment_rejected(self):
        d,en,fr=sample()
        d["review_batches"][0]["word_id_evidence"][0]["editorial_contextual_lexid_selection"]=a
        with self.assertRaises(ValueError):inspect(d,en,fr)

    def test_unsupported_source_count_rejected(self):
        d,en,fr=sample()
        d["original_multi_sense_word_count"]=3
        with self.assertRaises(ValueError):inspect(d,en,fr)

if __name__=="__main__":unittest.main()
