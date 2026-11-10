"""Source-native USFX evidence is text-free, strict, and edition-agnostic."""
from hashlib import sha256
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_usfx_structure import audit_source_usfx, USFXAuditError


class USFXStructureTests(unittest.TestCase):
    def test_preserve_all_structure_and_notes_as_metadata_only(self):
        raw = (b'<usfx><languageCode>fra</languageCode>'
               b'<book id="GEN"><h>PRIVATE HEADING</h><c id="1"/>'
               b'<p sfm="p"><v id="1"/>PRIVATE SCRIPTURE 1</p>'
               b'<q level="1"><v id="2-3"/>PRIVATE SCRIPTURE 2'
               b'<f caller="*"><ft>PRIVATE NOTE BODY</ft>'
               b'<ref tgt="GEN.1.1">PRIVATE TARGET</ref></f></q>'
               b'<s level="1">PRIVATE SECTION</s></book></usfx>')
        result = audit_source_usfx(raw)
        self.assertEqual(result["status"], "source_native_structural_inventory_only")
        self.assertEqual(result["original_xml_sha256"], sha256(raw).hexdigest())
        self.assertEqual(result["source_book_count"], 1)
        self.assertEqual(result["numbered_source_reference_count"], 3)
        self.assertEqual(result["source_note_types"], {"f": 1})
        self.assertEqual(result["note_caller_categories"], {"literal": 1})
        self.assertEqual(result["source_editorial_categories"]["poetry"], 1)
        self.assertEqual(result["source_editorial_categories"]["headings"], 2)
        self.assertEqual(result["source_editorial_categories"]["paragraphs"], 1)
        self.assertTrue(result["no_source_text_or_note_bodies_returned"])
        self.assertFalse(result["official_usfx_schema_validated"])
        self.assertFalse(result["compiled_verse_text_or_notes_verified"])
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("GEN.1.1", str(result))  # authored explicit target is not leaked

    def test_repeated_verse_and_chapter_are_blocking(self):
        cases = [
            b'<usfx><book id="GEN"><c id="1"/><v id="2"/><v id="2"/></book></usfx>',
            b'<usfx><book id="GEN"><c id="2"/><v id="1"/><c id="1"/><v id="1"/></book></usfx>',
            b'<usfx><book id="GEN"><c id="1"/><v id="2-3"/><v id="3"/></book></usfx>',
        ]
        for case in cases:
            with self.subTest(case=case):
                report = audit_source_usfx(case)
                self.assertEqual(report["status"], "blocked_source_structure_findings")
                self.assertTrue(report["source_structural_issues"])

    def test_invalid_reference_or_embedded_verse_in_note_blocks(self):
        cases = [
            b'<usfx><book id="GEN"><v id="1"/></book></usfx>',
            b'<usfx><book id="GEN"><c id="1"/><v id="1a"/></book></usfx>',
            b'<usfx><book id="GEN"><c id="1"/><v id="1"/><f><v id="2"/></f></book></usfx>',
        ]
        for case in cases:
            with self.subTest(case=case):
                report = audit_source_usfx(case)
                self.assertEqual(report["status"], "blocked_source_structure_findings")

    def test_malformed_unsafe_xml_rejected_without_recovery(self):
        for raw in (
            b'', b'<usfx/>', b'<usfx><book id="GEN">',
            b'<!DOCTYPE usfx [<!ENTITY x "evil">]><usfx>&x;</usfx>',
            b'<usfx><book id="GEN"/><book id="GEN"/></usfx>',
            b'<other><book id="GEN"><c id="1"/><v id="1"/></book></other>',
        ):
            with self.subTest(raw=raw), self.assertRaises(USFXAuditError):
                audit_source_usfx(raw)

    def test_book_order_and_no_arbitrary_66_book_requirement(self):
        raw = (b'<usfx><book id="FRT"><c id="1"/><v id="1"/></book>'
               b'<book id="GEN"><c id="1"/><v id="1"/></book></usfx>')
        report = audit_source_usfx(raw)
        self.assertEqual([b["code"] for b in report["all_original_books"]], ["FRT", "GEN"])
        self.assertEqual(report["numbered_source_reference_count"], 2)
        self.assertEqual(report["status"], "source_native_structural_inventory_only")


if __name__ == "__main__":
    unittest.main()
