#!/usr/bin/env python3
"""Reject fabricated original Strong aliases and semantic senses in Greek compounds."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
MOD=runpy.run_path(str(HERE/"build_reviewed_composite_strong_headwords.py"))
LEDGER=json.loads((HERE/"v1_reviewed_composite_strong_headwords.json").read_text(encoding="utf-8"))


class ReviewedGreekCompositeSourceTests(unittest.TestCase):
    def test_exact_three_lexical_families_and_five_word_ids(self):
        decisions=MOD["review_ledger"](LEDGER,{"source_editions":LEDGER["source_editions"]})
        self.assertEqual(len(decisions),3)
        self.assertEqual(sum(x["original_word_count"] for x in decisions.values()),5)
        self.assertTrue(all(MOD["PATTERN"].fullmatch(x["original_macula_strong"])
                            for x in decisions.values()))

    def test_word_specific_absent_original_ln_requires_explicit_approval(self):
        approved=MOD["review_ledger"](LEDGER,{"source_editions":LEDGER["source_editions"]})
        missing={x for row in approved.values() for x in row["exact_original_word_ids_with_missing_ln_allowed"]}
        self.assertEqual(missing,{"n52005013004"})
        bad=copy.deepcopy(LEDGER)
        bad["reviewed_families"][0]["exact_original_word_ids_with_missing_ln_allowed"].append("n52005013004")
        with self.assertRaisesRegex(ValueError,"independent evidence"):
            MOD["review_ledger"](bad,{"source_editions":LEDGER["source_editions"]})

    def test_authentic_bilingual_lexical_classes(self):
        self.assertTrue(MOD["grammar_supported"]("adv",["prep. (with gen.), advb."],
                                                   ["prep. (avec gen.), advb."]))
        self.assertTrue(MOD["grammar_supported"]("noun",["noun, f."],["nom, f."]))
        self.assertFalse(MOD["grammar_supported"]("noun",["advb."],["advb."]))
        self.assertFalse(MOD["grammar_supported"]("verb",["verb"],["verbe"]))

    def test_fails_closed_if_original_strong_components_normalized(self):
        wrong=copy.deepcopy(LEDGER)
        wrong["reviewed_families"][0]["original_macula_strong"]="G4053a"
        with self.assertRaisesRegex(ValueError,"independent evidence"):
            MOD["review_ledger"](wrong,{"source_editions":LEDGER["source_editions"]})

    def test_no_inferred_lexid_global_alias_or_publication(self):
        for key,value in (
            ("never_alias_macula_composite_to_ubs_strong",False),
            ("no_contextual_ubs_lexid_inferred",False),
            ("old_index_and_word_annotations_unmodified",False),
            ("no_publication",False),
        ):
            wrong=copy.deepcopy(LEDGER)
            wrong["editorial_policy"][key]=value
            with self.assertRaisesRegex(ValueError,"policy or pinned source"):
                MOD["review_ledger"](wrong,{"source_editions":LEDGER["source_editions"]})


if __name__=="__main__":
    unittest.main()
