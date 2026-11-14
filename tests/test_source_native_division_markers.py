"""Verify original editorial division level preservation in compiled SWORD XML."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_division_markers import (
    NativeDivisionAudit, NativeDivisionAuditError, source_divisions,
)

SOURCE = b"""<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText>
<div type="book" osisID="Gen"><chapter osisID="Gen.1">
<p><verse osisID="Gen.1.1" sID="Gen.1.1"/>
<milestone type="x-subject-division" subType="x-original-ascii-star-1"/>
A<verse eID="Gen.1.1"/></p>
<p><verse osisID="Gen.1.2" sID="Gen.1.2"/>
<milestone type="x-major-subject-division" subType="x-original-ascii-star-3"/>
B<verse eID="Gen.1.2"/></p>
</chapter></div></osisText></osis>"""

FRAG1 = b'<div sID="gen1" type="x-p"/><milestone type="x-subject-division" subType="x-original-ascii-star-1"/>A'
FRAG2 = b'<div sID="gen2" type="x-p"/><milestone type="x-major-subject-division" subType="x-original-ascii-star-3"/>B'


class TestSourceNativeDivisionMarkers(unittest.TestCase):
    def test_exact_original_level_and_host_parity(self):
        original = source_divisions(SOURCE)
        self.assertEqual(len(original), 2)
        scan = NativeDivisionAudit(SOURCE)
        scan.observe("I", "Gen.1.0", b"<title>Introduction</title>")
        scan.observe("K", "Gen.1.1", FRAG1)
        scan.observe("K", "Gen.1.2", FRAG2)
        result = scan.finish()
        self.assertEqual(result["source_marker_count"], 2)
        self.assertEqual(result["native_marker_count"], 2)
        self.assertTrue(result["all_displayable_marker_attributes_absent"])

    def test_wrong_host_rejected_even_if_total_count_equal(self):
        scan = NativeDivisionAudit(SOURCE)
        scan.observe("K", "Gen.1.1", FRAG2)
        scan.observe("K", "Gen.1.2", FRAG1)
        with self.assertRaises(NativeDivisionAuditError):
            scan.finish()

    def test_wrong_star_level_rejected(self):
        scan = NativeDivisionAudit(SOURCE)
        scan.observe("K", "Gen.1.1", FRAG1.replace(b"star-1",b"star-2"))
        scan.observe("K", "Gen.1.2", FRAG2)
        with self.assertRaises(NativeDivisionAuditError):
            scan.finish()

    def test_renderable_marker_attribute_blocks(self):
        scan = NativeDivisionAudit(SOURCE)
        with self.assertRaises(NativeDivisionAuditError):
            scan.observe("K", "Gen.1.1",
                         FRAG1.replace(b'/>A',b' marker="*"/>A'))

    def test_dropped_metadata_not_accepted(self):
        scan = NativeDivisionAudit(SOURCE)
        scan.observe("K", "Gen.1.1", b"A")
        scan.observe("K", "Gen.1.2", FRAG2)
        with self.assertRaises(NativeDivisionAuditError):
            scan.finish()


if __name__ == "__main__":
    unittest.main()
