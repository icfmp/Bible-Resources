#!/usr/bin/env python3
"""Negative tests for original UBS explicit bilingual alternative Greek lemmas."""
import copy,runpy,unittest
from pathlib import Path

MOD=runpy.run_path(str(Path(__file__).with_name("audit_ubs_explicit_alternate_lemmas.py")))

def fixture():
    en=[{"MainId":"A","Lemma":"Ἱεροσόλυμα",
         "AlternateLemmas":["Ἰερουσαλήμ"],
         "BaseForms":[{"PartsOfSpeech":["noun-name, f./n."],
                       "LEXMeanings":[{"LEXEntryCode":"93.480a"}]}],
         "StrongCodes":["G2414"]}]
    fr=copy.deepcopy(en)
    report={"status":"PRIVATE_Greek_456_original_word_ubs_v1_variants_READ_ONLY_NOT_APPROVED",
            "original_word_count":456,
            "new_source_lexical_headword_links":0,"publication_approved":False,
            "source_editions":{"ubs_greek_edition":"1.0"}}
    report["families"]=[
        {"original_lemma":"Ἰερουσαλήμ","original_strong":"2419",
         "original_word_ids":[f"n{i:011d}" for i in range(456)],
         "original_words":456,
         "original_word_witnesses":[{"original_word_id":f"n{i:011d}","original_ln":"93.480a","original_lemma":"Ἰερουσαλήμ","original_strong":"2419"} for i in range(456)],
         "original_ln_counts":{"93.480a":456},
         "original_class_counts":{"noun":456}}]
    return report,en,fr

class OriginalBilingualUBSAlternateLemmas(unittest.TestCase):
    def test_only_source_explicit_lemmas_qualify(self):
        r,en,fr=fixture()
        out=MOD["audit"](r,en,fr)
        self.assertEqual(out["source_evidence_counts"],
                         {"exact_original_ubs_alternate_lemma_and_ln":456})
        self.assertEqual(out["new_source_word_lexical_headwords_approved"],0)
        self.assertEqual(len(out["source_families"][0]["original_ubs_explicit_alternate_headwords"][0]["original_word_ids_with_bilingual_source_ln"]),456)
        self.assertEqual(out["source_families"][0]["original_ubs_explicit_alternate_headwords"][0]["ubs_original_main_id"],"A")

    def test_similar_but_not_original_alternate_is_not_identity(self):
        r,en,fr=fixture()
        en[0]["AlternateLemmas"]=fr[0]["AlternateLemmas"]=[]
        out=MOD["audit"](r,en,fr)
        self.assertEqual(out["source_evidence_counts"],{"not_in_original_ubs_alternate_lemmas":456})

    def test_bilingual_alternate_drift_rejected(self):
        r,en,fr=fixture()
        fr[0]["AlternateLemmas"]=[]
        with self.assertRaisesRegex(ValueError,"alternate or LN"):
            MOD["audit"](r,en,fr)

    def test_bilingual_source_lexical_ln_drift_rejected(self):
        r,en,fr=fixture()
        fr[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]="93.481"
        with self.assertRaisesRegex(ValueError,"alternate or LN"):
            MOD["audit"](r,en,fr)

    def test_missing_original_ln_keeps_candidate_unapproved(self):
        r,en,fr=fixture()
        r["families"][0]["original_ln_counts"]={}
        for word in r["families"][0]["original_word_witnesses"]:word["original_ln"]=""
        out=MOD["audit"](r,en,fr)
        self.assertEqual(out["source_evidence_counts"],
                         {"exact_original_ubs_alternate_lemma_NO_corresponding_source_ln":456})

if __name__=="__main__":unittest.main()
