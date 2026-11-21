#!/usr/bin/env python3
"""Offline UBS Hebrew crosswalk regression tests (synthetic original ID fixtures)."""
import json
import runpy
import tempfile
import unittest
from pathlib import Path

mod=runpy.run_path(str(Path(__file__).with_name("build_index.py")))
build,lookup,audit=mod["build"],mod["lookup"],mod["audit"]


def entry(mid, strong, sense, code="001001", lemma="אֱלֹהִים"):
    return {
        "MainId": mid, "Lemma": lemma, "StrongCodes": strong,
        "BaseForms": [{"LEXMeanings": [
            {"LEXID": sense, "LEXEntryCode": code}
        ]}],
    }


class UBSHebrewBridgeTest(unittest.TestCase):
    def setUp(self):
        self.a=entry("000001000000000", ["H0430"], "000001001001000")
        self.b=entry("000002000000000", ["H0430"], "000002001001000")

    def test_shared_bilingual_ids_and_ambiguous_strong(self):
        index=build([self.a,self.b], [self.b,self.a])
        self.assertEqual(index["statistics"]["shared_entries"], 2)
        direct=lookup(index, "000001001001000", "0430", "H")
        self.assertEqual(direct["status"],"direct_sense")
        self.assertEqual(direct["entry_ids"],[self.a["MainId"]])
        self.assertEqual(direct["sense_ids"],["000001001001000"])
        fallback=lookup(index,"","0430","H")
        self.assertEqual(fallback["status"],"ambiguous_entry_only")
        self.assertEqual(fallback["sense_ids"],[])
        self.assertEqual(fallback["entry_ids"],sorted([self.a["MainId"],self.b["MainId"]]))

    def test_original_language_and_suffix_not_guessed(self):
        index=build([self.a,entry("000003000000000",["A0430"],"000003001001000")],
                    [self.a,entry("000003000000000",["A0430"],"000003001001000")])
        aramaic=lookup(index,"","0430","A")
        self.assertEqual(aramaic["entry_ids"],["000003000000000"])
        self.assertEqual(lookup(index,"","0430a","H")["status"],"no_entry_match")
        self.assertEqual(lookup(index,"","430 431","H")["sense_ids"],[])
        self.assertEqual(lookup(index,"","0430","H")["entry_ids"],["000001000000000"])
        self.assertEqual(lookup(index,"999999999999999","0430","H")["status"],"entry_only")

    def test_exact_suffix_strong_is_distinct_and_never_collapsed(self):
        variant = entry("000004000000000", ["H0430a"], "000004001001000")
        other = entry("000005000000000", ["H0430b"], "000005001001000")
        index = build([self.a, variant, other], [self.a, variant, other])
        self.assertEqual(lookup(index, "", "0430a", "H")["entry_ids"], [variant["MainId"]])
        self.assertEqual(lookup(index, "", "0430b", "H")["entry_ids"], [other["MainId"]])
        self.assertEqual(lookup(index, "", "0430", "H")["entry_ids"], [self.a["MainId"]])
        self.assertEqual(lookup(index, "", "0430c", "H")["status"], "no_entry_match")
        self.assertEqual(lookup(index, "", "0430a", "H")["sense_ids"], [])
        self.assertEqual(lookup(index, "", "0430a", "A")["entry_ids"], [])
        self.assertEqual(lookup(index, "", "430a 430b", "H")["status"], "no_verified_lexical_link")

    def test_sdbh_numeric_id_collision_cannot_steal_unrelated_lexeme(self):
        # Old edition's 'beginning' ID now belongs to a 'head' UBS entry.
        wrong=entry("006653000000000", ["H7218"], "006653001001000", lemma="רֹאשׁ")
        right=entry("006660000000000", ["H7225"], "006660001001000", lemma="רֵאשִׁית")
        ix=build([wrong,right],[wrong,right])
        out=lookup(ix,"006653001001000","7225","H")
        self.assertEqual(out["status"],"entry_only")
        self.assertEqual(out["entry_ids"],[right["MainId"]])
        self.assertEqual(out["sense_ids"],[])
        self.assertEqual(out["evidence"],"macula_strong_exact_only")
        # No fallback may silently choose the unrelated entry.
        missing=lookup(ix,"006653001001000","9999","H")
        self.assertEqual(missing["status"],"no_entry_match")
        self.assertEqual(missing["entry_ids"],[])
        self.assertEqual(missing["sense_ids"],[])

    def test_correlated_sdbh_strong_family_allows_original_sense(self):
        only=entry("000001000000000",["H0430a"],"000001001001000")
        ix=build([only],[only])
        out=lookup(ix,"000001001001000","0430","H")
        self.assertEqual(out["status"],"direct_sense")
        self.assertEqual(out["sense_ids"],["000001001001000"])
        self.assertEqual(out["evidence"],"macula_sdbh_and_ubs_strong_numeric_family")
        self.assertEqual(lookup(ix,"000001001001000","0430","A")["entry_ids"],[])

    def test_fails_on_bilingual_drift_and_duplicates(self):
        changed=json.loads(json.dumps(self.a))
        changed["BaseForms"][0]["LEXMeanings"][0]["LEXID"]="000001001002000"
        with self.assertRaisesRegex(ValueError,"lexical ID drift"):
            build([self.a],[changed])
        with self.assertRaisesRegex(ValueError,"inventories differ"):
            build([self.a],[self.b])
        with self.assertRaisesRegex(ValueError,"Duplicate UBS MainId"):
            build([self.a,self.a],[self.a,self.a])

    def test_mixed_sdbh_and_strong_coverage_audit(self):
        ix=build([self.a],[self.a])
        rows=[
            ("o010010010011","000001001001000","0430","H"),
            ("o010010010021","","0430","H"),
            ("o010010010031","","0871a","H"),
            ("o010010010041ה","000001001001000","0430","H"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"wlc.tsv"
            path.write_text("xml:id\tsdbh\tstrongnumberx\tlang\n"+"".join(
                "\t".join(row)+"\n" for row in rows),encoding="utf-8")
            coverage,_=audit(ix,path)
        self.assertEqual(coverage["macula_words"],4)
        self.assertEqual(coverage["with_exact_ubs_sense_candidates"],2)
        self.assertEqual(coverage["with_ubs_entry_candidates"],3)
        self.assertEqual(coverage["no_entry_match"],1)
        self.assertEqual(coverage["entry_only"],1)


if __name__=="__main__":
    unittest.main()
