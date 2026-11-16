"""Synthetic-only regression cases for generic original commentary layout census."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_layout_census import NativeCommentaryLayoutCensus, layout_profile, layout_flags


class CommentaryLayoutCensusTests(unittest.TestCase):
    def test_nested_paragraph_and_tail_text_are_counted_once(self):
        raw = (b"<title>Commentary title</title>"
               b"<p>One <hi type='bold'>two</hi> three.</p>"
               b"<p>Four five.</p>")
        profile = layout_profile(raw)
        self.assertEqual(profile["word_count"], 7)
        self.assertEqual(profile["paragraph_count"], 2)
        self.assertEqual(profile["heading_count"], 1)
        self.assertEqual(profile["unwrapped_word_count"], 0)
        self.assertEqual(profile["longest_paragraph_words"], 3)
        self.assertFalse(layout_flags(profile))

    def test_long_unwrapped_commentary_is_review_only(self):
        prose = " ".join("word" for _ in range(301)).encode()
        profile = layout_profile(b"<div type='section'>" + prose + b"</div>")
        self.assertEqual(profile["word_count"], 301)
        self.assertEqual(profile["paragraph_count"], 0)
        self.assertIn("long_prose_without_internal_block_markup",
                      layout_flags(profile))
        self.assertNotIn("substantial_text_without_div_table_p_line_title_note",
                         layout_flags(profile))
        self.assertNotIn("long_single_paragraph", layout_flags(profile))

        inline = layout_profile(b"<p>" + prose + b"</p>")
        self.assertEqual(inline["paragraph_count"], 1)
        self.assertIn("long_single_paragraph", layout_flags(inline))
        self.assertNotIn("long_prose_without_internal_block_markup",
                         layout_flags(inline))

    def test_division_layout_is_not_misclassified_as_absent_paragraphs(self):
        words = b" ".join([b"word"] * 160)
        source = (
            b"<div type='paragraph'>" + words + b"</div>"
            b"<div type='paragraph'>" + words + b"</div>"
            b"<table><row><cell>Original table material</cell></row></table>"
        )
        profile = layout_profile(source)
        self.assertEqual(profile["paragraph_count"], 0)
        self.assertEqual(profile["div_count"], 2)
        self.assertEqual(profile["table_count"], 1)
        self.assertEqual(profile["row_count"], 1)
        self.assertNotIn("long_prose_without_internal_block_markup",
                         layout_flags(profile))
        self.assertNotIn("substantial_text_without_div_table_p_line_title_note",
                         layout_flags(profile))

    def test_highlighted_original_verse_heading_is_not_unstyled(self):
        source = b"<hi type='bold'>Verses 2, 3.</hi><div>Original text.</div>"
        profile = layout_profile(source)
        self.assertTrue(profile["visible_numbered_verse_lead"])
        self.assertTrue(profile["styled_numbered_verse_lead"])
        self.assertNotIn("visible_verse_lead_without_title_or_hi_markup",
                         layout_flags(profile))

    def test_heading_fidelity_and_empty_structural_elements(self):
        plain = layout_profile(b"<div>Verses 1, 2. A section.</div>")
        self.assertTrue(plain["visible_numbered_verse_lead"])
        self.assertIn("visible_verse_lead_without_title_or_hi_markup", layout_flags(plain))
        styled = layout_profile(b"<title>Verses 1, 2.</title><p>A section.</p>")
        self.assertTrue(styled["visible_numbered_verse_lead"])
        self.assertNotIn("visible_verse_lead_without_title_or_hi_markup", layout_flags(styled))
        empty = layout_profile(b"<title/><p></p><p>Actual words</p>")
        self.assertEqual(empty["empty_headings"], 1)
        self.assertEqual(empty["empty_paragraphs"], 1)
        self.assertIn("empty_heading_markup", layout_flags(empty))

    def test_original_aliases_not_counted_as_separate_authorial_bodies(self):
        source = b"<p>Shared authored original text.</p>"
        c = NativeCommentaryLayoutCensus()
        c.observe("I", "Gen", b"<title>Book</title>")
        c.observe("I", "Gen.1", b"<chapter osisID='Gen.1'/>")
        c.observe("K", "Gen.1.1", source)
        c.observe("K", "Gen.1.2", source)
        c.observe("U", "TOP", b"opaque")
        result = c.report()
        self.assertEqual(result["original_native_K_seen"], 2)
        self.assertEqual(result["original_native_I_seen"], 2)
        self.assertEqual(result["original_native_TOP_seen"], 1)
        self.assertEqual(result["distinct_original_raw_bodies"], 3)
        self.assertEqual(result["repeated_raw_native_aliases"], 1)
        self.assertEqual(result["original_verse_one_only_chapters"], 0)
        self.assertFalse(result["source_word_text_xml_and_targets_disclosed"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn("Shared authored original text", str(result))

    def test_single_key_chapter_is_not_automatically_expanded(self):
        c = NativeCommentaryLayoutCensus()
        raw = b"<p>Plain original chapter commentary.</p>"
        c.observe("K", "Ps.108.1", raw)
        c.observe("K", "Gen.1.1", b"<p>Other chapter prose.</p>")
        c.observe("K", "Gen.1.2", b"<p>Independent commentary.</p>")
        result = c.report()
        self.assertEqual(result["original_verse_one_only_chapters"], 1)
        self.assertEqual(result["single_key_chapter_structure"][
            "single_key_chapter_raw_body_count"], 1)
        self.assertTrue(result["all_cases_are_unapproved_diagnostic_only"])

    def test_reject_malformed_or_unsafe_xml_without_export(self):
        c = NativeCommentaryLayoutCensus()
        for bad in (b"", b"<p>unterminated", b"<p>bad\x00null</p>",
                    b"<!DOCTYPE x [<!ENTITY e 'bad'>]><p>&e;</p>"):
            with self.subTest(bad=bad[:10]), self.assertRaises(ValueError):
                c.observe("K", "Gen.1.1", bad)
        with self.assertRaises(ValueError):
            c.observe("K", "Gen.1.0", b"<p>Correct prose.</p>")


if __name__ == "__main__":
    unittest.main()
