"""Synthetic stock SWORD note-attribute storage inspection tests (no Bible text)."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lsg_stock_note_probe import summarize_note_storage
from pilot_preflight import PilotError


class NoteStoreTests(unittest.TestCase):
    def setUp(self):
        document=etree.fromstring(b'''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
          <osisText><div type="book" osisID="Gen">
            <verse sID="Gen.1.1"/><note>n</note><note>x</note><verse eID="Gen.1.1"/>
          </div><div type="book" osisID="Exod">
            <verse sID="Exod.1.1"/><note>t</note><verse eID="Exod.1.1"/>
          </div></osisText></osis>''')
        self.books=[e for e in document.iter() if
                    e.tag.endswith("div") and e.get("type") == "book"]
        self.rows=[
            "Gen\t2\t2\t2\t2",
            "Exod\t1\t1\t1\t1",
        ]

    def test_full_raw_note_and_attribute_inventory_is_diagnostic_only(self):
        report=summarize_note_storage(self.rows,self.books)
        self.assertEqual(report["status"],
                         "compiled_note_entry_attribute_storage_observed")
        self.assertEqual(report["source_note_elements"],3)
        self.assertEqual(report["footnote_entry_attribute_records"],3)
        self.assertEqual(report["nonempty_note_body_records"],3)
        self.assertFalse(report["full_note_text_and_targets_verified"])

    def test_missing_note_marker_is_reported_without_forgiving_loss(self):
        report=summarize_note_storage(["Gen\t1\t2\t2\t2",self.rows[1]],
                                      self.books)
        self.assertEqual(report["status"],"blocked_compiled_note_count_scope")
        self.assertEqual(report["books_with_different_note_marker_counts"][0]["book"],"Gen")

    def test_empty_note_body_count_remains_a_distinct_signal(self):
        report=summarize_note_storage(["Gen\t2\t2\t2\t0",self.rows[1]],self.books)
        self.assertEqual(report["nonempty_note_body_records"],1)
        self.assertFalse(report["full_note_text_and_targets_verified"])

    def test_malformed_or_unknown_counts_are_rejected(self):
        for bad in ("Lev\t1\t1\t1\t1","Gen\t0\tNaN\t0\t0",
                    "Gen\t1\t1\t1","Gen\t-1\t0\t0\t0"):
            with self.subTest(row=bad), self.assertRaises(PilotError):
                summarize_note_storage([bad], self.books)


if __name__=="__main__":
    unittest.main()
