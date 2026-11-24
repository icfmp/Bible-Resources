"""Source-preserving chapter-opening title semantics, independent of Bible UI."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from mark_osis_preverse_section_titles import annotate, PreverseSectionError

def example() -> bytes:
    return (b'<?xml version="1.0" encoding="utf-8"?>'
            b'<osis><div type="book" osisID="Rom">'
            b'<chapter sID="Rom.1" osisID="Rom.1" n="1"/>'
            b'<!-- s1 -->'
            b'<title>Adresse et salutation</title>'
            b'<!-- r --><title type="parallel">V. 1-7: cf.</title>'
            b'<p><verse sID="Rom.1.1" osisID="Rom.1.1"/>Texte.'
            b'<verse eID="Rom.1.1"/></p>'
            b'<title>Milieu du chapitre</title>'
            b'<p><verse sID="Rom.1.2" osisID="Rom.1.2"/>Suite.</p>'
            b'<chapter eID="Rom.1"/>'
            b'<chapter sID="Rom.2" osisID="Rom.2" n="2"/>'
            b'<!-- r --><!-- s1 --><title>Les paiens</title>'
            b'<title type="parallel">V. 1-16: cf.</title>'
            b'<p><verse sID="Rom.2.1" osisID="Rom.2.1"/>Texte.</p>'
            b'<chapter eID="Rom.2"/>'
            b'<chapter sID="Rom.3" osisID="Rom.3" n="3"/>'
            b'<title type="chapter">Un vrai titre de chapitre</title>'
            b'<title type="parallel">Cross reference</title>'
            b'<p><verse sID="Rom.3.1" osisID="Rom.3.1"/>Texte.</p>'
            b'</div></osis>')

class PreverseSectionTests(unittest.TestCase):
    def test_typed_only_first_section_titles_without_modifying_other_source(self):
        original=example()
        revised,report=annotate(original)
        self.assertEqual(report["typed_chapter_first_titles"],2)
        self.assertEqual(report["changed_chapters"],["Rom.1","Rom.2"])
        self.assertEqual(report["original_sha256"],sha256(original).hexdigest())
        self.assertEqual(report["candidate_sha256"],sha256(revised).hexdigest())
        self.assertIn(b'<title type="x-section">Adresse et salutation</title>',revised)
        self.assertIn(b'<title type="x-section">Les paiens</title>',revised)
        self.assertIn(b'<title>Milieu du chapitre</title>',revised)
        self.assertIn(b'<title type="chapter">Un vrai titre de chapitre</title>',revised)
        self.assertIn(b'<title type="parallel">V. 1-7: cf.</title>',revised)
        self.assertEqual(revised.count(b'type="x-section"'),2)
        self.assertEqual(
            revised.replace(b'<title type="x-section">',b'<title>'),original)
        self.assertEqual(
            [x.text for x in ET.fromstring(revised).iter("title")],
            [x.text for x in ET.fromstring(original).iter("title")])

    def test_incomplete_or_empty_source_fails_closed(self):
        for raw in (b'',b'<osis/>',b'not XML',
                    b'<osis><chapter sID="Rom.1" osisID="Rom.1"/>'
                    b'<title></title></osis>',
                    b'<osis><chapter sID="Rom.1" osisID="Rom.1"/>'
                    b'<title>incomplete'):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(PreverseSectionError):
                    annotate(raw)

    def test_duplicate_chapter_identifier_rejected(self):
        start=b'<chapter sID="Rom.1" osisID="Rom.1"/><title>X</title>'
        with self.assertRaises(PreverseSectionError):
            annotate(b'<osis>'+start+start+b'</osis>')

    def test_no_arbitrary_prior_or_midchapter_titles_rewritten(self):
        raw=(b'<osis><div type="book"><title>Book heading</title>'
             b'<chapter sID="Rom.1" osisID="Rom.1"/>'
             b'<title type="parallel">Cross refs</title>'
             b'<p><verse osisID="Rom.1.1"/>Body.</p>'
             b'<title>Middle</title>'
             b'</div></osis>')
        with self.assertRaises(PreverseSectionError):
            annotate(raw)

if __name__=="__main__":
    unittest.main()
