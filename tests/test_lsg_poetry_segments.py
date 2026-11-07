"""Synthetic fixtures for poetry-line attribution across verse milestones."""
from pathlib import Path
import sys
import unittest

from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_poetry_segments import audit_segments

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def audit(src_lines, dst_lines, *, verses=(1,2)):
    source=(f'<usfx><book id="GEN"><c id="1"/>{src_lines}</book></usfx>')
    target=(f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
            f'<chapter osisID="Gen.1">{dst_lines}</chapter></div></osisText></osis>')
    return audit_segments(etree.fromstring(source.encode()),
                          etree.fromstring(target.encode()),{"GEN":"Gen"},
                          [("GEN",1,v) for v in verses])


class PoetrySegmentOwnershipTests(unittest.TestCase):
    def test_markers_inside_a_line_do_not_count_it_against_old_verse(self):
        src=('<q sfm="q1"><v id="1"/>First<ve id="1"/></q>'
             '<q sfm="q1"><v id="2"/>Second<ve id="2"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>First</l>'
             '<l level="1"><verse eID="Gen.1.1"/>'
             '<verse sID="Gen.1.2"/>Second</l></lg>'
             '<verse eID="Gen.1.2"/>')
        result=audit(src,dst)
        self.assertEqual(result["matching_verse_line_counts_with_text_ownership"],2)
        self.assertEqual(result["matching_verse_line_text_sequences_ignoring_whitespace"],2)
        self.assertEqual(result["matching_verse_line_indentation_levels"],2)
        self.assertEqual(result["line_delta_histogram"],{0:2})
        self.assertTrue(result["all_poetry_segments_and_levels_verified"])
        self.assertFalse(result["full_editorial_poetry_layout_verified"])

    def test_one_line_can_legitimately_contain_parts_of_two_verses(self):
        src=('<q sfm="q1"><v id="1"/>First<ve id="1"/>'
             '<v id="2"/>Second<ve id="2"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>First'
             '<verse eID="Gen.1.1"/><verse sID="Gen.1.2"/>Second'
             '<verse eID="Gen.1.2"/></l></lg>')
        result=audit(src,dst)
        self.assertEqual(result["matching_verse_line_counts_with_text_ownership"],2)
        self.assertEqual(result["source_poetry"]["line_nodes_spanning_multiple_verses"],1)
        self.assertEqual(result["candidate_poetry"]["line_nodes_spanning_multiple_verses"],1)
        self.assertTrue(result["all_poetry_segments_and_levels_verified"])

    def test_verses_without_any_poetry_do_not_break_audit(self):
        src=('<q sfm="q1"><v id="1"/>One<ve id="1"/></q>'
             '<p><v id="2"/>Plain prose<ve id="2"/></p>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>One'
             '<verse eID="Gen.1.1"/></l></lg>'
             '<p><verse sID="Gen.1.2"/>Plain prose'
             '<verse eID="Gen.1.2"/></p>')
        result=audit(src,dst)
        self.assertEqual(result["matching_verse_line_counts_with_text_ownership"],2)
        self.assertEqual(result["matching_verse_line_text_sequences_ignoring_whitespace"],2)
        self.assertEqual(result["matching_verse_line_indentation_levels"],2)

    def test_actual_new_line_break_is_not_dismissed(self):
        src=('<q sfm="q1"><v id="1"/>FirstSecond<ve id="1"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>First</l>'
             '<l level="1">Second<verse eID="Gen.1.1"/></l></lg>')
        result=audit(src,dst,verses=(1,))
        self.assertEqual(result["matching_verse_line_counts_with_text_ownership"],0)
        self.assertFalse(result["all_poetry_segments_and_levels_verified"])
        self.assertEqual(result["line_delta_histogram"],{1:1})

    def test_indentation_change_fails_even_when_text_equal(self):
        src=('<q sfm="q2"><v id="1"/>First<ve id="1"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>First'
             '<verse eID="Gen.1.1"/></l></lg>')
        result=audit(src,dst,verses=(1,))
        self.assertEqual(result["matching_verse_line_text_sequences_ignoring_whitespace"],1)
        self.assertEqual(result["matching_verse_line_indentation_levels"],0)
        self.assertFalse(result["all_poetry_segments_and_levels_verified"])

    def test_changed_text_detected_without_leaking_text(self):
        src=('<q sfm="q1"><v id="1"/>SECRET_POETIC_SOURCE<ve id="1"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>Other'
             '<verse eID="Gen.1.1"/></l></lg>')
        result=audit(src,dst,verses=(1,))
        self.assertEqual(result["matching_verse_line_text_sequences_ignoring_whitespace"],0)
        self.assertNotIn("SECRET_POETIC_SOURCE",repr(result))
        self.assertFalse(result["all_poetry_segments_and_levels_verified"])

    def test_note_text_does_not_contaminate_poetry(self):
        src=('<q sfm="q1"><v id="1"/>First'
             '<x><xt>PRIVATE_NOTE</xt></x><ve id="1"/></q>')
        dst=('<lg><l level="1"><verse sID="Gen.1.1"/>First'
             '<note>PRIVATE_NOTE</note><verse eID="Gen.1.1"/></l></lg>')
        result=audit(src,dst,verses=(1,))
        self.assertEqual(result["matching_verse_line_text_sequences_ignoring_whitespace"],1)
        self.assertNotIn("PRIVATE_NOTE",repr(result))


if __name__=="__main__":
    unittest.main()
