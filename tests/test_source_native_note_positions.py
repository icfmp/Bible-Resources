"""Strict synthetic original-USFX versus actual-SWORD note position evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_note_positions import (
    NoteAnchorError, NumberedNoteAnchorAudit,
    native_note_anchor_positions, original_usfx_note_anchors,
)

REF = "Gen.1.1"
MAP = [("GEN", "Gen")]
VERSE = {REF: "ab cd ef"}
NOTES = {REF: [("f", "PRIVATE FIRST NOTE"), ("f", "PRIVATE SECOND NOTE")]}


def source_xml():
    return (b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
            b'ab<f caller="*">PRIVATE FIRST NOTE</f> cd '
            b'<f caller="*">PRIVATE SECOND NOTE</f>ef<ve/>'
            b'</p></book></usfx>')


def stock(second_location=True):
    if second_location:
        return (b'ab<note type="crossReference">PRIVATE FIRST NOTE</note> cd '
                b'<note type="crossReference">PRIVATE SECOND NOTE</note>ef')
    return (b'ab<note type="crossReference">PRIVATE FIRST NOTE</note>'
            b' c<note type="crossReference">PRIVATE SECOND NOTE</note>d ef')


class NotePositionTests(unittest.TestCase):
    def test_original_source_reconstruction_and_both_note_positions(self):
        pos = original_usfx_note_anchors(source_xml(), MAP, VERSE, NOTES)
        self.assertEqual(pos, {REF:(2,4)})
        self.assertEqual(native_note_anchor_positions(stock(), VERSE[REF]), (2,4))
        audit = NumberedNoteAnchorAudit(pos, VERSE)
        audit.observe(REF, stock())
        result = audit.finish()
        self.assertTrue(result["all_numbered_note_nonspace_anchor_positions_match"])
        self.assertEqual(result["original_compiled_note_anchor_counts"][
            "matching_note_anchor_nonspace_codepoint_ordinals"], 2)
        for confidential in ("PRIVATE", "FIRST", "SECOND"):
            self.assertNotIn(confidential, str(result))

    def test_move_note_without_changing_word_punctuation_or_note_count(self):
        pos = original_usfx_note_anchors(source_xml(), MAP, VERSE, NOTES)
        audit = NumberedNoteAnchorAudit(pos, VERSE)
        audit.observe(REF, stock(second_location=False))
        report = audit.finish()
        self.assertFalse(report["all_numbered_note_nonspace_anchor_positions_match"])
        self.assertEqual(report["original_compiled_note_anchor_counts"][
            "moved_note_anchor_nonspace_codepoint_ordinals"], 1)
        self.assertEqual(report["first_note_anchor_findings_reference_ordinals_only"][0][
            "source_ordinal"], 4)
        self.assertEqual(report["first_note_anchor_findings_reference_ordinals_only"][0][
            "native_ordinal"], 3)  # second note moved inside the word

    def test_note_deleted_is_blocking(self):
        pos = original_usfx_note_anchors(source_xml(), MAP, VERSE, NOTES)
        audit = NumberedNoteAnchorAudit(pos, VERSE)
        audit.observe(REF, b'ab<note>x</note> cd ef')
        out = audit.finish()
        self.assertFalse(out["all_numbered_note_nonspace_anchor_positions_match"])
        self.assertEqual(out["original_compiled_note_anchor_counts"][
            "verses_with_note_count_difference"], 1)

    def test_source_reconstruction_and_note_count_fail_closed(self):
        for changed_verses, changed_notes in (
            ({REF:"abXX cd ef"}, NOTES),
            (VERSE, {REF:[("f","one")]}),
        ):
            with self.assertRaises(NoteAnchorError):
                original_usfx_note_anchors(
                    source_xml(), MAP, changed_verses, changed_notes)
        with self.assertRaises(NoteAnchorError):
            original_usfx_note_anchors(source_xml(), [("DIFF","Gen")], VERSE, NOTES)

    def test_malformed_native_and_different_text_do_not_pass(self):
        for raw in (
            b'ab<note>first<note>nested</note></note> cd ef',
            b'ab<note>first</note> cd altered',
            b'<?xml version="1.0"?><note>invalid</note>',
            b'<!DOCTYPE x><note>invalid</note>',
            b'ab<note>unterminated',
        ):
            with self.subTest(raw=raw[:10]), self.assertRaises(NoteAnchorError):
                native_note_anchor_positions(raw, VERSE[REF])

    def test_incomplete_native_coverage_or_duplicate_fails(self):
        pos = original_usfx_note_anchors(source_xml(), MAP, VERSE, NOTES)
        audit = NumberedNoteAnchorAudit(pos, VERSE)
        with self.assertRaises(NoteAnchorError):
            audit.finish()
        audit.observe(REF, stock())
        with self.assertRaises(NoteAnchorError):
            audit.observe(REF, stock())


if __name__ == "__main__":
    unittest.main()
