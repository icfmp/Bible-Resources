#!/usr/bin/env python3
"""Offline source-integrity tests for 134 individual UBS headword reviews."""
from __future__ import annotations

import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = runpy.run_path(str(HERE / "verify_additional_word_headwords.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def fixtures():
    decision = read("v1_additional_word_headword_dispositions.json")
    report = read("positive_family_pending_original_words.json")
    ledger = read("v1_reviewed_headword_dispositions.json")
    preview = read("reviewed_word_anchor_preview.json")
    # Synthetic dictionary fixtures preserve the already-approved UBS ID and
    # attested English gloss, but deliberately do not supply original Strong
    # aliases. The real UBS source is checked in a separate pinned CI stage.
    en = [
        {
            "MainId": p["ubs_main_id"],
            "Lemma": p["lemma_editorial"],
            "StrongCodes": ["H99999"],
            "BaseForms": [{"LEXMeanings": [{
                "LEXID": p["ubs_main_id"],
                "LEXSenses": [{"Glosses": [p["ubs_attested_gloss"]]}],
            }]}],
        } for p in decision["reviewed_families"]
    ]
    index = BUILD["build"](en, en)
    index["by_macula_word"] = {}
    return decision, report, ledger, preview, index, en


class AdditionalOriginalWordEvidenceTests(unittest.TestCase):
    def test_exact_full_approved_partition_produces_only_sense_free_overlay(self):
        args = fixtures()
        overlay = CHECK["verify_editorial_dispositions"](*args)
        self.assertEqual(overlay["summary"], {
            "new_individually_approved_original_words": 134,
            "source_words_preserved_unlinked_as_uncertain": 1,
            "combined_staged_original_wlc_words": 273,
            "new_contextual_sense_ids": 0,
        })
        self.assertEqual(len(overlay["by_macula_word"]), 134)
        self.assertEqual(args[4]["by_macula_word"], {})

    def test_changed_source_english_and_wrong_ubs_word_rejected(self):
        d, report, ledger, preview, index, english = fixtures()
        d["approved_word_decisions"][0]["english_original"] = "UNSUPPORTED"
        with self.assertRaisesRegex(ValueError, "Original word evidence mismatch"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)
        d, report, ledger, preview, index, english = fixtures()
        d["approved_word_decisions"][0]["entry_id"] = "999999000000000"
        with self.assertRaisesRegex(ValueError, "unreviewed UBS headword"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)

    def test_unapproved_original_lexical_sense_and_missing_word_rejected(self):
        d, report, ledger, preview, index, english = fixtures()
        d["approved_word_decisions"][0]["contextual_sense_id_approved"] = True
        with self.assertRaisesRegex(ValueError, "Unsafe individual"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)
        d, report, ledger, preview, index, english = fixtures()
        d["approved_word_decisions"].pop()
        with self.assertRaisesRegex(ValueError, "Not every pending"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)

    def test_incorrect_dictionary_gloss_and_duplicate_word_rejected(self):
        d, report, ledger, preview, index, english = fixtures()
        english[0]["BaseForms"][0]["LEXMeanings"][0]["LEXSenses"][0]["Glosses"] = ["unrelated"]
        with self.assertRaisesRegex(ValueError, "meaning absent"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)
        d, report, ledger, preview, index, english = fixtures()
        d["approved_word_decisions"].append(copy.deepcopy(d["approved_word_decisions"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicated"):
            CHECK["verify_editorial_dispositions"](d, report, ledger, preview, index, english)

    def test_macula_field_mutation_rejected_without_source_edit(self):
        d, _, _, _, _, _ = fixtures()
        witness = d["approved_word_decisions"][0]
        with tempfile.TemporaryDirectory() as t:
            file = Path(t) / "source.tsv"
            file.write_text(
                "xml:id\tlemma\tstrongnumberx\tlang\tsdbh\tclass\tpos\tmorph\tenglish\tref\n"
                + "\t".join(str(witness[k]) for k in (
                    "word_id", "lemma_original", "strong_original", "lang",
                    "sdbh_original", "class_original", "pos_original",
                    "morph_original", "english_original", "reference"
                )) + "\n", encoding="utf-8"
            )
            one = {"approved_word_decisions": [witness]}
            CHECK["verify_macula_originals"](one, file)
            file.write_text(file.read_text(encoding="utf-8").replace(
                witness["english_original"], "CHANGED_SOURCE"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Original MACULA word changed"):
                CHECK["verify_macula_originals"](one, file)


if __name__ == "__main__":
    unittest.main()

