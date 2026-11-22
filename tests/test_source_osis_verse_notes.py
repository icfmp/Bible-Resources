"""Synthetic regression tests for the strict original OSIS verse/note reader."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from research.bible.source_osis_verse_notes import (
    OSISSourceReaderError, original_osis_verses_and_notes, _fold, _nonspace,
)


def source(verses: str) -> bytes:
    return ("""<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText osisIDWork="TEST"><div type="book" osisID="Gen">
<chapter osisID="Gen.1"/>""" + verses +
            "</div></osisText></osis>").encode("utf-8")


ONE = ('<p><verse osisID="Gen.1.1" sID="Gen.1.1"/>alpha'
       '<note type="x-footnote" n="a">PRIVATE <reference osisRef="Gen.1.2">'
       'synthetic</reference></note> beta<verse eID="Gen.1.1"/></p>')
TWO = '<p><verse osisID="Gen.1.2" sID="Gen.1.2"/>gamma<verse eID="Gen.1.2"/></p>'


class OriginalOSISReaderTests(unittest.TestCase):
    def test_preserves_literal_text_and_note_anchor_in_memory(self):
        data = source(ONE + TWO)
        verses, notes, meta = original_osis_verses_and_notes(data)
        self.assertEqual(set(verses), {"Gen.1.1", "Gen.1.2"})
        self.assertEqual(verses["Gen.1.1"], "alpha beta")
        self.assertEqual(notes["Gen.1.1"][0]["point"], 5)
        self.assertEqual(notes["Gen.1.1"][0]["caller"], "a")
        self.assertEqual(notes["Gen.1.1"][0]["targets"], ("Gen.1.2",))
        self.assertEqual(meta["publisher_numbered_verse_count"], 2)
        self.assertEqual(meta["publisher_numbered_note_count"], 1)
        self.assertIn(b"PRIVATE", data)

    def test_missing_verse_is_not_invented(self):
        verses, notes, _ = original_osis_verses_and_notes(source(ONE))
        self.assertEqual(set(verses), {"Gen.1.1"})
        self.assertNotIn("Gen.1.2", notes)

    def test_malformed_or_overlapping_milestones_fail_closed(self):
        with self.assertRaises((ValueError, OSISSourceReaderError)):
            original_osis_verses_and_notes(source(ONE.replace(
                '<verse eID="Gen.1.1"/>', '')))
        with self.assertRaises((ValueError, OSISSourceReaderError)):
            original_osis_verses_and_notes(source(ONE + ONE))

    def test_source_comparison_folding_never_changes_literal_values(self):
        original = "A\u00a0 B"
        self.assertEqual(_nonspace(original), "AB")
        self.assertEqual(_fold(original), "A B")
        self.assertEqual(original, "A\u00a0 B")


if __name__ == "__main__":
    unittest.main()
