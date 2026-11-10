"""Main-text source USFX vs true stock-SWORD raw: synthetic-only regressions.

No published Bible language is reproduced in test fixtures or CI reports.
Full native libraries are exercised in the separate pinned real-WEBP workflow.
"""
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_native_maintext_probe import (
    _classify, authored_usfx_main_text, compare_private_main_text,
    native_raw_main_text, MainTextParityError,
)
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

PAIR = [("AAA", "Alpha"), ("BBB", "Beta")]


def original(body="first, beta!", extra=True):
    after = ('<book id="GLO"><p>other authored introduction</p></book>'
             if extra else "")
    return (f'<usfx><book id="AAA"><c id="1"/><s>heading</s>'
            f'<v id="1"/> {body}<f caller="a">unrelated note</f> tail'
            '<v id="2"/>other <em>words</em>!'
            '</book><book id="BBB"><c id="1"/><v id="1"/>third verse</book>'
            f'{after}</usfx>').encode("utf-8")


class AuthoredMainTextTests(unittest.TestCase):
    def test_original_usfx_main_content_notes_headings_and_extra_books(self):
        verses, facts = authored_usfx_main_text(original(), PAIR)
        self.assertEqual(verses, {
            "Alpha.1.1": " first, beta! tail",
            "Alpha.1.2": "other words!",
            "Beta.1.1": "third verse",
        })
        self.assertEqual(facts["unmapped_authored_book_count"], 1)
        self.assertEqual(facts["mapped_numbered_source_keys"], 3)
        self.assertEqual(
            facts["excluded_source_heading_or_note_element_counts"],
            {"f": 1, "s": 1})
        self.assertNotIn("unrelated note", json.dumps(facts))
        self.assertNotIn("heading", json.dumps(facts))

    def test_characters_change_without_verse_count_change(self):
        a, _ = authored_usfx_main_text(original(), PAIR)
        b, _ = authored_usfx_main_text(original(body="first; beta?"), PAIR)
        self.assertEqual(set(a), set(b))
        self.assertNotEqual(a["Alpha.1.1"], b["Alpha.1.1"])

    def test_source_verse_range_unsupported_not_silently_split(self):
        with self.assertRaises(MainTextParityError):
            authored_usfx_main_text(original().replace(
                b'<v id="2"/>', b'<v id="2-3"/>'), PAIR)

    def test_repeated_crosswalk_or_source_key_rejected(self):
        with self.assertRaises(MainTextParityError):
            authored_usfx_main_text(original(), PAIR + [("BBB", "Beta")])
        with self.assertRaises(MainTextParityError):
            authored_usfx_main_text(original().replace(
                b'<v id="2"/>', b'<v id="1"/>'), PAIR)

    def test_source_entity_is_semantic_character_and_note_tail_survives(self):
        source, _ = authored_usfx_main_text(
            original(body="word &amp; word"), PAIR)
        self.assertIn("word & word tail", source["Alpha.1.1"])
        self.assertNotIn("unrelated note", source["Alpha.1.1"])

    def test_dtd_and_broken_source_rejected(self):
        with self.assertRaises(ValueError):
            authored_usfx_main_text(
                b'<!DOCTYPE usfx [<!ENTITY bad "x">]>' + original(), PAIR)
        with self.assertRaises(ValueError):
            authored_usfx_main_text(original().replace(
                b"</usfx>", b"</wrong>"), PAIR)

    def test_extra_authorial_numbered_book_remains_visible_in_counts(self):
        raw = original().replace(
            b'<book id="GLO"><p>other authored introduction</p></book>',
            b'<book id="GLO"><c id="1"/><v id="1"/>other authored text</book>')
        _, report = authored_usfx_main_text(raw, PAIR)
        self.assertEqual(report["unmapped_authored_book_count"], 1)
        self.assertEqual(report["unmapped_numbered_source_keys"], 1)


class RawNativeCharacterTests(unittest.TestCase):
    def test_capture_visible_characters_and_exclude_notes_titles(self):
        raw = (b'<title>chapter title</title>'
               b'<p>first, <hi type="italic">beta</hi>!'
               b'<note type="footnote">not Scripture</note> tail</p>')
        chars, skipped = native_raw_main_text(raw)
        self.assertEqual(chars, "first, beta! tail")
        self.assertEqual(skipped, {"title": 1, "note": 1})

    def test_punctuation_mutation_not_exact_even_if_words_unchanged(self):
        self.assertEqual(_classify("first, beta!", "first; beta!"),
                         "word_sequence_same_punctuation_or_spacing_differs")
        self.assertEqual(_classify("first, beta!", "changed, beta!"),
                         "word_sequence_differs")

    def test_unicode_nfc_and_whitespace_are_separate_categories(self):
        self.assertEqual(_classify("caf\u00e9!", "cafe\u0301!"),
                         "unicode_normalization_only")
        self.assertEqual(_classify("foo  bar", "foo bar"), "whitespace_only")

    def test_compiled_unterminated_markup_and_dtd_are_blocked(self):
        for raw in (b"<hi>unterminated", b"<!DOCTYPE x>", b"word &unknown;",
                    b"<note>unfinished", b"<?xml version='1.0'?>"):
            with self.subTest(raw=raw[:10]), self.assertRaises(MainTextParityError):
                native_raw_main_text(raw)

    def test_note_text_never_supplies_false_bible_maintext_match(self):
        source = {"Alpha.1.1": "word should remain"}
        result = compare_private_main_text(source, {}, [
            ("Alpha.1.1", b"<note>word should remain</note>different")])
        self.assertEqual(
            result["classifications"]["word_sequence_differs"], 1)
        self.assertFalse(result["exact_mapped_numbered_maintext_semantic_characters_verified"])

    def test_exact_three_verses_prove_only_scoped_maintext(self):
        source = {"Alpha.1.1": "first, beta!", "Alpha.1.2": "other words!",
                  "Beta.1.1": "third verse"}
        records = [
            ("Alpha.1.1", b'<p>first, <hi>beta</hi>!</p>'),
            ("Alpha.1.2", b'other words!'),
            ("Beta.1.1", b'third verse'),
        ]
        out = compare_private_main_text(source, {}, records)
        self.assertEqual(
            out["status"], "all_mapped_numbered_maintext_characters_match_index_only")
        self.assertEqual(out["classifications"]["exact_semantic_characters"], 3)
        self.assertFalse(out["notes_strong_references_poetry_layout_verified"])
        self.assertNotIn("first, beta!", json.dumps(out))

    def test_source_only_and_native_only_differ_never_silently_pass(self):
        source = {"Alpha.1.1": "first", "Alpha.1.2": "second"}
        out = compare_private_main_text(source, {}, [
            ("Alpha.1.1", b"first"), ("Alpha.1.3", b"unexpected")])
        self.assertEqual(out["classifications"]["source_verses_without_native_indexed_entry"], 1)
        self.assertEqual(out["classifications"]["native_verse_without_same_indexed_source_key"], 1)
        self.assertEqual(out["first_source_only_refs"], ["Alpha.1.2"])
        self.assertFalse(out["exact_mapped_numbered_maintext_semantic_characters_verified"])

    def test_private_corpus_callback_never_reproduces_original_words_in_receipt(self):
        raw = b'<verse osisID="Alpha.1.1">only synthetic words</verse>'
        stream = (f"K\tAlpha.1.1\t{len(raw)}\n".encode("ascii")
                  + raw + b"S\t1\t1\t0\t0\n")
        observed = []
        receipt, keys, _intro, _top = parse_native_raw_corpus(
            io.BytesIO(stream),
            on_entry=lambda kind, key, entry: observed.append((kind, key, entry)))
        self.assertEqual(observed[0], ("K", "Alpha.1.1", raw))
        self.assertEqual(keys, ["Alpha.1.1"])
        self.assertNotIn("only synthetic words", json.dumps(receipt))

    def test_corrupted_raw_callback_cannot_pass(self):
        raw = b"bad"
        stream = b"K\tAlpha.1.1\t3\nbadS\t1\t1\t0\t0\n"
        def disallow(*_):
            raise MainTextParityError("private readback processing blocked")
        with self.assertRaises(MainTextParityError):
            parse_native_raw_corpus(io.BytesIO(stream), on_entry=disallow)


if __name__ == "__main__":
    unittest.main()
