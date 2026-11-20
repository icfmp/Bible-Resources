#!/usr/bin/env python3
"""Negative tests: accentless comparison never authorizes source Greek mappings."""
import copy,runpy,unittest
from pathlib import Path

MOD=runpy.run_path(str(Path(__file__).with_name("audit_456_lexical_variants.py")))

class SourceGreekVariantsTests(unittest.TestCase):
    def test_greek_accents_are_only_diagnostic_not_lemma_identity(self):
        self.assertNotEqual(MOD["nfc"]("ἱερόν"),MOD["nfc"]("ἱερος"))
        self.assertEqual(MOD["accentless"]("ἱερόν"),"ιερον")
        self.assertNotEqual(MOD["nfc"]("Ἄλφα"),MOD["nfc"]("ἄλφα"))

    def test_original_source_lexical_ln_parity(self):
        en={"BaseForms":[{"LEXMeanings":[{"LEXEntryCode":"1.1"}]}]}
        self.assertEqual(MOD["source_codes"](en),{"1.1"})

    def test_private_report_cannot_be_preapproved_or_published(self):
        report={"status":"PRIVATE_459_UBS_Greek_v1_0_missing_exact_headword_source_evidence_ONLY",
                "original_words":459,"automatic_lemma_mappings_approved":0,
                "publication_approved":True}
        with self.assertRaisesRegex(ValueError,"source report drift"):
            MOD["audit"](report,[],[])
        report["publication_approved"]=False
        report["automatic_lemma_mappings_approved"]=1
        with self.assertRaisesRegex(ValueError,"source report drift"):
            MOD["audit"](report,[],[])

    def test_original_ubs_en_fr_lemma_disagreement_rejected(self):
        missing={"status":"PRIVATE_459_UBS_Greek_v1_0_missing_exact_headword_source_evidence_ONLY",
                 "original_words":459,"automatic_lemma_mappings_approved":0,
                 "publication_approved":False,"source_word_families":[]}
        en=[{"MainId":"x","Lemma":"ἱερός","BaseForms":[]}]
        fr=[{"MainId":"x","Lemma":"ἱερόν","BaseForms":[]}]
        with self.assertRaisesRegex(ValueError,"bilingual headword spelling drift"):
            MOD["audit"](missing,en,fr)

if __name__=="__main__":unittest.main()
