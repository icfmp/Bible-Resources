#!/usr/bin/env python3
"""Offline negative tests for source-pinned Greek UBS lexical reference metadata."""
from __future__ import annotations
import copy
import runpy
import unittest
from pathlib import Path
audit=runpy.run_path(str(Path(__file__).with_name("audit_sense_reference_shapes.py")))["audit"]

def fixture():
    batches={
        "status":"PRIVATE_Greek_UBS_contextual_review_batches_NO_CHOICES_YET",
        "original_multi_sense_word_count":2728,
        "contextually_verified":0,
        "published":False,
        "source_editions":{"ubs_greek_revision":"pinned"},
        "review_batches":[{
            "ubs_main_id":"mid","original_lemma":"λόγος","candidate_ubs_lexids":["sense-a","sense-b"],
            "word_id_evidence":[{"original_word_id":f"n{i:011d}"} for i in range(2728)],
        }],
    }
    record={"MainId":"mid","BaseForms":[{"LEXMeanings":[
        {"LEXID":"sense-a","LEXEntryCode":"33.98","LEXReferences":["40001001001"]},
        {"LEXID":"sense-b","LEXEntryCode":"33.98","LEXReferences":[{"Passage":"MAT 1:1"}]},
    ]}]}
    return batches,[record],[copy.deepcopy(record)]

class Tests(unittest.TestCase):
    def test_source_shapes_without_contextual_assignment(self):
        b,e,f=fixture()
        out=audit(b,e,f)
        self.assertEqual(out["original_multivalent_words"],2728)
        self.assertEqual(out["distinct_candidate_ubs_lexids"],2)
        self.assertEqual(out["reference_shape_counts"],{"list/list":2})
        self.assertEqual(out["contextual_senses_selected"],0)
        self.assertFalse(out["published"])

    def test_incomplete_word_ids_rejected(self):
        b,e,f=fixture()
        b["review_batches"][0]["word_id_evidence"].pop()
        with self.assertRaises(ValueError):audit(b,e,f)

    def test_duplicate_word_id_rejected(self):
        b,e,f=fixture()
        b["review_batches"][0]["word_id_evidence"][1]["original_word_id"]="n00000000000"
        with self.assertRaises(ValueError):audit(b,e,f)

    def test_missing_source_sense_rejected(self):
        b,e,f=fixture()
        f[0]["BaseForms"][0]["LEXMeanings"].pop()
        with self.assertRaises(ValueError):audit(b,e,f)

    def test_bilingual_ln_drift_rejected(self):
        b,e,f=fixture()
        f[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]="99.99"
        with self.assertRaises(ValueError):audit(b,e,f)

if __name__=="__main__":unittest.main()
