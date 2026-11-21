#!/usr/bin/env python3
"""Contract checks: every lexical source occurrence must be accounted for."""
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
b = runpy.run_path(str(HERE / "build_index.py"))
reg = runpy.run_path(str(HERE / "build_family_register.py"))

def entry(mid, lemma, strong):
    return {"MainId": mid, "Lemma": lemma, "StrongCodes": strong,
            "BaseForms": [{"LEXMeanings": [{"LEXID": mid[:6] + "001001000",
                                           "LEXEntryCode": ""}]}]}

class FamilyRegisterTests(unittest.TestCase):
    def test_all_unresolved_classified_without_accepting_candidates(self):
        one = entry("000001000000000", "קוֹל", ["H6963a"])
        two = entry("000002000000000", "אֲבַדּוֹן", ["H11"])
        two["AlternateLemmas"] = ["אֲבַדּוֹ"]
        en = [one, two]
        ix = b["build"](en, en)
        ix["by_macula_word"] = {}
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "words.tsv"
            tsv.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\tref\n"
                "w1\tקוֹל\t\t6963\tH\tnoun\tGEN 1:1\n"
                "w2\tכֹּל\t\t3605\tH\tnoun\tGEN 1:2\n"
                "w3\tכֹּל\t\t3605\tH\tnoun\tGEN 1:3\n"
                "w4\tאֲבַדּוֹ\t\t12\tH\tnoun\tGEN 1:4\n"
                "w5\tקוֹל\t\t9999\tH\tnoun\tGEN 1:5\n"
                "w6\tקוֹל\t\tinvalid\tH\tnoun\tGEN 1:6\n"
                "w7\tכֹּל\t\t3605\tH\tprep\tGEN 1:7\n",
                encoding="utf-8",
            )
            report = reg["collect"](ix, en, tsv)
        counts = report["summary"]
        self.assertEqual(counts["lexical_source_occurrences"], 6)
        self.assertEqual(counts["linked_occurrences"], 0)
        self.assertEqual(counts["unresolved_occurrences"], 6)
        self.assertEqual(counts["unresolved_families"], 5)
        self.assertEqual(counts["outside_scope_occurrences"], 2)
        self.assertEqual(counts["families_with_editorial_decision"], 0)
        self.assertTrue(all(x["review_decision"] == "not_editorially_validated"
                            for x in report["families"]))
        self.assertEqual(report["families"][0]["occurrences"], 2)
        self.assertTrue(all(len(x["source_witnesses"]) <= 3 for x in report["families"]))

    def test_source_scope_counter_disagreement_is_rejected(self):
        e = entry("000001000000000", "קוֹל", ["H6963a"])
        ix = b["build"]([e], [e])
        ix["by_macula_word"] = {}
        ix["coverage_scope"] = {
            "original_lexical_source_occurrences": 2, "linked_occurrences": 0,
            "outside_indexed_headword_scope": 1, "indexable_unresolved": 0
        }
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\tref\n"
                "w1\tכֹּל\t\t3605\tH\tnoun\tGEN 1:1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "Scope drift"):
                reg["collect"](ix, [e], source)

if __name__ == "__main__":
    unittest.main()
