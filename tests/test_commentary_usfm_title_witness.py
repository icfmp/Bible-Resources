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
    WitnessError, compare_original_first_paragraphs,
    compare_ambiguous_original_opening_paragraphs,
    compare_word_order_mismatch_opening_titles, independent_usfm_titles,
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
                    "single_matching_original_p_casefold_word_sha256":
                        sha256(" ".join(t.casefold() for t in tokens).encode("utf-8")).hexdigest(),
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
            "same_word_count_but_different_casefold_unicode_tokens": 1})

    def test_letter_case_variation_is_classified_without_text_edit(self):
        path, digest = self.make_archive(
            "\\id PSA\n\\c 7\n\\d To the chief Musician\n\\v 1 First\n")
        titles = independent_usfm_titles(path, digest, book_id="PSA")
        case = compare_original_first_paragraphs(
            metadata(7, ["to", "The", "CHIEF", "musician"]), titles, source_book="Ps")
        self.assertEqual(case["exact_original_title_case_classes"], {
            "same_unicode_word_tokens_after_only_casefold": 1})
        self.assertNotIn("CHIEF", json.dumps(case))
        self.assertFalse(case["matching_title_not_original_authorial_edition_or_redistribution_approval"] is False)

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

    def test_source_attested_nested_plusw_and_divine_name_title_markers(self):
        title=(
            r'To the \nd \+w LORD|strong="H3068"\+w*\nd*, '
            r'a \add psalm by \+w David|strong="H1732"\+w*\add*.'
        )
        visible=reviewed_usfm_title_visible_text(title)
        self.assertEqual(visible, "To the LORD, a psalm by David.")
        path,digest=self.make_archive(
            "\\id PSA\n\\c 7\n\\d "+title+"\n\\v 1 first\n")
        titles=independent_usfm_titles(path,digest,book_id="PSA")
        self.assertEqual(titles[7]["status"],"plain_original_d_title")
        result=compare_original_first_paragraphs(
            metadata(7,["To","the","LORD","a","psalm","by","David"]),
            titles,source_book="Ps")
        self.assertEqual(result["exact_original_title_case_classes"],{
            "exact_original_p1_equals_independent_usfm_d_title_word_tokens":1})
        self.assertNotIn("H3068",json.dumps(result))
        self.assertNotIn("LORD",json.dumps(result))
        self.assertNotIn("David",json.dumps(result))

    def test_unverified_usfm_markup_and_strongs_are_not_silently_removed(self):
        unsafe=[
            r'\w Musician|lemma="H5329"\w*',
            r'\w Musician|strong="H5329"|morph="He,N"\w*',
            r'\w Musician|strong="H5329"',
            r'\w Musician|strong="H5329"\add*',
            r'\add A Psalm\w David|strong="H1732"\w*\add*',
            r'\f + \fr 7.1 \ft note\f*',
            r'\w word|strong="H999999"\w*',
            r'\+w word|strong="H1234"\+w*',
            r'\nd \+w LORD|strong="H3068"\+w*',
            r'\nd \+w LORD|strong="H3068"\+w*\add*',
            r'\add word\nd*',
            r'\nd \w LORD|strong="H3068"\w*\nd*',
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
        case=output["original_chapter_source_sha_and_closed_verdict_only"][0]
        self.assertEqual(case["unsupported_usfm_inline_marker_shapes_only"], [
            r"\w", r"\w*"])
        self.assertNotIn("H1234",json.dumps(output))
        self.assertNotIn("Psalm",json.dumps(output))
        misplaced, pin = self.make_archive("\\id PSA\n\\c 3\n\\v 1 first\n\\d A Psalm\n")
        with self.assertRaises(WitnessError):
            independent_usfm_titles(misplaced, pin, book_id="PSA")

    def test_ambiguous_native_alignment_still_permits_separate_title_identity(self):
        path,digest=self.make_archive(
            "\\id PSA\n\\c 7\n\\d To the chief Musician\n\\v 1 First\n")
        titles=independent_usfm_titles(path,digest,book_id="PSA")
        words=["to","the","chief","musician"]
        report=metadata(7,words)
        scope=report["source_longer_both_source_and_native_reference_label_word_scope"]
        scope["original_book_source_extra_original_p_digest_case_classes"]["Ps"]={
            "ambiguous_extra_source_words_no_unique_gap_ownership":1}
        case=scope["source_extra_original_p_digest_source_line_sha_only_rows"][0]
        case["source_extra_p_digest_case_class"]=(
            "ambiguous_extra_source_words_no_unique_gap_ownership")
        case["all_extra_gap_full_original_p_digest_candidate_classes"]=[]
        case.update({
            "original_opening_p_document_ordinal":1,
            "original_opening_p_visible_word_count":len(words),
            "original_opening_p_exact_unicode_word_sha256":
                sha256(" ".join(words).encode("utf-8")).hexdigest(),
            "original_opening_p_casefold_unicode_word_sha256":
                sha256(" ".join(w.casefold() for w in words).encode("utf-8")).hexdigest(),
        })
        result=compare_ambiguous_original_opening_paragraphs(
            report,titles,source_book="Ps")
        self.assertEqual(result["original_source_extra_ambiguous_alignment_cases"],1)
        self.assertEqual(result["independent_original_opening_p_title_classes"],{
            "opening_p_casefold_biblical_title_tokens_but_gap_ownership_ambiguous":1})
        self.assertTrue(result["opening_title_match_never_resolves_extra_word_alignment"])
        self.assertNotIn("musician",json.dumps(result))
        case["original_opening_p_document_ordinal"]=2
        with self.assertRaises(WitnessError):
            compare_ambiguous_original_opening_paragraphs(
                report,titles,source_book="Ps")

    def test_separate_native_word_order_case_can_match_biblical_title_only(self):
        path,digest=self.make_archive(
            "\\id PSA\n\\c 8\n\\d To the chief Musician\n\\v 1 First\n")
        titles=independent_usfm_titles(path,digest,book_id="PSA")
        words=["to","the","chief","musician"]
        report=metadata(8,words)
        scope=report["source_longer_both_source_and_native_reference_label_word_scope"]
        scope["original_book_unlinked_word_relation_classes"]={
            "Ps":{"plain_word_order_or_selection_requires_editorial_review":1}}
        scope["original_line_SHA_and_two_sided_link_word_metadata_only_rows"]=[{
            "source_book":"Ps",
            "outside_link_word_relation":
                "plain_word_order_or_selection_requires_editorial_review",
            "original_source_chapter_number_from_actual_osis_start":8,
            "original_full_reference_sha256":sha256(b"original psalm ref").hexdigest(),
            "original_first_p_visible_word_identity_only":{
                "original_p_document_ordinal":1,
                "visible_words":4,
                "exact_unicode_word_sha256":
                    sha256(" ".join(words).encode()).hexdigest(),
                "casefold_unicode_word_sha256":
                    sha256(" ".join(w.casefold() for w in words).encode()).hexdigest(),
            },
        }]
        result=compare_word_order_mismatch_opening_titles(
            report,titles,source_book="Ps")
        self.assertEqual(result["independent_title_opening_comparison_classes"],{
            "opening_p_casefold_matches_title_but_native_order_mismatch_open":1})
        self.assertTrue(
            result["title_matches_never_resolve_original_native_word_order_selection"])
        self.assertNotIn("musician",json.dumps(result))
        scope["original_line_SHA_and_two_sided_link_word_metadata_only_rows"][0][
            "original_first_p_visible_word_identity_only"]["visible_words"]=0
        with self.assertRaises(WitnessError):
            compare_word_order_mismatch_opening_titles(
                report,titles,source_book="Ps")

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
