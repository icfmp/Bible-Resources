#!/usr/bin/env python3
"""Synthetic tests for the lexical-gap grouping; no original sources modified."""
import runpy
import tempfile
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent
gap = runpy.run_path(str(root / "audit_lexical_gaps.py"))["analyze"]
base = runpy.run_path(str(root / "build_index.py"))["build"]


class LexicalGapAuditTests(unittest.TestCase):
    def test_groups_exact_original_lemma_per_language_and_preserves_evidence(self):
        entry = lambda mid, lemma, strong, sense: {
            "MainId": mid, "Lemma": lemma, "StrongCodes": strong,
            "BaseForms": [{"LEXMeanings": [{"LEXID": sense, "LEXEntryCode": ""}]}],
        }
        records = [entry("000001000000000", "טוֹב", ["H999"], "000001001001000")]
        ix = base(records, records)
        rows = [
            ("o010010010011", "GEN 1:1!1", "noun", "טוֹב", "טוֹב", "5000", "", "Ncms", "H"),
            ("o010010010021", "GEN 1:1!2", "noun", "טוֹב", "טוֹב", "5000", "", "Ncms", "H"),
            ("o010010010031", "GEN 1:1!3", "noun", "טוֹב", "טוֹב", "5001", "", "Ncms", "A"),
            ("o010010010041", "GEN 1:1!4", "cj", "וְ", "וְ", "2050b", "", "C", "H"),
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.tsv"
            path.write_text(
                "xml:id\tref\tclass\tlemma\ttext\tstrongnumberx\tsdbh\tmorph\tlang\n" +
                "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
            result = gap(ix, records, path, expected_unresolved=3)
            with self.assertRaisesRegex(ValueError, "Lexical gap unexpectedly changed"):
                gap(ix, records, path, expected_unresolved=4)
        self.assertEqual(result["summary"]["all_source_rows"], 4)
        self.assertEqual(result["summary"]["lexical_unresolved"], 3)
        self.assertEqual(result["distinct_language_lemma_groups"], 2)
        self.assertEqual(result["top_groups"][0]["occurrences"], 2)
        self.assertEqual(result["top_groups"][0]["exact_lemma_candidate_count"], 1)
        self.assertEqual(result["top_groups"][0]["triage_bucket"], "exact_nfc_lemma_candidate_only")
        self.assertEqual(result["top_groups"][1]["language"], "A")


if __name__ == "__main__":
    unittest.main()
