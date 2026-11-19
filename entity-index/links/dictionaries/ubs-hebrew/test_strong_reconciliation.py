#!/usr/bin/env python3
"""Regression tests for conservative UBS Strong-family reconciliation candidates."""
from pathlib import Path
import tempfile
import runpy
import unittest

HERE=Path(__file__).resolve().parent
build=runpy.run_path(str(HERE/"build_index.py"))["build"]
analyze=runpy.run_path(str(HERE/"audit_strong_reconciliation.py"))["analyze"]

def entry(mid,lemma,strong,sid):
    return {"MainId":mid,"Lemma":lemma,"StrongCodes":strong,
            "BaseForms":[{"LEXMeanings":[{"LEXID":sid,"LEXEntryCode":""}]}]}

class ReconciliationAuditTest(unittest.TestCase):
    def run_data(self,entries,rows):
        index=build(entries,entries)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"words.tsv"
            fields="xml:id\tref\tclass\tlemma\tstrongnumberx\tsdbh\tlang\tmorph\n"
            p.write_text(fields+"".join("\t".join(x)+"\n" for x in rows),encoding="utf-8")
            return analyze(index,entries,p)

    def test_single_lemma_and_numeric_stem_only_candidate(self):
        e=[entry("000001000000000","קוֹל",["H6963a"],"000001001001000")]
        rows=[("o010010010011","GEN 1:1!1","noun","קוֹל","6963","","H","Ncmsa")]
        r=self.run_data(e,rows)
        self.assertEqual(r["counts"]["dual_evidence_candidate_occurrences"],1)
        self.assertEqual(r["candidates"][0]["verification_state"],"candidate_only_not_accepted_link")
        self.assertEqual(r["candidates"][0]["ubs_main_id"],"000001000000000")

    def test_equal_consonants_are_not_sufficient_and_hebrew_aramaic_separate(self):
        e=[entry("000001000000000","קוֹל",["H6963a"],"000001001001000")]
        rows=[("o010010010011","GEN 1:1!1","noun","קֹל","6963","","H","Ncmsa"),
              ("o010010010021","GEN 1:1!2","noun","קוֹל","6963","","A","Ncmsa"),
              ("o010010010031","GEN 1:1!3","noun","קוֹל","6964","","H","Ncmsa")]
        r=self.run_data(e,rows)
        self.assertEqual(r["counts"]["no_exact_joint_evidence"],3)
        self.assertEqual(r["candidates"],[])

    def test_ambiguous_entries_are_not_selected(self):
        e=[entry("000001000000000","טוֹב",["H2896a"],"000001001001000"),
           entry("000002000000000","טוֹב",["H2896b"],"000002001001000")]
        rows=[("o010010010011","GEN 1:1!1","adj","טוֹב","2896","","H","Aamsa")]
        r=self.run_data(e,rows)
        self.assertEqual(r["counts"]["ambiguous_joint_evidence"],1)
        self.assertEqual(r["candidates"],[])

if __name__=="__main__":
    unittest.main()
