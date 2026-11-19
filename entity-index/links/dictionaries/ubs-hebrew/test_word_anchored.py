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

    def test_source_sdbh_owner_and_exact_lemma_recover_different_strong_entry_only(self):
        # An original sense ID and independently identical headword corroborate
        # a different-Strong UBS entry. Never infer a contextual sense.
        entry_a = entry("001695000000000", "דָּנִיֵּאל", ["A1840"])
        ix = build([entry_a], [entry_a])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o270020130061\tדָּנִיֵּאל\t001695001001000\t1841\tA\tnoun\n"
                "o270020130071\tדָּנִיֵּאל\t001695001001000\t1841\tH\tnoun\n"
                "o270020130081\tדָּנִיֵּאל\t001695001001000\t1841\tA\tprep\n",
                encoding="utf-8",
            )
            links = build_word_links(ix, [entry_a], source)
        self.assertEqual(list(links), ["o270020130061"])
        ix["by_macula_word"] = links
        out=lookup_word(ix,"o270020130061","001695001001000","1841","A","דָּנִיֵּאל")
        self.assertEqual(out["entry_ids"],[entry_a["MainId"]])
        self.assertEqual(out["sense_ids"],[])
        self.assertEqual(out["evidence"],"macula_word_exact_lemma_and_source_sdbh_ubs_owner_entry_only")

    def test_cross_strong_sdbh_collision_different_lemma_and_duplicate_owners_fail_closed(self):
        root=entry("001695000000000","דָּנִיֵּאל",["A1840"])
        wrong=entry("001696000000000","דָּנִיֵּאל",["A1842"])
        ix=build([root,wrong],[root,wrong])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o270020130061\tדָּנִיֵּאל\t001695001001000\t1841\tA\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix,[root,wrong],source),{})
        different=entry("001695000000000","רֹאשׁ",["A1840"])
        ix=build([different],[different])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o270020130061\tדָּנִיֵּאל\t001695001001000\t1841\tA\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix,[different],source),{})

    def test_consonantal_sdbh_owner_allows_entry_only_for_unique_headword(self):
        lemma=entry("000010000000000","יָלַד",["H3204"])
        ix=build([lemma],[lemma])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tיָלָד\t000010001001000\t3205\tH\tverb\n",
                encoding="utf-8",
            )
            links=build_word_links(ix,[lemma],source)
        self.assertEqual(links["o010010010011"]["entry_id"],lemma["MainId"])
        ix["by_macula_word"]=links
        out=lookup_word(ix,"o010010010011","000010001001000","3205","H","יָלָד")
        self.assertEqual(out["sense_ids"],[])
        self.assertEqual(out["evidence"],"macula_word_consonants_and_source_sdbh_ubs_owner_entry_only")

    def test_consonantal_sdbh_owner_rejects_homographs_and_language_mismatch(self):
        a=entry("000010000000000","יָלַד",["H3204"])
        b=entry("000011000000000","יָלְד",["H3206"])
        ix=build([a,b],[a,b])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tיָלָד\t000010001001000\t3205\tH\tverb\n"
                "o010010010021\tיָלָד\t000010001001000\t3205\tA\tverb\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix,[a,b],source),{})
        ix=build([a],[a])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"words.tsv"
            source.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tיָלָד\t000010001001000\t3205\tA\tverb\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix,[a],source),{})

    def test_original_ubs_alternate_lemma_matches_only_unique_strong_family(self):
        original=entry("000009000000000", "אֲבַדּוֹן", ["H11a"])
        original["AlternateLemmas"]=["אֲבַדּוֹ", "אֲבַדֹּה"]
        ix=build([original],[original])
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/"words.tsv"
            src.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tאֲבַדּוֹ\t\t0011\tH\tnoun\n"
                "o010010010021\tאֲבַדּוֹ\t\t0011\tA\tnoun\n"
                "o010010010031\tאֲבַדּוֹ\t\t0012\tH\tnoun\n",
                encoding="utf-8",
            )
            links=build_word_links(ix,[original],src)
        self.assertEqual(list(links),["o010010010011"])
        ix["by_macula_word"]=links
        out=lookup_word(ix,"o010010010011","","0011","H","אֲבַדּוֹ")
        self.assertEqual(out["entry_ids"],[original["MainId"]])
        self.assertEqual(out["sense_ids"],[])
        self.assertEqual(out["evidence"],"macula_word_ubs_published_alternate_lemma_same_strong_family")

    def test_alternate_headword_homographs_are_rejected(self):
        a=entry("000009000000000","אֲבַדּוֹן",["H11a"])
        b=entry("000010000000000","אֲבַדּ",["H11b"])
        a["AlternateLemmas"]=["אֲבַדּוֹ"]
        b["AlternateLemmas"]=["אֲבַדּוֹ"]
        ix=build([a,b],[a,b])
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/"words.tsv"
            src.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tאֲבַדּוֹ\t\t0011\tH\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(ix,[a,b],src),{})

    def test_published_ubs_alternate_plus_exact_sdbh_owner_cross_strong(self):
        source_entry = entry("000009000000000", "אֲבַדּוֹן", ["H11a"])
        source_entry["AlternateLemmas"] = ["אֲבַדּוֹ"]
        index = build([source_entry], [source_entry])
        with tempfile.TemporaryDirectory() as directory:
            macula = Path(directory) / "words.tsv"
            macula.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tאֲבַדּוֹ\t000009001001000\t0012\tH\tnoun\n",
                encoding="utf-8",
            )
            index["by_macula_word"] = build_word_links(index, [source_entry], macula)
        out = lookup_word(index, "o010010010011", "000009001001000", "0012", "H", "אֲבַדּוֹ")
        self.assertEqual(out["entry_ids"], [source_entry["MainId"]])
        self.assertEqual(out["sense_ids"], [])
        self.assertEqual(
            out["evidence"],
            "macula_word_ubs_alternate_lemma_and_source_sdbh_owner_entry_only",
        )

    def test_cross_strong_alternate_rejects_unowned_ids_and_homographs(self):
        e = entry("000009000000000", "אֲבַדּוֹן", ["H11a"])
        e["AlternateLemmas"] = ["אֲבַדּוֹ"]
        with tempfile.TemporaryDirectory() as directory:
            macula = Path(directory) / "words.tsv"
            macula.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tאֲבַדּוֹ\t000999001001000\t0012\tH\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(build([e], [e]), [e], macula), {})
            twin = entry("000010000000000", "אֲבַדּ", ["H10a"])
            twin["AlternateLemmas"] = ["אֲבַדּוֹ"]
            macula.write_text(
                "xml:id\tlemma\tsdbh\tstrongnumberx\tlang\tclass\n"
                "o010010010011\tאֲבַדּוֹ\t000009001001000\t0012\tH\tnoun\n",
                encoding="utf-8",
            )
            self.assertEqual(build_word_links(build([e, twin], [e, twin]), [e, twin], macula), {})

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
