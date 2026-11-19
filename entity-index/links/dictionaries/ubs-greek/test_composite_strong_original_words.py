#!/usr/bin/env python3
"""Negative tests for immutable original Greek composite Strong source words."""
import copy
import runpy
import unittest
from pathlib import Path

MOD=runpy.run_path(str(Path(__file__).with_name("audit_composite_strong_original_words.py")))


def dataset():
    words=[]
    groups=[]
    for lemma,strong,count in (("ὑπερεκπερισσοῦ","5228+1537+4053",3),
                               ("δισμυριάς","1417+3461",1),
                               ("ἐκπερισσῶς","1537+4053",1)):
        ww=[]
        for i in range(count):
            ww.append({"original_word_id":f"n400010010{len(words)+1:02d}",
                       "original_lemma":lemma,
                       "original_strong":strong,
                       "original_ln":"55.1",
                       "original_class":"adv" if count==3 else "noun",
                       "original_morph":"ADV", "original_reference":"MAT 1:1"})
            words.append(ww[-1])
        groups.append({"source_reason":"unsupported_original_compound_strong",
                      "original_strong":strong,
                      "lemma_nfc_comparison_only":lemma,
                      "original_word_count":count,
                      "original_word_witnesses":ww})
    report={"status": MOD["EXPECTED"],
            "original_exception_counts":{"unsupported_original_compound_strong":5},
            "publication_approved":False,
            "source_editions":{"ubs_greek_edition":"1.0"},
            "original_exception_groups":groups}
    english=[{"MainId":"123","Lemma":"ὑπερεκπερισσοῦ",
              "BaseForms":[{"PartsOfSpeech":["advb."],
                            "LEXMeanings":[{"LEXEntryCode":"55.1"}]}]}]
    return report,english,copy.deepcopy(english)


class OriginalGreekCompositeStrongTests(unittest.TestCase):
    def test_original_composites_not_split_or_approved(self):
        source,en,fr=dataset()
        result=MOD["audit"](source,en,fr)
        self.assertEqual(result["original_word_count"],5)
        self.assertEqual(result["original_family_count"],3)
        self.assertEqual(sum(result["source_evidence_disposition_counts"].values()),5)
        self.assertEqual(result["new_source_headword_links_approved"],0)
        self.assertTrue(result["original_strong_components_preserved"])
        self.assertFalse(result["publication_approved"])

    def test_invalid_original_compound_strong_rejected(self):
        source,en,fr=dataset()
        source["original_exception_groups"][0]["original_strong"]="5228+0"
        with self.assertRaisesRegex(ValueError,"Unsupported original Greek composite"):
            MOD["audit"](source,en,fr)

    def test_inconsistent_original_bilingual_lexical_codes_rejected(self):
        source,en,fr=dataset()
        fr[0]["BaseForms"][0]["LEXMeanings"][0]["LEXEntryCode"]="55.2"
        with self.assertRaisesRegex(ValueError,"LN disagreement"):
            MOD["audit"](source,en,fr)

    def test_original_source_report_must_not_be_published(self):
        source,en,fr=dataset()
        source["publication_approved"]=True
        with self.assertRaisesRegex(ValueError,"provenance drift"):
            MOD["audit"](source,en,fr)


if __name__=="__main__":
    unittest.main()
