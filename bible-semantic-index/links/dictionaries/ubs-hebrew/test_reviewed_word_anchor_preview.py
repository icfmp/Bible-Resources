#!/usr/bin/env python3
"""Offline tests for WLC word-specific, sense-free UBS preview links."""
import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE = runpy.run_path(str(HERE / "stage_reviewed_word_anchors.py"))["stage"]
BUILD = runpy.run_path(str(HERE / "build_index.py"))
WORD = "o010010010011"
OTHER = "o010010010021"
MID = "000001000000000"


def fixture(strong="H9999"):
    e = {"MainId": MID, "Lemma": "דָּבָר", "StrongCodes": [strong],
         "BaseForms": [{"LEXMeanings": []}]}
    index = BUILD["build"]([e], [e])
    index["by_macula_word"] = {}
    decision = {
        "lang": "H", "lemma": "דָּבָר", "original_strong": "1697",
        "ubs_candidate_main_id": MID, "disposition": "source_reviewed_ubs_headword_entry_only",
        "headword_identity_reviewed": True,
        "contextual_sense_id_approved": False,
        "index_word_links_applied": False,
        "source_data_modified": False,
        "original_occurrences": 10,
        "original_source_classes": {"noun": 10},
        "original_word_witnesses": [
            {"original_word_id": WORD, "reference": "GEN 1:1!1", "original_sdbh": "old"}
        ],
    }
    ledger = {
        "source_editions": {
            "ubs_revision": index["dictionary"]["revision"],
            "macula_revision": index["macula"]["revision"],
        },
        "decisions": [decision],
    }
    return index, ledger


def source_file(directory):
    f = Path(directory) / "macula.tsv"
    f.write_text(
        "xml:id\tlemma\tlang\tstrongnumberx\tsdbh\tclass\tref\n"
        + WORD + "\tדָּבָר\tH\t1697\told\tnoun\tGEN 1:1!1\n"
        + OTHER + "\tדָּבָר\tH\t1697\told\tnoun\tGEN 1:1!2\n",
        encoding="utf-8",
    )
    return f


class ReviewedWordAnchorPreviewTests(unittest.TestCase):
    def test_only_documented_original_word_receives_entry_not_sense(self):
        index, ledger = fixture()
        with tempfile.TemporaryDirectory() as t:
            preview = STAGE(ledger, index, source_file(t))
        self.assertEqual(preview["summary"]["staged_original_word_ids"], 1)
        self.assertEqual(set(preview["by_macula_word"]), {WORD})
        self.assertEqual(preview["summary"]["new_contextual_senses"], 0)
        self.assertEqual(index["by_macula_word"], {})
        trial = copy.deepcopy(index)
        trial["by_macula_word"].update(preview["by_macula_word"])
        result = BUILD["lookup_word"](trial, WORD, "old", "1697", "H", "דָּבָר")
        self.assertEqual(result["entry_ids"], [MID])
        self.assertEqual(result["sense_ids"], [])
        self.assertEqual(result["evidence"], "macula_word_editorially_reviewed_headword_only")
        self.assertEqual(BUILD["lookup_word"](trial, OTHER, "old", "1697", "H", "דָּבָר")["entry_ids"], [])
        self.assertEqual(BUILD["lookup_word"](trial, WORD, "changed", "1697", "H", "דָּבָר")["status"], "source_word_mismatch")

    def test_unreviewed_or_changed_source_is_rejected(self):
        index, ledger = fixture()
        with tempfile.TemporaryDirectory() as t:
            src = source_file(t)
            ledger["decisions"][0]["headword_identity_reviewed"] = False
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                STAGE(ledger, index, src)
            ledger["decisions"][0]["headword_identity_reviewed"] = True
            ledger["decisions"][0]["original_word_witnesses"][0]["reference"] = "GEN 1:1!9"
            with self.assertRaisesRegex(ValueError, "witness changed"):
                STAGE(ledger, index, src)

    def test_existing_link_and_revision_drift_are_rejected(self):
        index, ledger = fixture()
        with tempfile.TemporaryDirectory() as t:
            src = source_file(t)
            index["by_macula_word"][WORD] = {
                "entry_id": MID, "lemma": "דָּבָר", "strong": "1697", "lang": "H",
                "match_type": "exact_lemma",
            }
            with self.assertRaisesRegex(ValueError, "originally unlinked"):
                STAGE(ledger, index, src)
            index["by_macula_word"] = {}
            ledger["source_editions"]["ubs_revision"] = "changed"
            with self.assertRaisesRegex(ValueError, "revisions disagree"):
                STAGE(ledger, index, src)

    def test_missing_word_and_duplicate_witness_rejected(self):
        index, ledger = fixture()
        with tempfile.TemporaryDirectory() as t:
            src = source_file(t)
            ledger["decisions"][0]["original_word_witnesses"][0]["original_word_id"] = "missing"
            with self.assertRaisesRegex(ValueError, "absent"):
                STAGE(ledger, index, src)
            ledger["decisions"][0]["original_word_witnesses"][0]["original_word_id"] = WORD
            ledger["decisions"][0]["original_word_witnesses"].append(
                copy.deepcopy(ledger["decisions"][0]["original_word_witnesses"][0]))
            with self.assertRaisesRegex(ValueError, "appears twice"):
                STAGE(ledger, index, src)


if __name__ == "__main__":
    unittest.main()

