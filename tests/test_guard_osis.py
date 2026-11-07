"""Offline test fixtures for fail-closed source validation.

The deliberately permissive XSD below tests the gate and diagnostics.
It is NOT the official OSIS schema and cannot be used for real imports.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from guard_osis import StructureFailure, inspect, main


NAMESPACE = "http://www.bibletechnologies.net/2003/OSIS/namespace"
TEST_ONLY_SCHEMA = f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="{NAMESPACE}" xmlns:o="{NAMESPACE}" elementFormDefault="qualified">
  <xs:element name="osis">
    <xs:complexType mixed="true">
      <xs:sequence>
        <xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
      </xs:sequence>
      <xs:anyAttribute processContents="lax"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
""".encode("utf-8")


class StrictOsisTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source.osis.xml"
        self.schema = self.root / "fixture.xsd"
        self.schema.write_bytes(TEST_ONLY_SCHEMA)
        self.policy = self.root / "policy.json"
        policy = json.loads((ROOT / "config/osis-policy.json").read_text(encoding="utf-8"))
        policy["schema_sha256"] = hashlib.sha256(TEST_ONLY_SCHEMA).hexdigest()
        policy["schema_status"] = "reviewed"  # Fixture exercises code; NOT the official XSD
        policy["schema_dependencies"] = []  # Synthetic fixture has no imported XSD
        self.policy.write_text(json.dumps(policy), encoding="utf-8")

    def write(self, lines):
        self.source.write_text("\n".join(lines), encoding="utf-8")

    def validate(self):
        return inspect(self.source, self.schema, self.policy)

    def assert_problem(self, code, line):
        with self.assertRaises(StructureFailure) as error:
            self.validate()
        self.assertEqual(error.exception.code, code)
        self.assertEqual(error.exception.line, line)
        self.assertIn(str(self.source), str(error.exception))

    def test_preserves_poetry_quotes_heading_and_translator_markup(self):
        self.write([
            f'<osis xmlns="{NAMESPACE}">',
            " <osisText>",
            "  <div type=\"book\" osisID=\"Exod\">",
            "   <chapter osisID=\"Exod.15\">",
            "    <title>Song of Moses</title>",
            "    <verse sID=\"Exod.15.1\" osisID=\"Exod.15.1\"/>",
            "    <lg><l level=\"1\">Line one</l>",
            "        <l level=\"2\"><q>Quoted line</q> <hi type=\"italic\">italics</hi></l></lg>",
            "    <verse eID=\"Exod.15.1\"/>",
            "   </chapter>",
            "  </div>",
            " </osisText>",
            "</osis>",
        ])
        original = self.source.read_bytes()
        report = self.validate()
        self.assertEqual(report["status"], "validated")
        self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["elements"]["l"], 2)
        self.assertTrue(report["no_transformation_performed"])
        self.assertEqual(original, self.source.read_bytes())

    def test_reviewed_standard_metadata_tables_and_lists_survive_source_gate(self):
        self.write([
            f'<osis xmlns="{NAMESPACE}">',
            ' <osisText>',
            '  <header><revisionDesc><date>2026-11-07</date><p>Revision record</p></revisionDesc>',
            '   <work><description>Full provenance</description><identifier type="OSIS">Bible.Test</identifier>',
            '   <type type="OSIS">Bible</type><refSystem>Bible</refSystem></work></header>',
            '  <div type="book" osisID="John"><div type="introduction">',
            '   <list><item>Outline heading</item></list>',
            '   <table><row><cell>Heading</cell><cell>Column</cell></row>',
            '   <row><cell>First</cell><cell>Entry</cell></row></table>',
            '  </div><chapter osisID="John.1"><verse osisID="John.1.1"/>Verse text</chapter></div>',
            ' </osisText></osis>',
        ])
        before=self.source.read_bytes()
        report=self.validate()
        self.assertEqual(report["elements"]["cell"],4)
        self.assertEqual(report["elements"]["table"],1)
        self.assertEqual(report["elements"]["revisionDesc"],1)
        self.assertEqual(report["elements"]["list"],1)
        self.assertEqual(self.source.read_bytes(),before)

    def test_bounded_original_xml_comments_are_preserved_without_approval_of_scripts(self):
        self.write([
            f'<osis xmlns="{NAMESPACE}">',
            '  <!-- USFM source provenance: keep as XML comment -->',
            '  <osisText><p>Original words<!-- converter marker --> unchanged</p></osisText>',
            '</osis>',
        ])
        original=self.source.read_bytes()
        r=self.validate()
        self.assertEqual(r["elements"]["xml_comment"],2)
        self.assertEqual(original,self.source.read_bytes())
        self.assertEqual(hashlib.sha256(original).hexdigest(),r["source_sha256"])

    def test_processing_instruction_is_still_blocked(self):
        self.write([f'<osis xmlns="{NAMESPACE}">',' <?dangerous step?>', '</osis>'])
        self.assert_problem("UNREVIEWED_NODE",2)

    def test_large_comment_requires_review(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<!-- '+("x"*4097)+' -->', '</osis>'])
        self.assert_problem("UNREVIEWED_COMMENT_SIZE",2)

    def test_valid_but_unreviewed_element_fails_at_line(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', ' <custom>Do not discard</custom>', '</osis>'])
        self.assert_problem("UNREVIEWED_ELEMENT", 2)

    def test_invalid_xml_fails_at_file_line(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<p>wrong closing</q>', '</osis>'])
        with self.assertRaises(StructureFailure) as error:
            self.validate()
        self.assertEqual(error.exception.code, "MALFORMED_XML")
        self.assertGreaterEqual(error.exception.line, 2)
        self.assertIn(str(self.source), str(error.exception))

    def test_different_xml_root_fails(self):
        self.write([f'<osisText xmlns="{NAMESPACE}"/>'])
        self.assert_problem("UNEXPECTED_ROOT", 1)

    def test_unrecognized_emphasis_fails(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<hi type="x-special">Important</hi>', '</osis>'])
        self.assert_problem("UNREVIEWED_EMPHASIS", 2)

    def test_invalid_poetry_level_fails(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<lg><l level="intro">Line</l></lg>', '</osis>'])
        self.assert_problem("UNREVIEWED_POETRY_LEVEL", 2)

    def test_orphan_end_milestone_fails(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<verse eID="Gen.1.1"/>', '</osis>'])
        self.assert_problem("UNMATCHED_MILESTONE", 2)

    def test_unclosed_milestone_points_to_opening_line(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<verse sID="Gen.1.1"/>', '</osis>'])
        self.assert_problem("UNCLOSED_MILESTONE", 2)

    def test_duplicate_milestone_is_not_silently_repaired(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<verse sID="Gen.1.1"/>',
                    '<verse eID="Gen.1.1"/>', '<verse sID="Gen.1.1"/>', '</osis>'])
        self.assert_problem("DUPLICATE_MILESTONE", 4)

    def test_milestone_type_mismatch_fails(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<verse sID="Gen.1.1"/>',
                    '<q eID="Gen.1.1"/>', '</osis>'])
        self.assert_problem("MILESTONE_TYPE_MISMATCH", 3)

    def test_doctype_blocked_with_line(self):
        self.write([f'<!DOCTYPE osis [<!ENTITY bad "text">]>',
                    f'<osis xmlns="{NAMESPACE}">plain</osis>'])
        self.assert_problem("DOCTYPE_UNREVIEWED", 1)

    def test_unpinned_policy_blocks_instead_of_guessing(self):
        policy = json.loads(self.policy.read_text(encoding="utf-8"))
        policy["schema_sha256"] = None
        self.policy.write_text(json.dumps(policy), encoding="utf-8")
        self.write([f'<osis xmlns="{NAMESPACE}"/>'])
        with self.assertRaises(StructureFailure) as error:
            self.validate()
        self.assertEqual(error.exception.code, "UNPINNED_SCHEMA")

    def test_schema_checksum_difference_blocks(self):
        policy = json.loads(self.policy.read_text(encoding="utf-8"))
        policy["schema_sha256"] = "a" * 64
        self.policy.write_text(json.dumps(policy), encoding="utf-8")
        self.write([f'<osis xmlns="{NAMESPACE}"/>'])
        with self.assertRaises(StructureFailure) as error:
            self.validate()
        self.assertEqual(error.exception.code, "SCHEMA_HASH_MISMATCH")

    def test_blocked_report_cannot_leave_stale_success(self):
        self.write([f'<osis xmlns="{NAMESPACE}">', '<custom/>', '</osis>'])
        report = self.root / "report.json"
        report.write_text('{"status":"validated"}', encoding="utf-8")
        result = main([str(self.source), "--schema", str(self.schema),
                       "--policy", str(self.policy), "--report", str(report)])
        self.assertEqual(result, 1)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "blocked")
        self.assertEqual(data["diagnostic"]["line"], 2)

    def test_report_pass_when_valid(self):
        self.write([f'<osis xmlns="{NAMESPACE}"><p>text</p></osis>'])
        report = self.root / "report.json"
        self.assertEqual(main([str(self.source), "--schema", str(self.schema),
                               "--policy", str(self.policy), "--report", str(report)]), 0)
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "validated")


if __name__ == "__main__":
    unittest.main()
