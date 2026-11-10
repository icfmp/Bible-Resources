"""Synthetic tests for private USFX↔stock SWORD note-body diagnostics."""
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_native_notes_audit import (
    collect_usfx_numbered_notes, parse_native_numbered_notes,
    NoteAudit, NoteEvidenceError,
)

MAP = [("AAA", "Alpha")]


def source(note='<f caller="+"><fr>1:1</fr><ft>hello, world!</ft></f>'):
    return (f'<usfx><book id="AAA"><c id="1"/><v id="1"/>'
            f'first{note} tail<v id="2"/>second</book>'
            '<book id="ZZZ"><c id="1"/><v id="1"/>extra</book></usfx>').encode()


class NotesTests(unittest.TestCase):
    def test_note_body_and_source_scope(self):
        notes, facts = collect_usfx_numbered_notes(source(), MAP)
        self.assertEqual(notes, {"Alpha.1.1": [("f", "1:1hello, world!")]})
        self.assertEqual(facts["unmapped_source_book_count"], 1)
        self.assertEqual(facts["mapped_source_numbered_note_count"], 1)
        self.assertFalse(facts["source_note_caller_type_anchor_reference_target_verified"])

    def test_no_note_body_leaks_to_metadata(self):
        notes, _ = collect_usfx_numbered_notes(source(), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.1", b'<note>1:1hello, world!</note>')
        audit.inspect("Alpha.1.2", b'second')
        out = audit.finish()
        self.assertEqual(out["classifications"]["ordered_note_body_characters_equal"], 1)
        self.assertFalse(out["source_note_body_exact_full_parity_verified"])
        self.assertNotIn("hello, world!", json.dumps(out))

    def test_footnote_body_mutation_does_not_silently_pass(self):
        notes, _ = collect_usfx_numbered_notes(source(), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.1", b'<note>1:1hello, universe!</note>')
        out = audit.finish()
        self.assertEqual(out["classifications"]["ordered_note_bodies_differ"], 1)
        self.assertFalse(out["source_note_callers_anchors_types_and_crossreference_targets_verified"])

    def test_note_count_missing_and_extra(self):
        notes, _ = collect_usfx_numbered_notes(source(), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.1", b'no note')
        audit.inspect("Alpha.1.2", b'<note>unexpected note</note>')
        out = audit.finish()
        self.assertEqual(out["classifications"]["note_count_differs"], 2)
        self.assertEqual(out["native_parseable_numbered_note_count"], 1)

    def test_note_whitespace_is_distinguished_from_exact(self):
        notes, _ = collect_usfx_numbered_notes(
            source('<f>one  two</f>'), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.1", b'<note>one two</note>')
        self.assertEqual(
            audit.finish()["classifications"]["ordered_note_bodies_equal_after_whitespace_folding"], 1)

    def test_native_malformed_markup_is_unknown_not_zero(self):
        notes, _ = collect_usfx_numbered_notes(source(), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.1", b'<note>unclosed')
        out = audit.finish()
        self.assertEqual(out["classifications"]["native_fragment_unparseable_notes_unverified"], 1)
        self.assertNotIn("note_count_differs", out["classifications"])

    def test_note_with_verse_marker_is_ambiguous(self):
        with self.assertRaises(NoteEvidenceError):
            collect_usfx_numbered_notes(source('<f><v id="3"/></f>'), MAP)

    def test_notes_outside_numbered_verse_are_explicitly_counted(self):
        xml = source().replace(b'<c id="1"/>', b'<f>intro</f><c id="1"/>', 1)
        notes, facts = collect_usfx_numbered_notes(xml, MAP)
        self.assertEqual(facts["notes_outside_numbered_verses"], 1)
        self.assertEqual(len(notes["Alpha.1.1"]), 1)

    def test_extra_source_note_not_in_native_is_reported(self):
        notes, _ = collect_usfx_numbered_notes(source(), MAP)
        audit = NoteAudit(notes)
        audit.inspect("Alpha.1.2", b'second')
        out = audit.finish()
        self.assertEqual(out["classifications"]["source_note_bearing_verses_without_native_slot"], 1)
        self.assertEqual(out["source_note_bearing_refs_without_native_slots"], ["Alpha.1.1"])

    def test_native_note_xml_entity_is_semantically_decoded(self):
        self.assertEqual(parse_native_numbered_notes(b'<note>A &amp; B</note>'),
                         [("note", "A & B")])

    def test_native_xml_doctype_and_unclosed_tag_rejected(self):
        for raw in (b'<!DOCTYPE x>', b'<note>bad', b'<?xml version="1.0"?>'):
            with self.subTest(raw=raw[:8]), self.assertRaises(NoteEvidenceError):
                parse_native_numbered_notes(raw)

    def test_duplicate_native_verse_is_rejected(self):
        audit = NoteAudit({})
        audit.inspect("Alpha.1.1", b'word')
        with self.assertRaises(NoteEvidenceError):
            audit.inspect("Alpha.1.1", b'word')

    def test_source_verse_end_does_not_assign_later_note(self):
        xml = source().replace(b'<v id="2"/>second',
                               b'<ve id="1"/><f>outside</f><v id="2"/>second')
        notes, facts = collect_usfx_numbered_notes(xml, MAP)
        self.assertEqual(facts["notes_outside_numbered_verses"], 1)
        self.assertEqual(len(notes["Alpha.1.1"]), 1)


if __name__ == "__main__":
    unittest.main()
