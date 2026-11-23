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

    def test_source_unchanged(self):
        content = document('<verse osisID="Gen.1.1">Test</verse>')
        self.path.write_text(content, encoding="utf-8")
        before = self.path.read_bytes()
        check(self.path, "bible")
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
