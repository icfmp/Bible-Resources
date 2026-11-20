#!/usr/bin/env python3
"""Fail closed on source Greek word-ID omissions and inferred UBS inflection identities."""
import copy,runpy,unittest
from pathlib import Path
MOD=runpy.run_path(str(Path(__file__).with_name("audit_last_47_lexical_forms.py")))

def fixture():
    english=[{"MainId":"a","Lemma":"ἱερός","BaseForms":[
        {"Inflections":["ἱερον","ἱεροῦ"],"LEXMeanings":[{"LEXEntryCode":"7.16"}]}]}]
    french=copy.deepcopy(english)
    report={"status":"PRIVATE_Greek_original_UBS_explicit_alternate_lemmas_source_evidence_UNAPPROVED",
            "source_evidence_counts":{"exact_original_ubs_alternate_lemma_and_ln":409,
                                      "not_in_original_ubs_alternate_lemmas":47},
            "new_source_word_lexical_headwords_approved":0,
            "publication_approved":False,
            "source_editions":{"ubs_revision":"pinned"}}
    words=[{"original_word_id":f"n{i:011d}","original_ln":"7.16"} for i in range(47)]
    report["source_families"]=[
        {"source_evidence_disposition":"not_in_original_ubs_alternate_lemmas",
         "source_original_lemma":"ἱερον","source_original_strong":"2411",
         "source_original_word_count":47,"source_original_word_ids":[x["original_word_id"] for x in words],
         "source_original_word_witnesses":words,"source_original_ln_counts":{"7.16":47},
         "source_original_class_counts":{"noun":47}}]
    return report,english,french

class OriginalGreekFinalGapsTests(unittest.TestCase):
    def test_original_inflection_is_only_diagnostic(self):
        report,en,fr=fixture()
        out=MOD["audit"](report,en,fr)
        self.assertEqual(out["remaining_original_word_ids"],47)
        self.assertEqual(out["new_lexical_headwords_approved"],0)
        self.assertEqual(out["source_evidence_counts"],{"source_inflection_string_exists_NOT_APPROVED":47})
        self.assertEqual(out["contextual_senses_inferred"],0)

    def test_source_lemma_not_in_inflections_remains_unlinked(self):
        report,en,fr=fixture()
        en[0]["BaseForms"][0]["Inflections"]=[]
        fr[0]["BaseForms"][0]["Inflections"]=[]
        out=MOD["audit"](report,en,fr)
        self.assertEqual(out["source_evidence_counts"],{"no_exact_inflection_metadata_match_IN_UBS_1_0":47})

    def test_original_ubs_bilingual_ln_drift_rejected(self):
        report,en,fr=fixture()
        fr[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]="7.17"
        with self.assertRaisesRegex(ValueError,"EN/FR lexical"):
            MOD["audit"](report,en,fr)

    def test_never_publish_unverified_source_words(self):
        report,en,fr=fixture()
        report["publication_approved"]=True
        with self.assertRaisesRegex(ValueError,"lexical exclusion report drift"):
            MOD["audit"](report,en,fr)

if __name__=="__main__":unittest.main()
