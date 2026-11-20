#!/usr/bin/env python3
"""Negative lexical / source-original regression for UBS Greek gap triage."""
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOD = runpy.run_path(str(ROOT / "audit_source_gaps.py"))
BUILD = runpy.run_path(str(ROOT / "build_index.py"))


def entry(mid, lemma, strong, ln=None):
    senses = [] if ln is None else [
        {"LEXID": mid+"-one", "LEXEntryCode": ln, "LEXSenses": []}
    ]
    return {
        "MainId": mid, "Lemma": lemma, "StrongCodes": strong,
        "BaseForms": [{"LEXMeanings": senses}],
    }


def row(lemma, strong, ln):
    return {
        "lemma": lemma,
        "strong": strong,
        "ln": ln,
        "xml:id": "n40001001001",
        "ref": "MAT 1:1!1",
        "class": "pron",
        "type": "personal",
        "morph": "P-2NP",
    }


class GreekOriginalGapTests(unittest.TestCase):
    def prepare(self, english):
        index = BUILD["build"](english, english)
        lemmas, domains = MOD["source_lexicon"](english, english, index)
        return index, lemmas, domains

    def test_unique_original_nfc_and_ln_is_unapproved_not_a_sense(self):
        ix, headwords, domains = self.prepare([
            entry("ubs-you", "σύ", ["G4675"], "92.7")
        ])
        reason, candidate, codes = MOD["classify"](
            row("σύ", "5213", "92.7"), ix, headwords, domains
        )
        self.assertEqual(
            reason, "dual_source_lemma_and_ln_candidate_unapproved"
        )
        self.assertEqual(candidate["MainId"], "ubs-you")
        self.assertEqual(codes, ("92.7",))
        self.assertEqual(BUILD["lookup"](ix, "5213", "92.7")["entry_ids"], [])

    def test_previously_linked_word_never_overwritten(self):
        ix, heads, domains = self.prepare([
            entry("ubs-you", "σύ", ["G4675"], "92.7")
        ])
        reason, candidate, code = MOD["classify"](
            row("σύ", "4675", "92.7"), ix, heads, domains
        )
        self.assertEqual(reason, "existing_ubs_entry_word")
        self.assertIsNone(candidate)
        self.assertEqual(code, ())

    def test_no_lexical_sense_cannot_be_invented_from_ln(self):
        ix, heads, domains = self.prepare([
            entry("ubs-be", "εἰμί", ["G2258"], None)
        ])
        reason, candidate, codes = MOD["classify"](
            row("εἰμί", "2076", "13.1"), ix, heads, domains
        )
        self.assertEqual(reason, "nfc_lemma_only_no_attested_ubs_ln")
        self.assertEqual(candidate["MainId"], "ubs-be")
        self.assertEqual(codes, ())

    def test_ln_only_or_greek_accent_stripping_is_not_lexical_identity(self):
        ix, heads, domains = self.prepare([
            entry("ubs-one", "ἰδέ", ["G1234"], "91.13")
        ])
        reason, candidate, codes = MOD["classify"](
            row("ἴδε", "2396", "91.13"), ix, heads, domains
        )
        self.assertEqual(reason, "no_nfc_identical_ubs_lemma")
        self.assertIsNone(candidate)
        self.assertEqual(codes, ())

    def test_similar_lemma_with_different_ln_is_not_approved(self):
        ix, heads, domains = self.prepare([
            entry("ubs-one", "οὗτος", ["G5023"], "92.29")
        ])
        reason, candidate, codes = MOD["classify"](
            row("οὗτος", "5026", "89.999"), ix, heads, domains
        )
        self.assertEqual(reason, "nfc_lemma_only_no_attested_ubs_ln")
        self.assertEqual(codes, ())

    def test_homograph_ambiguous_even_if_ln_matches_one_entry(self):
        ix, heads, domains = self.prepare([
            entry("ubs-one", "λόγος", ["G1001"], "33.98"),
            entry("ubs-two", "λόγος", ["G1002"], "33.99"),
        ])
        reason, candidate, codes = MOD["classify"](
            row("λόγος", "9999", "33.98"), ix, heads, domains
        )
        self.assertEqual(reason, "multiple_nfc_identical_ubs_headwords_unresolved")
        self.assertIsNone(candidate)
        self.assertEqual(codes, ())

    def test_original_composite_strong_remains_unsupported(self):
        ix, heads, domains = self.prepare([
            entry("ubs-one", "λόγος", ["G3056"], "33.98")
        ])
        reason, candidate, codes = MOD["classify"](
            row("λόγος", "3056+1234", "33.98"), ix, heads, domains
        )
        self.assertEqual(reason, "unsupported_original_compound_strong")
        self.assertIsNone(candidate)
        self.assertEqual(codes, ())

    def test_different_ubs_language_sense_identity_refused(self):
        en = [entry("ubs-one", "λόγος", ["G3056"], "33.98")]
        fr = [entry("ubs-one", "λόγος", ["G3056"], "33.99")]
        ix = BUILD["build"](en, en)
        with self.assertRaisesRegex(ValueError, "English and French IDs differ"):
            MOD["source_lexicon"](en, fr, ix)

    def test_historic_greek_index_immutable(self):
        source = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(source["coverage"]["macula_words"], 137741)
        self.assertEqual(source["coverage"]["with_ubs_entry_candidates"], 128090)
        self.assertEqual(source["coverage"]["no_ubs_entry"], 9646)
        self.assertEqual(source["coverage"]["unsupported_compound_strong"], 5)
        self.assertNotIn("by_macula_word", source)


if __name__ == "__main__":
    unittest.main()

