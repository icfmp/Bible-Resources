"""Synthetic, text-free metadata regressions for the poetry segmentation audit."""
from pathlib import Path
import sys
import unittest
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_poetry_parity import audit_poetry

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def analyze(source_poetry: str, generated_poetry: str):
    raw=(
        '<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
        +source_poetry+'<ve id="1"/></p></book></usfx>')
    generated=(
        f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
        '<chapter osisID="Gen.1"><p><verse sID="Gen.1.1"/>'
        +generated_poetry+'<verse eID="Gen.1.1"/></p>'
        '</chapter></div></osisText></osis>')
    return audit_poetry(etree.fromstring(raw.encode()),
                        etree.fromstring(generated.encode()),
                        {"GEN":"Gen"},[("GEN",1,1)])


class PoetryParityTests(unittest.TestCase):
    def test_line_open_before_verse_start_is_counted_in_global_inventory(self):
        raw=('<usfx><book id="GEN"><c id="1"/>'
             '<q level="1"><v id="1"/>Alpha<ve id="1"/></q>'
             '</book></usfx>')
        xml=(f'<osis xmlns="{NS}"><osisText>'
             '<div type="book" osisID="Gen"><chapter osisID="Gen.1">'
             '<lg><l level="1"><verse sID="Gen.1.1"/>Alpha'
             '<verse eID="Gen.1.1"/></l></lg></chapter></div>'
             '</osisText></osis>')
        report=audit_poetry(etree.fromstring(raw.encode()),
                            etree.fromstring(xml.encode()),
                            {"GEN":"Gen"},[("GEN",1,1)])
        self.assertEqual(report["all_original_usfx_q_elements"],1)
        self.assertEqual(report["all_candidate_osis_l_elements"],1)
        self.assertEqual(report["source_q_elements_with_nested_verse_start"],1)
        self.assertEqual(report["source_q_elements_not_counted_in_active_verses"],1)
        self.assertEqual(report["candidate_l_elements_not_counted_in_active_verses"],1)

    def test_equal_source_and_candidate_lines(self):
        report=analyze('<q level="1">Alpha</q>',
                       '<lg><l level="1">Alpha</l></lg>')
        self.assertEqual(report["matching_per_verse_line_counts"],1)
        self.assertEqual(report["source_poetry_line_count"],1)
        self.assertEqual(report["candidate_poetry_line_count"],1)
        self.assertEqual(report["per_verse_line_count_delta_histogram"],{0:1})
        self.assertFalse(report["all_poetry_layout_verified"])

    def test_extra_empty_candidate_line_is_reported_not_waived(self):
        report=analyze('<q level="1">Alpha</q>',
                       '<lg><l level="1">Alpha</l><l level="1"/></lg>')
        self.assertEqual(report["matching_per_verse_line_counts"],0)
        self.assertEqual(report["candidate_empty_poetry_line_count"],1)
        self.assertEqual(report["per_verse_line_count_delta_histogram"],{1:1})
        self.assertEqual(report["mismatch_classifications"],
                         {"additional_empty_candidate_lines_present":1})
        self.assertFalse(report["all_poetry_line_counts_verified"])
        self.assertNotIn("Alpha",repr(report))

    def test_extra_populated_line_is_not_dismissed_as_empty(self):
        report=analyze('<q level="1">AlphaBeta</q>',
                       '<lg><l level="1">Alpha</l><l level="2">Beta</l></lg>')
        self.assertEqual(report["mismatch_classifications"],
                         {"additional_populated_candidate_line_or_split":1})
        self.assertEqual(report["first_mismatches"][0]["candidate_levels"],
                         ["1","2"])
        self.assertEqual(report["first_mismatches"][0]["source_levels"],["1"])
        self.assertFalse(report["all_poetry_layout_verified"])

    def test_missing_source_line_must_block(self):
        report=analyze('<q level="1">Alpha</q><q level="2">Beta</q>',
                       '<lg><l level="1">AlphaBeta</l></lg>')
        self.assertEqual(report["per_verse_line_count_delta_histogram"],{-1:1})
        self.assertFalse(report["all_poetry_line_counts_verified"])

    def test_note_text_is_not_counted_as_poetry_text(self):
        report=analyze('<q level="1"><x><xt>Secret source note</xt></x></q>',
                       '<lg><l level="1"><note>Secret source note</note></l></lg>')
        self.assertEqual(report["source_empty_poetry_line_count"],1)
        self.assertEqual(report["candidate_empty_poetry_line_count"],1)
        self.assertNotIn("Secret source note",repr(report))

    def test_embedded_verse_markers_are_explicitly_flagged(self):
        original=(
            '<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
            '<q level="1">Alpha<ve id="1"/></q></p></book></usfx>')
        converted=(
            f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
            '<chapter osisID="Gen.1"><verse sID="Gen.1.1"/>'
            '<lg><l level="1">Alpha<verse eID="Gen.1.1"/></l></lg>'
            '</chapter></div></osisText></osis>')
        result=audit_poetry(etree.fromstring(original.encode()),
                            etree.fromstring(converted.encode()),
                            {"GEN":"Gen"},[("GEN",1,1)])
        self.assertEqual(result["matching_per_verse_line_counts"],1)
        self.assertFalse(result["all_poetry_layout_verified"])


if __name__=="__main__":
    unittest.main()
