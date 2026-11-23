"""Synthetic, offline tests for the read-only BRNP v0.1 structural pilot."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_brnp import check  # noqa: E402

NS = 'http://www.bibletechnologies.net/2003/OSIS/namespace'


def document(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<osis xmlns="{NS}"><osisText osisIDWork="Demo" '
        f'osisRefWork="Bible"><header/><div type="book" osisID="Gen">'
        f'{body}</div></osisText></osis>'
    )


class BRNPStructuralPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "synthetic.osis.xml"

    def tearDown(self):
        self.temp.cleanup()

    def inspect(self, content, kind="bible"):
        self.path.write_text(content, encoding="utf-8")
        return check(self.path, kind)

    def test_bible_with_paragraph_and_paired_verses(self):
        xml = document(
            '<chapter osisID="Gen.1"><p>'
            '<verse osisID="Gen.1.1" sID="Gen.1.1"/>One.'
            '<verse eID="Gen.1.1"/>'
            '<verse osisID="Gen.1.2" sID="Gen.1.2"/>Two.'
            '<verse eID="Gen.1.2"/>'
            '</p></chapter>'
        )
        report = self.inspect(xml)
        self.assertEqual(report["status"], "pilot_structural_checks_passed")
        self.assertEqual(report["verse_identifier_count"], 2)

    def test_commentary_entry_with_range(self):
        xml = document(
            '<div type="section" annotateType="commentary" '
            'annotateRef="Gen.1.1-Gen.1.2"><p>One note.</p></div>'
        )
        report = self.inspect(xml, "commentary")
        self.assertEqual(report["commentary_entry_count"], 1)
        self.assertEqual(report["finding_count"], 0)

    def test_unmatched_verse_is_blocked(self):
        report = self.inspect(document(
            '<verse osisID="Gen.1.1" sID="Gen.1.1"/>Text'
        ))
        self.assertIn("UNCLOSED_VERSE_MILESTONE", [f["code"] for f in report["findings"]])

    def test_unknown_markup_is_blocked_without_loss(self):
        content = document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">A'
            '<invented>word</invented>.</verse></chapter>'
        )
        report = self.inspect(content)
        self.assertIn("UNREVIEWED_ELEMENT", [f["code"] for f in report["findings"]])
        self.assertEqual(report["finding_codes"]["UNREVIEWED_ELEMENT"], 1)
        self.assertEqual(report["unreviewed_elements"]["invented"], 1)
        self.assertIn("<invented>word</invented>", self.path.read_text(encoding="utf-8"))

    def test_commentary_missing_reference_is_blocked(self):
        report = self.inspect(document(
            '<div annotateType="commentary"><p>Note</p></div>'
        ), "commentary")
        self.assertIn("ANNOTATE_REF", [f["code"] for f in report["findings"]])

    def test_reports_do_not_include_source_prose(self):
        report = self.inspect(document(
            '<verse osisID="Gen.1.1">Private sentinel phrase</verse>'
        ))
        self.assertNotIn("Private sentinel phrase", json.dumps(report))
        self.assertFalse(report["publication_approved"])
        self.assertEqual(report["official_osis"]["status"], "not_run")


    def test_duplicate_book_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse></chapter>'
            '<div type="book" osisID="Gen"><chapter osisID="Gen.2">'
            '<verse osisID="Gen.2.1">Two</verse></chapter></div>'
        ))
        self.assertIn("BOOK_ID", [f["code"] for f in report["findings"]])

    def test_unclosed_chapter_milestone_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="Gen.1"/>'
            '<verse osisID="Gen.1.1">One</verse>'
        ))
        self.assertIn("UNCLOSED_CHAPTER_MILESTONE", [f["code"] for f in report["findings"]])

    def test_chapter_pair_is_accepted(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="Gen.1"/>'
            '<verse osisID="Gen.1.1">One</verse>'
            '<chapter eID="Gen.1"/>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["chapter_identifier_count"], 1)

    def test_duplicate_chapter_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse></chapter>'
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.2">Two</verse></chapter>'
        ))
        self.assertIn("CHAPTER_CONTAINER_ID", [f["code"] for f in report["findings"]])


    def test_official_osis_table_and_list_are_not_flattened(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
            '<table><row><cell>Cell</cell></row></table>'
            '<list><item>Item</item></list></chapter>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["element_counts"]["cell"], 1)

    def test_commentary_repeated_book_divisions_not_rejected_as_bible_duplicates(self):
        report = self.inspect(document(
            '<div type="book" osisID="Gen"><div type="section" '
            'annotateType="commentary" annotateRef="Gen.1.1">'
            '<p>First</p></div></div>'
            '<div type="book" osisID="Gen"><div type="section" '
            'annotateType="commentary" annotateRef="Gen.1.2">'
            '<p>Second</p></div></div>'
        ), kind="commentary")
        self.assertIn("COMMENTARY_REPEATED_BOOK_DIVISION", report["finding_codes"])
        self.assertEqual(report["commentary_entry_count"], 2)


    def test_osis_milestone_pairing_id_may_differ_from_canonical_osis_id(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1" sID="v-001"/>'
            'Text<verse eID="v-001"/></chapter>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["verse_identifier_count"], 1)


    def test_canonical_and_pairing_ids_are_independently_unique(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1">'
            '<verse osisID="Gen.1.1" sID="v-001"/>One<verse eID="v-001"/>'
            '<verse osisID="Gen.1.1" sID="v-002"/>Two<verse eID="v-002"/>'
            '</chapter>'
        ))
        self.assertIn("VERSE_START_ID", report["finding_codes"])
        self.assertEqual(report["verse_start_reasons"]["duplicate_osisID"], 1)

    def test_repeated_pairing_key_is_blocked_even_for_different_verses(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1">'
            '<verse osisID="Gen.1.1" sID="v-001"/>One<verse eID="v-001"/>'
            '<verse osisID="Gen.1.2" sID="v-001"/>Two<verse eID="v-001"/>'
            '</chapter>'
        ))
        self.assertEqual(report["verse_start_reasons"]["duplicate_sID"], 1)

    def test_wrong_table_cell_or_list_item_parent_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
            '<cell>Wrongly detached cell</cell>'
            '<list><row><item>Wrongly detached item</item></row></list>'
            '</chapter>'
        ))
        self.assertGreaterEqual(report["finding_codes"]["INVALID_STRUCTURAL_PARENT"], 3)

    def test_source_unchanged(self):
        content = document('<verse osisID="Gen.1.1">Test</verse>')
        self.path.write_text(content, encoding="utf-8")
        before = self.path.read_bytes()
        check(self.path, "bible")
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
