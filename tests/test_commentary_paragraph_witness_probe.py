"""Invented cross-edition ThML paragraph-locator samples; no historical prose."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_paragraph_witness_probe import compare_paragraph_witness


def document(body: bytes):
    return etree.fromstring(b"<root>" + body + b"</root>").getroottree()


class ParagraphWitnessProbeTest(unittest.TestCase):
    def test_source_section_p_boundaries_have_unique_original_lexical_offsets(self):
        a = b"These eight or more distinct words mark the first source paragraph clearly"
        b = b"Another completely distinct group of original words shows the second paragraph boundary"
        source = document(
            b"<div1><div2><p><scripCom osisRef='Bible:John.3.1-John.3.4'/>"
            + a + b"</p><p>" + b + b"</p>"
            b"<p><scripCom osisRef='Bible:John.3.5-John.3.7'/>"
            b"Following passage after the next marker remains independent</p>"
            b"</div2></div1>")
        original = b"<div type='wrapper'/><hi>Verses 1-4</hi> " + a + b" " + b
        result = compare_paragraph_witness(source, [("K", "John.3.1", original)])
        self.assertEqual(result["selected_original_native_I_K_entries"], 1)
        self.assertFalse(result["source_text_xml_annotation_attributes_exported"])
        self.assertFalse(result["public_release_authorized"])
        row = result["results"][0]
        self.assertEqual(row["status"], "SOURCE_CHAPTER_SECTION_MARKER_LOCATED")
        self.assertEqual(row["source_chapter_scripcom_count"], 2)
        self.assertTrue(row["marker_inside_p"])
        self.assertEqual(row["candidate_source_section_p_count"], 2)
        self.assertEqual(row["paragraphs_with_both_unique_8_word_anchors"], 2)
        self.assertLess(row["source_paragraph_lexical_anchors"][0][
            "unique_native_start_token_offset"], row["source_paragraph_lexical_anchors"][1][
                "unique_native_start_token_offset"])
        self.assertNotIn("distinct words", str(result))
        self.assertNotIn("another", str(result))

    def test_chapter_intro_annotation_can_be_compared_without_moving_I_prose(self):
        a = b"Original introduction has a long independent string of words to locate"
        source = document(b"<div1><div2><p><scripCom osisRef='Bible:Lev.19'/>"
                          + a + b"</p></div2></div1>")
        result = compare_paragraph_witness(source, [("I", "Lev.19", a)])
        self.assertEqual(result["results"][0]["candidate_source_section_p_count"], 1)
        self.assertEqual(result["results"][0]["paragraphs_with_both_unique_8_word_anchors"], 1)
        self.assertFalse(result["results"][0]["candidate_para_boundaries_authorized"])

    def test_missing_or_duplicate_source_marker_is_not_converted_to_a_boundary(self):
        source = document(b"<div1><div2><scripCom osisRef='Bible:John.3.1'/>"
                          b"<p>First source</p><scripCom osisRef='Bible:John.3.1'/>"
                          b"<p>Second source</p></div2></div1>")
        result = compare_paragraph_witness(source, [
            ("K", "John.3.1", b"<div/>Example original text"),
            ("K", "John.4.1", b"<div/>Another example original text")])
        self.assertEqual([x["status"] for x in result["results"]],
                         ["NO_UNIQUE_INDEPENDENT_MARKER",
                          "NO_UNIQUE_INDEPENDENT_MARKER"])
        self.assertFalse(result["original_stock_or_source_modified"])

    def test_chapter_marker_outside_div2_remains_unresolved(self):
        source = document(b"<div1><scripCom osisRef='Bible:Lev.19'/>"
                          b"<p>Independent source</p></div1>")
        result = compare_paragraph_witness(source, [
            ("I", "Lev.19", b"<div/>Original source")])
        self.assertEqual(result["results"][0]["status"],
                         "SOURCE_MARKER_OUTSIDE_CHAPTER_DIV2")

    def test_reject_duplicate_or_untrusted_samples(self):
        source = document(b"<div1><div2/></div1>")
        sample = ("K", "John.3.1", b"<div/>Text")
        with self.assertRaises(ValueError):
            compare_paragraph_witness(source, [sample, sample])
        with self.assertRaises(ValueError):
            compare_paragraph_witness(source, [("U", "TOP", b"raw")])
        with self.assertRaises(ValueError):
            compare_paragraph_witness(source, [("K", "John.3.1", b"<p>bad")])


if __name__ == "__main__":
    unittest.main()
