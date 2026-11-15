"""Invented-only, exact-byte reversible commentary reference erratum previews."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_literal_erratum_preflight import (
    preview_exact_reversible_commentary_reference_erratum,
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


if __name__ == "__main__":
    unittest.main()
