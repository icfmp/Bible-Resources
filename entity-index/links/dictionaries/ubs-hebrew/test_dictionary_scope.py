#!/usr/bin/env python3
"""Synthetic checks for edition-scope denominator classifications."""
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
buildmod=runpy.run_path(str(HERE/"build_index.py"))
auditmod=runpy.run_path(str(HERE/"audit_dictionary_scope.py"))
build=buildmod["build"]
analyze=auditmod["analyze"]

def make(mid,lemma,strong):
    return {"MainId":mid,"Lemma":lemma,"StrongCodes":strong,
        "BaseForms":[{"LEXMeanings":[{"LEXID":mid[:6]+"001001000","LEXEntryCode":""}]}]}

class DictionaryScopeTests(unittest.TestCase):
    def test_unmatched_different_strong_does_not_prove_absence(self):
        a=make("000001000000000","כֹּל",["H3606"])
        b=make("000002000000000","קוֹל",["H6963a"])
        en=[a,b]
        index=build(en,en)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source.tsv"
            p.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\tref\n"
                "o010010010011\tכֹּל\t\t3605\tH\tnoun\tGEN 1:1!1\n"
                "o010010010021\tיָלַד\t\t3205\tH\tverb\tGEN 1:1!2\n"
                "o010010010031\tקוֹל\t\t6963\tH\tnoun\tGEN 1:1!3\n",
                encoding="utf-8")
            index["by_macula_word"] = buildmod["build_word_links"](index,en,p)
            result=analyze(index,en,p)
        c=result["summary"]
        self.assertEqual(c["different_strong_same_exact_headword_review"],1)
        self.assertEqual(c["no_matching_strong_or_headword_in_ubs_inventory"],1)
        self.assertEqual(c["linked_occurrences"],1)
        self.assertEqual(c["indexable_scope_denominator"],2)
        self.assertEqual(c["indexable_scope_unresolved"],1)
        self.assertEqual(c["indexable_scope_coverage_pct"],50)

    def test_ubs_published_alternate_lemma_is_not_marked_absent(self):
        entry=make("000001000000000","כֻּלָּם",["H9999"])
        entry["AlternateLemmas"]=["כֹּל"]
        ix=build([entry],[entry])
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\tref\n"
                "o010010010011\tכֹּל\t\t3605\tH\tnoun\tGEN 1:1!1\n",
                encoding="utf-8",
            )
            ix["by_macula_word"]={}
            out=analyze(ix,[entry],source)
        self.assertEqual(out["summary"]["outside_indexed_ubs_headword_scope"],0)
        self.assertEqual(out["summary"]["different_strong_same_exact_headword_review"],1)
        self.assertEqual(out["summary"]["indexable_scope_denominator"],1)

    def test_shin_and_sin_do_not_share_inventory_identity(self):
        a=make("000001000000000","שׁבר",["H7665"])
        en=[a]
        idx=build(en,en)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"words.tsv"
            p.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\tref\n"
                "o010010010011\tשָׂבַר\t\t7666\tH\tverb\tGEN 1:1!1\n",
                encoding="utf-8")
            idx["by_macula_word"] = {}
            result=analyze(idx,en,p)
        self.assertEqual(result["summary"]["outside_indexed_ubs_headword_scope"],1)

if __name__=="__main__":
    unittest.main()
