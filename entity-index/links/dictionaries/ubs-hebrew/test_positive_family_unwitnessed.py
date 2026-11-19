#!/usr/bin/env python3
"""Offline safety tests: source census is not an implicit editorial link."""
import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLLECT = runpy.run_path(str(HERE / "audit_positive_family_unwitnessed.py"))["collect"]
EDITIONS = {"ubs_revision": "ubs-frozen", "macula_revision": "macula-frozen"}


def fixtures(directory):
    source = Path(directory) / "wlc.tsv"
    source.write_text(
        "xml:id\tlemma\tlang\tstrongnumberx\tsdbh\tclass\tpos\tenglish\tmorph\tref\n"
        "o010010010011\tשָׁלוֹם\tH\t7965\torig1\tnoun\tN\tpeace\tNcmsa\tGEN 1:1!1\n"
        "o010010010021\tשָׁלוֹם\tH\t7965\torig2\tnoun\tN\twell-being\tNcmsa\tGEN 1:1!2\n",
        encoding="utf-8",
    )
    d = {
        "lang": "H", "lemma": "שָׁלוֹם", "original_strong": "7965",
        "original_occurrences": 2, "original_source_classes": {"noun": 2},
        "ubs_candidate_main_id": "006001000000000",
        "editorial_meaning": "Peace / completeness",
        "evidence": {"ubs_attested_gloss": "peace"}
    }
    ledger = {"source_editions": EDITIONS, "decisions": [d]}
    preview = {
        "source_editions": EDITIONS,
        "by_macula_word": {
            "o010010010011": {
                "lemma": "שָׁלוֹם", "lang": "H", "strong": "7965",
                "original_sdbh": "orig1", "reference": "GEN 1:1!1",
                "entry_id": "006001000000000",
            }
        },
    }
    return ledger, preview, {"by_macula_word": {}}, source


class PositiveFamilyCensusTests(unittest.TestCase):
    def test_only_unwitnessed_source_words_become_pending_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            l, p, i, f = fixtures(t)
            result = COLLECT(l, p, i, f)
        self.assertEqual(result["summary"]["additional_words_pending_individual_review"], 1)
        self.assertEqual(result["families"][0]["new_word_id_count"], 1)
        self.assertEqual(result["families"][0]["source_words_pending_individual_review"][0]["english_original"], "well-being")
        self.assertEqual(i["by_macula_word"], {})
        self.assertNotIn("entry_id", result["families"][0]["source_words_pending_individual_review"][0])

    def test_source_lemma_and_witness_drift_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            l, p, i, f = fixtures(t)
            p["by_macula_word"]["o010010010011"]["lemma"] = "שָׁלֹם"
            with self.assertRaisesRegex(ValueError, "preview word drift"):
                COLLECT(l, p, i, f)

    def test_family_count_and_existing_link_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            l, p, i, f = fixtures(t)
            l["decisions"][0]["original_occurrences"] = 3
            with self.assertRaisesRegex(ValueError, "count drift"):
                COLLECT(l, p, i, f)
            l["decisions"][0]["original_occurrences"] = 2
            i["by_macula_word"]["o010010010021"] = {"entry_id": "some-other"}
            with self.assertRaisesRegex(ValueError, "already-linked"):
                COLLECT(l, p, i, f)


if __name__ == "__main__":
    unittest.main()

