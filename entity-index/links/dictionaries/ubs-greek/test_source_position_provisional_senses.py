#!/usr/bin/env python3
"""Offline rejection and accounting tests for 40 UBS position-source defaults."""
from __future__ import annotations
import copy
import runpy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
make=runpy.run_path(str(ROOT/"build_source_position_provisional_senses.py"))["make"]
prior=runpy.run_path(str(ROOT/"test_source_verse_provisional_senses.py"))
verse_build=runpy.run_path(str(ROOT/"build_source_verse_provisional_senses.py"))["make"]


def fixture():
    report,unresolved,high,low,form=prior["fixture"]()
    verse=verse_build(report,unresolved,high,low,form)
    ids=list(unresolved["word_id_to_unresolved_original_source_evidence"])
    formids=list(form["new_word_id_to_source_form_supported_provisional_lexid"])
    verseids=list(verse["word_id_to_new_UBS_source_verse_provisional_lexid"])
    newids=ids[651:691]
    matched=set(formids[:220])|set(verseids[:251])|set(newids)
    assert len(matched)==511
    raw={}
    for wid in ids[:2728]:
        is_new=wid in newids
        fields={"original_word_id":wid,"original_reference":"MAT 1:1!1",
                "original_lemma":"λόγος","original_strong":"3056",
                "original_ln":"33.98","original_class":"noun","original_morph":"N-NSM"}
        if is_new:
            unresolved["word_id_to_unresolved_original_source_evidence"][wid]={
                **fields,
                "editorial_status":"multiple_original_ubs_lexid_candidates_NOT_contextually_disambiguated",
                "source_original_ubs_main_id_candidates":["mid"],
                "source_ubs_lexid_candidate_pairs":[
                    {"original_ubs_lexid":"chosen"},
                    {"original_ubs_lexid":"alternative"}]}
        raw[wid]={
            **fields,"ubs_original_main_id":"mid",
            "all_original_candidate_lexids":["alternative","chosen"],
            "source_position_match_diagnostics":{
                "2":{"status":"unique_exact_source_position_candidate" if wid in matched else
                     "multiple_exact_source_position_candidates",
                     "source_lexid_candidates":["chosen"] if wid in matched else ["chosen","alternative"]}}}
    position={
        "status":"PRIVATE_Greek_UBS_LexReferences_original_token_ordinal_alignment_DIAGNOSTIC_ONLY",
        "source_editions":report["source_editions"],
        "original_source_unique_sense_calibration_words":122504,
        "source_unique_words_with_comparable_reference_metadata":119761,
        "calibration_matches_by_exact_UBS_to_MACULA_position_factor":{"2":115145},
        "original_ambiguous_words":2728,
        "new_editorial_source_senses_selected":0,
        "no_automatic_word_position_equivalence_asserted":True,
        "published":False,
        "word_id_to_candidate_position_diagnostics":raw}
    return position,unresolved,high,low,form,verse


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=fixture()

    def test_stage_only_40_genuine_new_word_ids(self):
        out=make(*self.args)
        self.assertEqual(out["new_position_supported_provisional_word_count"],40)
        self.assertEqual(out["all_five_disjoint_private_provisional_tier_word_count"],123195)
        self.assertEqual(out["original_words_still_without_unique_provisional_lexid"],14546)
        self.assertEqual(out["original_multi_lexid_words_still_without_unique_provisional_choice"],2207)
        self.assertTrue(all(not x["independently_contextually_validated"] for x in
                            out["word_id_to_source_position_provisional_lexid"].values()))
        self.assertFalse(out["published"])

    def test_calibration_cannot_be_invented(self):
        args=list(self.args)
        args[0]={**args[0],"calibration_matches_by_exact_UBS_to_MACULA_position_factor":{"2":120000}}
        with self.assertRaises(ValueError):make(*args)

    def test_false_unique_source_position_rejected(self):
        args=list(self.args)
        raw=dict(args[0]["word_id_to_candidate_position_diagnostics"])
        first=next(wid for wid,item in raw.items() if item["source_position_match_diagnostics"]["2"]["status"]==
                   "multiple_exact_source_position_candidates")
        raw[first]={**raw[first],"source_position_match_diagnostics":{"2":{
            "status":"unique_exact_source_position_candidate","source_lexid_candidates":["chosen"]}}}
        args[0]={**args[0],"word_id_to_candidate_position_diagnostics":raw}
        with self.assertRaises(ValueError):make(*args)

    def test_source_revision_mismatch_rejected(self):
        args=list(self.args)
        args[0]={**args[0],"source_editions":{"ubs_greek_revision":"different"}}
        with self.assertRaises(ValueError):make(*args)


if __name__=="__main__":unittest.main()
