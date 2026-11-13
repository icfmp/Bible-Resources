"""Complete source ThML div1 coverage without inventing unmarked scripture anchors."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_unmarked_division_coverage import source_div1_coverage
from pilot_preflight import PilotError

def original_xml():
    return (
      b'<?xml version="1.0"?><ThML><ThML.body>'
      b'<div1 title="Annotated original division"><div2>'
      b'<scripCom osisRef="Bible:Gen.1.1"/>'
      b'<div><p>Full original authored paragraph.</p></div>'
      b'</div2></div1>'
      b'<div1 title="Unmarked original chapter"><div2>'
      b'<h2>Original unmarked heading</h2>'
      b'<p>Unmarked authorial paragraph <scripRef osisRef="Bible:Gen.2.2">'
      b'visible scripture label</scripRef> remains.</p>'
      b'<note>Original editorial note</note>'
      b'</div2><div2><p>Another unmarked chapter.</p></div2></div1>'
      b'<div1 title="Unmarked division without direct chapters">'
      b'<p>Other original content outside direct chapter markers.</p>'
      b'</div1></ThML.body></ThML>'+b" "*1100
    )

class OriginalUnmarkedDivisionTests(unittest.TestCase):
    def test_actual_source_structure_is_complete_and_crosschecked(self):
        report=source_div1_coverage(original_xml())
        self.assertEqual(report["source_all_div1_total"],3)
        self.assertEqual(report["source_div1_with_direct_chapters"],2)
        self.assertEqual(report["source_total_direct_chapters"],3)
        self.assertEqual(report["source_div1_with_any_scripCom"],1)
        self.assertEqual(report["source_div1_without_any_scripCom"],2)
        self.assertEqual(report["source_unmarked_div1_with_direct_chapters"],1)
        self.assertEqual(report["source_unmarked_div1_without_direct_chapters"],1)
        self.assertEqual(report["source_verse_or_range_scripCom_count"],1)
        cases=report["original_no_scripCom_div1_exact_content_hash_and_tag_name_only_cases"]
        self.assertEqual([c["original_div1_document_ordinal"] for c in cases],[2,3])
        self.assertEqual(cases[0]["original_div1_direct_chapter_div2_count"],2)
        self.assertEqual(cases[0]["original_div1_chapter_text_nonempty_count"],2)
        self.assertEqual(cases[0]["original_div1_scripRef_element_count"],1)
        self.assertEqual(cases[0]["original_div1_note_element_count"],1)
        self.assertEqual(cases[1]["original_div1_direct_chapter_div2_count"],0)
        self.assertEqual(cases[1]["original_div1_paragraph_nonempty_element_count"],1)
        self.assertTrue(report[
            "source_unmarked_division_has_no_inferred_biblical_book_or_verse_reference"])
        text=json.dumps(report)
        self.assertNotIn("Unmarked original chapter",text)
        self.assertNotIn("visible scripture label",text)
        self.assertNotIn("Gen.2.2",text)
        self.assertNotIn("Other original content",text)

    def test_invalid_source_xml_does_not_silently_fallback(self):
        with self.assertRaises(PilotError):
            source_div1_coverage(b'<ThML><div1></ThML>')

    def test_every_original_division_can_be_unmarked_without_guessed_book(self):
        original=(
            b'<ThML><ThML.body><div1 title="One"><div2>'
            b'<p>Original source only, no scripture marker.</p></div2></div1>'
            b'</ThML.body></ThML>'+b' '*1100
        )
        report=source_div1_coverage(original)
        self.assertEqual(report["source_div1_without_any_scripCom"],1)
        self.assertEqual(report["source_all_scripCom_count"],0)
        self.assertEqual(report["source_unmarked_div1_with_direct_chapters"],1)
        self.assertFalse("book_name" in json.dumps(report))

if __name__=="__main__":
    unittest.main()
