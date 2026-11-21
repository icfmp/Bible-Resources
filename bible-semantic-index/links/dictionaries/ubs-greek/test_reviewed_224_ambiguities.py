#!/usr/bin/env python3
"""Negative tests for original Greek 220-word lexical disambiguation review."""
import copy
import json
import runpy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "build_reviewed_224_ambiguities.py"))
LEDGER = json.loads((HERE / "v1_reviewed_ambiguous_headwords.json").read_text(encoding="utf-8"))


class GreekSourceAmbiguityTests(unittest.TestCase):
    def test_reviewed_families_pin_exact_source_lexemes(self):
        plan = MOD["plan"](LEDGER, {
            "source_editions": LEDGER["source_editions"]})
        self.assertEqual(len(plan), 5)
        self.assertEqual(sum(r["original_word_count"] for r in plan.values()), 220)
        self.assertEqual(plan[("πόλις", "4172", "004075000000000")]["original_word_count"], 162)

    def test_reject_unverified_changes_or_global_strong_alias(self):
        for field, value in (
            ("preserve_all_original_ubs_strong_candidates", False),
            ("no_contextual_semantic_lexid", False),
            ("no_global_strong_alias", False),
            ("no_publication", False),
        ):
            edited = copy.deepcopy(LEDGER)
            edited["editorial_policy"][field] = value
            with self.assertRaisesRegex(ValueError, "authorization drift"):
                MOD["plan"](edited, {"source_editions": LEDGER["source_editions"]})

    def test_lookup_requires_exact_original_annotations(self):
        row = {
            "entry_id": "004075000000000", "match_type": MOD["STATUS"],
            "original_reference": "MAT 2:23!5", "original_lemma": "πόλις",
            "original_strong": "4172", "original_ln": "1.89",
            "original_morph": "N-ASF",
            "original_strong_ubs_main_ids_preserved": [
                "004075000000000", "004612000000000"],
        }
        candidate = {"by_macula_ambiguous_word": {"n40002023005": row}}
        lookup = lambda **changes: MOD["lookup_reviewed_ambiguity"](
            candidate, changes.get("word_id", "n40002023005"),
            changes.get("reference", "MAT 2:23!5"),
            changes.get("lemma", "πόλις"),
            changes.get("strong", "4172"),
            changes.get("ln", "1.89"),
            changes.get("morph", "N-ASF"),
        )
        good = lookup()
        self.assertEqual(good["entry_ids"], ["004075000000000"])
        self.assertEqual(good["sense_ids"], [])
        self.assertEqual(len(good["original_legacy_Strong_entry_ids_preserved"]), 2)
        for wrong in (
            {"word_id": "n40002023006"},
            {"reference": "MAT 2:23!6"},
            {"lemma": "Πόλις"},
            {"strong": "4173"},
            {"ln": "1.90"},
            {"morph": "N-NSF"},
        ):
            self.assertEqual(lookup(**wrong)["entry_ids"], [], wrong)


if __name__ == "__main__":
    unittest.main()
