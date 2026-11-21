#!/usr/bin/env python3
"""Fail-closed original word-ID tests for 258 Greek UBS verse-source defaults."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path
make=runpy.run_path(str(Path(__file__).with_name("build_source_verse_provisional_senses.py")))["make"]
SOURCES={"ubs_greek_revision":"pinned","macula_sblgnt_revision":"pinned"}


def fixture():
    unresolved_ids=[f"n{i:011d}" for i in range(15237)]
    high_ids=[f"n{i:011d}" for i in range(15237,137741)]
    sources={wid:{"editorial_status":"other"} for wid in unresolved_ids}
    earlier={
        "high":{"source_editions":SOURCES,"provisional_source_supported_original_word_count":122504,
                "published":False,"word_id_to_provisional_ubs_lexid":dict.fromkeys(high_ids)},
        "low":{"source_editions":SOURCES,"additional_original_word_ids":170,"published":False,
               "word_id_to_lower_confidence_provisional_ubs_lexid":dict.fromkeys(unresolved_ids[:170])},
        "form":{"source_editions":SOURCES,"additional_original_word_provisional_choices":223,
                "published":False,"new_word_id_to_source_form_supported_provisional_lexid":
                dict.fromkeys(unresolved_ids[170:393])},
    }
    proposals={}
    for wid in unresolved_ids[393:651]:
        original={"original_word_id":wid,"original_reference":"MAT 1:1!1","original_lemma":"λόγος",
                  "original_strong":"3056","original_ln":"33.98","original_class":"noun",
                  "original_morph":"N-NSM"}
        sources[wid]={**original,
                      "editorial_status":"multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated",
                      "source_original_ubs_main_id_candidates":["mid"],
                      "source_ubs_lexid_candidate_pairs":[
                          {"original_ubs_lexid":"chosen"},
                          {"original_ubs_lexid":"other"}],
                      "verse_context_semantically_verified":False}
        proposals[wid]={**original,
                        "ubs_original_main_id":"mid",
                        "source_ubs_original_lexid_reference_candidate":"chosen",
                        "other_original_UBS_lexid_candidates":["other"],
                        "original_MACULA_verse_key":"040001001",
                        "independently_verse_context_semantically_verified":False}
    report={
        "status":"PRIVATE_UBS_Greek_word_specific_original_source_verse_sense_candidate_AUDIT_NOT_CONTEXT_VALIDATION",
        "source_editions":SOURCES,
        "all_initial_original_multi_lexid_words":2728,
        "previously_staged_source_form_word_ids":223,
        "original_reference_witness_candidate_word_count":258,
        "independently_contextually_validated":0,
        "published":False,"publication_approved":False,
        "word_id_to_possible_UBS_original_source_reference_sense":proposals,
    }
    unresolved={"status":"PRIVATE_UNRESOLVED_Greek_contextual_sense_word_IDs_for_editorial_review",
                "source_editions":SOURCES,"unresolved_original_word_count":15237,
                "published":False,"word_id_to_unresolved_original_source_evidence":sources}
    return report,unresolved,earlier["high"],earlier["low"],earlier["form"]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=fixture()

    def test_private_258_disjoint_source_choices(self):
        out=make(*self.args)
        self.assertEqual(out["new_source_verse_supported_provisional_word_count"],258)
        self.assertEqual(out["all_provisional_original_word_ids_across_disjoint_tiers"],123155)
        self.assertEqual(out["remaining_without_a_unique_provisional_UBS_LEXID"],14586)
        self.assertEqual(out["unresolved_original_multi_lexid_after_form_and_verse"],2247)
        self.assertEqual(out["independently_contextually_validated"],0)
        self.assertFalse(out["published"])

    def test_duplicate_existing_lexid_tier_fails(self):
        report,unresolved,high,low,form=self.args
        modified={**low,"word_id_to_lower_confidence_provisional_ubs_lexid":{
            **low["word_id_to_lower_confidence_provisional_ubs_lexid"],
            next(iter(report["word_id_to_possible_UBS_original_source_reference_sense"])):None}}
        with self.assertRaises(ValueError):make(report,unresolved,high,modified,form)

    def test_missing_original_source_word_id_fails(self):
        report,unresolved,high,low,form=self.args
        original=dict(report["word_id_to_possible_UBS_original_source_reference_sense"])
        original.pop(next(iter(original)))
        with self.assertRaises(ValueError):make({**report,"word_id_to_possible_UBS_original_source_reference_sense":original},
                                                 unresolved,high,low,form)

    def test_false_contextual_certification_fails(self):
        report,unresolved,high,low,form=self.args
        with self.assertRaises(ValueError):make({**report,"independently_contextually_validated":258},
                                                 unresolved,high,low,form)

if __name__=="__main__":unittest.main()
