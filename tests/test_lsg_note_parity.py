"""Offline, synthetic checks for fail-closed USFX-to-OSIS note auditing."""
import sys
import unittest
from pathlib import Path

from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_note_parity import audit_notes

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def example(*, source_note=None, target_note=None, before_word=False):
    source_note=source_note or (
        '<x caller="a"><xo>1.1</xo><xt>Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</xt></x>')
    target_note=target_note or (
        '<note type="crossReference" n="a">'
        '<reference type="annotateRef" subType="x-origin">1.1</reference>'
        '<reference>Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</reference></note>')
    source=(
        '<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
        f'Alpha <w s="H123">Word</w>{source_note}<ve id="1"/></p>'
        '</book><book id="EXO"><c id="1"/><v id="1"/>Exo<ve id="1"/>'
        '</book></usfx>')
    converted=(
        f'<osis xmlns="{NS}"><osisText>'
        '<div type="book" osisID="Gen"><chapter osisID="Gen.1">'
        '<p><verse sID="Gen.1.1" osisID="Gen.1.1"/>'
        + (target_note if before_word else "") +
        'Alpha <w lemma="strong:H123">Word</w>'
        + ("" if before_word else target_note) +
        '<verse eID="Gen.1.1"/></p></chapter></div>'
        '<div type="book" osisID="Exod"><chapter osisID="Exod.1">'
        '<verse sID="Exod.1.1" osisID="Exod.1.1"/>Exo'
        '<verse eID="Exod.1.1"/></chapter></div>'
        '</osisText></osis>')
    return (etree.fromstring(source.encode()),
            etree.fromstring(converted.encode()))


def run(**kwargs):
    source, candidate=example(**kwargs)
    return audit_notes(source,candidate,{"GEN":"Gen","EXO":"Exod"})


class NoteParityTests(unittest.TestCase):
    def test_equivalent_notes_verify_content_reference_caller_and_anchor(self):
        result=run()
        self.assertEqual(result["source_note_count"],1)
        self.assertEqual(result["candidate_note_count"],1)
        self.assertEqual(result["matching_note_component_text"],1)
        self.assertEqual(result["matching_note_word_anchors"],1)
        self.assertEqual(result["matching_note_caller_markers"],1)
        self.assertTrue(result["all_note_contents_metadata_and_positions_verified"])
        self.assertTrue(result["textual_target_references_verified"])
        self.assertNotIn("SPECIAL_NOTE_TEXT_SECRET",repr(result))

    def test_changed_target_text_fails_without_count_difference(self):
        altered=(
            '<note type="crossReference" n="a">'
            '<reference type="annotateRef" subType="x-origin">1.1</reference>'
            '<reference>Ps 1:2. SPECIAL_NOTE_TEXT_SECRET</reference></note>')
        result=run(target_note=altered)
        self.assertEqual(result["source_note_count"],result["candidate_note_count"])
        self.assertEqual(result["matching_note_component_text"],0)
        self.assertFalse(result["textual_target_references_verified"])
        self.assertIn("component_text",result["first_mismatches"][0]["failed_checks"])

    def test_moved_note_anchor_detected_despite_same_verse(self):
        result=run(before_word=True)
        self.assertEqual(result["matching_note_component_text"],1)
        self.assertEqual(result["matching_note_word_anchors"],0)
        self.assertFalse(result["all_note_contents_metadata_and_positions_verified"])

    def test_caller_glyph_loss_is_not_silently_approved(self):
        target=(
            '<note type="crossReference">'
            '<reference type="annotateRef" subType="x-origin">1.1</reference>'
            '<reference>Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</reference></note>')
        result=run(target_note=target)
        self.assertEqual(result["matching_note_component_text"],1)
        self.assertEqual(result["matching_note_caller_markers"],0)
        self.assertFalse(result["all_note_contents_metadata_and_positions_verified"])

    def test_unknown_source_nested_marker_blocks_approval(self):
        source=(
            '<x caller="a"><xo>1.1</xo><xk>keyword</xk>'
            '<xt>Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</xt></x>')
        result=run(source_note=source)
        self.assertFalse(result["all_note_contents_metadata_and_positions_verified"])
        self.assertGreater(result["unsupported_note_substructures"],0)
        self.assertNotIn("keyword",repr(result))
        self.assertIn("xk",repr(result["first_mismatches"]))

    def test_machine_link_is_compared_when_source_provides_one(self):
        source=(
            '<x caller="a"><xo>1.1</xo>'
            '<xt link-ref="Ps.1.1">Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</xt></x>')
        candidate=(
            '<note type="crossReference" n="a">'
            '<reference type="annotateRef" subType="x-origin">1.1</reference>'
            '<reference osisRef="Ps.1.1">Ps 1:1. SPECIAL_NOTE_TEXT_SECRET</reference>'
            '</note>')
        result=run(source_note=source,target_note=candidate)
        self.assertEqual(result["matching_explicit_machine_links"],1)
        self.assertEqual(result["source_explicit_link_count"],1)
        self.assertEqual(result["candidate_explicit_link_count"],1)
        self.assertTrue(result["all_note_contents_metadata_and_positions_verified"])
        candidate=candidate.replace('osisRef="Ps.1.1"','osisRef="Ps.1.2"')
        result=run(source_note=source,target_note=candidate)
        self.assertEqual(result["matching_note_component_text"],1)
        self.assertEqual(result["matching_explicit_machine_links"],0)
        self.assertFalse(result["all_note_contents_metadata_and_positions_verified"])

    def test_extra_out_of_verse_note_fails_closed(self):
        source,candidate=example()
        inserted=etree.SubElement(candidate.find(f".//{NS}chapter"),NS+"note")
        inserted.set("type","crossReference")
        result=audit_notes(source,candidate,{"GEN":"Gen","EXO":"Exod"})
        self.assertEqual(result["candidate_notes_outside_verses"],1)
        self.assertFalse(result["all_note_contents_metadata_and_positions_verified"])


if __name__=="__main__":
    unittest.main()
