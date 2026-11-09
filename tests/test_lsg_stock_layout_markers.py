"""Synthetic, text-free SWORD compiled layout marker parity fixtures."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_layout_markers import compare_compiled_layout_marker_rows
from pilot_preflight import PilotError


class LayoutMarkupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/"structure.osis.xml"
        self.source.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText><div type="book" osisID="Gen"><chapter sID="Gen.1"/>
<title>heading</title><p><verse sID="Gen.1.1"/>
<lg><q>poetry</q></lg><verse eID="Gen.1.1"/></p></div></osisText></osis>''',
            encoding="utf-8")
        self.plan=[
            ("Genesis 0:0","Gen","1"),
            ("Genesis 1:0","Gen","1"),
            ("Genesis 1:1","Gen","0"),
        ]
        self.rows=[
            "Gen\tGenesis 0:0\t0\t0\t0\t0\t0\t0\t0\t0",
            "Gen\tGenesis 1:0\t0\t0\t1\t0\t0\t0\t0\t0",
            "Gen\tGenesis 1:1\t1\t0\t0\t0\t1\t0\t1\t0",
        ]

    def test_all_layout_starts_match_even_in_verse_zero_intro(self):
        report=compare_compiled_layout_marker_rows(
            self.source,self.plan,self.rows)
        self.assertEqual(report["status"],
                         "compiled_source_layout_start_marker_counts_match")
        self.assertEqual(report["books_matching_all_logical_layout_starts"],1)
        self.assertEqual(report["source_global_layout_marker_counts"]
                         ["title_starts"],1)
        self.assertEqual(report["compiled_global_layout_marker_counts"]
                         ["title_starts"],1)
        self.assertFalse(report["frontend_visual_rendering_verified"])

    def test_missing_paragraph_start_is_diagnosed_without_approval(self):
        altered=list(self.rows)
        altered[2]="Gen\tGenesis 1:1\t0\t0\t0\t0\t1\t0\t1\t0"
        report=compare_compiled_layout_marker_rows(
            self.source,self.plan,altered)
        self.assertEqual(report["status"],
                         "compiled_source_layout_start_markers_need_review")
        self.assertEqual(report["books_matching_all_logical_layout_starts"],0)
        self.assertEqual(report["first_books_with_layout_marker_differences"][0]
                         ["book"],"Gen")

    def test_extra_compiler_milestones_are_separately_reported(self):
        altered=list(self.rows)
        altered[2]="Gen\tGenesis 1:1\t1\t1\t0\t0\t1\t0\t1\t0"
        report=compare_compiled_layout_marker_rows(
            self.source,self.plan,altered)
        self.assertEqual(report["books_matching_all_logical_layout_starts"],1)
        self.assertEqual(report["books_matching_all_explicit_end_milestones"],0)
        self.assertEqual(report["compiled_global_layout_marker_counts"]
                         ["p_ends"],1)

    def test_source_paragraph_div_milestones_are_logically_paragraphs(self):
        original=self.source.read_text(encoding="utf-8")
        source=original.replace(
            '<p><verse sID="Gen.1.1"/>',
            '<div type="x-p" sID="p1"/><verse sID="Gen.1.1"/>'
        ).replace('</p></div></osisText>',
                  '<div type="x-p" eID="p1"/></div></osisText>')
        self.assertNotEqual(source,original)
        self.source.write_text(source,encoding="utf-8")
        compiled=list(self.rows)
        compiled[2]="Gen\tGenesis 1:1\t1\t1\t0\t0\t1\t0\t1\t0"
        report=compare_compiled_layout_marker_rows(
            self.source,self.plan,compiled)
        self.assertEqual(report["status"],
                         "compiled_source_layout_start_marker_counts_match")
        self.assertEqual(report["books_matching_all_explicit_end_milestones"],1)
        self.assertTrue(report["sword_x_p_paragraph_milestones_normalized"])

    def test_missing_or_reordered_rows_fail(self):
        for rows in (self.rows[:2], self.rows[::-1],
                     ["Gen\tGenesis 0:0\tbad\t0\t0\t0\t0\t0\t0\t0"]
                     +self.rows[1:]):
            with self.subTest(rows=rows),self.assertRaises(PilotError):
                compare_compiled_layout_marker_rows(self.source,self.plan,rows)


if __name__ == "__main__":
    unittest.main()
