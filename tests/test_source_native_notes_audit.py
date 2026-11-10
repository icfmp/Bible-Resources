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

    def test_substantive_note_mismatch_is_not_hidden_by_whitespace_findings(self):
        authored = {
            f"Alpha.1.{i}": [("f", "one  two")] for i in range(1, 60)
        }
        audit = NoteAudit(authored)
        for i in range(1, 59):
            audit.inspect(f"Alpha.1.{i}", b"<note>one two</note>")
        audit.inspect("Alpha.1.59", b"<note>changed words</note>")
        result = audit.finish()
        self.assertEqual(result["first_findings_without_note_text"][0]["ref"], "Alpha.1.59")
        self.assertEqual(result["first_findings_without_note_text"][0]["kind"],
                         "ordered_note_bodies_differ")
        self.assertNotIn("changed words", json.dumps(result))

    def test_metadata_crossref_caller_and_machine_targets_are_inspected(self):
        text = source(
            '<x caller="+"><xt><ref tgt="GEN.1.2">do not log me</ref></xt></x>')
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(text, MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect(
            "Alpha.1.1",
            b'<note type="crossReference" n="a">'
            b'<reference osisRef="GEN.1.2">another private text</reference></note>')
        out = audit.finish()["note_annotation_structure_diagnostic"]
        counts = out["classifications"]
        self.assertEqual(counts["cross_reference_class_agrees"], 1)
        self.assertEqual(counts["source_caller_automatic_absent_or_unverifiable"], 1)
        self.assertEqual(counts["explicit_target_raw_strings_equal"], 1)
        self.assertFalse(out["source_to_compiled_reference_targets_resolved_verified"])
        self.assertNotIn("GEN.1.2", json.dumps(out))
        self.assertNotIn("do not log", json.dumps(out))

    def test_crossref_type_mismatch_is_not_hidden_by_same_note_body(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(source('<x>same</x>'), MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note>same</note>')
        out = audit.finish()
        self.assertEqual(out["classifications"]["ordered_note_body_characters_equal"], 1)
        structural = out["note_annotation_structure_diagnostic"]
        self.assertEqual(structural["classifications"]["cross_reference_class_differs"], 1)
        self.assertEqual(structural["first_material_findings_no_note_text"][0]["ref"], "Alpha.1.1")

    def test_literal_caller_mismatch_is_reported_without_values(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(
            source('<f caller="SOURCE_SECRET">same</f>'), MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note n="NATIVE_SECRET">same</note>')
        out = audit.finish()["note_annotation_structure_diagnostic"]
        self.assertEqual(out["classifications"]["literal_caller_string_differs"], 1)
        self.assertNotIn("SOURCE_SECRET", json.dumps(out))
        self.assertNotIn("NATIVE_SECRET", json.dumps(out))

    def test_caller_shapes_are_metadata_only(self):
        examples = (("a", "single_lowercase_ascii_letter"),
                    ("Z", "single_uppercase_ascii_letter"),
                    ("12", "ascii_decimal"),
                    ("*", "single_symbol"),
                    ("SECRET_PRIVATE_CALLER", "other_unreviewed_literal"))
        for label, shape in examples:
            with self.subTest(shape=shape):
                attrs = {}
                notes, _ = collect_usfx_numbered_notes(
                    source(f'<f caller="{label}">same</f>'),
                    MAP, attributes_out=attrs)
                audit = NoteAudit(notes, source_attributes=attrs)
                audit.inspect("Alpha.1.1", b'<note>same</note>')
                receipt = audit.finish()["note_annotation_structure_diagnostic"]
                counts = receipt["classifications"]
                self.assertEqual(counts["source_caller_shape_" + shape], 1)
                self.assertEqual(counts["native_note_n_absent"], 1)
                self.assertNotIn(label, json.dumps(receipt))

    def test_source_machine_target_disappeared_in_native(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(
            source('<x><ref tgt="AUTHORED_SECRET">cross</ref></x>'),
            MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note type="crossReference">cross</note>')
        out = audit.finish()["note_annotation_structure_diagnostic"]
        self.assertEqual(
            out["classifications"]["authored_explicit_target_absent_in_native"], 1)
        self.assertNotIn("AUTHORED_SECRET", json.dumps(out))

    def test_generated_annotate_ref_not_counted_as_crossreference_target(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(
            source('<f>same</f>'), MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note><reference type="annotateRef" '
                      b'osisRef="Gen.1.1">1:1</reference>same</note>')
        out = audit.finish()["note_annotation_structure_diagnostic"]
        self.assertEqual(
            out["classifications"]["neither_side_has_explicit_machine_target"], 1)

    def test_note_count_mismatch_blocks_attribute_pairing(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(
            source('<f>one</f><f>two</f>'), MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note>one</note>')
        out = audit.finish()["note_annotation_structure_diagnostic"]
        self.assertEqual(out["classifications"]["note_count_alignment_unavailable"], 1)
        self.assertNotIn("cross_reference_class_agrees", out["classifications"])

    def test_annotation_inventory_cannot_disagree_with_source_notes(self):
        with self.assertRaises(NoteEvidenceError):
            NoteAudit({"Alpha.1.1": [("f", "word")]}, source_attributes={})

    def test_malformed_native_note_has_no_false_structural_evidence(self):
        attrs = {}
        notes, _ = collect_usfx_numbered_notes(
            source('<x>same</x>'), MAP, attributes_out=attrs)
        audit = NoteAudit(notes, source_attributes=attrs)
        audit.inspect("Alpha.1.1", b'<note type="crossReference">broken')
        result = audit.finish()
        self.assertEqual(
            result["classifications"]["native_fragment_unparseable_notes_unverified"], 1)
        self.assertEqual(
            result["note_annotation_structure_diagnostic"]["classifications"], {})

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
