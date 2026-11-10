"""USFX source layout starts vs original native SWORD: no silent repositioning."""
import sys
from pathlib import Path
import unittest

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_native_layout_anchors import (
    SourceLayoutError, source_usfx_layout_start_anchors, compare_start_anchors)
from native_sword_markup_census import NativeMarkupCensus
from source_native_maintext_probe import native_raw_main_text

MAPPING=[("GEN", "Gen")]
AUTHORIAL=(b'<usfx><book id="GEN"><c id="1"/>'
           b'<p><v id="1"/>PRIVATE SCRIPTURE A</p>'
           b'<q><v id="2"/>PRIVATE SCRIPTURE B</q>'
           b'<p><v id="3"/>PRIVATE SCRIPTURE C</p>'
           b'</book></usfx>')


def stock(shift_poetry=False):
    census=NativeMarkupCensus()
    native_raw_main_text(
        b'<div type="paragraph">COMPILED A</div>',
        markup_census=census,reference="Gen.1.1")
    native_raw_main_text(
        b'COMPILED B' if shift_poetry else b'<lg><l>COMPILED B</l></lg>',
        markup_census=census,reference="Gen.1.2")
    native_raw_main_text(
        b'<div type="paragraph"><l>COMPILED C</l></div>'
        if shift_poetry else b'<div type="paragraph">COMPILED C</div>',
        markup_census=census,reference="Gen.1.3")
    return census


class StartAnchorTests(unittest.TestCase):
    def test_source_events_are_anchored_to_next_verse_in_document_order(self):
        source=source_usfx_layout_start_anchors(AUTHORIAL,MAPPING)
        self.assertEqual(source["source_start_event_counts"]["paragraph_start_events"],2)
        self.assertEqual(source["source_start_event_counts"]["poetry_start_events"],1)
        self.assertEqual(source["source_start_ref_sets_private"]["paragraph"],
                         {"Gen.1.1","Gen.1.3"})
        self.assertEqual(source["source_start_ref_sets_private"]["poetry"],{"Gen.1.2"})
        self.assertTrue(source["source_start_anchors_are_next_verse_estimates"])

    def test_coarse_native_coverage_not_editorial_approval(self):
        source=source_usfx_layout_start_anchors(AUTHORIAL,MAPPING)
        witness=compare_start_anchors(source,stock())
        self.assertEqual(witness["source_paragraph_next_verse_ref_count"],2)
        self.assertEqual(witness["source_poetry_next_verse_ref_count"],1)
        self.assertEqual(witness["source_paragraph_next_verse_refs_with_native_div"],2)
        self.assertEqual(witness["source_poetry_next_verse_refs_with_native_line"],1)
        self.assertEqual(witness["source_poetry_next_verse_refs_without_native_line"],0)
        self.assertFalse(witness["direct_event_or_exact_position_equivalence_verified"])
        self.assertFalse(witness["editorial_layout_or_publication_approved"])
        self.assertNotIn("PRIVATE",str(witness))
        self.assertNotIn("COMPILED",str(witness))

    def test_moved_poetry_line_is_reported_by_source_ref(self):
        source=source_usfx_layout_start_anchors(AUTHORIAL,MAPPING)
        witness=compare_start_anchors(source,stock(shift_poetry=True))
        self.assertEqual(witness["source_poetry_next_verse_refs_without_native_line"],1)
        self.assertEqual(witness["sample_poetry_next_ref_without_native_line"],["Gen.1.2"])

    def test_last_book_event_without_next_verse_not_silently_dropped(self):
        xml=AUTHORIAL.replace(b'</book>', b'<p/>PRIVATE END</book>')
        src=source_usfx_layout_start_anchors(xml,MAPPING)
        self.assertEqual(src["source_unanchored_end_events"], {
            "paragraph_without_later_numbered_verse":1})
        self.assertIn("paragraph_start_events_after_last_verse",
                      src["source_start_event_counts"])

    def test_source_duplicate_verse_is_not_usable_for_anchors(self):
        bad=AUTHORIAL.replace(b'v id="3"', b'v id="2"')
        with self.assertRaises(SourceLayoutError):
            source_usfx_layout_start_anchors(bad,MAPPING)

    def test_native_type_values_are_categorized_without_leaking(self):
        census=NativeMarkupCensus()
        native_raw_main_text(b'<div type="PRIVATE_IDENTIFIER" subType="SECRET">'
                             b'PRIVATE CONTENT</div>',markup_census=census,
                             reference="Gen.1.1")
        report=census.finish()
        self.assertEqual(report["native_structure_style_counts_allowlisted"][
            "div:other_unreviewed_style"],1)
        self.assertEqual(report["unrecognized_native_structural_style_occurrences"],1)
        self.assertNotIn("PRIVATE",str(report))
        self.assertNotIn("SECRET",str(report))

    def test_structural_marker_positions_and_milestone_types(self):
        c=NativeMarkupCensus()
        native_raw_main_text(b'<div type="paragraph" sID="a"/>alpha '
                             b'<div type="paragraph" eID="a"/> beta '
                             b'<l>gamma</l><milestone type="x-q1"/>',
                             markup_census=c,reference="Gen.1.1")
        r=c.finish()
        self.assertEqual(r["native_structure_endpoint_counts"]["div:open_sID"],1)
        self.assertEqual(r["native_structure_endpoint_counts"]["div:close_eID"],1)
        self.assertEqual(r["native_structure_style_counts_allowlisted"]["div:paragraph"],2)
        self.assertGreater(r["native_structure_relative_word_position_counts"][
            "div:close_eID:inside_verse"],0)
        self.assertFalse(r["source_to_compiled_structure_fidelity_verified"])


if __name__=="__main__":
    unittest.main()
