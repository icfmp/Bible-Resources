#!/usr/bin/env python3
"""Source and editorial regression tests for the last Greek temporal headword."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
MOD=runpy.run_path(str(HERE/"build_reviewed_hopote_headword.py"))
LEDGER=json.loads((HERE/"v1_reviewed_hopote_temporal_headword.json").read_text(encoding="utf-8"))


def evidence():
    row=LEDGER["reviewed_original_word"]
    return {"source_editions":LEDGER["source_editions"],
            "original_word_id":row["original_word_id"],
            "original_lemma":row["original_lemma"],
            "original_strong":row["original_strong"],
            "original_ln":row["original_ln"],
            "original_reference":row["original_reference"],
            "original_class":row["original_class"],
            "original_morph":row["original_morph"],
            "ubs_original_lemma_en":"ὁπότε",
            "ubs_original_pos_en":["advb."],
            "ubs_original_pos_fr":["advb."],
            "ubs_original_main_id":row["ubs_main_id"],
            "corroborated_bilingual_ln":["67.30"]}


class TemporalGreekLexicalHeadwordTests(unittest.TestCase):
    def test_original_conj_morph_adv_and_ubs_adv_can_be_preserved(self):
        row=MOD["ledger_approval"](LEDGER,evidence())
        self.assertEqual(row["original_class"],"conj")
        self.assertEqual(row["original_morph"],"ADV")
        self.assertEqual(row["ubs_original_pos_en"],["advb."])
        self.assertEqual(row["original_strong"],"3698")

    def test_no_source_or_contextual_meaning_changes_allowed(self):
        for key,value in (
            ("original_source_conj_class_retained",False),
            ("original_source_adv_morphology_retained",False),
            ("original_bilingual_ln_lexical_code_attested",False),
            ("no_contextual_ubs_lexid",False),
            ("publication_approved",True),
        ):
            mutated=copy.deepcopy(LEDGER)
            mutated["editorial_policy"][key]=value
            with self.assertRaisesRegex(ValueError,"authorization drift"):
                MOD["ledger_approval"](mutated,evidence())

    def test_independent_original_word_ln_or_grammar_mismatch_rejected(self):
        for key,value in (("original_ln","1.1"),("original_morph","CONJ"),
                          ("original_strong","3699"),("original_class","adv")):
            evidence_changed=evidence()
            evidence_changed[key]=value
            with self.assertRaisesRegex(ValueError,"source evidence incomplete|source word|temporal word ID"):
                MOD["ledger_approval"](LEDGER,evidence_changed)

    def test_bilingual_original_greek_canonical_headword(self):
        self.assertEqual(MOD["nfc"]("ὁπότε"),"ὁπότε")
        self.assertNotEqual(LEDGER["reviewed_original_word"]["original_class"],
                            LEDGER["reviewed_original_word"]["ubs_original_pos_en"][0])


if __name__=="__main__":
    unittest.main()
