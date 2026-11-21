#!/usr/bin/env python3
"""Regression checks for Greek UBS bilingual lexical crosswalk."""
import json
import runpy
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
mod=runpy.run_path(str(ROOT/"build_index.py"))
build=mod["build"]
lookup=mod["lookup"]


def record(mid, lemma, strong, code, lex_id, lang):
    return {
        "MainId": mid, "Lemma": lemma, "StrongCodes": strong,
        "BaseForms": [{"LEXMeanings": [{
            "LEXID": lex_id, "LEXEntryCode": code,
            "LEXSenses": [{"LanguageCode": lang, "DefinitionShort": "different language"}]
        }]}],
    }


class UBSCrosswalkTests(unittest.TestCase):
    def test_shared_ids_support_both_languages_without_copying_definitions(self):
        en=[record("entry-a","λόγος",["G3056"],"33.98","sense-a","en")]
        fr=[record("entry-a","λόγος",["G3056"],"33.98","sense-a","fr")]
        output=build(en,fr)
        self.assertEqual(output["by_strong"]["3056"], ["entry-a"])
        self.assertEqual(output["by_ln"]["33.98"], [["entry-a","sense-a"]])
        self.assertEqual(lookup(output,"3056","33.98")["sense_ids"], ["sense-a"])
        self.assertNotIn("different language", json.dumps(output))
        self.assertEqual(output["languages"], ["en","fr"])

    def test_bilingual_sense_id_drift_is_rejected(self):
        en=[record("entry-a","λόγος",["G3056"],"33.98","sense-a","en")]
        fr=[record("entry-a","λόγος",["G3056"],"33.98","sense-b","fr")]
        with self.assertRaisesRegex(ValueError,"English and French IDs differ"):
            build(en,fr)

    def test_multiple_lexemes_not_silently_collapsed(self):
        en=[
            record("entry-a","λόγος",["G3056"],"33.98","sense-a","en"),
            record("entry-b","λόγος",["G3056"],"33.99","sense-b","en"),
        ]
        fr=[
            record("entry-a","λόγος",["G3056"],"33.98","sense-a","fr"),
            record("entry-b","λόγος",["G3056"],"33.99","sense-b","fr"),
        ]
        index=build(en,fr)
        result=lookup(index,"3056","33.98")
        self.assertEqual(result["status"],"ambiguous_entry")
        self.assertEqual(result["entry_ids"],["entry-a","entry-b"])
        self.assertEqual(result["sense_ids"],["sense-a"])
        # A semantic domain belonging to a different lexeme is never substituted.
        self.assertEqual(lookup(index,"3056","50.1")["sense_ids"], [])

    def test_strong_suffix_and_compound_strongs_are_not_guessed(self):
        en=[record("entry-a","λόγος",["G3056a"],"33.98","sense-a","en")]
        fr=[record("entry-a","λόγος",["G3056a"],"33.98","sense-a","fr")]
        index=build(en,fr)
        self.assertEqual(index["statistics"]["excluded_suffixed_strong_codes"],1)
        self.assertEqual(lookup(index,"3056","33.98")["status"],"no_entry_match")
        self.assertEqual(lookup(index,"3056+123","33.98")["status"],"unsupported_strong_structure")

    def test_real_output_available_and_keyterm_free(self):
        index=json.loads((ROOT/"index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["statistics"]["shared_entries"],5507)
        self.assertEqual(index["statistics"]["shared_senses"],9160)
        self.assertEqual(index["coverage"]["macula_words"],137741)
        self.assertEqual(index["coverage"]["with_ubs_entry_candidates"],128090)
        self.assertEqual(index["dictionary"]["edition"],"1.0")
        self.assertNotIn("keyterm:",json.dumps(index))
        self.assertIn("002427000000000", index["by_strong"]["2424"])
        self.assertEqual(index["by_ln"]["93.169a"],[["002427000000000","002427001001000"]])


if __name__ == "__main__":
    unittest.main()
