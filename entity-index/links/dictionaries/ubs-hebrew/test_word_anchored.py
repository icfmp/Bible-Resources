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
            out["evidence"], "macula_word_exact_lemma_unique_entry_within_ubs_strong_family"
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

    def test_unique_exact_lemma_is_selected_within_family(self):
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
        self.assertEqual(result["o010010010011"]["entry_id"], voice["MainId"])

    def test_different_lemmas_within_same_strong_family_are_resolved(self):
        # Homonymous Strong numeric families can split by actual lemma.
        voice = entry("000001000000000", "קוֹל", ["H6963a"])
        sound = entry("000002000000000", "קֹל", ["H6963b"])
        other = entry("000003000000000", "שִׁיר", ["H7892a"])
        ix = build([voice, sound, other], [voice, sound, other])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקוֹל\t\t6963\tH\tnoun\n"
                "o010010010021\tקֹל\t\t6963\tH\tnoun\n",
                encoding="utf-8",
            )
            links = build_word_links(ix, [voice, sound, other], source)
        self.assertEqual(links["o010010010011"]["entry_id"], voice["MainId"])
        self.assertEqual(links["o010010010021"]["entry_id"], sound["MainId"])

    def test_identical_homograph_lemma_stays_ambiguous(self):
        a = entry("000001000000000", "קוֹל", ["H6963a"])
        b = entry("000002000000000", "קוֹל", ["H6963b"])
        ix = build([a, b], [a, b])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקוֹל\t\t6963\tH\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix, [a, b], source), {})

    def test_verb_vocalization_only_same_strong_family(self):
        root = entry("000010000000000", "ילד", ["H3205a"])
        ix = build([root], [root])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tיָלַד\t\t3205\tH\tverb\n"
                "o010010010021\tיָלַד\t\t3205\tH\tnoun\n",
                encoding="utf-8",
            )
            ix["by_macula_word"] = build_word_links(ix, [root], source)
        self.assertEqual(list(ix["by_macula_word"]), ["o010010010011", "o010010010021"])
        out = lookup_word(ix, "o010010010011", "", "3205", "H", "יָלַד")
        self.assertEqual(out["entry_ids"], [root["MainId"]])
        self.assertEqual(out["sense_ids"], [])
        self.assertEqual(
            out["evidence"],
            "macula_word_verb_consonants_unique_entry_same_strong_family",
        )
        self.assertEqual(
            lookup_word(ix, "o010010010011", "", "3205", "H", "יַלַד")["status"],
            "source_word_mismatch",
        )

    def test_verb_shin_sin_and_homographs_remain_distinct(self):
        shin = entry("000010000000000", "שׁבר", ["H7665a"])
        sin = entry("000011000000000", "שׂבר", ["H7665b"])
        ix = build([shin, sin], [shin, sin])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tשָׁבַר\t\t7665\tH\tverb\n"
                "o010010010021\tשָׂבַר\t\t7665\tH\tverb\n",
                encoding="utf-8",
            )
            links = build_word_links(ix, [shin, sin], source)
        self.assertEqual(links["o010010010011"]["entry_id"], shin["MainId"])
        self.assertEqual(links["o010010010021"]["entry_id"], sin["MainId"])
        conflicting = entry("000012000000000", "שׁבר", ["H7665c"])
        ix = build([shin, sin, conflicting], [shin, sin, conflicting])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tשָׁבַר\t\t7665\tH\tverb\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix, [shin, sin, conflicting], source), {})

    def test_nonverb_vocalization_same_strong_and_original_word_only(self):
        item = entry("000020000000000", "קול", ["H6963a"])
        ix = build([item], [item])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקוֹל\t\t6963\tH\tnoun\n"
                "o010010010021\tקוֹל\t\t6963\tH\tadj\n"
                "o010010010031\tקוֹל\t\t6963\tH\tadv\n"
                "o010010010041\tקוֹל\t\t6963\tH\tptcl\n",
                encoding="utf-8",
            )
            ix["by_macula_word"] = build_word_links(ix, [item], source)
        self.assertEqual(len(ix["by_macula_word"]), 3)
        for wid in ("o010010010011", "o010010010021", "o010010010031"):
            response = lookup_word(ix, wid, "", "6963", "H", "קוֹל")
            self.assertEqual(response["entry_ids"], [item["MainId"]])
            self.assertEqual(response["sense_ids"], [])
            self.assertEqual(
                response["evidence"],
                "macula_word_nonverb_consonants_unique_entry_same_strong_family",
            )
        self.assertEqual(
            lookup_word(ix, "o010010010041", "", "6963", "H", "קוֹל")["entry_ids"],
            [],
        )

    def test_nonverb_consonantal_homographs_remain_unresolved(self):
        first = entry("000020000000000", "קָרְבָּן", ["H7133a"])
        second = entry("000021000000000", "קֻרְבָּן", ["H7133b"])
        ix = build([first, second], [first, second])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tקׇרְבָּן\t\t7133\tH\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix, [first, second], source), {})

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
