"""Synthetic original OSIS ↔ native p/l/lg exact position tests, no Bible text."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from publisher_osis_body_boundaries import (
    source_osis_body_events, NativeOSISBodyBoundaryScan, OSISBodyBoundaryError,
)

ORIGINAL = b'''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText osisIDWork="SYNTHETIC" osisRefWork="Bible">
<div type="book" osisID="Gen">
<p><verse osisID="Gen.1.1" sID="Gen.1.1"/>abc
<note n="a" type="x-footnote">SECRET PRIVATE NOTE</note>
<verse eID="Gen.1.1"/></p>
<lg><l><verse osisID="Gen.1.2" sID="Gen.1.2"/>def
<verse eID="Gen.1.2"/></l></lg>
</div></osisText></osis>'''
VERSES = {"Gen.1.1": "abc\n", "Gen.1.2": "def\n"}
RAW1 = (b'<div type="x-p" sID="private-id"/>abc'
        b'<note n="a" type="x-footnote">SECRET PRIVATE NOTE</note>'
        b'<div type="x-p" eID="private-id"/>')
RAW2 = (b'<lg sID="private-group"/><l sID="private-line"/>def'
        b'<l eID="private-line"/><lg eID="private-group"/>')


class PublisherBodyBoundaryTests(unittest.TestCase):
    def test_full_source_and_compiled_order_and_codepoints(self):
        source=source_osis_body_events(ORIGINAL,VERSES)
        self.assertEqual(source["Gen"],[
            ("p","open",0),("p","close",3),
            ("lg","open",3),("l","open",3),
            ("l","close",6),("lg","close",6)])
        native=NativeOSISBodyBoundaryScan(VERSES,source)
        native.observe("K","Gen.1.1",RAW1)
        native.observe("K","Gen.1.2",RAW2)
        result=native.finish()
        self.assertTrue(result["source_to_compiled_exact_p_l_lg_event_position_parity_verified"])
        self.assertEqual(result["counts"]["books_with_identical_event_kinds_endpoints_and_positions"],1)
        self.assertNotIn("SECRET PRIVATE",json.dumps(result))
        self.assertNotIn("private-id",json.dumps(result))

    def test_moved_close_detected_despite_same_markers_and_text(self):
        source=source_osis_body_events(ORIGINAL,VERSES)
        moved=(b'<div type="x-p" sID="private-id"/>'
               b'<div type="x-p" eID="private-id"/>abc'
               b'<note n="a">SECRET PRIVATE NOTE</note>')
        native=NativeOSISBodyBoundaryScan(VERSES,source)
        native.observe("K","Gen.1.1",moved)
        native.observe("K","Gen.1.2",RAW2)
        result=native.finish()
        self.assertFalse(result["source_to_compiled_exact_p_l_lg_event_position_parity_verified"])
        self.assertEqual(result["first_mismatching_books_and_nonspace_positions"][0][
            "native_ordinal"],0)

    def test_swapped_line_and_group_detected(self):
        source=source_osis_body_events(ORIGINAL,VERSES)
        native=NativeOSISBodyBoundaryScan(VERSES,source)
        native.observe("K","Gen.1.1",RAW1)
        swapped=(b'<l sID="private-line"/><lg sID="private-group"/>def'
                 b'<lg eID="private-group"/><l eID="private-line"/>')
        native.observe("K","Gen.1.2",swapped)
        self.assertFalse(native.finish()[
            "source_to_compiled_exact_p_l_lg_event_position_parity_verified"])

    def test_changed_prose_and_missing_entry_block(self):
        source=source_osis_body_events(ORIGINAL,VERSES)
        native=NativeOSISBodyBoundaryScan(VERSES,source)
        with self.assertRaises(OSISBodyBoundaryError):
            native.observe("K","Gen.1.1",RAW1.replace(b"abc",b"ABX"))
        with self.assertRaises(OSISBodyBoundaryError):
            NativeOSISBodyBoundaryScan(VERSES,source).finish()

    def test_untrusted_xml_and_duplicate_verse_fail_closed(self):
        with self.assertRaises((OSISBodyBoundaryError,ValueError)):
            source_osis_body_events(ORIGINAL.replace(b"Gen.1.2",b"Gen.1.1"),VERSES)
        source=source_osis_body_events(ORIGINAL,VERSES)
        scan=NativeOSISBodyBoundaryScan(VERSES,source)
        with self.assertRaises(OSISBodyBoundaryError):
            scan.observe("K","Gen.1.1",b"<p>unclosed")


if __name__=="__main__":
    unittest.main()
