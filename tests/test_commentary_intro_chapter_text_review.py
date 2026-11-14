"""Synthetic-only original intro and verse-slot text location tests."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_intro_chapter_text_review import (
    review_original_intro_against_numbered_chapter,
    independent_thml_chapter_intro_witness,
)
from lxml import etree


class OriginalIntroTextLocationTests(unittest.TestCase):
    def test_full_intro_prose_can_be_present_only_in_intro(self):
        report = review_original_intro_against_numbered_chapter(
            "Gen.1",
            b'<chapter osisID="Gen.1"/><div type="section"/>'
            b'Original invented introductory words here.',
            [("Gen.1.1", b'<p>Different invented verse explanation.</p>'),
             ("Gen.1.2", b'<p>Another distinct verse explanation.</p>')],
        )
        self.assertEqual(report["original_intro_unicode_word_count"], 5)
        self.assertFalse(report["full_original_intro_visible_text_in_a_numbered_body"])
        self.assertEqual(report["original_intro_text_runs_of_at_least_three_words"], 1)
        self.assertEqual(report["runs_not_exactly_repeated_in_numbered_body"], 1)
        self.assertEqual(report["unmatched_intro_text_owning_element_classes"],
                         {"div_tail":1})
        self.assertFalse(report["original_intro_text_deleted_or_reassigned"])

    def test_repeated_intro_prose_is_observed_not_deleted(self):
        intro=b'<chapter osisID="Gen.1"/>Shared invented introductory content.'
        report = review_original_intro_against_numbered_chapter(
            "Gen.1", intro,
            [("Gen.1.1", b'<p>Shared invented introductory content.</p>')]
        )
        self.assertTrue(report["full_original_intro_visible_text_in_a_numbered_body"])
        self.assertEqual(report["runs_exactly_repeated_in_numbered_body"], 1)
        self.assertFalse(report["original_full_chapter_commentary_coverage_proven"])

    def test_no_verse_slot_keeps_intro_text_unassigned(self):
        report=review_original_intro_against_numbered_chapter(
            "Ps.108", b'<div type="section"/>Unmatched invented psalm introduction.',
            []
        )
        self.assertEqual(report["numbered_keys_present_in_original_chapter"], 0)
        self.assertEqual(report["runs_not_exactly_repeated_in_numbered_body"], 1)

    def test_independent_annotation_locates_intro_without_edit_permission(self):
        doc=etree.fromstring(
            b'<root><div2><h2>Chapter 19</h2>'
            b'<scripCom osisRef="Bible:Lev.19"/>'
            b'<p>Invented explanation for the whole chapter.</p>'
            b'</div2></root>'
        )
        witness=independent_thml_chapter_intro_witness(
            doc, {"Lev.19":
                b'<chapter osisID="Lev.19"/>'
                b'<div type="original"/>Invented explanation for the whole chapter.'
            }
        )
        row=witness["case_rows"][0]
        self.assertEqual(row["independent_explicit_chapter_annotation_div2_count"],1)
        self.assertTrue(row["native_intro_full_word_sequence_is_in_source_div2"])
        self.assertFalse(row["original_original_source_scope_approved"])
        self.assertFalse(witness["chapter_scope_and_verse_navigation_approved"])

    def test_unannotated_source_is_not_a_verified_chapter_witness(self):
        doc=etree.fromstring(
            b'<root><div2><h2>Chapter 19</h2><p>Invented explanation.</p></div2></root>'
        )
        witness=independent_thml_chapter_intro_witness(
            doc, {"Lev.19": b'<div/>Invented explanation.'}
        )
        self.assertEqual(witness["case_rows"][0]["status"],
                         "NO_UNIQUE_PINNED_THML_CHAPTER_ANNOTATION")
        self.assertFalse(witness["case_rows"][0]["original_original_source_scope_approved"])

    def test_reject_wrong_chapter_or_nonnumeric_intro(self):
        for name, slot in (
            ("Gen", "Gen.1.1"),
            ("Gen.1", "Exod.1.1"),
            ("Gen.1", "Gen.2.1")
        ):
            with self.assertRaises(ValueError):
                review_original_intro_against_numbered_chapter(
                    name, b'<div/>Invented passage words',
                    [(slot, b'<p>Invented</p>')]
                )


if __name__=="__main__":
    unittest.main()
