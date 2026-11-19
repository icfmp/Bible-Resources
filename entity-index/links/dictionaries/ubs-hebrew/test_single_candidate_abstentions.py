#!/usr/bin/env python3
"""Offline regression guards for documented UBS single-candidate abstentions."""
import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = runpy.run_path(str(HERE / "verify_single_candidate_abstentions.py"))
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))
LEDGER = json.loads((HERE / "v1_single_candidate_abstentions.json").read_text(encoding="utf-8"))


class SingleCandidateAbstentionTests(unittest.TestCase):
    def test_all_sixteen_original_families_and_reviewed_words(self):
        result = VERIFY["verify_register"](LEDGER, REGISTER)
        self.assertEqual(result["families"], 16)
        self.assertEqual(result["occurrences"], 25)
        self.assertEqual(len(result["word_witnesses"]), 19)
        self.assertTrue(all(
            d["lexical_identity_approved"] is False
            and d["contextual_sense_approved"] is False
            and d["index_word_links_applied"] is False
            and d["source_data_modified"] is False
            for d in LEDGER["dispositions"]
        ))

    def test_duplicate_and_changed_candidate_are_rejected(self):
        modified = copy.deepcopy(LEDGER)
        modified["dispositions"].append(copy.deepcopy(modified["dispositions"][0]))
        with self.assertRaisesRegex(ValueError, "Repeated lexical abstention"):
            VERIFY["verify_register"](modified, REGISTER)
        modified = copy.deepcopy(LEDGER)
        modified["dispositions"][0]["ubs_candidate"]["main_id"] = "000000000000000"
        with self.assertRaisesRegex(ValueError, "Unknown or changed sole"):
            VERIFY["verify_register"](modified, REGISTER)

    def test_original_word_ids_counts_and_revisions_cannot_drift(self):
        modified = copy.deepcopy(LEDGER)
        modified["dispositions"][0]["original_occurrences"] += 1
        with self.assertRaisesRegex(ValueError, "Original source lexical family changed"):
            VERIFY["verify_register"](modified, REGISTER)
        modified = copy.deepcopy(LEDGER)
        modified["dispositions"][0]["source_first_word"]["word_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "Original word source evidence invalid"):
            VERIFY["verify_register"](modified, REGISTER)
        modified = copy.deepcopy(LEDGER)
        modified["source_editions"]["ubs_revision"] = "other"
        with self.assertRaisesRegex(ValueError, "source revisions changed"):
            VERIFY["verify_register"](modified, REGISTER)

    def test_unsubstantiated_positive_or_sense_assignment_rejected(self):
        for key in ("lexical_identity_approved", "contextual_sense_approved",
                    "index_word_links_applied", "source_data_modified"):
            modified = copy.deepcopy(LEDGER)
            modified["dispositions"][0][key] = True
            with self.assertRaisesRegex(ValueError, "Unsafe or unexplained"):
                VERIFY["verify_register"](modified, REGISTER)
        modified = copy.deepcopy(LEDGER)
        modified["dispositions"][0]["rationale"] = "ambiguous"
        with self.assertRaisesRegex(ValueError, "Unsafe or unexplained"):
            VERIFY["verify_register"](modified, REGISTER)

    def test_ubs_headword_meaning_and_family_drift_are_rejected(self):
        d = LEDGER["dispositions"][0]
        u = d["ubs_candidate"]
        original = {
            "MainId": u["main_id"],
            "Lemma": u["lemma"],
            "StrongCodes": u["strong_codes"],
            "BaseForms": [{
                "PartsOfSpeech": u["parts_of_speech"],
                "LEXMeanings": [{"LEXSenses": [{"Glosses": [u["attested_gloss"]]}]}],
            }],
        }
        VERIFY["verify_ubs"]({"dispositions": [d]}, [original])
        modified = copy.deepcopy(original)
        modified["BaseForms"][0]["LEXMeanings"][0]["LEXSenses"][0]["Glosses"] = ["UNRELATED"]
        with self.assertRaisesRegex(ValueError, "metadata or meaning changed"):
            VERIFY["verify_ubs"]({"dispositions": [d]}, [modified])
        modified = copy.deepcopy(original)
        modified["StrongCodes"] = ["H9999"]
        with self.assertRaisesRegex(ValueError, "metadata or meaning changed"):
            VERIFY["verify_ubs"]({"dispositions": [d]}, [modified])

    def test_first_witness_original_english_and_pos_are_guarded(self):
        d = LEDGER["dispositions"][0]
        w = d["original_word_witnesses"][0]
        first = d["source_first_word"]
        fields = ["xml:id", "lang", "lemma", "strongnumberx", "ref", "sdbh",
                  "class", "english", "pos"]
        row = [first["word_id"], d["lang"], d["lemma"],
               d["original_strong"], w["reference"], w["original_sdbh"],
               first["class"], first["english"], first["pos"]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.tsv"
            path.write_text("\t".join(fields) + "\n" + "\t".join(row) + "\n",
                            encoding="utf-8")
            review = {"word_witnesses": {first["word_id"]: (d, w)}}
            VERIFY["verify_macula"](review, path)
            row[-1] = "changed"
            path.write_text("\t".join(fields) + "\n" + "\t".join(row) + "\n",
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "English/POS witness changed"):
                VERIFY["verify_macula"](review, path)


if __name__ == "__main__":
    unittest.main()

