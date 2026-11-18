#!/usr/bin/env python3
"""Synthetic safeguards for source-anchored UBS Hebrew entry-only reconciliation."""
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
mod = runpy.run_path(str(HERE / "build_index.py"))
build = mod["build"]
build_word_links = mod["build_word_links"]
lookup_word = mod["lookup_word"]


def entry(mid, lemma, codes):
    return {
        "MainId": mid, "Lemma": lemma, "StrongCodes": codes,
        "BaseForms": [{"LEXMeanings": [{
            "LEXID": mid[:6] + "001001000", "LEXEntryCode": ""
        }]}],
    }


class OriginalWordAnchoredLinksTest(unittest.TestCase):
    def test_exact_lemma_unique_family_and_strict_word_anchor(self):
        voice = entry("000001000000000", "קוֹל", ["H6963a"])
        other = entry("000002000000000", "טוֹב", ["H2896a"])
        records = [voice, other]
        ix = build(records, records)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקוֹל\t\t6963\tH\tnoun\n"
                "o010010010021\tקוֹל\t\t6963\tA\tnoun\n"
                "o010010010031\tקֹל\t\t6963\tH\tnoun\n"
                "o010010010041\tקוֹל\t\t6963\tH\tcj\n",
                encoding="utf-8",
            )
            ix["by_macula_word"] = build_word_links(ix, records, source)
        self.assertEqual(list(ix["by_macula_word"]), ["o010010010011"])
        out = lookup_word(ix, "o010010010011", "", "6963", "H", "קוֹל")
        self.assertEqual(out["status"], "entry_only")
        self.assertEqual(out["entry_ids"], [voice["MainId"]])
        self.assertEqual(out["sense_ids"], [])
        self.assertEqual(
            out["evidence"], "macula_word_exact_lemma_unique_ubs_strong_family"
        )
        self.assertEqual(
            lookup_word(ix, "o010010010011", "", "6963a", "H", "קוֹל")["evidence"],
            "macula_strong_exact_only",
        )
        self.assertEqual(
            lookup_word(ix, "o010010010011", "", "6964", "H", "קוֹל")["status"],
            "source_word_mismatch",
        )
        self.assertEqual(
            lookup_word(ix, "o010010010011", "", "6963", "H", "קֹל")["status"],
            "source_word_mismatch",
        )
        self.assertEqual(
            lookup_word(ix, "o010010010021", "", "6963", "A", "קוֹל")["entry_ids"],
            [],
        )

    def test_ubs_family_ambiguous_even_if_only_one_same_lemma(self):
        voice = entry("000001000000000", "קוֹל", ["H6963a"])
        different = entry("000002000000000", "קֹל", ["H6963b"])
        ix = build([voice, different], [voice, different])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקוֹל\t\t6963\tH\tnoun\n",
                encoding="utf-8",
            )
            result = build_word_links(ix, [voice, different], source)
        self.assertEqual(result, {})

    def test_no_promotion_of_sense_id_collision(self):
        wrong = entry("006653000000000", "רֹאשׁ", ["H7218"])
        right = entry("006660000000000", "רֵאשִׁית", ["H7225a"])
        ix = build([wrong, right], [wrong, right])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tרֵאשִׁית\t006653001001000\t7225\tH\tnoun\n",
                encoding="utf-8",
            )
            ix["by_macula_word"] = build_word_links(ix, [wrong, right], source)
        out = lookup_word(ix, "o010010010011", "006653001001000", "7225",
                          "H", "רֵאשִׁית")
        self.assertEqual(out["entry_ids"], [right["MainId"]])
        self.assertEqual(out["sense_ids"], [])


if __name__ == "__main__":
    unittest.main()
