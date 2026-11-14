"""Read-only complete-native-stream OSIS transport preflight regressions.

Fixtures are entirely invented. No MHCC text or source XML is included.
"""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_osis_rebuild_preflight import NativeOSISRebuildPreflight


class NativeOSISRebuildPreflightTests(unittest.TestCase):
    def test_simple_note_and_reference_wrapped_without_text_loss(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1",
                  b'<title>Invented heading</title><p>Plain <reference '
                  b'osisRef="Exod.1.1">reference</reference> with '
                  b'<note type="explanation">invented note</note>.</p>')
        report = c.report(expected_count=1)
        self.assertEqual(report["status"],
                         "COMPLETE_NATIVE_OSIS_WRAPPER_PREFLIGHT_NOT_A_REBUILD")
        self.assertEqual(report["raw_record_kinds"], {"K": 1})
        self.assertEqual(
            report["original_markup_shape_counts"][
                "visible_unicode_text_exactly_preserved_in_wrapper"], 1
        )
        self.assertEqual(report["original_element_counts_by_name"]["reference"], 1)
        self.assertEqual(report["original_element_counts_by_name"]["note"], 1)
        self.assertEqual(report["original_attribute_name_counts"]["osisRef"], 1)
        self.assertFalse(report["compiled_osis_to_stock_byte_parity_proven"])

    def test_native_intro_and_opaque_top_are_not_silently_discarded(self):
        c = NativeOSISRebuildPreflight()
        c.observe("U", "TOP:1", b"Invented control data")
        c.observe("U", "TOP:2", b"Invented other control data")
        c.observe("I", "Gen.0.0", b"<p>Invented book intro</p>")
        c.observe("I", "Gen.1.0", b"<p>Invented chapter intro</p>")
        report = c.report(expected_count=4)
        self.assertEqual(report["raw_record_kinds"], {"I": 2, "U": 2})
        self.assertEqual(
            report["blocking_or_unresolved_structure_counts"][
                "opaque_top_record_requires_distinct_preservation_plan"], 2
        )
        self.assertFalse(report["canonical_original_introductions_and_TOP_reconstructed"])

    def test_repeated_raw_keys_not_inferred_as_authorial_verse_range(self):
        c = NativeOSISRebuildPreflight()
        for key in ("Gen.1.7", "Gen.1.8", "Gen.2.1"):
            c.observe("K", key, b"<p>Invented shared text</p>")
        report = c.report(expected_count=3)
        self.assertEqual(report["unique_nonopaque_payload_sha256_count"], 1)
        self.assertEqual(report["payload_sharing_groups_by_number_of_index_keys"],
                         {"3": 1})
        self.assertEqual(report["same_raw_payload_across_chapter_group_count"], 1)
        self.assertEqual(report["same_raw_payload_across_book_group_count"], 0)
        self.assertEqual(
            report["original_markup_shape_counts"][
                "duplicate_index_key_same_exact_raw_body"], 2
        )

    def test_raw_shared_between_book_and_chapter_intro_is_not_assumed_same_scope(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1", b"<p>Invented shared text</p>")
        c.observe("I", "Gen.1.0", b"<p>Invented shared text</p>")
        c.observe("K", "Exod.1.1", b"<p>Invented shared text</p>")
        r = c.report(expected_count=3)
        self.assertEqual(r["same_raw_payload_shared_by_intro_and_numbered_keys_count"], 1)
        self.assertEqual(r["same_raw_payload_across_book_group_count"], 1)

    def test_malformed_raw_is_blocked_not_normalized(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1", b"<p>Invented malformed element")
        r = c.report(expected_count=1)
        self.assertEqual(
            r["blocking_or_unresolved_structure_counts"][
                "source_fragment_or_standard_osis_wrapper_invalid"], 1
        )
        self.assertFalse(r["full_stock_original_raw_entries_preserved_in_new_module_proven"])

    def test_mixed_text_and_tail_are_reported_without_disclosure(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1", b"Opening text <p>invented paragraph</p> tail text")
        r = c.report(expected_count=1)
        self.assertEqual(r["original_markup_shape_counts"][
            "leading_root_level_nonwhitespace_text"], 1)
        self.assertEqual(r["original_markup_shape_counts"][
            "direct_element_tail_nonwhitespace_text"], 1)
        self.assertNotIn("Opening text", str(r))
        self.assertNotIn("invented paragraph", str(r))

    def test_cdata_and_original_namespace_declaration_need_preservation(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1",
                  b'<p xmlns:ext="urn:invented"><ext:q><![CDATA[Invented prose]]>'
                  b'</ext:q></p>')
        r = c.report(expected_count=1)
        self.assertEqual(r["original_markup_shape_counts"][
            "cdata_lexical_boundaries_to_preserve"], 1)
        self.assertEqual(r["original_markup_shape_counts"][
            "source_local_namespace_declaration_to_preserve"], 1)

    def test_xml_declaration_is_not_silently_swallowed(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1",
                  b'<?xml version="1.0"?><p>Invented</p>')
        r = c.report(expected_count=1)
        self.assertEqual(r["blocking_or_unresolved_structure_counts"][
            "inline_document_declaration_requires_special_handling"], 1)

    def test_count_mismatch_blocks_completion(self):
        c = NativeOSISRebuildPreflight()
        c.observe("K", "Gen.1.1", b"<p>Invented</p>")
        with self.assertRaises(ValueError):
            c.report(expected_count=2)

    def test_invalid_native_key_or_binary_content_rejected(self):
        c = NativeOSISRebuildPreflight()
        for kind, ref, raw in (
            ("K", "Gen.1.0", b"<p>Invented</p>"),
            ("I", "Gen.1.1", b"<p>Invented</p>"),
            ("U", "TOP:0", b"Inert"),
            ("K", "Gen.1.1", b"Binary\x00"),
        ):
            with self.assertRaises(ValueError):
                c.observe(kind, ref, raw)
        with self.assertRaises(ValueError):
            c.report(expected_count=1)


if __name__ == "__main__":
    unittest.main()
