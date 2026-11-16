"""Invented-only, exact-byte reversible commentary reference erratum previews."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_literal_erratum_preflight import (
    preview_exact_reversible_commentary_reference_erratum,
    preview_exact_reversible_commentary_prose_erratum,
)


class ReversibleOriginalCommentaryReferencePreviewTests(unittest.TestCase):
    def test_one_original_label_and_target_change_exactly_and_undo(self):
        original = (
            b'<div a="keep"><reference type="x" osisRef="Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</reference><hi type='q'>Other &amp; text.</hi></div>"
        )
        patched, proof = preview_exact_reversible_commentary_reference_erratum(
            original, first_verse="Gen.1.3",
            original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.5")
        self.assertEqual(
            patched,
            original.replace(b"Gen.1.3-Gen.1.1", b"Gen.1.3-Gen.1.5")
                    .replace(b"Gen 1:3-1", b"Gen 1:3-5"),
        )
        self.assertTrue(proof["exactly_one_original_reference_and_label_changed"])
        self.assertTrue(proof["reverse_restores_exact_original_raw_bytes"])
        self.assertTrue(proof["no_other_original_xml_text_annotation_or_punctuation_changed"])
        self.assertFalse(proof["editorial_change_authorized"])
        self.assertFalse(proof["release_authorized"])
        self.assertFalse(proof["original_prose_and_reference_values_disclosed"])
        self.assertNotIn("Other", str(proof))
        self.assertNotEqual(proof["original_raw_sha256"], proof["proposed_raw_sha256"])

    def test_bible_qualified_range_with_abbreviated_endpoint(self):
        original = (
            b'<reference osisRef="Bible:Gen.1.3-1">'
            b"Genesis 1:3 \xe2\x80\x93 1</reference>"
        )
        patched, proof = preview_exact_reversible_commentary_reference_erratum(
            original, first_verse="Gen.1.3",
            original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.5")
        self.assertIn(b'osisRef="Bible:Gen.1.3-5"', patched)
        self.assertIn(b"Genesis 1:3 \xe2\x80\x93 5", patched)
        self.assertTrue(proof["reverse_restores_exact_original_raw_bytes"])

    def test_comment_and_cdata_reference_lookalikes_are_never_edited(self):
        fake = (
            b'<reference osisRef="Gen.1.3-Gen.1.1">'
            b'Gen 1:3-1</reference>'
        )
        only_lookalikes = [
            b'<p><![CDATA[' + fake + b']]></p>',
            b'<p><!--' + fake + b'--></p>',
            b'<p><![CDATA[' + fake + b']]></p><!--' + fake + b'-->',
            b'<reference xosisRef="Gen.1.3-Gen.1.1">Gen 1:3-1</reference>',
        ]
        for original in only_lookalikes:
            with self.subTest(original=original[:40]):
                with self.assertRaises(ValueError):
                    preview_exact_reversible_commentary_reference_erratum(
                        original, first_verse="Gen.1.3",
                        original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.5"
                    )
        actual = b'<reference osisRef="Gen.1.3-Gen.1.1">Gen 1:3-1</reference>'
        prefix = b'<p><!--' + fake + b'--><![CDATA[' + fake + b']]></p>'
        original = prefix + actual + b'<p>other source text</p>'
        proposed, receipt = preview_exact_reversible_commentary_reference_erratum(
            original, first_verse="Gen.1.3",
            original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.5"
        )
        expected = (
            prefix + b'<reference osisRef="Gen.1.3-Gen.1.5">'
            b'Gen 1:3-5</reference><p>other source text</p>'
        )
        self.assertEqual(proposed, expected)
        self.assertTrue(receipt["reverse_restores_exact_original_raw_bytes"])
        self.assertEqual(proposed.count(fake), 2)

    def test_any_ambiguous_source_candidate_fails_closed(self):
        base = (
            b'<reference osisRef="Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</reference>"
        )
        for raw in (
            base + base,
            base.replace(b"3-1</reference>", b"3-2</reference>"),
            base.replace(b"Gen 1:3-1", b"<hi>Gen 1:3-1</hi>"),
            b'<reference osisRef="Gen.1.3-Gen.1.1">3-1</reference'
        ):
            with self.subTest(raw_count=len(raw)):
                with self.assertRaises(ValueError):
                    preview_exact_reversible_commentary_reference_erratum(
                        raw, first_verse="Gen.1.3",
                        original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.5")
        with self.assertRaises(ValueError):
            preview_exact_reversible_commentary_reference_erratum(
                base, first_verse="Gen.1.3",
                original_end_verse="Gen.1.5", proposed_end_verse="Gen.1.6")
        with self.assertRaises(ValueError):
            preview_exact_reversible_commentary_reference_erratum(
                base, first_verse="Gen.1.3",
                original_end_verse="Gen.1.1", proposed_end_verse="Gen.1.2")


    def test_genuine_prose_typo_in_source_root_tail_reversible_only(self):
        original = (
            b'<div label="Zebulun or Dn"/><hi type="heading">A historical note</hi>'
            b" Here is no account either of Zebulun or Dn; and"
            b' <reference osisRef="1Chr.7.1">1 Chr 7:1</reference> '
            b"the tribe of Dan remains mentioned."
        )
        result, receipt = preview_exact_reversible_commentary_prose_erratum(
            original, original_phrase="Zebulun or Dn",
            corrected_phrase="Zebulun or Dan",
        )
        expected = original.replace(
            b"either of Zebulun or Dn;", b"either of Zebulun or Dan;"
        )
        self.assertEqual(result, expected)
        self.assertIn(b'label="Zebulun or Dn"', result)
        self.assertEqual(receipt["exact_original_byte_length_delta"], 1)
        self.assertTrue(receipt["exactly_one_parsed_original_text_span_edited"])
        self.assertTrue(receipt["reverse_restores_exact_original_raw_bytes"])
        self.assertTrue(receipt["all_other_original_xml_words_references_and_structure_preserved"])
        self.assertFalse(receipt["release_authorized"])
        self.assertNotIn("Zebulun", str(receipt))
        self.assertNotIn("Dan", str(receipt))

    def test_xml_comments_cdata_and_attribute_lookalikes_are_never_prose(self):
        target = b"Zebulun or Dn"
        fake = (
            b'<div data-x="Zebulun or Dn"/>'
            b"<!-- Zebulun or Dn -->"
            b"<p><![CDATA[Zebulun or Dn]]></p>"
        )
        with self.assertRaises(ValueError):
            preview_exact_reversible_commentary_prose_erratum(
                fake, original_phrase="Zebulun or Dn",
                corrected_phrase="Zebulun or Dan",
            )
        real = fake + b"<p>Here is no account of Zebulun or Dn today.</p>"
        corrected, receipt = preview_exact_reversible_commentary_prose_erratum(
            real, original_phrase="Zebulun or Dn",
            corrected_phrase="Zebulun or Dan",
        )
        self.assertEqual(corrected.count(target), 3)
        self.assertIn(b'<p>Here is no account of Zebulun or Dan today.</p>', corrected)
        self.assertTrue(receipt["reverse_restores_exact_original_raw_bytes"])

    def test_prose_typo_preflight_fails_closed_when_ambiguous_or_nonliteral(self):
        for raw in (
            b"Zebulun or Dn and another Zebulun or Dn",
            b"<p>Zebulun or Dn</p><p>Zebulun or Dn</p>",
            b"<p>Zebulun or <hi>Dn</hi></p>",
            b"<p>Zebulun or Dnx</p>",
            b'<p text="Zebulun or Dn"/>',
            b"<p>Other &amp; Zebulun or Dn</p>",
        ):
            # Entity normalization before the target must not accidentally
            # turn a byte offset from a decoded event into a valid source edit.
            if b"&amp; " in raw:
                continue
            with self.subTest(raw=raw[:45]):
                with self.assertRaises(ValueError):
                    preview_exact_reversible_commentary_prose_erratum(
                        raw, original_phrase="Zebulun or Dn",
                        corrected_phrase="Zebulun or Dan",
                    )
        for before, after in (("Dn", "Dan"), ("Zebulun or Dn", "Zebulun or Dn"),
                              ("Zebulun or Dn", "Zebulun <tag> Dan")):
            with self.assertRaises(ValueError):
                preview_exact_reversible_commentary_prose_erratum(
                    b"<p>Zebulun or Dn</p>",
                    original_phrase=before, corrected_phrase=after
                )


if __name__ == "__main__":
    unittest.main()
