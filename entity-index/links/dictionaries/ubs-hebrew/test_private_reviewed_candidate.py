#!/usr/bin/env python3
"""Synthetic source-fidelity guards for a nonpublished reviewed UBS candidate."""
import copy
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_private_reviewed_candidate.py"))
BUILD = runpy.run_path(str(HERE / "build_index.py"))
WID = "o010010010011"
EID = "000001000000000"


def fixture():
    entry = {"MainId": EID, "Lemma": "דָּבָר",
             "StrongCodes": ["H9999"],
             "BaseForms": [{"LEXMeanings": [{
                 "LEXID": "000001001001000", "LEXEntryCode": ""
             }]}]}
    base = BUILD["build"]([entry], [entry])
    base["by_macula_word"] = {}
    editions = {
        "ubs_revision": base["dictionary"]["revision"],
        "macula_revision": base["macula"]["revision"],
    }
    rec = {
        "entry_id": EID, "match_type":
        "editorially_reviewed_original_wlc_headword_only",
        "lemma": "דָּבָר", "strong": "1697", "lang": "H",
        "original_sdbh": "original-sdbh", "reference": "GEN 1:1!1",
    }
    first = {"source_editions": editions, "by_macula_word": {WID: rec}}
    second = {"source_editions": editions, "by_macula_word": {}}
    return entry, base, first, second


class OriginalReviewCandidateTest(unittest.TestCase):
    def test_exact_headword_only_overlay_does_not_modify_baseline(self):
        entry, base, first, second = fixture()
        links = MOD["combine_source_word_overlays"](base, first, second)
        self.assertEqual(len(links), 1)
        trial = copy.deepcopy(base)
        trial["by_macula_word"] = links
        result = BUILD["lookup_word"](
            trial, WID, "original-sdbh", "1697", "H", "דָּבָר")
        self.assertEqual(result["entry_ids"], [EID])
        self.assertEqual(result["sense_ids"], [])
        self.assertEqual(base["by_macula_word"], {})
        self.assertEqual(BUILD["lookup_word"](
            trial, WID, "changed-sdbh", "1697", "H", "דָּבָר"
        )["status"], "source_word_mismatch")

    def test_duplicate_source_word_and_pinned_revision_drift(self):
        _, base, first, second = fixture()
        second["by_macula_word"][WID] = copy.deepcopy(
            first["by_macula_word"][WID])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            MOD["combine_source_word_overlays"](base, first, second)
        second["by_macula_word"].clear()
        first["source_editions"]["ubs_revision"] = "altered"
        with self.assertRaisesRegex(ValueError, "Source-revision mismatch"):
            MOD["combine_source_word_overlays"](base, first, second)

    def test_exact_lexical_original_source_fields_are_mandatory(self):
        entry, base, first, second = fixture()
        overlays = MOD["combine_source_word_overlays"](base, first, second)
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "words.tsv"
            src.write_text(
                "xml:id\tlemma\tstrongnumberx\tlang\tsdbh\tclass\tref\n" +
                WID + "\tדָּבָר\t1697\tH\toriginal-sdbh\tnoun\tGEN 1:1!1\n",
                encoding="utf-8",
            )
            check = MOD["verify_original_macula_words"](
                base, overlays, src, [entry])
            self.assertEqual(check["verified_new_word_anchors"], 1)
            self.assertEqual(check["original_macula_lexical_word_rows"], 1)
            src.write_text(src.read_text(encoding="utf-8").replace(
                "original-sdbh", "changed"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source word changed"):
                MOD["verify_original_macula_words"](base, overlays, src, [entry])

    def test_never_overwrite_preexisting_word_or_missing_ubs_entry(self):
        entry, base, first, second = fixture()
        base["by_macula_word"][WID] = {"entry_id": EID}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            MOD["combine_source_word_overlays"](base, first, second)
        base["by_macula_word"] = {}
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "words.tsv"
            src.write_text(
                "xml:id\tlemma\tstrongnumberx\tlang\tsdbh\tclass\tref\n" +
                WID + "\tדָּבָר\t1697\tH\toriginal-sdbh\tnoun\tGEN 1:1!1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "headword absent"):
                MOD["verify_original_macula_words"](
                    base, first["by_macula_word"], src, [])


if __name__ == "__main__":
    unittest.main()

