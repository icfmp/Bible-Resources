#!/usr/bin/env python3
"""Negative source tests: blank original Greek LN cannot be fabricated."""
import copy,runpy,unittest
from pathlib import Path
M=runpy.run_path(str(Path(__file__).with_name("audit_unresolved_semantic_priorities.py")))

def data():
    entry={"MainId":"x","BaseForms":[{"LEXMeanings":[{"LEXID":"s","LEXEntryCode":"10.1"}]}]}
    report={"status":"PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review",
            "unresolved_original_word_count":15237,
            "contextual_senses_independently_verified":0,
            "published":False,"public_release_approved":False}
    report["word_id_to_unresolved_original_source_evidence"]={
        f"n{i:011d}":{"editorial_status":"no_original_ln_matching_ubs_lexical_sense",
                     "source_original_ubs_main_id_candidates":["x"],
                     "source_ubs_lexid_candidate_pairs":[],
                     "original_ln":"","original_lemma":"λόγος","original_reference":"MAT 1:1"}
        for i in range(15237)}
    return report,[entry],copy.deepcopy([entry])

class OriginalSourceSemanticPrioritiesTests(unittest.TestCase):
    def test_nonrelease_source_only(self):
        report,en,fr=data()
        with self.assertRaisesRegex(ValueError,"inventory drift"):
            M["audit"](report,en,fr)
        self.assertEqual(M["source_lexids"](en),{"x":{"s":{"10.1"}}})
    def test_original_lexid_bilingual_consistency_and_no_invention(self):
        report,en,fr=data()
        en[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]=""
        self.assertEqual(M["source_lexids"](en)["x"]["s"],{""})
        en[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]=None
        with self.assertRaisesRegex(ValueError,"code malformed"):
            M["source_lexids"](en)
    def test_report_does_not_approve_publication(self):
        report,en,fr=data()
        report["public_release_approved"]=True
        with self.assertRaisesRegex(ValueError,"report drift"):
            M["audit"](report,en,fr)

if __name__=="__main__":unittest.main()
