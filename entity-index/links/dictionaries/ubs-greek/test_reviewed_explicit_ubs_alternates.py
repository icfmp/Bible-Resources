#!/usr/bin/env python3
"""Fail-closed tests for source-explicit UBS Greek bilingual alternate headwords."""
import copy,json,runpy,unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
MOD=runpy.run_path(str(HERE/"build_reviewed_explicit_ubs_alternates.py"))
LEDGER=json.loads((HERE/"v1_reviewed_explicit_ubs_alternates.json").read_text(encoding="utf-8"))

class OriginalUBSBilingualAltReviewTests(unittest.TestCase):
    def test_twenty_original_source_families_exact_and_counted(self):
        reviewed=MOD["check_ledger"](LEDGER,{"source_editions":LEDGER["source_editions"]})
        self.assertEqual(len(reviewed),20)
        self.assertEqual(sum(x["macula_original_word_count"] for x in reviewed.values()),409)
        self.assertEqual(reviewed[("Ἰερουσαλήμ","2419","002418000000000")]["macula_original_word_count"],76)
        self.assertEqual(reviewed[("ἰδού","2400","003615000000000")]["macula_original_word_count"],200)

    def test_source_original_strong_codes_not_reinterpreted(self):
        reviewed=MOD["check_ledger"](LEDGER,{"source_editions":LEDGER["source_editions"]})
        source=reviewed[("Ἰερουσαλήμ","2419","002418000000000")]
        self.assertEqual(source["ubs_original_strong_codes_separate"],["G2414"])
        self.assertNotEqual(source["macula_original_strong"],"2414")
        self.assertTrue(LEDGER["editorial_policy"]["original_strong_never_aliased"])
        self.assertTrue(LEDGER["editorial_policy"]["no_contextual_lexid_inferred"])

    def test_scope_or_source_edition_changes_refused(self):
        for key,value in (
            ("publication_approved",True),
            ("bilingual_ubs_AlternateLemmas_exact_nfc",False),
            ("original_word_specific_bilingual_ln_intersection",False),
            ("source_pos_differences_not_rewritten",False),
            ("no_contextual_lexid_inferred",False),
        ):
            altered=copy.deepcopy(LEDGER)
            altered["editorial_policy"][key]=value
            with self.assertRaisesRegex(ValueError,"authorization drift"):
                MOD["check_ledger"](altered,{"source_editions":LEDGER["source_editions"]})
        altered=copy.deepcopy(LEDGER)
        altered["source_editions"]["ubs_revision"]="different"
        with self.assertRaisesRegex(ValueError,"authorization drift"):
            MOD["check_ledger"](altered,{"source_editions":LEDGER["source_editions"]})

    def test_lexicographic_word_class_can_differ_without_original_source_edit(self):
        reviewed=MOD["check_ledger"](LEDGER,{"source_editions":LEDGER["source_editions"]})
        original=reviewed[("ἰδού","2400","003615000000000")]
        self.assertEqual(original["macula_original_class_counts"],{"intj":2,"ptcl":198})
        self.assertEqual(original["ubs_original_pos_en"],["verb"])
        self.assertEqual(original["ubs_original_pos_fr"],["verbe"])
        self.assertEqual(MOD["ln"]({"BaseForms":[{"LEXMeanings":[{"LEXEntryCode":"91.13"}]}]}),{"91.13"})

if __name__=="__main__":unittest.main()
