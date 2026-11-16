"""Invented-only original K raw -> temporary OSIS transport tests."""
from pathlib import Path
import sys
import unittest
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_osis_transport_probe import (
    build_numbered_transport_sample, classify_native_osis_roundtrip_delta
)


class OriginalRawNumberedTransportTests(unittest.TestCase):
    def test_noncontiguous_identical_payloads_do_not_link_across_gap(self):
        one = b"<title>Invented section</title>\n<p>First original body.</p>"
        middle = b"<p>Different original body.</p>"
        later = b"<p>Another original body.</p>"
        records = [
            ("Gen.1.1", one), ("Gen.1.2", one), ("Gen.1.3", middle),
            ("Gen.1.4", later), ("Gen.1.5", later),
            ("Gen.1.7", later), ("Gen.1.8", later),
        ]
        xml, report = build_numbered_transport_sample(
            records, work_id="TransportProbe"
        )
        self.assertEqual(report["input_numbered_native_keys"], 7)
        self.assertEqual(report["contiguous_identical_raw_body_groups"], 4)
        self.assertEqual(report["groups_with_multiple_original_native_verse_keys"], 3)
        self.assertTrue(report["source_unmodified_unicode_visible_text_in_syntax_approved_osis"])
        self.assertFalse(report["original_introductions_preserved_in_candidate"])
        self.assertFalse(report["compiler_roundtrip_parity_proven"])
        self.assertNotIn("Gen.1.6", xml.decode())
        root=etree.fromstring(xml)
        annotations=root.xpath("//*[local-name()='div' and @annotateType='commentary']")
        self.assertEqual([a.get("annotateRef") for a in annotations], [
            "Gen.1.1-Gen.1.2", "Gen.1.3",
            "Gen.1.4-Gen.1.5", "Gen.1.7-Gen.1.8"
        ])
        self.assertIn(one, xml)
        self.assertIn(middle, xml)
        self.assertIn(later, xml)

    def test_multiple_books_chapters_preserve_original_order(self):
        entries=[
            ("Gen.36.1", b"<p>Text for Gen 36</p>"),
            ("Exod.1.1", b"<p>Text for Exod 1</p>"),
        ]
        xml,report=build_numbered_transport_sample(entries,work_id="ProofWork")
        self.assertEqual(report["input_numbered_native_keys"],2)
        self.assertIn(b'osisID="Gen"',xml)
        self.assertIn(b'osisID="Exod"',xml)

    def test_rejects_duplicate_noncanonical_or_invalid_xml(self):
        for entries in (
            [("Gen.1.1", b"<p>x</p>"), ("Gen.1.1", b"<p>x</p>")],
            [("Gen.1.2", b"<p>x</p>"), ("Gen.1.1", b"<p>y</p>")],
            [("Gen.1.0", b"<p>x</p>")],
            [("Gen.1.1", b"<p>unclosed")],
            [("Gen.1.1", b"bad\x00bytes")],
        ):
            with self.assertRaises(ValueError):
                build_numbered_transport_sample(entries,work_id="ProbeModule")

    def test_intro_and_opaque_top_not_passed_off_as_verse_entries(self):
        for entries in (
            [("Gen.0.0", b"<p>Book intro</p>")],
            [("TOP:1", b"<div/>")],
        ):
            with self.assertRaises(ValueError):
                build_numbered_transport_sample(entries,work_id="ProbeModule")

    def test_metadata_only_detects_whitespace_changes_without_text_loss(self):
        got=classify_native_osis_roundtrip_delta(
            b"<p>Invented  body text.</p>",
            b"<p>Invented body text.</p>"
        )
        self.assertEqual(got["word_sequence_relation"], "EXACT_ORIGINAL_WORD_SEQUENCE")
        self.assertTrue(got["normalized_whitespace_visible_unicode_equal"])
        self.assertTrue(got["all_original_markup_element_names_and_counts_preserved"])
        self.assertNotIn("Invented", str(got))

    def test_added_compiled_heading_is_not_accepted_as_same_authorial_prose(self):
        got=classify_native_osis_roundtrip_delta(
            b"<p>Synthetic prose</p>",
            b"<title>Additional heading</title> <p>Synthetic prose</p>"
        )
        self.assertEqual(got["word_sequence_relation"],
                         "ALL_ORIGINAL_WORDS_IN_ORDER_WITH_ADDITIONAL_COMPILED_WORDS")
        self.assertFalse(got["normalized_whitespace_visible_unicode_equal"])
        self.assertFalse(got["all_original_markup_element_names_and_counts_preserved"])

    def test_dropped_synthetic_word_is_detected(self):
        got=classify_native_osis_roundtrip_delta(
            b"<p>Synthetic prose remains</p>",
            b"<p>Synthetic remains</p>"
        )
        self.assertEqual(got["word_sequence_relation"],
                         "COMPILED_WORDS_A_SUBSEQUENCE_OF_ORIGINAL")
        self.assertFalse(got["source_prose_and_markup_parity_approved"])

    def test_added_div_wrapper_can_preserve_original_element_attributes(self):
        source = (b'<div type="commentary"><reference osisRef="Gen.1.2">'
                  b'Invented citation</reference></div>')
        compiled = (b'<div type="technical"><div type="commentary">'
                    b'<reference osisRef="Gen.1.2">Invented citation</reference>'
                    b'</div></div>')
        result=classify_native_osis_roundtrip_delta(source,compiled)
        self.assertTrue(result["only_div_element_count_added_not_other_element_names"])
        self.assertTrue(result["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertTrue(result["original_div_elements_exact_attribute_multiset_preserved"])
        self.assertTrue(result["reference_attribute_values_in_original_document_order_preserved"])
        self.assertFalse(result["all_original_markup_element_names_and_counts_preserved"])

    def test_same_visible_citation_words_with_changed_link_target_is_detected(self):
        source=b'<p><reference osisRef="Gen.1.2">An invented phrase</reference></p>'
        compiled=b'<div type="technical"><p><reference osisRef="Gen.1.3">An invented phrase</reference></p></div>'
        result=classify_native_osis_roundtrip_delta(source,compiled)
        self.assertTrue(result["normalized_whitespace_visible_unicode_equal"])
        self.assertFalse(result["reference_attribute_values_in_original_document_order_preserved"])
        self.assertFalse(result["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertTrue(result["only_div_element_count_added_not_other_element_names"])

    def test_same_words_and_reference_attributes_cannot_change_clickable_text_scope(self):
        original = (
            b'<p><reference osisRef="Gen.1.1">Gen 1:1</reference>'
            b' and Gen 1:2</p>'
        )
        moved = (
            b'<p><reference osisRef="Gen.1.1">'
            b'Gen 1:1 and Gen 1:2</reference></p>'
        )
        delta = classify_native_osis_roundtrip_delta(original, moved)
        self.assertEqual(delta["word_sequence_relation"], "EXACT_ORIGINAL_WORD_SEQUENCE")
        self.assertTrue(delta["normalized_whitespace_visible_unicode_equal"])
        self.assertTrue(delta["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertTrue(delta["reference_attribute_values_in_original_document_order_preserved"])
        self.assertFalse(delta["original_nondiv_text_and_tail_ownership_preserved"])
        self.assertNotIn("Gen 1:2", str(delta))

        punctuation_original = (
            b'<p><reference osisRef="Gen.1.1">Gen 1:1</reference>, next</p>'
        )
        punctuation_moved = (
            b'<p><reference osisRef="Gen.1.1">Gen 1:1,</reference> next</p>'
        )
        punctuation = classify_native_osis_roundtrip_delta(
            punctuation_original, punctuation_moved
        )
        self.assertTrue(punctuation["normalized_whitespace_visible_unicode_equal"])
        self.assertFalse(punctuation["original_nondiv_text_and_tail_ownership_preserved"])

    def test_empty_semantic_element_boundary_still_controls_text_tail_position(self):
        # Both fragments have identical flattened words, identical XML element
        # order/attributes and the same text owning paragraph. The previous
        # owner-ID-only check could incorrectly certify both as equivalent.
        before = b"<p>Before <hi type='q'/> after</p>"
        after = b"<p>Before after<hi type='q'/></p>"
        delta = classify_native_osis_roundtrip_delta(before, after)
        self.assertEqual(delta["word_sequence_relation"], "EXACT_ORIGINAL_WORD_SEQUENCE")
        self.assertTrue(delta["normalized_whitespace_visible_unicode_equal"])
        self.assertTrue(delta["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertFalse(delta["original_nondiv_text_and_tail_ownership_preserved"])
        self.assertNotIn("Before", str(delta))
        self.assertNotIn("after", str(delta))

    def test_semantic_xml_nesting_cannot_move_original_reference_into_other_paragraph(self):
        original = (
            b'<p><reference osisRef="Gen.1.1">Gen 1:1</reference></p>'
            b'<p> and context</p>'
        )
        moved = (
            b"<p/>"
            b'<reference osisRef="Gen.1.1">Gen 1:1</reference>'
            b'<p> and context</p>'
        )
        delta = classify_native_osis_roundtrip_delta(original, moved)
        self.assertEqual(delta["word_sequence_relation"], "EXACT_ORIGINAL_WORD_SEQUENCE")
        self.assertTrue(delta["normalized_whitespace_visible_unicode_equal"])
        self.assertTrue(delta["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertTrue(delta["reference_attribute_values_in_original_document_order_preserved"])
        self.assertFalse(delta["original_nondiv_text_and_tail_ownership_preserved"])

    def test_compiler_div_wrappers_do_not_change_semantic_text_ownership(self):
        original = (
            b'<div type="original"><p>Hello '
            b'<reference osisRef="Gen.1.1">Gen 1:1</reference>'
            b' and other words.</p></div>'
        )
        compiled = (
            b'<div type="technical"><div type="original"><div type="technical">'
            b'<p>Hello <reference osisRef="Gen.1.1">Gen 1:1</reference>'
            b' and other words.</p></div></div></div>'
        )
        result = classify_native_osis_roundtrip_delta(original, compiled)
        self.assertTrue(result["original_nondiv_text_and_tail_ownership_preserved"])
        self.assertTrue(result["non_div_element_order_and_exact_attribute_values_preserved"])
        self.assertTrue(result["original_div_elements_exact_attribute_multiset_preserved"])
        self.assertTrue(result["normalized_whitespace_visible_unicode_equal"])

    def test_invalid_work_id_cannot_inject_xml_attributes(self):
        with self.assertRaises(ValueError):
            build_numbered_transport_sample(
                [("Gen.1.1", b"<p>x</p>")],
                work_id='Invalid" module'
            )


if __name__=="__main__":
    unittest.main()
