#!/usr/bin/env python3
"""Offline regression tests for source-keyed UBS positive headword decisions."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = runpy.run_path(str(HERE / "verify_reviewed_headwords.py"))
LEDGER = json.loads((HERE / "v1_reviewed_headword_dispositions.json").read_text(encoding="utf-8"))
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))


class ReviewedHeadwordTests(unittest.TestCase):
    def test_all_pinned_source_reviewed_families(self):
        result = CHECK["verify_register"](LEDGER, REGISTER)
        self.assertEqual(result["families"], 81)
        self.assertEqual(result["occurrences"], 274)
        self.assertEqual(len(result["word_witnesses"]), 139)
        self.assertTrue(all(not d["contextual_sense_id_approved"]
                            and not d["index_word_links_applied"]
                            for d in LEDGER["decisions"]))

    def test_missing_rationale_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        del ledger["decisions"][0]["rationale"]
        with self.assertRaisesRegex(ValueError, "Unsafe or undocumented"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_changed_candidate_and_original_witness_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["ubs_candidate_main_id"] = "000000000000000"
        with self.assertRaisesRegex(ValueError, "candidate source changed"):
            CHECK["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["original_word_witnesses"][0]["reference"] = "DAN 2:1"
        with self.assertRaisesRegex(ValueError, "witnesses/counts changed"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_drift_and_unauthorized_sense_link_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["source_editions"]["macula_revision"] = "changed"
        with self.assertRaisesRegex(ValueError, "Source revisions"):
            CHECK["verify_register"](ledger, REGISTER)
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["contextual_sense_id_approved"] = True
        with self.assertRaisesRegex(ValueError, "Unsafe or undocumented"):
            CHECK["verify_register"](ledger, REGISTER)

    def test_wrong_lexical_relation_and_gloss_evidence_are_rejected(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["decisions"][0]["candidate_relation"] = "same_strong_family_unresolved"
        with self.assertRaisesRegex(ValueError, "candidate source changed"):
            CHECK["verify_register"](ledger, REGISTER)
        d = LEDGER["decisions"][0]
        original = {"MainId": d["ubs_candidate_main_id"], "Lemma": d["lemma"],
                    "StrongCodes": ["H1841"],
                    "BaseForms": [{"LEXMeanings": [
                        {"LEXSenses": [{"Glosses": ["NOT DANIEL"]}]}
                    ]}]}
        with self.assertRaisesRegex(ValueError, "meaning absent"):
            CHECK["verify_dictionary"]({"decisions": [d]}, [original])

    def test_consonantal_and_same_numeric_source_evidence_is_distinct(self):
        consonantal = next(d for d in LEDGER["decisions"]
                           if d["candidate_relation"] == "different_strong_same_consonants")
        similar = {"MainId": consonantal["ubs_candidate_main_id"],
                   "Lemma": consonantal["lemma"],
                   "StrongCodes": ["H0746"],
                   "BaseForms": [{"LEXMeanings": [
                       {"LEXSenses": [{"Glosses": [consonantal["evidence"]["ubs_attested_gloss"]]}]}
                   ]}]}
        CHECK["verify_dictionary"]({"decisions": [consonantal]}, [similar])
        invalid = copy.deepcopy(similar)
        invalid["Lemma"] = "UNRELATED"
        with self.assertRaisesRegex(ValueError, "consonantal candidate changed"):
            CHECK["verify_dictionary"]({"decisions": [consonantal]}, [invalid])
        same = next(d for d in LEDGER["decisions"]
                    if d["candidate_relation"] == "same_strong_family_unresolved")
        entry = {"MainId": same["ubs_candidate_main_id"],
                 "Lemma": "DIFFERENT",
                 "StrongCodes": ["H4147"],
                 "BaseForms": [{"LEXMeanings": [
                     {"LEXSenses": [{"Glosses": [same["evidence"]["ubs_attested_gloss"]]}]}
                 ]}]}
        CHECK["verify_dictionary"]({"decisions": [same]}, [entry])
        entry["StrongCodes"] = ["H9999"]
        with self.assertRaisesRegex(ValueError, "numeric Strong family changed"):
            CHECK["verify_dictionary"]({"decisions": [same]}, [entry])

    def test_original_english_witness_drift_rejected(self):
        import tempfile
        d = next(x for x in LEDGER["decisions"]
                 if x["evidence"].get("original_word_english"))
        w = d["original_word_witnesses"][0]
        header = "\t".join((
            "xml:id", "lang", "lemma", "strongnumberx", "class",
            "ref", "sdbh", "english",
        )) + "\n"
        fields = [w["original_word_id"], d["lang"], d["lemma"],
                  d["original_strong"], next(iter(d["original_source_classes"])),
                  w["reference"], w["original_sdbh"], "changed"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "witness.tsv"
            path.write_text(header + "\t".join(fields) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "English witness changed"):
                CHECK["verify_macula"]({"word_witnesses": {
                    w["original_word_id"]: (d, w)
                }}, path)

    def test_original_dictionary_entry_and_cross_strong_invariant(self):
        d = LEDGER["decisions"][0]
        original = {"MainId": d["ubs_candidate_main_id"], "Lemma": d["lemma"],
                    "StrongCodes": ["H1840", "H1841"],
                    "BaseForms": [{"LEXMeanings": [{"LEXSenses": [{"Glosses": ["Daniel"]}]}]}]}
        CHECK["verify_dictionary"]({"decisions": [d]}, [original])
        invalid = copy.deepcopy(original)
        invalid["StrongCodes"] = ["A1841"]
        with self.assertRaisesRegex(ValueError, "now shares numeric Strong"):
            CHECK["verify_dictionary"]({"decisions": [d]}, [invalid])
        invalid = copy.deepcopy(original)
        invalid["Lemma"] = "UNRELATED"
        with self.assertRaisesRegex(ValueError, "canonical/alternate"):
            CHECK["verify_dictionary"]({"decisions": [d]}, [invalid])


if __name__ == "__main__":
    unittest.main()

