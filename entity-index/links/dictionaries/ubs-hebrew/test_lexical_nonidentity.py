#!/usr/bin/env python3
"""Synthetic guards for the editorial nonidentity evidence verifier."""
import runpy
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
verify = runpy.run_path(str(HERE / "verify_lexical_nonidentity.py"))
source_versions = {"ubs_revision": "ubs-test", "macula_revision": "macula-test"}


def fixture():
    candidate = {"main_id": "000001000000000", "lemma": "אֵל",
                 "strong_codes": ["H0410"], "parts_of_speech": ["noun m"]}
    row = {"lang": "H", "lemma": "אַל", "original_strong": "0408",
           "occurrences": 2, "decision": "candidate_lexical_nonidentity",
           "rationale": "Negative particle is not the noun.",
           "candidate_relation": "different_strong_same_consonants",
           "ubs_candidate": candidate,
           "source_witness": {"word_id": "word-one", "reference": "GEN 1:1!1",
                              "english": "not", "pos": "particle", "class": "adv"}}
    report = {"source_editions": source_versions,
              "families": [{"lang": "H", "lemma": "אַל", "original_strong": "0408",
                            "occurrences": 2, "reason": "different_strong_same_consonants",
                            "ubs_candidate_entries": [candidate["main_id"]],
                            "source_witnesses": [{"original_word_id": "word-one",
                                                  "reference": "GEN 1:1!1"}]}]}
    ledger = {"schema_version": 1, "source_editions": source_versions,
              "decisions": [row]}
    entries = [{"MainId": candidate["main_id"], "Lemma": "אֵל",
                "StrongCodes": ["H0410"],
                "BaseForms": [{"PartsOfSpeech": ["noun m"]}]}]
    return ledger, report, entries


class VerifyNonidentityTests(unittest.TestCase):
    def test_valid_source_and_candidate(self):
        ledger, report, entries = fixture()
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "macula.tsv"
            p.write_text("xml:id\tlang\tlemma\tstrongnumberx\tref\tenglish\tpos\tclass\n"
                         "word-one\tH\tאַל\t0408\tGEN 1:1!1\tnot\tparticle\tadv\n",
                         encoding="utf-8")
            self.assertEqual(verify["verify"](ledger, report, entries, p),
                             {"families": 1, "occurrences": 2})
            p.write_text(p.read_text(encoding="utf-8").replace("not\tparticle", "god\tparticle"),
                         encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Original MACULA witness changed"):
                verify["verify"](ledger, report, entries, p)

    def test_candidate_change_and_source_revision_are_rejected(self):
        ledger, report, entries = fixture()
        modified = deepcopy(entries)
        modified[0]["StrongCodes"] = ["H0408"]
        with self.assertRaisesRegex(ValueError, "candidate Strong metadata changed"):
            verify["verify_metadata"](ledger, report, modified)
        changed = deepcopy(ledger)
        changed["source_editions"]["ubs_revision"] = "other"
        with self.assertRaisesRegex(ValueError, "Source revisions differ"):
            verify["verify_metadata"](changed, report, entries)

    def test_missing_editorial_reason_is_rejected_explicitly(self):
        ledger, report, entries = fixture()
        del ledger["decisions"][0]["rationale"]
        with self.assertRaisesRegex(ValueError, "Unexplained or unsupported"):
            verify["verify_metadata"](ledger, report, entries)

    def test_same_strong_compound_source_component_rejection(self):
        ledger, report, entries = fixture()
        d = ledger["decisions"][0]
        f = report["families"][0]
        d["candidate_relation"] = "same_strong_family_unresolved"
        f["reason"] = "same_strong_family_unresolved"
        d["original_strong"] = f["original_strong"] = "7417b"
        d["lemma"] = f["lemma"] = "רִמּוֹן"
        d["source_witness"] = {
            "word_id": "word-one", "reference": "2KI 5:18!9",
            "original_sdbh": "006818002005000"
        }
        f["source_witnesses"] = [{
            "original_word_id": "word-one", "reference": "2KI 5:18!9",
            "original_sdbh": "006818002005000"
        }]
        d["source_classes"] = f["source_classes"] = {"noun": 2}
        d["ubs_candidate"] = {
            "main_id": "000001000000000", "lemma": "רִמּוֹנוֹ",
            "strong_codes": ["H7417"], "parts_of_speech": ["name"]
        }
        entries[0]["Lemma"] = "רִמּוֹנוֹ"
        entries[0]["StrongCodes"] = ["H7417"]
        entries[0]["BaseForms"][0]["PartsOfSpeech"] = ["name"]
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "macula.tsv"
            p.write_text(
                "xml:id\\tlang\\tlemma\\tstrongnumberx\\tref\\tsdbh\\tclass\\n"
                "word-one\\tH\\tרִמּוֹן\\t7417b\\t2KI 5:18!9\\t"
                "006818002005000\\tnoun\\n",
                encoding="utf-8"
            )
            self.assertEqual(verify["verify"](ledger, report, entries, p),
                             {"families": 1, "occurrences": 2})
            p.write_text(p.read_text(encoding="utf-8").replace(
                "006818002005000", "WRONG_ID"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Original MACULA witness changed"):
                verify["verify"](ledger, report, entries, p)
        changed = deepcopy(ledger)
        changed["decisions"][0]["source_classes"] = {"verb": 2}
        with self.assertRaisesRegex(ValueError, "source-class counts changed"):
            verify["verify_metadata"](changed, report, entries)
        changed = deepcopy(entries)
        changed[0]["StrongCodes"] = ["H7418"]
        with self.assertRaisesRegex(ValueError, "candidate Strong metadata changed"):
            verify["verify_metadata"](ledger, report, changed)

    def test_original_candidate_reason_drift_rejected(self):
        ledger, report, entries = fixture()
        ledger["decisions"][0]["candidate_relation"] = "same_strong_family_unresolved"
        with self.assertRaisesRegex(ValueError, "supported unresolved family"):
            verify["verify_metadata"](ledger, report, entries)

    def test_non_exhaustive_candidate_rejection_is_rejected(self):
        ledger, report, entries = fixture()
        report["families"][0]["ubs_candidate_entries"].append("000002000000000")
        with self.assertRaisesRegex(ValueError, "Not an exhaustive sole-candidate rejection"):
            verify["verify_metadata"](ledger, report, entries)


if __name__ == "__main__":
    unittest.main()
