"""Offline structural XML observation tests; no authorial text exposure."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_xml_witness import inspect_xml, xml_structure
from pilot_preflight import PilotError


class CommentaryXMLSourceTests(unittest.TestCase):
    def sample(self):
        return (b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b"<ThML><div1 title='Book'>"
                b"<div2 title='Chapter'><p>" + b"Sample original words. " * 80 +
                b"</p><scripRef passage='Gen 1:1'>Gen 1:1</scripRef></div2>"
                b"</div1><!-- original comment --></ThML>")

    def test_metadata_names_and_counts_not_text(self):
        result = xml_structure(self.sample())
        self.assertEqual(result["root_element_name"], "ThML")
        self.assertEqual(result["element_counts"]["div2"], 1)
        self.assertEqual(result["attribute_name_counts"]["passage"], 1)
        self.assertEqual(result["comment_node_count"], 1)
        self.assertTrue(result["no_source_text_disclosed"])
        self.assertFalse(result["authored_ranges_verified"])
        self.assertFalse(result["source_format_validated"])
        self.assertNotIn("Sample original words", json.dumps(result))

    def test_commentary_section_reference_classes_are_read_only_and_order_sensitive(self):
        source = self.sample().replace(
            b"<div2 title='Chapter'>",
            b"<div2 title='Chapter'>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.5' passage='Gen 1:1-5' type='section'/>"
            b"<scripCom osisRef='Bible:Gen.1.6' passage='Gen 1:6' type='section'/>"
            b"<scripCom osisRef='Bible:Gen.1.6' passage='Gen 1:6' type='section'/>"
        )
        result = xml_structure(source)
        self.assertEqual(result['candidate_commentary_reference_classes']['work_qualified_same_book_verse_range'], 1)
        self.assertEqual(result['candidate_commentary_reference_classes']['work_qualified_verse'], 2)
        self.assertEqual(result['candidate_commentary_distinct_reference_count'], 2)
        self.assertEqual(result['candidate_commentary_duplicate_identical_reference_count'], 1)
        self.assertEqual(result['candidate_commentary_attribute_name_counts']['osisRef'], 3)
        self.assertFalse(result['candidate_sections_are_verified_annotations'])
        self.assertNotIn('Gen 1:1-5', json.dumps(result))

    def test_unreviewed_reference_grammar_remains_visible_as_count_not_guessed(self):
        source = self.sample().replace(
            b"<div2 title='Chapter'>",
            b"<div2 title='Chapter'><scripCom osisRef='Gen 1:1-3'/>"
        )
        result = xml_structure(source)
        self.assertEqual(result['candidate_commentary_reference_classes']['unreviewed_missing_or_unqualified_work_ref'], 1)
        self.assertFalse(result['authored_ranges_verified'])
        self.assertTrue(all('Gen' not in shape for shape in result['candidate_commentary_reference_shapes']))
    def test_thml_work_qualified_chapters_and_cross_book_ranges_do_not_rewrite(self):
        source = self.sample().replace(
            b"<div2 title='Chapter'>",
            b"<div2 title='Chapter'>"
            b"<scripCom osisRef='Bible:Gen.1'/>"
            b"<scripCom osisRef='Bible:Gen.1.1-Exod.1.1'/>"
        )
        result = xml_structure(source)
        self.assertEqual(result["candidate_commentary_reference_classes"]["work_qualified_chapter"], 1)
        self.assertEqual(result["candidate_commentary_reference_classes"]["cross_book_range_requires_order_review"], 1)
        self.assertFalse(result["authored_ranges_verified"])

    def test_chapter_bearing_division_without_scripcom_is_not_discarded(self):
        source = self.sample().replace(
            b"</div1><!-- original comment -->",
            b"</div1><div1 title='Jude'>"
            b"<div2 title='Chapter'><p>Unmarked source still contains genuine authorial prose.</p></div2>"
            b"</div1><!-- original comment -->"
        )
        result = xml_structure(source)
        self.assertEqual(result['source_div1_with_direct_chapters'], 2)
        self.assertEqual(result['source_direct_chapters_inside_div1'], 2)
        self.assertEqual(len(result['source_chapter_bearing_div1_without_scripCom']), 2)
        self.assertGreater(result['source_chapter_bearing_div1_without_scripCom'][1]['original_text_unicode_characters'], 10)
        self.assertEqual(result['source_chapter_bearing_div1_without_scripCom'][1]['nonempty_paragraph_elements'], 1)
        self.assertNotIn('Unmarked source still contains', json.dumps(result))
        self.assertNotIn('Jude', json.dumps(result))
        self.assertTrue(result['source_division_text_stream_sha_is_not_original_file_byte_hash'])
    def test_original_xml_with_dtd_is_never_marked_schema_validated(self):
        raw = self.sample().replace(b"<ThML>", b'<!DOCTYPE ThML [<!ENTITY original "text">]><ThML>')
        result = xml_structure(raw)
        self.assertTrue(result["doctype_declared"])
        self.assertFalse(result["source_format_validated"])

    def test_external_entity_is_never_resolved_or_exported(self):
        raw = (b'<?xml version="1.0"?>'
               b'<!DOCTYPE ThML [<!ENTITY hidden SYSTEM "file:///etc/passwd">]>'
               b'<ThML><div1>&hidden;</div1></ThML>'
               + b" " * 1100)
        result = xml_structure(raw)
        self.assertGreaterEqual(result["unresolved_entity_node_count"], 1)
        self.assertNotIn("root:", json.dumps(result))
        self.assertFalse(result["source_format_validated"])

    def test_malformed_xml_blocks_instead_of_returning_partial_counts(self):
        for data in (b"<ThML><div1>broken" + b" " * 1100,
                     b"", b"\x00" * 1100):
            with self.subTest(size=len(data)):
                with self.assertRaises(PilotError):
                    xml_structure(data)

    def test_exact_url_provenance_and_pin_checked_before_source_parse(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            manifest = {
                "schema_version": 1,
                "resource_id": "example-commentary", "category": "commentary",
                "module_id": "ExampleCom", "title": "Test", "language": "en",
                "version": "2.0", "provider": "crosswire",
                "source_page_url": "https://crosswire.org/example",
                "sword_zip_url": "https://crosswire.org/modules/ExampleCom.zip",
                "authorial_witness_url": "https://ccel.org/example.txt",
                "sample_references": ["Gen 1:1", "Ps 23:1"],
                "archive_sha256": None,
                "rights": {"status": "research_only", "owner_approved": False,
                           "evidence_url": "https://crosswire.org/copyright"},
                "commentary_source": {"xml_witness_url": "https://untrusted.invalid/ThML.xml",
                                      "xml_witness_sha256": None}
            }
            path = directory / "example-commentary.json"
            path.write_text(json.dumps(manifest))
            with patch("commentary_xml_witness.fetch", side_effect=AssertionError("unexpected fetch")):
                with self.assertRaisesRegex(PilotError, "provenance"):
                    inspect_xml("example-commentary", directory=directory)


if __name__ == "__main__":
    unittest.main()
