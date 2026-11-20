#!/usr/bin/env python3
"""Regression tests: original UBS sense LEXID candidate is not contextual proof."""
import copy
import runpy
import unittest
from pathlib import Path
MOD=runpy.run_path(str(Path(__file__).with_name("audit_contextual_sense_candidates.py")))

def fixture():
    index={"by_strong":{"1":["A"],"2":["B","C"]},"by_ln":{}}
    overlay={"by_macula_word":{},
             "by_macula_ambiguous_word":{}}
    original={"xml:id":"n40001001001","lemma":"λόγος","strong":"1",
              "ln":"33.98","ref":"Matt.1.1","class":"noun","morph":"N-NSM"}
    return index,overlay,original

class OriginalGreekSenseCandidateTests(unittest.TestCase):
    def test_unique_source_lexid_is_only_evidence(self):
        index,overlay,word=fixture()
        senses={"A":{("s1","33.98"),("s2","33.99")}}
        group,mids,found=MOD["candidates_for_original_word"](word,index,overlay,senses)
        self.assertEqual(group,"historical_unique_strong_headword")
        self.assertEqual(mids,["A"])
        self.assertEqual(found,[("A","s1","33.98")])

    def test_ambiguity_is_not_erased_by_shared_ln(self):
        index,overlay,word=fixture()
        word["strong"]="2"
        senses={"B":{("b","33.98")},"C":{("c","33.98")}}
        group,mids,found=MOD["candidates_for_original_word"](word,index,overlay,senses)
        self.assertEqual(group,"unresolved_historical_multiheadword_strong")
        self.assertEqual(len(mids),2)
        self.assertEqual(len(found),2)

    def test_independent_original_source_word_lexical_overlay(self):
        index,overlay,word=fixture()
        word["strong"]="0"
        overlay["by_macula_word"][word["xml:id"]]={
            "entry_id":"A","original_lemma":word["lemma"],"original_strong":"0",
            "original_ln":word["ln"],"original_reference":word["ref"],
            "original_class":word["class"],"original_morph":word["morph"]}
        group,mids,found=MOD["candidates_for_original_word"](word,index,overlay,{"A":{("s","33.98")}})
        self.assertEqual(group,"reviewed_original_source_word_headword")
        self.assertEqual(found,[("A","s","33.98")])
        overlay["by_macula_word"][word["xml:id"]]["original_ln"]="forged"
        with self.assertRaisesRegex(ValueError,"source witness drift"):
            MOD["candidates_for_original_word"](word,index,overlay,{"A":{("s","33.98")}})

    def test_no_ln_produces_no_contextual_sense(self):
        index,overlay,word=fixture()
        word["ln"]=""
        _,_,found=MOD["candidates_for_original_word"](word,index,overlay,{"A":{("s","33.98")}})
        self.assertEqual(found,[])

    def test_source_ubs_lexid_code_pairs_preserved_without_definitions(self):
        en=[{"MainId":"A","BaseForms":[{"LEXMeanings":[
            {"LEXID":"source-sense","LEXEntryCode":"33.98","LEXSenses":[{"DefinitionShort":"do not redistribute"}]}]}]}]
        self.assertEqual(MOD["extract_lexical_senses"](en),{"A":{("source-sense","33.98")}})
        en[0]["BaseForms"][0]["LEXMeanings"][0]["LEXID"]=""
        with self.assertRaisesRegex(ValueError,"invalid LEXID"):
            MOD["extract_lexical_senses"](en)

    def test_original_reviewed_strong_ambiguity_must_retain_ubs_candidates(self):
        index,overlay,word=fixture()
        word["strong"]="2"
        overlay["by_macula_ambiguous_word"][word["xml:id"]]={
            "entry_id":"B","original_lemma":word["lemma"],"original_strong":"2",
            "original_ln":word["ln"],"original_reference":word["ref"],
            "original_class":word["class"],"original_morph":word["morph"]}
        group,mids,found=MOD["candidates_for_original_word"](
            word,index,overlay,{"B":{("b","33.98")},"C":{("c","33.98")}})
        self.assertEqual(group,"reviewed_original_strong_ambiguity_headword")
        self.assertEqual(mids,["B"])
        overlay["by_macula_ambiguous_word"][word["xml:id"]]["entry_id"]="D"
        with self.assertRaisesRegex(ValueError,"outside authentic UBS"):
            MOD["candidates_for_original_word"](
                word,index,overlay,{"B":{("b","33.98")},"C":{("c","33.98")}})

if __name__=="__main__":unittest.main()
