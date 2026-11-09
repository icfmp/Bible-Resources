"""Stock SWORD semantic layout-boundary regression tests (synthetic text only)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_layout_boundaries import compare_compiled_layout_boundaries
from pilot_preflight import PilotError


class StockLayoutBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)/"source.osis.xml"
        self.source.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText><div type="book" osisID="Gen">
<chapter sID="Gen.1"/>
<title>heading</title>
<p><verse sID="Gen.1.1"/><w>one</w>
<lg><q><w>two</w></q></lg>
<verse eID="Gen.1.1"/></p>
</div></osisText></osis>''',encoding="utf-8")
        self.plan=[
            ("Genesis 0:0","Gen","1"),
            ("Genesis 1:0","Gen","1"),
            ("Genesis 1:1","Gen","0"),
        ]
        self.rows=[
            "Gen\tGenesis 0:0\t0\t+title:0,-title:0",
            "Gen\tGenesis 1:0\t0\t+p:0",
            "Gen\tGenesis 1:1\t2\t+lg:1,+q:1,-q:2,-lg:2,-p:2",
        ]

    def test_regular_source_containers_match_compiled_milestones(self):
        report=compare_compiled_layout_boundaries(
            self.source,self.plan,self.rows)
        self.assertEqual(report["status"],
                         "compiled_book_global_layout_boundaries_verified")
        self.assertEqual(report["books_with_exact_full_boundary_order"],1)
        self.assertEqual(report["books_with_exact_all_opening_events"],1)
        self.assertEqual(report["books_with_exact_all_closing_events"],1)
        self.assertEqual(report["source_global_boundary_counts"]["-p"],1)
        self.assertFalse(report["frontend_rendering_verified"])

    def test_omitted_paragraph_end_is_reported_even_with_all_starts(self):
        altered=list(self.rows)
        altered[2]="Gen\tGenesis 1:1\t2\t+lg:1,+q:1,-q:2,-lg:2"
        report=compare_compiled_layout_boundaries(
            self.source,self.plan,altered)
        self.assertEqual(report["status"],"compiled_layout_boundaries_need_review")
        self.assertEqual(report["books_with_exact_all_opening_events"],1)
        self.assertEqual(report["books_with_exact_all_closing_events"],0)
        self.assertEqual(report["source_global_boundary_counts"]["-p"],1)
        self.assertEqual(report["compiled_global_boundary_counts"].get("-p",0),0)
        self.assertNotIn("heading",str(report))

    def test_same_closing_counts_but_shifted_end_blocks(self):
        altered=list(self.rows)
        altered[2]="Gen\tGenesis 1:1\t2\t+lg:1,+q:1,-q:1,-lg:2,-p:2"
        report=compare_compiled_layout_boundaries(
            self.source,self.plan,altered)
        self.assertEqual(report["status"],"compiled_layout_boundaries_need_review")
        self.assertEqual(report["books_with_exact_all_opening_events"],1)
        self.assertEqual(report["books_with_exact_all_closing_events"],0)
        self.assertEqual(report["compiled_global_boundary_counts"]["-q"],1)
        self.assertEqual(report["source_global_boundary_counts"]["-q"],1)

    def test_same_start_and_end_offsets_but_swapped_nesting_blocks(self):
        altered=list(self.rows)
        altered[2]="Gen\tGenesis 1:1\t2\t+lg:1,+q:1,-lg:2,-q:2,-p:2"
        report=compare_compiled_layout_boundaries(
            self.source,self.plan,altered)
        self.assertEqual(report["status"],"compiled_layout_boundaries_need_review")
        self.assertEqual(report["books_with_exact_all_opening_events"],1)
        self.assertEqual(report["books_with_exact_all_closing_events"],0)

    def test_source_paragraph_milestone_end_equivalent_to_container(self):
        source=self.source.read_text(encoding="utf-8")
        self.source.write_text(
            source.replace('<p><verse sID="Gen.1.1"/>',
                           '<div type="x-p" sID="para-1"/><verse sID="Gen.1.1"/>')
                  .replace('</p>','<div type="x-p" eID="para-1"/>'),
            encoding="utf-8")
        report=compare_compiled_layout_boundaries(
            self.source,self.plan,self.rows)
        self.assertEqual(report["status"],
                         "compiled_book_global_layout_boundaries_verified")

    def test_reader_key_wrong_order_or_out_of_bounds_fails(self):
        for altered in (
            self.rows[:2],
            [self.rows[1],self.rows[0],self.rows[2]],
            self.rows[:2]+["Gen\tGenesis 1:1\t2\t-p:3"],
            self.rows[:2]+["Gen\tGenesis 1:1\t2\t-q:NaN"],
            self.rows[:2]+["Gen\tGenesis 1:1\t2\tunknown:1"],
        ):
            with self.subTest(rows=altered),self.assertRaises(PilotError):
                compare_compiled_layout_boundaries(
                    self.source,self.plan,altered)


if __name__=="__main__":
    unittest.main()
