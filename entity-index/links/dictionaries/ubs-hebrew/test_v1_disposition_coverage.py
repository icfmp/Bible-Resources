#!/usr/bin/env python3
"""Offline invariants for the complete source-bound UBS editorial decision audit."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLLECT = runpy.run_path(str(HERE / "audit_v1_disposition_coverage.py"))["collect"]


def load_full():
    file = lambda name: json.loads((HERE / name).read_text(encoding="utf-8"))
    return (
        file("family_register.json"),
        file("v1_scope_dispositions.json"),
        {
            "lexical_nonidentity_rejections": file("v1_lexical_nonidentity_dispositions.json"),
            "multiple_headword_abstentions": file("v1_multi_headword_abstentions.json"),
            "grammatical_morpheme_nonlinks": file("v1_source_morpheme_abstentions.json"),
            "single_candidate_abstentions": file("v1_single_candidate_abstentions.json"),
            "positive_headword_only_reviews": file("v1_reviewed_headword_dispositions.json"),
        },
        file("index.json"),
    )


def miniature():
    editions = {"ubs_revision": "ubs-frozen", "macula_revision": "macula-frozen"}
    families = [
        {"lang": "H", "lemma": "כֹּל", "original_strong": "3605",
         "occurrences": 1, "reason": "unattested_indexed_headword",
         "ubs_candidate_entries": [], "source_witnesses": []},
        {"lang": "H", "lemma": "שָׁלוֹם", "original_strong": "7965",
         "occurrences": 2, "reason": "same_strong_family_unresolved",
         "ubs_candidate_entries": ["a"], "source_witnesses": []},
        {"lang": "H", "lemma": "תּוֹר", "original_strong": "8450",
         "occurrences": 1, "reason": "same_strong_family_unresolved",
         "ubs_candidate_entries": ["b"], "source_witnesses": [
             {"original_word_id": "w-1", "reference": "GEN 1:1", "original_sdbh": ""}
         ]},
    ]
    register = {"source_editions": editions, "families": families,
                "summary": {"lexical_source_occurrences": 4,
                            "linked_occurrences": 0,
                            "unresolved_families": 3,
                            "unresolved_occurrences": 4,
                            "outside_scope_occurrences": 1,
                            "inside_scope_unresolved_occurrences": 3}}
    scope = {"ubs_revision": "ubs-frozen", "macula_revision": "macula-frozen",
             "dispositions": [
                 {"lang": "H", "lemma": "כֹּל", "original_strong": "3605",
                  "original_occurrences": 1, "source_data_modified": False,
                  "disposition": "approved_ubs_0_9_4_indexed_headword_scope_exclusion"}
             ]}
    ledgers = {
        "lexical_nonidentity_rejections": {"source_editions": editions, "decisions": []},
        "multiple_headword_abstentions": {"source_editions": editions, "dispositions": []},
        "grammatical_morpheme_nonlinks": {"source_editions": editions, "decisions": []},
        "single_candidate_abstentions": {"source_editions": editions, "dispositions": []},
        "positive_headword_only_reviews": {"source_editions": editions, "decisions": [
            {"lang": "H", "lemma": "שָׁלוֹם", "original_strong": "7965",
             "original_occurrences": 2, "ubs_candidate_main_id": "a",
             "disposition": "source_reviewed_ubs_headword_entry_only",
             "contextual_sense_id_approved": False,
             "index_word_links_applied": False,
             "source_data_modified": False},
        ]},
    }
    index = {"coverage_scope": {
        "original_lexical_source_occurrences": 4,
        "linked_occurrences": 0,
        "outside_indexed_headword_scope": 1,
        "indexable_unresolved": 3,
    }}
    return register, scope, ledgers, index


class V1EditorialAuditTests(unittest.TestCase):
    def test_real_source_ledgers_are_disjoint_and_conservative(self):
        register, scope, ledgers, index = load_full()
        report = COLLECT(register, scope, ledgers, index)
        counts = report["counts"]
        snapshot = json.loads(
            (HERE / "v1_disposition_coverage.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report, snapshot)
        self.assertEqual(counts["original_unresolved_families"], len(register["families"]))
        self.assertEqual(
            counts["original_unresolved_occurrences"],
            counts["in_scope_unresolved_occurrences_at_baseline"]
            + counts["edition_scope_excluded_occurrences"],
        )
        self.assertEqual(
            counts["in_scope_unresolved_occurrences_at_baseline"],
            counts["in_scope_occurrences_with_any_disposition"]
            + counts["not_yet_dispositioned_original_occurrences"],
        )
        self.assertEqual(
            len(report["pending_families"]),
            counts["not_yet_dispositioned_original_families"],
        )
        self.assertIs(report["policy"]["publication_approved"], False)
        self.assertEqual(counts["not_yet_dispositioned_original_families"], 0)
        self.assertEqual(counts["not_yet_dispositioned_original_occurrences"], 0)
        self.assertEqual(counts["in_scope_families_with_any_disposition"], 197)
        self.assertEqual(counts["in_scope_lexical_family_dispositions"], 195)
        self.assertEqual(counts["composite_source_code_preservations"]["families"], 2)
        self.assertEqual(counts["single_candidate_abstentions"],
                         {"families": 16, "occurrences": 25})

    def test_synthetic_coverage_and_pending_partition(self):
        data = miniature()
        report = COLLECT(*data)
        counts = report["counts"]
        self.assertEqual(counts["in_scope_lexical_family_dispositions"], 1)
        self.assertEqual(counts["not_yet_dispositioned_original_families"], 1)
        self.assertEqual(counts["not_yet_dispositioned_original_occurrences"], 1)
        self.assertEqual(report["pending_families"][0]["lemma"], "תּוֹר")

    def test_duplicate_manual_disposition_is_fatal(self):
        register, scope, ledgers, index = miniature()
        ledgers["lexical_nonidentity_rejections"]["decisions"].append({
            "lang": "H", "lemma": "שָׁלוֹם", "original_strong": "7965",
            "occurrences": 2, "decision": "candidate_lexical_nonidentity",
            "ubs_candidate": {"main_id": "a"},
            "source_data_modified": False,
        })
        with self.assertRaisesRegex(ValueError, "recorded twice"):
            COLLECT(register, scope, ledgers, index)

    def test_original_source_rev_and_candidate_drift_are_fatal(self):
        register, scope, ledgers, index = miniature()
        changed = copy.deepcopy(ledgers)
        changed["positive_headword_only_reviews"]["source_editions"] = {
            "ubs_revision": "different", "macula_revision": "macula-frozen"
        }
        with self.assertRaisesRegex(ValueError, "source revisions"):
            COLLECT(register, scope, changed, index)
        changed = copy.deepcopy(ledgers)
        changed["positive_headword_only_reviews"]["decisions"][0][
            "ubs_candidate_main_id"
        ] = "wrong"
        with self.assertRaisesRegex(ValueError, "unsafe or changed positive identity"):
            COLLECT(register, scope, changed, index)

    def test_frozen_scope_mismatch_and_source_modification_are_fatal(self):
        register, scope, ledgers, index = miniature()
        changed = copy.deepcopy(index)
        changed["coverage_scope"]["linked_occurrences"] = 1
        with self.assertRaisesRegex(ValueError, "index scope disagrees"):
            COLLECT(register, scope, ledgers, changed)
        changed = copy.deepcopy(ledgers)
        changed["positive_headword_only_reviews"]["decisions"][0][
            "source_data_modified"
        ] = True
        with self.assertRaisesRegex(ValueError, "source modification"):
            COLLECT(register, scope, changed, index)


if __name__ == "__main__":
    unittest.main()

