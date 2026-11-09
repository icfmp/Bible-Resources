"""Stock SWORD note word-offset verification fixtures, with no biblical text."""
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_note_anchors import (
    compare_note_anchors, compare_book_global_note_anchors, read_anchor_rows
)
from pilot_preflight import PilotError


class StockNoteAnchorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.osis=Path(self.tmp.name)/"synthetic.osis.xml"
        self.osis.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText><div type="book" osisID="Gen"><chapter sID="Gen.1"/>
<verse sID="Gen.1.1"/><w>a</w><note type="crossReference" n="a">n</note><w>b</w><verse eID="Gen.1.1"/>
<verse sID="Gen.1.2"/><w>c</w><note type="crossReference" n="b">m</note><verse eID="Gen.1.2"/>
</div></osisText></osis>''',encoding="utf-8")
        self.aliases=[("Gen.1.1","Genesis 1:1"),("Gen.1.2","Genesis 1:2")]
        self.words={"Gen.1.1":Counter({"w":2}),
                    "Gen.1.2":Counter({"w":1})}
        self.rows=[
            "Gen\tGenesis 0:0\t0\t",
            "Gen\tGenesis 1:0\t0\t",
            "Gen\tGenesis 1:1\t2\t1",
            "Gen\tGenesis 1:2\t1\t1",
        ]

    def test_ordinary_reader_note_word_offsets_are_exact(self):
        report=compare_note_anchors(self.osis,self.aliases,[],self.words,self.rows)
        self.assertEqual(report["status"],
                         "ordinary_reader_note_word_anchors_verified_with_reviewed_exceptions")
        self.assertEqual(report["notes_with_verified_exact_intra_verse_word_offset"],2)
        self.assertEqual(report["notes_in_interverse_or_explicitly_merged_keys_needing_review"],0)

    def test_interverse_word_is_reported_as_unresolved_not_silently_approved(self):
        rows=list(self.rows)
        rows[2]="Gen\tGenesis 1:1\t3\t2"
        report=compare_note_anchors(self.osis,self.aliases,[],self.words,rows)
        self.assertEqual(report["notes_in_interverse_or_explicitly_merged_keys_needing_review"],1)
        self.assertEqual(report["notes_with_verified_exact_intra_verse_word_offset"],1)
        self.assertEqual(report["unexpected_note_anchor_or_count_mismatches"],0)

    def test_unexplained_note_move_blocks(self):
        rows=list(self.rows)
        rows[2]="Gen\tGenesis 1:1\t2\t2"
        report=compare_note_anchors(self.osis,self.aliases,[],self.words,rows)
        self.assertEqual(report["status"],"blocked_unexplained_note_word_anchor_shift")
        self.assertEqual(report["unexpected_note_anchor_or_count_mismatches"],1)

    def test_intro_note_is_unapproved(self):
        rows=list(self.rows)
        rows[1]="Gen\tGenesis 1:0\t0\t0"
        report=compare_note_anchors(self.osis,self.aliases,[],self.words,rows)
        self.assertEqual(report["status"],"blocked_unexplained_note_word_anchor_shift")

    def test_book_global_note_offsets_are_identical_without_interverse_words(self):
        report = compare_book_global_note_anchors(
            self.osis, self.aliases, self.rows)
        self.assertEqual(
            report["status"], "compiled_book_global_note_word_offsets_verified")
        self.assertEqual(report["notes_with_exact_source_book_global_word_offset"], 2)
        self.assertFalse(report["note_rendered_visual_position_verified"])

    def test_book_global_note_alignment_survives_interverse_word_relocation(self):
        # A word between source verses is attached by the compiler to
        # the next reader entry. Its *book* ordering stays unchanged.
        original = self.osis.read_text(encoding="utf-8")
        self.osis.write_text(
            original.replace('<verse sID="Gen.1.2"/>',
                             '<w>interverse</w><verse sID="Gen.1.2"/>'),
            encoding="utf-8")
        shifted = list(self.rows)
        shifted[3] = "Gen\tGenesis 1:2\t2\t2"
        report = compare_book_global_note_anchors(
            self.osis, self.aliases, shifted)
        self.assertEqual(
            report["status"], "compiled_book_global_note_word_offsets_verified")
        self.assertEqual(report["notes_with_exact_source_book_global_word_offset"], 2)
        # Moving the note ahead of the original verse word is real corruption.
        shifted[3] = "Gen\tGenesis 1:2\t2\t1"
        bad = compare_book_global_note_anchors(
            self.osis, self.aliases, shifted)
        self.assertEqual(
            bad["status"], "blocked_book_global_note_word_offset_mismatch")
        self.assertEqual(bad["notes_with_exact_source_book_global_word_offset"], 1)
        self.assertEqual(bad["first_global_note_offset_mismatches"][0]
                         ["note_ordinal_in_book"], 2)

    def test_book_global_note_count_loss_and_word_loss_block(self):
        missing_note = list(self.rows)
        missing_note[3] = "Gen\tGenesis 1:2\t1\t"
        bad_note = compare_book_global_note_anchors(
            self.osis, self.aliases, missing_note)
        self.assertEqual(
            bad_note["status"], "blocked_book_global_note_word_offset_mismatch")
        self.assertEqual(bad_note["compiled_notes"], 1)
        missing_word = list(self.rows)
        missing_word[3] = "Gen\tGenesis 1:2\t0\t0"
        bad_word = compare_book_global_note_anchors(
            self.osis, self.aliases, missing_word)
        self.assertEqual(
            bad_word["status"], "blocked_book_global_note_word_offset_mismatch")
        self.assertTrue(bad_word["first_book_word_or_note_count_mismatches"])

    def test_book_intro_note_cannot_be_accepted_as_an_original_note(self):
        rows = list(self.rows)
        rows[0] = "Gen\tGenesis 0:0\t0\t0"
        bad = compare_book_global_note_anchors(self.osis, self.aliases, rows)
        self.assertEqual(bad["source_notes"], 2)
        self.assertEqual(bad["compiled_notes"], 3)
        self.assertEqual(
            bad["status"], "blocked_book_global_note_word_offset_mismatch")

    def test_invalid_ordinal_or_word_bounds_fail(self):
        plan=[("Genesis 1:1","Gen","0")]
        for row in ("Gen\tGenesis 1:1\t1\t2",
                    "Gen\tGenesis 1:1\tNaN\t0",
                    "Exod\tGenesis 1:1\t1\t0",
                    "Gen\tGenesis 1:2\t1\t0"):
            with self.subTest(row=row),self.assertRaises(PilotError):
                read_anchor_rows([row],plan)


if __name__=="__main__":
    unittest.main()
