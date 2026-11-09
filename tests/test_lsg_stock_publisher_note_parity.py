"""Compare immutable synthetic USFX notes directly with binary-note attributes."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_publisher_note_parity import compare_publisher_usfx_to_compiled_notes
from pilot_preflight import PilotError


class PublisherOriginalNoteAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.candidate=Path(self.temp.name)/"candidate.osis.xml"
        self.candidate.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText><div type="book" osisID="Gen">
<chapter sID="Gen.1"/>
<verse sID="Gen.1.1"/>
<note type="crossReference" n="a">first note</note>
<note type="crossReference" n="b">second note</note>
<verse eID="Gen.1.1"/>
</div></osisText></osis>''',encoding="utf-8")
        self.original=b'''<usfx><book id="GEN">
<c id="1"/><p><v id="1"/>
<x caller="a">first note</x><x caller="b">second note</x>
<ve/></p></book></usfx>'''
        self.aliases=[("Gen.1.1","Genesis 1:1")]
        self.compiled={
            ("Gen","Genesis 1:1"):{
                "1":{"body":"first note"},
                "2":{"body":"second note"},
            }
        }

    def test_source_note_raw_text_exact(self):
        report=compare_publisher_usfx_to_compiled_notes(
            self.original,self.candidate,self.aliases,[],self.compiled)
        self.assertEqual(report["publisher_source_note_count"],2)
        self.assertEqual(report["publisher_raw_note_bodies_exact_in_compiled_sword"],2)
        self.assertEqual(report["publisher_normalized_note_bodies_equal"],2)
        self.assertEqual(report["status"],
                         "publisher_usfx_to_compiled_sword_notes_normalized_match")
        self.assertFalse(report["full_editorial_whitespace_approved"])

    def test_only_compiled_newline_difference_is_recorded_safely(self):
        records={("Gen","Genesis 1:1"):{
            "1":{"body":"first\nnote"},
            "2":{"body":"second note"}}}
        report=compare_publisher_usfx_to_compiled_notes(
            self.original,self.candidate,self.aliases,[],records)
        self.assertEqual(report["publisher_raw_note_bodies_exact_in_compiled_sword"],1)
        self.assertEqual(report["publisher_normalized_note_bodies_equal"],2)
        self.assertEqual(report["publisher_vs_compiled_changed_whitespace_features"]
                         ["compiled_newline_runs_changed"],1)
        self.assertNotIn("first\nnote",str(report))
        self.assertNotIn("first note",str(report))

    def test_source_word_change_does_not_get_approved(self):
        records={("Gen","Genesis 1:1"):{
            "1":{"body":"first altered"},
            "2":{"body":"second note"}}}
        report=compare_publisher_usfx_to_compiled_notes(
            self.original,self.candidate,self.aliases,[],records)
        self.assertEqual(report["status"],
                         "publisher_to_compiled_sword_note_text_mismatch")
        self.assertEqual(report["publisher_normalized_note_bodies_equal"],1)
        self.assertNotIn("altered",str(report))

    def test_unreviewed_missing_original_note_is_diagnosed(self):
        records={("Gen","Genesis 1:1"):{"1":{"body":"first note"}}}
        report=compare_publisher_usfx_to_compiled_notes(
            self.original,self.candidate,self.aliases,[],records)
        self.assertTrue(report["note_count_mismatches"])
        self.assertEqual(report["status"],
                         "publisher_to_compiled_sword_note_text_mismatch")

    def test_dangerous_doctype_is_rejected(self):
        with self.assertRaises(PilotError):
            compare_publisher_usfx_to_compiled_notes(
                b'<!DOCTYPE usfx SYSTEM "file:///etc/passwd">'+self.original,
                self.candidate,self.aliases,[],self.compiled)


if __name__=="__main__":
    unittest.main()
