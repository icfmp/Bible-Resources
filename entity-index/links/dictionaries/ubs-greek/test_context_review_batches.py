#!/usr/bin/env python3
"""Offline regression tests for source-preserving Greek UBS review batches."""
from __future__ import annotations
import runpy
import unittest
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name("build_context_review_batches.py")))
group_for_review = MOD["group_for_review"]
MULTI = MOD["MULTI"]
STATUS = MOD["EXPECTED_STATUS"]


def fixture():
    rows = {}
    for n in range(15237):
        wid = f"n{n:011d}"
        if n < 2728:
            rows[wid] = {
                "original_word_id": wid, "original_reference": "Matt.1.1",
                "original_lemma": "λόγος", "original_strong": "3056",
                "original_ln": "33.98", "original_class": "noun",
                "original_morph": "N-NSM", "editorial_status": MULTI,
                "source_original_ubs_main_id_candidates": ["0001"],
                "source_ubs_lexid_candidate_pairs": [
                    {"original_ubs_main_id": "0001", "original_ubs_lexid": "a", "original_ln": "33.98"},
                    {"original_ubs_main_id": "0001", "original_ubs_lexid": "b", "original_ln": "33.98"},
                ],
            }
        else:
            rows[wid] = {"editorial_status": "no_original_ln_matching_ubs_lexical_sense"}
    return {"status": STATUS, "unresolved_original_word_count": 15237,
            "contextual_senses_independently_verified": 0,
            "published": False, "public_release_approved": False,
            "source_editions": {"ubs_greek_revision": "pinned"},
            "word_id_to_unresolved_original_source_evidence": rows}


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input = fixture()

    def test_partition_and_source_witnesses(self):
        result = group_for_review(self.input, batch_size=100)
        self.assertEqual(result["original_multi_sense_word_count"], 2728)
        self.assertEqual(result["review_groups"], 1)
        self.assertEqual(len(result["review_batches"]), 28)
        self.assertEqual(sum(len(x["word_id_evidence"]) for x in result["review_batches"]), 2728)
        self.assertTrue(all(w["editorial_contextual_lexid_selection"] is None
                            and w["contextually_verified"] is False
                            for batch in result["review_batches"] for w in batch["word_id_evidence"]))
        self.assertFalse(result["published"])

    def test_invalid_source_pair_rejected(self):
        data = fixture()
        first = next(iter(data["word_id_to_unresolved_original_source_evidence"].values()))
        first["source_ubs_lexid_candidate_pairs"][0]["original_ln"] = "99.99"
        with self.assertRaises(ValueError):
            group_for_review(data)

    def test_missing_word_id_rejected(self):
        data = fixture()
        data["word_id_to_unresolved_original_source_evidence"].pop(next(iter(
            data["word_id_to_unresolved_original_source_evidence"])))
        with self.assertRaises(ValueError):
            group_for_review(data)

    def test_invalid_batch_size_rejected(self):
        with self.assertRaises(ValueError):
            group_for_review(self.input, 0)

    def test_bogus_context_validation_rejected(self):
        data = fixture()
        data["contextual_senses_independently_verified"] = 2728
        with self.assertRaises(ValueError):
            group_for_review(data)


if __name__ == "__main__":
    unittest.main()
