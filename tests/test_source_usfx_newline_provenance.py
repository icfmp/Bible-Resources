"""Independent USFX text/tail fragment newline provenance, metadata only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_maintext_probe import authored_usfx_main_text
from source_native_word_boundaries import original_usfx_body_boundaries
from source_native_structural_whitespace import (
    MainTextStructuralWhitespaceTriage, StructuralWhitespaceError,
)
from source_usfx_newline_provenance import (
    SourceNewlineProvenanceError, classify_source_newline_gaps,
    newline_gaps_from_text,
)

MAP = [("GEN", "Gen")]


def source(body):
    xml = (b'<usfx><book id="GEN"><p sfm="mt">PRIVATE BOOK TITLE</p>'
           b'<c id="1"/>' + body + b'</book></usfx>')
    verses, _ = authored_usfx_main_text(xml, MAP)
    boundaries, _ = original_usfx_body_boundaries(xml, MAP, verses)
    origins = classify_source_newline_gaps(xml, MAP, verses)
    return xml, verses, boundaries, origins


def triage(body, native):
    _xml, verses, boundaries, origins = source(body)
    observer = MainTextStructuralWhitespaceTriage(
        verses, boundaries, source_xml_newline_origins=origins)
    observer.observe("Gen.1.1", native)
    return observer.finish()


class OriginalXmlNewlineProvenanceTests(unittest.TestCase):
    def test_text_vs_tail_origins_for_two_internal_unmarked_newlines(self):
        body = (b'<p><v id="1"/>alpha <hi>beta\ngamma</hi>'
                b'\ndelta<ve/></p>')
        receipt = triage(body, "alpha beta gamma delta")
        c = receipt["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["unmarked_internal_source_newline_review"], 2)
        self.assertEqual(c["unmarked_internal_newline_origin_text_within_inline_element"], 1)
        self.assertEqual(c["unmarked_internal_newline_origin_tail_after_inline_element"], 1)
        self.assertTrue(receipt["source_xml_fragment_newline_gap_coverage_verified"])
        self.assertFalse(receipt["source_native_original_whitespace_layout_verified"])
        self.assertTrue(receipt["source_xml_fragment_origin_does_not_prove_editorial_linebreak"])
        for secret in ("alpha", "beta", "gamma", "delta", "PRIVATE", "\n"):
            self.assertNotIn(secret, str(receipt))

    def test_verse_milestone_tail_origin_not_called_poetic_linebreak(self):
        body = b'<p><v id="1"/>alpha\nbeta<ve/></p>'
        result = triage(body, "alpha beta")
        c = result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c[
            "unmarked_internal_newline_origin_tail_after_numbering_milestone"], 1)
        self.assertEqual(c["unmarked_internal_source_newline_review"], 1)
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])

    def test_newline_after_note_is_counted_only_from_note_tail(self):
        body = (b'<p><v id="1"/>alpha<f>PRIVATE NOTE \n TEXT</f>'
                b'\nbeta<ve/></p>')
        result = triage(body, "alpha beta")
        counts = result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(counts[
            "unmarked_internal_newline_origin_tail_after_annotation_element"], 1)
        self.assertEqual(counts["unmarked_internal_source_newline_review"], 1)
        self.assertNotIn("NOTE", str(result))

    def test_multiple_xml_fragment_origins_at_one_whitespace_gap_remain_ambiguous(self):
        body = (b'<p><v id="1"/>alpha<hi>\n</hi>\nbeta<ve/></p>')
        result = triage(body, "alpha beta")
        c = result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c[
            "unmarked_internal_newline_origin_mixed_source_xml_text_and_tail_fragments"], 1)
        self.assertEqual(c["unmarked_internal_source_newline_review"], 1)
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])

    def test_poetry_opening_newline_source_origin_is_not_silently_certified(self):
        body = b'<p><v id="1"/>alpha\n<q>beta</q><ve/></p>'
        result = triage(body, "alpha beta")
        c = result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["source_newline_absent_at_q_open_candidate"], 1)
        self.assertEqual(c.get("unmarked_internal_source_newline_review", 0), 0)
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])

    def test_xml_newline_provenance_cannot_include_source_note_body_or_title(self):
        body = b'<p><v id="1"/>alpha<f>PRIVATE\nNOTE</f> beta<ve/></p>'
        xml, verses, boundaries, origins = source(body)
        self.assertEqual(origins["Gen.1.1"], {})
        o = MainTextStructuralWhitespaceTriage(
            verses, boundaries, source_xml_newline_origins=origins)
        o.observe("Gen.1.1", "alpha beta")
        r = o.finish()
        self.assertTrue(r["source_xml_fragment_newline_gap_coverage_verified"])
        self.assertEqual(r["source_native_original_whitespace_gap_counts"][
            "unmarked_internal_source_newline_review"], 0)
        self.assertNotIn("PRIVATE", str(r))

    def test_independent_exact_source_verse_text_is_required(self):
        xml, verses, _boundaries, _origins = source(
            b'<p><v id="1"/>alpha\nbeta<ve/></p>')
        altered = dict(verses)
        altered["Gen.1.1"] = "alpha beta"
        with self.assertRaises(SourceNewlineProvenanceError):
            classify_source_newline_gaps(xml, MAP, altered)
        with self.assertRaises(SourceNewlineProvenanceError):
            classify_source_newline_gaps(xml, [("OTHER", "Gen")], verses)

    def test_partial_missing_unsafe_or_extra_fragment_provenance_fails_closed(self):
        _xml, verses, boundaries, origins = source(
            b'<p><v id="1"/>alpha\nbeta<ve/></p>')
        for corrupted in (
            {}, {"Gen.1.1": {}},
            {"Gen.1.1": {5: frozenset({"PRIVATE_UNKNOWN_STYLE"})}},
            {"Gen.1.1": {5: frozenset()}},
            {"Gen.1.1": {5: frozenset({"text_within_paragraph_element"}),
                         6: frozenset({"text_within_paragraph_element"})},
        ):
            with self.subTest(corrupted=bool(corrupted)), self.assertRaises(
                StructuralWhitespaceError
            ):
                MainTextStructuralWhitespaceTriage(
                    verses, boundaries, source_xml_newline_origins=corrupted)
        self.assertEqual(set(origins["Gen.1.1"]), newline_gaps_from_text(verses["Gen.1.1"]))

    def test_no_synthetic_book_verse_separator_falsely_called_original_newline(self):
        body = (b'<p><v id="1"/>alpha<ve/></p>'
                b'<p><v id="2"/>beta<ve/></p>')
        xml, verses, boundaries, origins = source(body)
        self.assertEqual(origins, {"Gen.1.1": {}, "Gen.1.2": {}})
        o = MainTextStructuralWhitespaceTriage(
            verses, boundaries, source_xml_newline_origins=origins)
        o.observe("Gen.1.1", "alpha")
        o.observe("Gen.1.2", "beta")
        self.assertEqual(o.finish()["source_native_original_whitespace_gap_counts"][
            "unmarked_internal_source_newline_review"], 0)

    def test_non_linebreak_whitespace_does_not_gain_xml_newline_provenance(self):
        self.assertEqual(newline_gaps_from_text("alpha\tbeta\u00a0gamma"), set())
        self.assertEqual(newline_gaps_from_text("alpha\r\nbeta"), {5})


if __name__ == "__main__":
    unittest.main()
