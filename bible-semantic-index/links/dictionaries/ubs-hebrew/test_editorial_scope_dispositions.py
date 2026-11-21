#!/usr/bin/env python3
"""Verify source-bound UBS scope decisions without turning them into lexeme links."""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTER = json.loads((HERE / "family_register.json").read_text(encoding="utf-8"))
DECISIONS = json.loads((HERE / "v1_scope_dispositions.json").read_text(encoding="utf-8"))


def family_key(row):
    return (row["lang"], row["lemma"], row["original_strong"])


class EditorialScopeDispositionTests(unittest.TestCase):
    def test_pinned_source_versions_and_complete_expected_coverage(self):
        self.assertEqual(DECISIONS["ubs_revision"], REGISTER["source_editions"]["ubs_revision"])
        self.assertEqual(DECISIONS["macula_revision"], REGISTER["source_editions"]["macula_revision"])
        selected = [f for f in REGISTER["families"] if f["reason"] in
                    ("unattested_indexed_headword", "source_strong_unreadable")]
        records = DECISIONS["dispositions"]
        self.assertEqual(len(records), len(selected))
        self.assertEqual(len(records), len({family_key(x) for x in records}))
        self.assertEqual({family_key(f) for f in selected},
                         {family_key(x) for x in records})

    def test_scope_exclusion_is_exact_and_no_source_is_modified(self):
        original = {family_key(f): f for f in REGISTER["families"]}
        excluded_occurrences = 0
        unresolved_codes = 0
        for decision in DECISIONS["dispositions"]:
            f = original[family_key(decision)]
            self.assertEqual(decision["original_occurrences"], f["occurrences"])
            self.assertIn(decision["original_word_witness"],
                          [w["original_word_id"] for w in f["source_witnesses"]])
            self.assertIs(decision["lexical_identity_approved"], False)
            self.assertIs(decision["source_data_modified"], False)
            if f["reason"] == "unattested_indexed_headword":
                self.assertEqual(decision["disposition"],
                                 "approved_ubs_0_9_4_indexed_headword_scope_exclusion")
                self.assertEqual(f["ubs_candidate_entries"], [])
                excluded_occurrences += f["occurrences"]
            else:
                self.assertEqual(f["reason"], "source_strong_unreadable")
                self.assertEqual(decision["disposition"],
                                 "preserve_composite_source_code_pending_original_annotation_review")
                self.assertIn("|", f["original_strong"])
                unresolved_codes += f["occurrences"]
        self.assertEqual(excluded_occurrences, REGISTER["summary"]["outside_scope_occurrences"])
        self.assertEqual(unresolved_codes, REGISTER["summary"]["occurrences_by_reason"]["source_strong_unreadable"])

    def test_lexical_coverage_and_unresolved_identity_not_rewritten(self):
        self.assertEqual(REGISTER["summary"]["linked_occurrences"], 240098)
        self.assertEqual(REGISTER["summary"]["inside_scope_unresolved_occurrences"], 2649)
        self.assertEqual(REGISTER["summary"]["families_with_editorial_decision"], 0)
        self.assertTrue(all(x["review_decision"] == "not_editorially_validated"
                            for x in REGISTER["families"]))


if __name__ == "__main__":
    unittest.main()
