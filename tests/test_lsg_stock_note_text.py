"""Synthetic compiled SWORD note-payload parity tests (no Scripture)."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_note_text import compare_compiled_notes, load_private_note_rows
from pilot_preflight import PilotError


def encoded_row(book,query,note_id,name,value):
    return "\t".join((book,query,note_id.encode().hex(),
                      name.encode().hex(),value.encode().hex()))


class StockNoteTextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/"source.osis.xml"
        self.source.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText><div type="book" osisID="Gen"><chapter sID="Gen.1"/>
<verse sID="Gen.1.1"/>
<w lemma="strong:H1">x</w>
<note type="crossReference" n="a">first note</note>
<note type="crossReference" n="b">second note</note>
<verse eID="Gen.1.1"/>
</div></osisText></osis>''',encoding="utf-8")
        self.aliases=[("Gen.1.1","Genesis 1:1")]
        self.rows=[
            encoded_row("Gen","Genesis 1:1","1","body","first note"),
            encoded_row("Gen","Genesis 1:1","2","body","second note"),
        ]

    def test_exact_text_matches_in_original_note_order(self):
        report=compare_compiled_notes(self.source,self.aliases,[],self.rows)
        self.assertEqual(report["status"],
                         "compiled_note_normalized_body_text_verified_only")
        self.assertEqual(report["source_note_count"],2)
        self.assertEqual(report["matching_normalized_note_body_text"],2)
        self.assertEqual(report["matching_raw_note_body_text"],2)
        self.assertFalse(report["note_kind_caller_and_anchor_fidelity_verified"])

    def test_text_changed_is_reported_as_hash_only(self):
        rows=list(self.rows)
        rows[1]=encoded_row("Gen","Genesis 1:1","2","body","altered note")
        report=compare_compiled_notes(self.source,self.aliases,[],rows)
        self.assertEqual(report["status"],
                         "blocked_or_unresolved_compiled_note_text_parity")
        self.assertEqual(report["matching_normalized_note_body_text"],1)
        self.assertNotIn("altered note",str(report))
        self.assertIn("compiled_normalized_sha256",
                      report["first_normalized_text_or_parse_mismatches"][0])

    def test_nonxml_fragment_is_rejected_without_recovery(self):
        rows=list(self.rows)
        rows[0]=encoded_row("Gen","Genesis 1:1","1","body","a < b")
        report=compare_compiled_notes(self.source,self.aliases,[],rows)
        self.assertEqual(report["body_xml_fragment_parse_failures"],1)
        self.assertNotEqual(report["status"],
                            "compiled_note_normalized_body_text_verified_only")

    def test_note_ordinal_swap_detected(self):
        rows=[
            encoded_row("Gen","Genesis 1:1","1","body","second note"),
            encoded_row("Gen","Genesis 1:1","2","body","first note"),
        ]
        report=compare_compiled_notes(self.source,self.aliases,[],rows)
        self.assertEqual(report["matching_normalized_note_body_text"],0)

    def test_missing_note_is_not_accepted(self):
        report=compare_compiled_notes(self.source,self.aliases,[],self.rows[:1])
        self.assertEqual(report["compiled_note_count"],1)
        self.assertEqual(report["source_note_count"],2)
        self.assertTrue(report["first_note_count_mismatches"])

    def test_duplicate_attribute_and_unexpected_book_are_errors(self):
        with self.assertRaises(PilotError):
            load_private_note_rows([self.rows[0],self.rows[0]],{"Gen"})
        with self.assertRaises(PilotError):
            load_private_note_rows(
                [encoded_row("Exod","Exodus 1:1","1","body","x")],{"Gen"})


if __name__=="__main__":
    unittest.main()
