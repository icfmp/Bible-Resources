"""Synthetic metadata-only structural screens for original OSIS and native SWORD."""
import sys
from pathlib import Path
import unittest

from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_osis_structure_screen import (
    NativeStructuralCensus, OSISStructureScreenError, _markup_elements,
    authorial_body_opening_sequences,
)


class StructuralCensusTests(unittest.TestCase):
    def test_note_and_header_markup_are_excluded(self):
        root=etree.fromstring(
            b'<osis><p>visible<note><p>private note layout</p></note></p>'
            b'<header><title>private heading</title></header>'
            b'<l>visible poetry</l></osis>')
        elements=[name for _,name in _markup_elements(root)]
        self.assertEqual(elements.count("p"),1)
        self.assertEqual(elements.count("l"),1)
        self.assertNotIn("title",elements)

    def test_raw_native_census_is_bounded_and_does_not_emit_text(self):
        census=NativeStructuralCensus()
        census.observe(
            b'<div type="x-p" sID="private-1"/>'
            b'<l>SECRET VERSE</l><note n="a"><p>SECRET NOTE</p></note>'
            b'<div type="x-p" eID="private-1"/>')
        report=census.receipt()
        self.assertEqual(report["actual_compiled_raw_entries_scanned"],1)
        self.assertEqual(report["original_to_native_editorial_structure_counts"],{
            "native_l_container_elements":1,"native_paragraph_open_elements":1,
            "native_paragraph_close_elements":1})
        self.assertNotIn("SECRET",str(report))
        self.assertFalse(report["semantic_source_native_event_position_or_scope_verified"])

    def test_milestone_distinction_and_invalid_shape(self):
        census=NativeStructuralCensus()
        census.observe(b'<l sID="poem"/><l eID="poem"/>')
        self.assertEqual(census.receipt()["original_to_native_editorial_structure_counts"],
                         {"native_l_open_elements":1,"native_l_close_elements":1})
        with self.assertRaises(OSISStructureScreenError):
            census.observe(b'<div type="x-p"/>')

    def test_authorial_osis_order_tracks_paragraph_and_poetry_not_notes(self):
        source=(b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
                b'<osisText><div type="book" osisID="Gen"><chapter osisID="Gen.1">'
                b'<p>alpha<note><l>PRIVATE</l></note></p>'
                b'<verse osisID="Gen.1.1"/>'
                b'<lg><l>beta</l></lg><p>gamma</p>'
                b'</chapter></div></osisText></osis>')
        original,counts=authorial_body_opening_sequences(source)
        self.assertEqual(original,{"Gen":[("p","Gen"),("q","Gen.1.1"),
                                           ("p","Gen.1.1")]})
        self.assertEqual(counts["source_body_p_openings"],2)
        self.assertEqual(counts["source_body_q_openings"],1)
        self.assertNotIn("PRIVATE",str(counts))

    def test_repeated_osis_book_and_invalid_key_fail(self):
        prefix=b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
        duplicate=(prefix+b'<div type="book" osisID="Gen"/>'
                   b'<div type="book" osisID="Gen"/></osis>')
        with self.assertRaises(OSISStructureScreenError):
            authorial_body_opening_sequences(duplicate)
        unsafe=(prefix+b'<div type="book" osisID="unsafe secret"/>'
                b'</osis>')
        with self.assertRaises(OSISStructureScreenError):
            authorial_body_opening_sequences(unsafe)

    def test_malformed_native_xml_fails_closed(self):
        with self.assertRaises(OSISStructureScreenError):
            NativeStructuralCensus().observe(b"<l>unfinished")

    def test_no_empty_positive_receipt(self):
        with self.assertRaises(OSISStructureScreenError):
            NativeStructuralCensus().receipt()
