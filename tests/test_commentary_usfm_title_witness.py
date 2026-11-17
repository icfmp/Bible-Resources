"""Synthetic metadata-only independent USFM superscription/source-paragraph audit."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_usfm_title_witness import (
    WitnessError, compare_original_first_paragraphs, independent_usfm_titles,
    reviewed_usfm_title_visible_text,
)


def metadata(chapter: int, tokens: list[str]) -> dict:
    return {
        "original_source_words_or_binaries_exported": False,
        "source_longer_both_source_and_native_reference_label_word_scope": {
            "excluded_only_original_scripRef_and_real_native_reference_labels": True,
            "original_book_source_extra_original_p_digest_case_classes": {
                "Ps": {"at_least_one_unique_entire_original_p_visible_word_match": 1}
            },
            "source_extra_original_p_digest_source_line_sha_only_rows": [{
                "original_book": "Ps",
                "source_extra_p_digest_case_class":
                    "at_least_one_unique_entire_original_p_visible_word_match",
                "original_source_chapter_number_from_actual_osis_start": chapter,
                "original_full_reference_sha256":
                    sha256(b"original source chapter reference").hexdigest(),
                "all_extra_gap_full_original_p_digest_candidate_classes": [{
                    "single_matching_original_p_document_ordinal": 1,
                    "distinct_full_original_p_exact_visible_word_matches": 1,
                    "single_matching_original_p_exact_unicode_word_sha256":
                        sha256(" ".join(tokens).encode("utf-8")).hexdigest(),
                    "original_extra_unlinked_word_count": len(tokens),
                }],
            }],
        },
    }


class IndependentBiblicalTitleWitnessTests(unittest.TestCase):
    def make_archive(self, body: str):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "independent-usfm.zip"
        with ZipFile(path, "w") as zipped:
            zipped.writestr("eng-kjv/19PSA.usfm", body)
            zipped.writestr("eng-kjv/01GEN.usfm", "\\id GEN\n\\c 1\n\\v 1 in\n")
        return path, sha256(path.read_bytes()).hexdigest()

    def test_exact_title_and_metadata_only_report(self):
        path, digest = self.make_archive(
            "\\id PSA\n\\c 3\n"
            "\\d A Psalm of David, when he fled from his son Absalom.\n"
            "\\v 1 LORD, how\n\\c 4\n\\d To the chief Musician on Neginoth.\n"
            "\\v 1 Hear me\n")
        titles = independent_usfm_titles(path, digest, book_id="PSA")
        self.assertEqual(set(titles), {3, 4})
        tokens = "A Psalm of David when he fled from his son Absalom".split()
        result = compare_original_first_paragraphs(
            metadata(3, tokens), titles, source_book="Ps")
        self.assertEqual(result["exact_original_title_case_classes"], {
            "exact_original_p1_equals_independent_usfm_d_title_word_tokens": 1})
        self.assertEqual(result["original_first_paragraph_cases_checked"], 1)
        self.assertNotIn("Absalom", json.dumps(result))
        self.assertNotIn("Neginoth", json.dumps(result))
        self.assertFalse(result["source_or_bible_text_or_native_verse_keys_exported"])
        changed = compare_original_first_paragraphs(
            metadata(4, tokens), titles, source_book="Ps")
        self.assertEqual(changed["exact_original_title_case_classes"], {
            "source_p1_and_usfm_d_title_word_counts_differ": 1})

    def test_unmatched_equal_word_count_is_not_accepted(self):
        path, digest = self.make_archive("\\id PSA\n\\c 7\n\\d To the chief Musician\n\\v 1 First\n")
        titles = independent_usfm_titles(path, digest, book_id="PSA")
        result = compare_original_first_paragraphs(
            metadata(7, ["To", "the", "chief", "MusicianX"]),
            titles, source_book="Ps")
        self.assertEqual(result["exact_original_title_case_classes"], {
            "same_word_count_but_different_case_sensitive_unicode_tokens": 1})

    def test_original_strongs_and_translator_additions_preserve_displayed_title(self):
        rendered=r'To the chief \w Musician|strong="H5329"\w*, \add A Psalm\add* of \w David|strong="H1732"\w*.'
        visible=reviewed_usfm_title_visible_text(rendered)
        self.assertEqual(visible,"To the chief Musician, A Psalm of David.")
        self.assertNotIn("5329",visible)
        self.assertNotIn("strong",visible)
        path,digest=self.make_archive(
            "\\id PSA\n\\c 7\n\\d "+rendered+"\n\\v 1 first\n")
        titles=independent_usfm_titles(path,digest,book_id="PSA")
        self.assertEqual(titles[7]["status"],"plain_original_d_title")
        words=["To","the","chief","Musician","A","Psalm","of","David"]
        result=compare_original_first_paragraphs(
            metadata(7,words),titles,source_book="Ps")
        self.assertEqual(result["exact_original_title_case_classes"],{
            "exact_original_p1_equals_independent_usfm_d_title_word_tokens":1})
        self.assertNotIn("Music",json.dumps(result))
        self.assertNotIn("David",json.dumps(result))
        self.assertNotIn("H5329",json.dumps(result))

    def test_unverified_usfm_markup_and_strongs_are_not_silently_removed(self):
        unsafe=[
            r'\w Musician|lemma="H5329"\w*',
            r'\w Musician|strong="H5329"|morph="He,N"\w*',
            r'\w Musician|strong="H5329"',
            r'\w Musician|strong="H5329"\add*',
            r'\add A Psalm\w David|strong="H1732"\w*\add*',
            r'\f + \fr 7.1 \ft note\f*',
            r'\nd LORD\nd*',
            r'\w word|strong="H999999"\w*',
        ]
        for title in unsafe:
            with self.subTest(title=title):
                self.assertIsNone(reviewed_usfm_title_visible_text(title))
        self.assertIsNone(reviewed_usfm_title_visible_text(""))
        self.assertIsNone(reviewed_usfm_title_visible_text("A"*8193))

    def test_pinned_zip_and_unreviewed_markup_fail_closed(self):
        path, digest = self.make_archive("\\id PSA\n\\c 3\n\\d A Psalm\n\\v 1 LORD\n")
        with self.assertRaises(WitnessError):
            independent_usfm_titles(path, "0" * 64, book_id="PSA")
        with self.assertRaises(WitnessError):
            independent_usfm_titles(path, digest, book_id="XXX")
        altered, sha = self.make_archive(
            "\\id PSA\n\\c 3\n\\d A \\w Psalm|lemma=H1234\\w*\n\\v 1 LORD\n")
        titles = independent_usfm_titles(altered, sha, book_id="PSA")
        output = compare_original_first_paragraphs(
            metadata(3, ["A", "Psalm"]), titles, source_book="Ps")
        self.assertEqual(output["exact_original_title_case_classes"], {
            "unreviewed_inline_usfm_d_title": 1})
        misplaced, pin = self.make_archive("\\id PSA\n\\c 3\n\\v 1 first\n\\d A Psalm\n")
        with self.assertRaises(WitnessError):
            independent_usfm_titles(misplaced, pin, book_id="PSA")

    def test_exact_original_chapter_and_count_reconciliation_are_mandatory(self):
        path, digest = self.make_archive("\\id PSA\n\\c 3\n\\d A Psalm\n\\v 1 LORD\n")
        titles = independent_usfm_titles(path, digest, book_id="PSA")
        report = metadata(3, ["A", "Psalm"])
        entries = report[
            "source_longer_both_source_and_native_reference_label_word_scope"
        ]["source_extra_original_p_digest_source_line_sha_only_rows"]
        entries.append(dict(entries[0]))
        with self.assertRaises(WitnessError):
            compare_original_first_paragraphs(report, titles, source_book="Ps")
        report = metadata(3, ["A", "Psalm"])
        del report[
            "source_longer_both_source_and_native_reference_label_word_scope"
        ]["source_extra_original_p_digest_source_line_sha_only_rows"][0][
            "original_source_chapter_number_from_actual_osis_start"]
        with self.assertRaises(WitnessError):
            compare_original_first_paragraphs(report, titles, source_book="Ps")


if __name__ == "__main__":
    unittest.main()
